from captcha.models import CaptchaStore
from django.contrib import auth
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import _get_new_csrf_string, _mask_cipher_secret
# from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from scripts.crypt_pwd import CryptPwd


class FormulaTokenObtainPairSerializer(TokenObtainPairSerializer):
    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass

    def validate(self, attrs):
        # print('attrs', attrs)
        # 解密
        attrs['password'] = CryptPwd().de_js_encrypt(attrs['password'])
        # 验证码解析
        captcha_code = CaptchaStore.objects.filter(id=attrs['captchaKey']).first()
        if captcha_code and (
                captcha_code.response == attrs['captchaValue'] or captcha_code.challenge == attrs['captchaValue']):
            captcha_code and captcha_code.delete()
            data = super().validate(attrs)

            # refresh = self.get_token(self.user)
            data['userName'] = self.user.username
            data['nickName'] = self.user.nick_name
            data['userId'] = self.user.id
            data['roleId'] = self.user.is_superuser
            data['roles'] = [{
                "roleCode": "ROLE_admin",
                "roleId": self.user.id,
                "roleName": "超级管理员"
            }]
            data['code'] = 200
            data['token'] = data['access']
            return {"code": 200, "msg": "ok", "data": data}
        else:
            # captcha_code and captcha_code.delete()
            return {"code": 400, "msg": "ok", "data": {'message': '验证码错误'}}


class FormulaTokenObtainPairView(TokenObtainPairView):
    serializer_class = FormulaTokenObtainPairSerializer

    # print(FormulaTokenObtainPairSerializer.data)

    def post(self, request, *args, **kwargs):
        if 'CSRF_COOKIE' not in request.META:
            csrf_secret = _get_new_csrf_string()
            request.META['CSRF_COOKIE'] = _mask_cipher_secret(csrf_secret)
            csrf_token = request.META['CSRF_COOKIE']

        else:
            # csrf_secret = _unsalt_cipher_token(request.META["CSRF_COOKIE"])
            csrf_token = request.META['CSRF_COOKIE']
        # request.META["CSRF_COOKIE_USED"] = True
        request_data = request.POST.dict()
        print(request_data)
        crypt = CryptPwd()
        de_password = crypt.de_js_encrypt(request_data['password'])
        # 做用户鉴权用作webssh记录命令信息
        # user = auth.authenticate(username=request_data['username'], password=de_password)
        # auth.login(request, user)
        request.session['username'] = request_data['username']
        request.session['password'] = crypt.encrypt_pwd(pwd=de_password)
        serializer = self.get_serializer(data=request_data)
        response_data = serializer.validate(request_data)
        response_data['data']['csrf_token'] = csrf_token
        return HttpResponse(JsonResponse(response_data, safe=False), content_type="application/json")
