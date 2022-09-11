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
        # 解密
        attrs['password'] = CryptPwd().de_js_encrypt(attrs['password'])
        data = super().validate(attrs)
        # refresh = self.get_token(self.user)
        data['userName'] = self.user.username
        data['nickName'] = self.user.username
        data['userId'] = self.user.id
        data['roleId'] = self.user.id
        data['roles'] = [{
            "roleCode": "ROLE_admin",
            "roleId": self.user.id,
            "roleName": "超级管理员"
        }]
        data['code'] = 200
        data['token'] = data['access']

        return {"code": 200, "msg": "ok", "data": data}


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
        request.session['username'] = request_data['username']
        request.session['password'] = crypt.encrypt_pwd(pwd=de_password)
        serializer = self.get_serializer(data=request_data)
        response_data = serializer.validate(request_data)
        # 标注websocket的sessionid
        # request.session['v3'] = 'netopsv3'
        response_data['data']['csrf_token'] = csrf_token
        return HttpResponse(JsonResponse(response_data, safe=False), content_type="application/json")
