from django.utils.translation import gettext_lazy as _
from rest_framework import serializers, status
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


from apps.users.models import UserProfile
from utils.crypt_pwd import CryptPwd
from utils.custom.json_response import DetailResponse, Response, SuccessResponse
from utils.custom.request_util import save_login_log
from utils.custom.viewset import CustomModelViewSet


class LoginSerializer(TokenObtainPairSerializer):
    """
    登录的序列化器:
    重写djangorestframework-simplejwt的序列化器
    """

    captcha = serializers.CharField(max_length=6, required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = UserProfile
        fields = "__all__"
        read_only_fields = ["id"]

    default_error_messages = {"no_active_account": _("账号/密码错误")}

    def validate(self, attrs):
        data = super().validate(attrs)
        refresh = self.get_token(self.user)
        data["username"] = self.user.username
        data['token'] = str(refresh.access_token)
        data["isSuperuser"] = self.user.is_superuser
        # 记录登录日志
        request = self.context.get("request")
        request.user = self.user
        save_login_log(request=request)
        return {"code": 200, "msg": "请求成功", "data": data}


class LoginView(TokenObtainPairView):
    """
    登录接口
    """

    serializer_class = LoginSerializer
    permission_classes = []

    def post(self, request, *args, **kwargs):
        request.data._mutable = True
        password = request.data.get("password")
        request.data["password"] = CryptPwd().de_js_encrypt(password)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """
    登出接口
    """
    def post(self, request):
        return DetailResponse(msg="注销成功")

class LoginViewSet(APIView):

    def get(self, request, *args, **kwargs):
        return SuccessResponse(data="已登录")

