from django.db import models


# Create your models here.
class ConfigCompliance(models.Model):
    """配置合规"""
    VENDOR_CHOICES = (
        ('H3C', 'H3C'),
        ('Huawei', 'Huawei'),
        ('Cisco', 'Cisco')
    )
    CATEGORY_CHOICES = (
        ('switch', 'switch'),
        ('firewall', 'firewall'),
        ('router', 'router')
    )
    PATTEN_CHOICES = (
        ('contain', 'contain'),
        ('match', 'match'),
    )
    vendor = models.CharField(verbose_name='厂商', choices=VENDOR_CHOICES, max_length=50, default='H3C')
    category = models.CharField(verbose_name='类型', choices=CATEGORY_CHOICES, max_length=50, default='交换机')
    regex = models.TextField(verbose_name='表达式', null=False, default='', blank=False)
    pattern = models.CharField(verbose_name="模式", choices=PATTEN_CHOICES, max_length=50, default='contain')
    datetime = models.DateTimeField(auto_now=True, verbose_name='创建日期')

    def __str__(self):
        return '%s-%s-%s' % (self.vendor, self.category, self.pattern)

    class Meta:
        verbose_name_plural = '配置合规表'
        verbose_name = '配置合规表'
        db_table = 'config_compliance'  # 通过db_table自定义数据表名
        indexes = [models.Index(fields=['vendor', ]),
                   models.Index(fields=['category', ]),
                   models.Index(fields=['pattern', ]),
                   models.Index(fields=['datetime', ])]
