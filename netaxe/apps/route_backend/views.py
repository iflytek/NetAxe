import base64
import os

from django.http import JsonResponse
from django.db.models import Count
from captcha.models import CaptchaStore
from captcha.views import captcha_image
from django.views import View
from apps.asset.models import NetworkDevice
from django_celery_beat.models import PeriodicTask, PeriodicTasks, CrontabSchedule, IntervalSchedule
# Create your views here.

# 根据角色的菜单组件
from rest_framework.views import APIView

from .models import NavigationProfile
from netboost import settings
from utils.crypt_pwd import CryptPwd
from utils.sftp import SFTP

from apps.automation.models import CollectionPlan

from utils.connect_layer.NETCONF.h3c_netconf import H3CinfoCollection, H3CSecPath
from utils.connect_layer.NETCONF.huawei_netconf import HuaweiUSG, HuaweiCollection

from .serializers import CrontabSerializer, IntervalSerializer


class MenuListByRoleId(APIView):

    def get(self, request):
        """

        :param request:
        :return:
        """
        # get_param = request.GET.dict()
        return JsonResponse({'code': 200})

    def post(self, request):
        navigate = []
        res = NavigationProfile.objects.all().order_by('showOrder')
        for i in res:
            tmp = {
                "menuUrl": i.menuUrl,
                "menuName": i.menuName,
                "iconPrefix": i.iconPrefix,
                "icon": i.icon,
                "parentPath": "",
                "children": []
            }
            if i.badge:
                tmp['badge'] = i.badge
            # 二级菜单
            sub_q = i.sub_profile.all().order_by('showOrder')
            if sub_q:
                for sub in sub_q:
                    sub_tmp = {
                        "parentPath": i.menuUrl,
                        "menuUrl": sub.menuUrl,
                        "menuName": sub.menuName,
                    }
                    if sub.badge:
                        sub_tmp["badge"] = sub.badge
                    if sub.cacheable:
                        sub_tmp["cacheable"] = sub.cacheable
                    third_q = sub.sub_on.all().order_by('showOrder')
                    if third_q:
                        sub_tmp["children"] = []
                        for third in third_q:
                            third_tmp = {
                                "parentPath": sub.menuUrl,
                                "menuUrl": third.menuUrl,
                                "menuName": third.menuName,
                            }
                            if third.cacheable:
                                third_tmp["cacheable"] = third.cacheable
                            fourth_q = third.sub_on.all().order_by('showOrder')
                            if fourth_q:
                                third_tmp["children"] = []
                                for fourth in fourth_q:
                                    fourth_tmp = {
                                        "parentPath": third.menuUrl,
                                        "menuUrl": fourth.menuUrl,
                                        "menuName": fourth.menuName,
                                    }
                                    third_tmp["children"].append(fourth_tmp)
                            sub_tmp["children"].append(third_tmp)
                    tmp["children"].append(sub_tmp)
            navigate.append(tmp)
        data = {
            "code": 200,
            "data": navigate,
            "msg": "获取菜单列表成功"
        }
        return JsonResponse(data)


class DashboardChart(APIView):
    def get(self, request):
        get_params = request.GET.dict()
        if "device_idc_dimension" in get_params:
            idc_dimension_data = []
            idc_dimension_queryset = NetworkDevice.objects.values('idc__name').annotate(sum_count=Count('idc'))
            for i in idc_dimension_queryset:
                idc_dimension_data.append(i)
            result = {
                "code": 200,
                "data": idc_dimension_data
            }
            return JsonResponse(result, safe=False)


class CaptchaView(View):
    """
    获取图片验证码
    """
    authentication_classes = []

    def get(self, request):
        hashkey = CaptchaStore.generate_key()
        id = CaptchaStore.objects.filter(hashkey=hashkey).first().id
        imgage = captcha_image(request, hashkey)
        # 将图片转换为base64
        image_base = base64.b64encode(imgage.content)
        json_data = {"key": id, "image_base": "data:image/png;base64," + image_base.decode('utf-8')}
        result = {
            'code': 200,
            'data': json_data
        }
        return JsonResponse(data=result)


class WebSshView(APIView):
    def get(self, request):
        get_param = request.GET.dict()
        server_obj = NetworkDevice.objects.get(id=get_param.get('pk'))
        init_cmd = ''
        if server_obj.vendor.name in ['华三', '华为', '锐捷', '盛科']:
            init_cmd = 'terminal monitor'
        ssh_server_ip = server_obj.manage_ip
        download_file = request.GET.get('download_file')
        if download_file:
            download_file_path = os.path.join(settings.MEDIA_ROOT, 'admin_files', request.user.username, 'download',
                                              ssh_server_ip)

            sftp = SFTP(ssh_server_ip, server_obj.port, server_obj.username,
                        CryptPwd().decrypt_pwd(server_obj.password))

            response = sftp.download_file(download_file, download_file_path)
            return response
        else:
            remote_ip = request.META.get('REMOTE_ADDR')
            return JsonResponse({'code': 200, 'data': {'init_cmd': init_cmd, 'remote_ip': remote_ip}})

    def post(self, request):
        post_data = request.POST
        server_obj = NetworkDevice.objects.get(id=post_data.get('pk'))
        ssh_server_ip = server_obj.manage_ip
        try:
            upload_file = request.FILES.get('upload_file')
            upload_file_path = os.path.join(settings.MEDIA_ROOT, 'fort_files', request.user.username, 'upload',
                                            server_obj.assets.asset_management_ip)
            sftp = SFTP(ssh_server_ip, server_obj.port, server_obj.username,
                        CryptPwd().decrypt_pwd(server_obj.password))
            sftp.upload_file(upload_file, upload_file_path)

            return JsonResponse({'code': 200, 'msg': '上传成功！文件默认放在{}用户家目录下'.format(server_obj.username)})
        except Exception as e:
            return JsonResponse({'code': 500, 'msg': '上传失败！{}'.format(e)})


