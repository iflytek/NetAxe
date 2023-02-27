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
    memo = models.TextField(verbose_name='描述', null=True, blank=True)

    def bgbu_list(self):
        return ','.join([i.name for i in self.bgbu.all()])

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '拓扑表'
        db_table = 'topology'  # 通过db_table自定义数据表名
        indexes = [models.Index(fields=['name'])]