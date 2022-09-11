# Create your views here.
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from netboost.settings import BASE_DIR
from apps.config_center.config_parse.config_parse import ConfigTree
from apps.config_center.git_tools.git_proc import ConfigGit

_ConfigGit = ConfigGit()


class GitConfig(APIView):
    permission_classes = (IsAuthenticated,)

    # authentication_classes = (JWTAuthentication, SessionAuthentication)

    def get(self, request):
        """

        :param request:
        :return:
        """
        get_param = request.GET.dict()
        # print('get_param', get_param)
        if 'get_tree' in get_param.keys():
            _tree = ConfigTree()
            _tree.produce_tree()
            data = {
                "code": 200,
                "data": _tree.tree_final,
                "msg": "获取配置文件树成功"
            }
            return JsonResponse(data)
        if 'filename' in get_param.keys():
            with open(BASE_DIR + '/media/device_config/' + get_param['filename'], "r") as f:
                file_content = f.read()
                data = {
                    "code": 200,
                    "data": file_content,
                    "msg": "获取配置文件内容成功"
                }
                return JsonResponse(data, safe=False)
        if 'get_commit' in get_param.keys():
            res = _ConfigGit.get_commit()
            # print(res)
            data = {
                "code": 200,
                "data": res,
                "msg": "获取commit记录成功"
            }
            return JsonResponse(data, safe=False)
        if 'commit_detail' in get_param.keys():
            res = _ConfigGit.get_commit_detail(get_param['commit_detail'])
            data = {
                "code": 200,
                "data": res,
                "msg": "获取commit轨迹成功"
            }
            return JsonResponse(data, safe=False)
        if all(k in get_param for k in ("file", "from_commit", "to_commit")):
            res = _ConfigGit.get_commit_by_file(**get_param)
            data = {
                "code": 200,
                "data": [res],
                "msg": "获取文件变更详情成功"
            }
            return JsonResponse(data, safe=False)
        if all(k in get_param for k in ("file", "single_commit")):
            res = _ConfigGit.get_commit_by_filename(get_param['single_commit'], get_param['file'])
            data = {
                "code": 200,
                "data": [res],
                "msg": "获取文件变更详情成功"
            }
            return JsonResponse(data, safe=False)
        data = {
            "code": 400,
            "data": [],
            "msg": "没有捕获任何操作"
        }
        return JsonResponse(data)