# 设备采集方案
class DeviceCollectView(APIView):
    def get(self, request):
        get_param = request.GET.dict()
        if all(k in get_param for k in ("vendor", "netconf_class")):
            vendor = get_param['vendor']
            data = {
                'H3C': ['H3CinfoCollection', 'H3CSecPath'],
                'Huawei': ['HuaweiUSG', 'HuaweiCollection'],
            }
            if vendor in data.keys():
                return JsonResponse(dict(code=200, data=data[vendor]))
            else:
                return JsonResponse(dict(code=400, data=[]))

        if all(k in get_param for k in ("get_method", "netconf_class")):
            netconf_class = get_param['netconf_class']
            data = {
                'H3CinfoCollection': H3CinfoCollection,
                'H3CSecPath': H3CSecPath,
                'HuaweiUSG': HuaweiUSG,
                'HuaweiCollection': HuaweiCollection,
            }
            if netconf_class in data.keys():
                res = data[netconf_class].get_method()
                return JsonResponse(dict(code=200, data=res))
            else:
                return JsonResponse(dict(code=400, data=[]))


# 自动化chart
class AutomationChart(APIView):
    def get(self, request):
        get_params = request.GET.dict()

        if "collection_plan" in get_params:
            collection_plan_list = []
            collection_plan_queryset = CollectionPlan.objects.values("vendor").annotate(sum_count=Count("vendor"))
            for i in collection_plan_queryset:
                collection_plan_list.append(i)

            result = {
                'code': 200,
                'data': collection_plan_list
            }
            return JsonResponse(result, safe=False)


# 调度管理
class DispatchManageView(View):
    def post(self, request):
        post_params = request.POST.dict()
        if post_params.get("add_crontab_schedule", ''):
            try:
                crontab_schedule = request.POST.dict()
                crontab_schedule_obj = CrontabSchedule.objects.create(
                    minute=crontab_schedule['minute'],
                    hour=crontab_schedule['hour'],
                    day_of_week=crontab_schedule['day_of_week'],
                    day_of_month=crontab_schedule['day_of_month'],
                    month_of_year=crontab_schedule['month_of_year'],
                    timezone=crontab_schedule['timezone'],
                )
                # crontab_schedule_obj = CrontabSchedule.objects.create(**crontab_schedule)
                return JsonResponse({'code': 200, 'msg': '添加crontab_schedule成功', 'data': crontab_schedule_obj.id})
            except Exception as e:
                return JsonResponse({'code': 500, 'msg': '添加crontab_schedule失败，{}'.format(e)})
        if post_params.get('add_interval_schedule', ''):
            try:
                interval_schedule = request.POST.dict()
                interval_schedule_obj = IntervalSchedule.objects.create(
                    every=int(interval_schedule.get('every')),
                    period=interval_schedule.get('period')
                )
                return JsonResponse({'code': 200, 'msg': '添加interval_schedule成功', 'data': interval_schedule_obj.id})
            except Exception as e:
                return JsonResponse({'code': 500, 'msg': '添加interval_schedule失败，{}'.format(e)})

        if post_params.get('delete', ''):
            schedule_type = request.POST.get('schedule_type', '')
            pk = request.POST.get('id', '')
            if schedule_type == 'crontab_schedule':
                try:
                    CrontabSchedule.objects.get(id=pk).delete()
                    return JsonResponse({'code': 200, 'msg': '删除crontab_schedule成功'})
                except Exception as e:
                    return JsonResponse({'code': 500, 'msg': '删除crontab_schedule失败，{}'.format(e)})
            elif schedule_type == 'interval_schedule':
                try:
                    IntervalSchedule.objects.get(id=pk).delete()
                    return JsonResponse({'code': 200, 'msg': '删除interval_schedule成功'})
                except Exception as e:
                    return JsonResponse({'code': 500, 'msg': '删除interval_schedule失败，{}'.format(e)})

    def get(self, request):
        crontab_schedules = CrontabSchedule.objects.all()

        interval_schedules = IntervalSchedule.objects.all()

        return JsonResponse(
            {'code': 200, 'msg': 'success', 'crontab_data': CrontabSerializer(crontab_schedules, many=True).data,
             "interval_data": IntervalSerializer(interval_schedules, many=True).data})
