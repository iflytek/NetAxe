from django.db import models

# Create your models here.

"""
导航菜单没有借鉴 mysql的外键方式
在二级菜单模型中用parentid 的模式对一级菜单进行关联
"""


# 导航一级菜单
class NavigationProfile(models.Model):
    menuName = models.CharField(verbose_name="菜单名", max_length=100, blank=True, null=True)
    menuUrl = models.CharField(verbose_name="路径", max_length=100, blank=True, null=True)
    icon = models.CharField(verbose_name="图标样式", max_length=100, blank=True, null=True)
    parentPath = models.CharField(verbose_name="父路径", max_length=100, blank=True, null=True, default="")
    badge = models.CharField(verbose_name="badge", max_length=100, blank=True, null=True, default="")
    iconPrefix = models.CharField(verbose_name="图标样式", max_length=100, blank=True, null=True, default='iconfont')
    showOrder = models.IntegerField(verbose_name="排序序号", blank=True, null=True)

    def __str__(self):
        return '%s-%s' % (self.menuName, self.menuUrl)

    class Meta:
        verbose_name_plural = '一级菜单'
        db_table = 'navigation'


# 导航二级菜单
class NavigationSubProfile(models.Model):
    menuName = models.CharField(verbose_name="菜单名", max_length=100, blank=True, null=True)
    menuUrl = models.CharField(verbose_name="路径", max_length=100, blank=True, null=True)
    badge = models.CharField(verbose_name="badge", max_length=100, blank=True, null=True, default="")
    subParent = models.ForeignKey("self", verbose_name="子菜单", blank=True,
                                  related_name='sub_on', null=True, on_delete=models.SET_NULL)
    parent = models.ForeignKey(
        "NavigationProfile",
        verbose_name='一级菜单', related_name='sub_profile', null=True, blank=True,
        on_delete=models.SET_NULL)
    showOrder = models.IntegerField(verbose_name="排序序号", blank=True, null=True)
    cacheable = models.BooleanField(verbose_name='是否缓存', blank=True, default=False)

    def __str__(self):
        return '%s-%s' % (self.menuName, self.menuUrl)

    class Meta:
        verbose_name_plural = '二级菜单'
        db_table = 'navigation_sub'
