from django.db import models
# import mongoengine
# Create your models here.
# from django.core.exceptions import ValidationError
# from django.core.validators import MaxValueValidator, MinValueValidator
"""
-------------------------------------------------
   Description:     Topology
   Author:          jmli12
   date：           2021/12/17
   Soft:            PyCharm
   CodeStyle:       PEP8   

-------------------------------------------------
   Change Activity:

-------------------------------------------------
"""

# Create your models here.


# 设备层级选择
class DeviceLevelChoise(object):

    ONE = '1'
    TWO = '2'
    THREE = '3'
    FOUR = '4'
    FIVE = '5'

    CHOICES = (
        (ONE, ONE),
        (TWO, TWO),
        (THREE, THREE),
        (FOUR, FOUR),
        (FIVE, FIVE),
    )


# 拓扑主机子表
class TopologyHost(models.Model):
    name = models.CharField(verbose_name='主机名', null=True, blank=True, max_length=32)
    host = models.GenericIPAddressField(verbose_name='主机IP', null=True, blank=True, max_length=32)

    def __str__(self):
        return '%s(%s)' % (self.name, self.host)

    class Meta:
        # unique_together = (("name", "host", "group"),)
        db_table = 'topology_host'
        verbose_name = '拓扑主机表'
        verbose_name_plural = '拓扑主机表'


class TopologyStatus(object):

    FINISHED = 'Finished'
    PENDING = 'Pending'

    CHOICES = (
        (FINISHED, FINISHED),
        (PENDING, PENDING),
    )


class Topology(models.Model):
    """
    拓扑表
    Topology
    """
    name = models.CharField(
        verbose_name='名称',
        max_length=50,
        null=False,
        unique=True)
    bgbu = models.ManyToManyField("users.BgBu", verbose_name='关联业务', blank=True, related_name='bgbu_topology_group')
    # group_hosts = models.ManyToManyField("TopologyHost", related_name='to_topology_group', verbose_name='组内主机')
    memo = models.TextField(verbose_name='描述', null=True, blank=True)

    def bgbu_list(self):
        return ','.join([i.name for i in self.bgbu.all()])

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '拓扑表'
        db_table = 'topology'  # 通过db_table自定义数据表名
        indexes = [models.Index(fields=['name'])]