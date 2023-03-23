import json
from collections import OrderedDict
import ipaddr
from django.http import JsonResponse

from netaddr import iter_iprange
from rest_framework import serializers, pagination
from django.utils.translation import gettext_lazy as _
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import ListAPIView, get_object_or_404, RetrieveAPIView
from rest_framework.permissions import DjangoModelPermissions
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param, remove_query_param
from rest_framework.views import APIView
from .models import Subnet, IpAddress, TagsModel
from .serializers import HostsResponseSerializer, TagsModelSerializer
from utils.ipam_utils import IpAmForNetwork


class HostsResponse(object):
    def __init__(self, address, used, tag, subnet, lastOnlineTime, description):
        self.address = address
        self.used = used
        self.tag = tag
        self.subnet = subnet
        self.lastOnlineTime = lastOnlineTime
        self.description = description


class HostsSet:
    # Needed for DjangoModelPermissions to check the right model
    model = Subnet

    def __init__(self, subnet, start=0, stop=None):
        self.start = start
        self.stop = stop
        self.subnet = subnet
        self.network = int(self.subnet.subnet.network_address)
        self.used_set = subnet.ipaddress_set.all()

    def __getitem__(self, i):
        if isinstance(i, slice):
            start = i.start
            stop = i.stop
            if start is None:  # pragma: no cover
                start = 0
            if stop is None:  # pragma: no cover
                stop = self.count()
            else:
                stop = min(stop, self.count())
            return HostsSet(self.subnet, self.start + start, self.start + stop)
        if i >= self.count():
            raise IndexError
        # Host starts from next address
        host = self.subnet.subnet._address_class(self.network + 1 + i + self.start)
        # print()
        # In case of single hosts ie subnet/32 & /128
        if self.subnet.subnet.prefixlen in [32, 128]:
            host = host - 1
        used = self.used_set.filter(ip_address=str(host)).exists()
        tag = 1
        host_instance = self.used_set.filter(ip_address=str(host)).first()
        if used:
            tag = host_instance.tag
        description = ''
        lastOnlineTime = ''
        # bgbu = []
        if host_instance:
            description = host_instance.description
            lastOnlineTime = host_instance.lastOnlineTime
            # bgbu = [i['name'] for i in list(host_instance.bgbu.all().values())]
        return HostsResponse(str(host), used, tag, self.subnet, lastOnlineTime, description)

    def count(self):
        if self.stop is not None:
            return self.stop - self.start
        broadcast = int(self.subnet.subnet.broadcast_address)
        # IPV4
        if self.subnet.subnet.version == 4:
            # Networks with a mask of 32 will return a list
            # containing the single host address
            if self.subnet.subnet.prefixlen == 32:
                return 1
            # Other than subnet /32, exclude broadcast
            return broadcast - self.network - 1
        # IPV6
        else:
            # Subnet/128 only contains single host address
            if self.subnet.subnet.prefixlen == 128:
                return 1
            return broadcast - self.network

    def __len__(self):
        return self.count()

    def index_of(self, address):
        index = int(self.subnet.subnet._address_class(address)) - self.network - 1
        if index < 0 or index >= self.count():  # pragma: no cover
            raise serializers.ValidationError({'detail': _('Invalid Address')})
        return index


