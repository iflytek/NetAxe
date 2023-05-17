import json
import os
from collections import OrderedDict
from datetime import datetime, date
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from apps.topology.icon_manage import IconTree
from apps.topology.tasks import TopologyTask
from apps.topology.models import Topology
from .serializers import TopologySerializer
from utils.db.mongo_ops import MongoOps, MongoNetOps
from apps.api.tools.custom_viewset_base import CustomViewBase
from apps.api.tools.custom_pagination import LargeResultsSetPagination

# Create your views here.
# 设备二层接口表
interface_mongo = MongoOps(db='Automation', coll='layer2interface')

ICON_PATH = 'topology/img/'


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime("%Y-%m-%d")
        else:
            return json.JSONEncoder.default(self, obj)


# 拓扑清单
class TopologyViewSet(CustomViewBase):
    """
    处理  GET POST , 处理 /api/post/<pk>/ GET PUT PATCH DELETE
    """
    queryset = Topology.objects.all().order_by('-id')
    # queryset = TopologySerializer.setup_eager_loading(queryset)
    serializer_class = TopologySerializer
    # permission_classes = (permissions.IsAuthenticated,)
    # 配置搜索功能
    filter_backends = (DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter)
    filter_fields = '__all__'
    pagination_class = LargeResultsSetPagination


# 拓扑显示
class TopologyShow(APIView):
    # permission_classes = (IsAuthenticated,)
    permission_classes = ()
    authentication_classes = ()

    def get(self, request):
        get_param = request.GET.dict()
        if get_param.get('graph'):
            content = MongoNetOps.get_topology(get_param['graph'])
            if content:
                return JsonResponse(dict(code=200, data=content, msg='获取拓扑数据成功'), content_type="application/json",
                                    safe=False)
            else:
                return JsonResponse(dict(code=400, msg='没有拓扑数据'), content_type="application/json", safe=False)
        if get_param.get('get_interface_by_manage_ip'):
            content = interface_mongo.find(query_dict={"hostip": get_param['get_interface_by_manage_ip']},
                                           fileds={"_id": 0})
            if content:
                return JsonResponse(dict(code=200, data=content, msg='success'), content_type="application/json",
                                    safe=False)
            else:
                return JsonResponse(dict(code=400, data='没有匹配的数据', msg='success'), content_type="application/json",
                                    safe=False)

        data = {
            "code": 400,
            "data": [],
            "msg": "没有匹配的操作"
        }
        return JsonResponse(data)

    def post(self, request):
        # post_param = request.body
        post_param = request.data
        # print(post_param, type(post_param))
        # 保存拓扑图
        if all(k in post_param for k in ("name", "graph")):
            _TopologyTask = TopologyTask(post_param['name'])
            graph_data = post_param['graph']
            # 只有link 连线需要重写source 和 target ，d3.js会把source和target改成对应node的字典格式, 默认给到前端是字符串格式的设备ID
            for i in graph_data['links']:
                i['target'] = i['target']['id']
                i['source'] = i['source']['id']
            _TopologyTask.save_graph(graph_data)
            MongoNetOps.topology_ops(**graph_data)
            data = {
                "code": 200,
                "data": [],
                "msg": "保存拓扑图成功"
            }
            return JsonResponse(data, content_type="application/json", safe=False)
        # 新建节点
        if all(k in post_param for k in ("name", "add_nodes")):
            _TopologyTask = TopologyTask(post_param['name'])
            graph_data = _TopologyTask.get_graph()
            if not graph_data:
                nodes = post_param['add_nodes']
                result = OrderedDict()
                # 多字典合并去重
                for item in nodes:
                    result.setdefault(item['manage_ip'], {**item})
                result = list(result.values())
                # print(result)
                _TopologyTask.add_node(result)
            else:
                _TopologyTask.add_node(post_param['add_nodes'])
            data = {
                "code": 200,
                "data": [],
                "msg": "新建节点成功"
            }
            return JsonResponse(data, content_type="application/json", safe=False)
        # 删除节点
        if all(k in post_param for k in ("name", "del_nodes")):
            _TopologyTask = TopologyTask(post_param['name'])
            del_nodes = json.loads(post_param['del_nodes'])
            _TopologyTask.del_node(del_nodes)
            data = {
                "code": 200,
                "data": [],
                "msg": "删除节点成功"
            }
            return JsonResponse(data, content_type="application/json", safe=False)
        # 删除拓扑图
        if all(k in post_param for k in ("name", "del_graph")):
            _TopologyTask = TopologyTask(post_param['name'])
            _TopologyTask.del_graph()
            data = {
                "code": 200,
                "data": [],
                "msg": "删除拓扑图成功"
            }
            return JsonResponse(data, content_type="application/json", safe=False)
        # 增加手动连线
        if all(k in post_param for k in
               ("name", "a_name", "b_name", "a_device", "b_device", "a_interface", "b_interface")):
            _TopologyTask = TopologyTask(post_param['name'])
            tmp = dict(source_ip=post_param['a_device'],
                       source_name=post_param['a_name'],
                       source_interface=post_param['a_interface'],
                       target_ip=post_param['b_device'],
                       target_name=post_param['b_name'],
                       target_interface=post_param['b_interface'])
            res = _TopologyTask.add_manual_link(**tmp)
            if res:
                data = {
                    "code": 200,
                    "data": [],
                    "msg": "增加手动连线成功"
                }
                return JsonResponse(data, content_type="application/json", safe=False)
            data = {
                "code": 400,
                "data": [],
                "msg": "增加手动连线失败"
            }
            return JsonResponse(data, content_type="application/json", safe=False)
        # 删除手动连线
        if all(k in post_param for k in ("name", "del_link")):
            _TopologyTask = TopologyTask(post_param['name'])
            _TopologyTask.del_link(post_param['del_link'])
            data = {
                "code": 200,
                "data": [],
                "msg": "删除手动连线成功"
            }
            return JsonResponse(data, content_type="application/json", safe=False)
        # # 修改单个节点信息(比如图标)
        # if all(k in post_param for k in ("name", "edit_node")):
        #     _TopologyTask = TopologyTask(post_param['name'])
        #     data = {
        #         "code": 200,
        #         "data": [],
        #         "msg": "删除手动连线成功"
        #     }
        #     return JsonResponse(data, content_type="application/json", safe=False)

        data = {
            "code": 400,
            "data": [],
            "msg": "删除手动连线失败"
        }
        return JsonResponse(data, content_type="application/json", safe=False)


