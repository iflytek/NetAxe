from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.
class UserProfile(AbstractUser):
    login_status = (
        (0, '在线'),
        (1, '离线'),
        (2, '忙碌'),
    )
    nick_name = models.CharField(max_length=30, null=True, blank=True, verbose_name='昵称')
    mobile = models.CharField(max_length=11, null=True, blank=True, verbose_name='手机号码')
    image = models.ImageField(upload_to='images/%Y/%m/%d/', default='images/default.png', max_length=100)
    login_status = models.SmallIntegerField(choices=login_status, default=0, verbose_name='登录状态')

    def get_login_status(self):
        return self.login_status

    class Meta:
        db_table = 'ops_user'
        verbose_name = '用户表'
        verbose_name_plural = '用户表'


class BgBu(models.Model):
    """ """
    name = models.CharField(verbose_name='业务名称', max_length=20, null=False, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '业务表'
        verbose_name_plural = '业务表'
        db_table = 'bgbu'  # 通过db_table自定义数据表名
        indexes = [models.Index(fields=['name', ]), ]