# 地址列表分页及数据格式化方法
class HostsListPagination(pagination.BasePagination):
    limit = 256
    start_query_param = 'start'

    def paginate_queryset(self, queryset, request, view=None):
        self.count = queryset.count()
        self.queryset = queryset
        self.request = request
        self.offset = self.get_offset(request)
        return list(queryset[self.offset: self.offset + self.limit])  # noqa

    def get_paginated_response(self, data):
        empty = round(len([i for i in data if i['tag'] == 1]) * 100 / len(data), 2)
        dist_and_used = round(len([i for i in data if i['tag'] == 2]) * 100 / len(data), 2)
        reserved = round(len([i for i in data if i['tag'] == 3]) * 100 / len(data), 2)
        not_dist_used = round(len([i for i in data if i['tag'] == 4]) * 100 / len(data), 2)
        dist_not_used = round(len([i for i in data if i['tag'] == 6]) * 100 / len(data), 2)
        self_empty = round(len([i for i in data if i['tag'] == 7]) * 100 / len(data), 2)
        return Response(
            OrderedDict(
                [
                    ('next', self.get_next_link()),
                    ('previous', self.get_previous_link()),
                    ('results', data),
                    ('code', 200),
                    # ('ip_used', [i for i in data]),
                    ('data', {'ip_used': data,
                              'sub_net': Subnet.objects.filter(subnet=data[0]['subnet']).values("name", "description",
                                                                                                "id"),
                              'subnet_used': {
                                  'freehosts': round(100 - dist_and_used - not_dist_used, 2),
                                  'freehosts_percent': round(100 - dist_and_used - not_dist_used, 2),
                                  'maxhosts': len(data),
                                  'used': round(dist_and_used + not_dist_used, 2),
                                  'Used_percent': round(dist_and_used + not_dist_used, 2),
                                  'empty_percent': empty,
                                  '自定义空闲_percent': self_empty,
                                  '已分配已使用_percent': dist_and_used,
                                  '保留_percent': reserved,
                                  '未分配已使用_percent': not_dist_used,
                                  '已分配未使用_percent': dist_not_used,
                              }}),
                ]
            )
        )

    def get_offset(self, request):
        try:
            return self.queryset.index_of(request.query_params[self.start_query_param])
        except (KeyError, ValueError):
            return 0

    def get_next_link(self):
        if self.offset + self.limit >= self.count:
            return None
        url = self.request.build_absolute_uri()
        offset = self.offset + self.limit
        return replace_query_param(
            url, self.start_query_param, self.queryset[offset].address
        )

    def get_previous_link(self):
        if self.offset <= 0:
            return None
        url = self.request.build_absolute_uri()
        if self.offset - self.limit <= 0:
            return remove_query_param(url, self.start_query_param)
        offset = self.offset - self.limit
        return replace_query_param(
            url, self.start_query_param, self.queryset[offset].address
        )


class ProtectedAPIMixin(object):
    authentication_classes = [SessionAuthentication]
    permission_classes = [DjangoModelPermissions]
    throttle_scope = 'ipam'


# 给admin后台使用，根据子网id获取地址信息
class SubnetHostsView(ProtectedAPIMixin, ListAPIView):
    subnet_model = Subnet
    queryset = Subnet.objects.none()
    serializer_class = HostsResponseSerializer
    pagination_class = HostsListPagination

    def get_queryset(self):
        super().get_queryset()
        subnet = get_object_or_404(self.subnet_model, pk=self.kwargs['subnet_id'])
        qs = HostsSet(subnet)
        return qs


# 获取可用地址
class AvailableIpView(RetrieveAPIView):
    subnet_model = Subnet
    queryset = IpAddress.objects.none()
    serializer_class = serializers.Serializer

    def get(self, request, *args, **kwargs):
        subnet = get_object_or_404(self.subnet_model, pk=self.kwargs['subnet_id'])
        return Response(subnet.get_next_available_ip())


# 根据网段ID获取对应下面IP地址信息
class SubnetAddressView(ListAPIView):
    subnet_model = Subnet
    queryset = Subnet.objects.none()
    serializer_class = HostsResponseSerializer
    pagination_class = HostsListPagination

    def get_queryset(self):
        super().get_queryset()
        subnet = get_object_or_404(self.subnet_model, pk=self.kwargs['subnet_id'])
        qs = HostsSet(subnet)
        return qs


# 获取subnet_tree
class IpAmSubnetTreeView(APIView):
    def get(self, request):
        get_params = request.GET.dict()
        if 'subnet' in get_params:
            ip_am_network = IpAmForNetwork()
            res_list = list(Subnet.objects.all().order_by('subnet').values())
            # 处理树结构返回前端
            tree = ip_am_network.generate_netops_tree(res_list)
            res = {'data': tree, 'code': 200, }
            return JsonResponse(res, safe=True)
        if "tags" in get_params:
            tag_choices = TagsModel.objects.all()
            tags = TagsModelSerializer(tag_choices, many=True)
            res = {'data': tags.data, 'code': 200, 'count': len(tags.data)}
            return JsonResponse(res, safe=True)