# 图标库
class IconView(APIView):
    permission_classes = ()
    authentication_classes = ()

    def get(self, request):
        get_param = request.GET.dict()
        # print(get_param)
        if get_param.get('get_tree'):
            _tree = IconTree()
            _tree.produce_tree()
            res = _tree.tree_final
            if res:
                return JsonResponse(dict(code=200, data=res, msg='获取图标库成功'), content_type="application/json",
                                    safe=False)
            else:
                return JsonResponse(dict(code=400, msg='没有数据'), content_type="application/json", safe=False)
        data = {
            "code": 400,
            "data": [],
            "msg": "没有匹配的操作"
        }
        return JsonResponse(data)

    def post(self, request):
        post_param = request.data
        # print(post_param)
        # 新建目录
        if all(k in post_param for k in ("dir_name", "current_path")):
            data = {
                "code": 400,
                "data": [],
                "msg": ""
            }
            if post_param['current_path'] == '/':
                # print('根目录新建')
                if os.path.exists(ICON_PATH + post_param['dir_name']):
                    data['msg'] = '已经存在该目录'
                else:
                    os.mkdir(ICON_PATH + post_param['dir_name'])
                    data['code'] = 200
                    data['msg'] = '新建完成'
            else:
                if os.path.exists(ICON_PATH + post_param['current_path'] + '/' + post_param['dir_name']):
                    data['msg'] = '已经存在该目录'
                else:
                    os.mkdir(ICON_PATH + post_param['current_path'] + '/' + post_param['dir_name'])
                    data['code'] = 200
                    data['msg'] = '新建完成'
            return JsonResponse(data, content_type="application/json", safe=False)
        # 上传图标
        if post_param.get('upload_path'):
            icons = request.FILES['icons']
            # print(ICON_PATH + post_param['upload_path'] + post_param['filename'])
            path = default_storage.save(ICON_PATH + post_param['upload_path'] + '/' + post_param['filename'],
                                        ContentFile(icons.read()))
            # print(path)
            data = {
                "code": 200,
                "data": [],
                "msg": "上传完成"
            }
            return JsonResponse(data, content_type="application/json", safe=False)
        data = {
            "code": 400,
            "data": [],
            "msg": "没有匹配的动作"
        }
        return JsonResponse(data, content_type="application/json", safe=False)
