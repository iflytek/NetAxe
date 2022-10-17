# Create your views here.
import base64
from django.views import View
from django.http import JsonResponse
from captcha.models import CaptchaStore
from captcha.views import captcha_image


class CaptchaView(View):
    """
    获取图片验证码
    """
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