# 地址操作
class IpAmHandleView(APIView):
    permission_classes = ()
    authentication_classes = ()
    def post(self, request):
        update = request.POST.get('update')
        range_update = request.POST.get('range_update')
        delete = request.POST.get('delete')
        subnet_id = request.POST.get('subnet_id')
        description = request.POST.get('description')
        add_subnet = request.POST.get('add_subnet')
        add_description = request.POST.get('add_description')
        add_master_id = request.POST.get('add_master_id')
        room_group_name = request.POST.get('room_group_name')
        if update:
            update_list = json.loads(update)
            for update_info in update_list:
                IpAddress.objects.update_or_create(ip_address=update_info['ipaddr'], tag=update_info['tag'],
                                                   description=update_info['description'],
                                                   subnet_id=update_info['subnet_id'])
            res = {'message': '地址分配成功', 'code': 200, 'update_ip_list': [j['ipaddr'] for j in update_list]}
            return JsonResponse(res, safe=True)
        if range_update:
            range_data = json.loads(range_update)
            # print(range_data)
            start_ip = range_data['start_ip']
            end_ip = range_data['end_ip']
            description = range_data['description']
            subnet_id = range_data['subnet_id']
            update_ip_list = []
            for host_ip in iter_iprange(start_ip, end_ip):
                # print(host_ip)

                IpAddress.objects.update_or_create(ip_address=str(host_ip), tag=range_data['tag'],
                                                   description=description,
                                                   subnet_id=subnet_id)
                update_ip_list.append(str(host_ip))

            res = {'message': '地址批量分配成功', 'code': 200, 'update_ip_list': update_ip_list}
            return JsonResponse(res, safe=True)
        if delete:
            delete_ip_list = json.loads(delete)
            print(delete_ip_list)
            for delete_info in delete_ip_list:
                IpAddress.objects.filter(ip_address=delete_info['ipaddr']).delete()
            res = {'message': '地址回收成功', 'code': 200, 'delete_ip_list': [j['ipaddr'] for j in delete_ip_list]}
            return JsonResponse(res, safe=True)
        if description:
            Subnet.objects.filter(id=subnet_id).update(description=description)
            res = {'message': '网段描述更新成功', 'code': 200, }
            return JsonResponse(res, safe=True)
        if add_subnet:
            try:
                # print(add_master_id, type(add_master_id))
                master_subnet_id = Subnet.objects.filter(id=int(add_master_id)).first()
                add_kwargs = {
                    "name": add_subnet,
                    "mask": add_subnet.split("/")[1],
                    "subnet": add_subnet,
                    "description": add_description,
                    "master_subnet": master_subnet_id
                }
                subnet_list = [str(i.subnet) for i in Subnet.objects.all()]
                if add_master_id == "0":
                    add_kwargs.pop('master_subnet')
                    if add_subnet in subnet_list:
                        res = {'message': '新增网段失败,当前新增网段已经存在', 'code': 400, }
                    else:
                        Subnet.objects.update_or_create(**add_kwargs)
                        res = {'message': '新增网段成功', 'code': 200, }
                    return JsonResponse(res, safe=True)
                else:
                    master_subnet = Subnet.objects.get(id=add_master_id)
                    if str(master_subnet.subnet) == str(add_subnet):
                        res = {'message': '新增网段失败,请校验参数,不能新建跟父节点相同的子网段', 'code': 400, }
                        return JsonResponse(res, safe=True)
                    else:

                        master_subnet_detail = ipaddr.IPv4Network(str(master_subnet.subnet))
                        add_subnet_detail = ipaddr.IPv4Network(str(str(add_subnet)))
                        if add_subnet_detail in master_subnet_detail:
                            if add_subnet in subnet_list:
                                res = {'message': '新增网段失败,当前新增网段已经存在', 'code': 400, }
                            else:
                                Subnet.objects.update_or_create(**add_kwargs)
                                res = {'message': '新增网段成功', 'code': 200, }
                        else:
                            res = {'message': '新增网段失败,请校验网段归属', 'code': 400, }
                        return JsonResponse(res, safe=True)
                # print(add_kwargs)
                # 校验是否有归属关系

                # print(str(master_subnet.subnet))
                # print(str(add_subnet))
                # print(str(add_subnet) == str(add_subnet))
                # 判断是否和父节点一致
            except Exception as e:
                res = {'message': e, 'code': 400, }
                return JsonResponse(res, safe=True)
