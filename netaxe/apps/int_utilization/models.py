from django.db import models

# Create your models here.


class InterfaceUsedNew(models.Model):
    """接口使用率新"""
    host = models.CharField(verbose_name='主机名', max_length=200, null=True, blank=True)
    host_id = models.CharField(verbose_name='硬件ID', max_length=50, null=True, blank=True)
    host_ip = models.GenericIPAddressField(verbose_name='管理IP', null=True, blank=True)
    int_total = models.IntegerField(verbose_name='总接口数', null=True, blank=True)
    int_used = models.IntegerField(verbose_name='已使用', null=True, blank=True)
    int_unused = models.IntegerField(verbose_name='未使用', null=True, blank=True)
    utilization = models.FloatField(verbose_name='使用率', null=True, blank=True)
    int_used_1g = models.IntegerField(verbose_name='1G接口使用', null=True, blank=True)
    int_used_10m = models.IntegerField(verbose_name='10M接口使用', null=True, blank=True)
    int_used_100m = models.IntegerField(verbose_name='100M接口使用', null=True, blank=True)
    int_used_10g = models.IntegerField(verbose_name='10G接口使用', null=True, blank=True)
    int_used_20g = models.IntegerField(verbose_name='20G接口使用', null=True, blank=True)
    int_used_25g = models.IntegerField(verbose_name='25G接口使用', null=True, blank=True)
    int_used_40g = models.IntegerField(verbose_name='40G接口使用', null=True, blank=True)
    int_used_100g = models.IntegerField(verbose_name='100G接口使用', null=True, blank=True)
    int_used_irf = models.IntegerField(verbose_name='堆叠接口使用', null=True, blank=True)
    int_used_auto = models.IntegerField(verbose_name='auto接口使用', null=True, blank=True)
    int_unused_1g = models.IntegerField(verbose_name='1G接口未使用', null=True, blank=True)
    int_unused_10m = models.IntegerField(verbose_name='10M接口未使用', null=True, blank=True)
    int_unused_100m = models.IntegerField(verbose_name='100M接口未使用', null=True, blank=True)
    int_unused_10g = models.IntegerField(verbose_name='10G接口未使用', null=True, blank=True)
    int_unused_20g = models.IntegerField(verbose_name='20G接口未使用', null=True, blank=True)
    int_unused_25g = models.IntegerField(verbose_name='25G接口未使用', null=True, blank=True)
    int_unused_40g = models.IntegerField(verbose_name='40G接口未使用', null=True, blank=True)
    int_unused_100g = models.IntegerField(verbose_name='100G接口未使用', null=True, blank=True)
    int_unused_irf = models.IntegerField(verbose_name='堆叠接口未使用', null=True, blank=True)
    int_unused_auto = models.IntegerField(verbose_name='auto接口未使用', null=True, blank=True)
    log_time = models.DateTimeField(verbose_name='记录时间', null=True, blank=True)
    # bgbu = models.ManyToManyField("network.BgBu", verbose_name='BGBU', blank=True)

    def __str__(self):
        return '%s-%s' % (self.host, self.utilization)

    class Meta:
        verbose_name_plural = '接口利用率表'
        db_table = 'interface_used_new'  # 通过db_table自定义数据表名
        indexes = [models.Index(fields=['host', ]),
                   models.Index(fields=['host_id', ]),
                   models.Index(fields=['host_ip', ]),
                   models.Index(fields=['int_total', ]),
                   models.Index(fields=['int_used', ]),
                   models.Index(fields=['int_unused', ]),
                   models.Index(fields=['utilization', ]),
                   models.Index(fields=['int_used_1g', ]),
                   models.Index(fields=['int_used_10m', ]),
                   models.Index(fields=['int_used_100m', ]),
                   models.Index(fields=['int_used_10g', ]),
                   models.Index(fields=['int_used_20g', ]),
                   models.Index(fields=['int_used_25g', ]),
                   models.Index(fields=['int_used_40g', ]),
                   models.Index(fields=['int_used_100g', ]),
                   models.Index(fields=['int_used_irf', ]),
                   models.Index(fields=['int_used_auto', ]),
                   models.Index(fields=['int_unused_1g', ]),
                   models.Index(fields=['int_unused_10m', ]),
                   models.Index(fields=['int_unused_100m', ]),
                   models.Index(fields=['int_unused_10g', ]),
                   models.Index(fields=['int_unused_20g', ]),
                   models.Index(fields=['int_unused_25g', ]),
                   models.Index(fields=['int_unused_40g', ]),
                   models.Index(fields=['int_unused_100g', ]),
                   models.Index(fields=['int_unused_irf', ]),
                   models.Index(fields=['int_unused_auto', ]),
                   models.Index(fields=['log_time', ]),
                   ]