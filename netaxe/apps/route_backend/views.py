import base64
import os

from django.http import JsonResponse
from django.db.models import Count
from captcha.models import CaptchaStore
from captcha.views import captcha_image
from django.views import View
from apps.asset.models import NetworkDevice
from django_celery_beat.models import PeriodicTask, PeriodicTasks
# Create your views here.

# 根据角色的菜单组件
from rest_framework.views import APIView

from .models import NavigationProfile
from netboost import settings
from utils.crypt_pwd import CryptPwd
from utils.sftp import SFTP


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
