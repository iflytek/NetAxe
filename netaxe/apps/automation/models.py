from django.db import models
import json
# Create your models here.


# 设备信息采集方案
class CollectionPlan(models.Model):
    vendor = models.CharField(verbose_name='厂商', max_length=50, default='')
    name = models.CharField(verbose_name='采集方案', max_length=100, null=True, blank=True)
    commands = models.TextField(
        blank=True, default='[]',
        verbose_name='下发命令',
    )
    netconf_method = models.TextField(
        blank=True, default='[]',
        verbose_name='方法列表',
    )
    memo = models.TextField(verbose_name='备注', null=True, blank=True)
    netconf_class = models.CharField(verbose_name="Netconf连接类", null=True, blank=True, max_length=100)

    def get_commands(self):
        return '\n'.join(json.loads(self.commands))

    def get_netconf_method(self):
        return '\n'.join(json.loads(self.netconf_method))

    def __str__(self):
        return '%s' % self.name

    class Meta:
        unique_together = (("name", "vendor"),)
        verbose_name = '设备数据采集方案'
        verbose_name_plural = '设备数据采集方案表'
        db_table = 'device_collection_plan'  # 通过db_table自定义数据表名