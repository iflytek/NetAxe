from django.db import models


class SupportVendor:
    CHOICES = (
        ('H3C', 'H3C'),
        ('HUAWEI', 'HUAWEI'),
        ('Cisco_ios', 'Cisco_ios'),
        ('Ruijie', 'Ruijie'),
        ('Hillstone', 'Hillstone'),
    )


# 配置合规表
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
    MATCH_CHOICES = (
        ('match-compliance', 'match-compliance'),  # 匹配-合规 反之 不匹配-不合规
        # ('match-non-compliance', 'match-non-compliance'),  # 匹配-不合规
        ('mismatch-compliance', 'mismatch-compliance'),  # 不匹配-合规 反之 匹配-不合规
        # ('mismatch-non-compliance', 'mismatch-non-compliance'),  # 不匹配-不合规
    )
    name = models.CharField(verbose_name='名称', max_length=50, null=False, unique=True)
    vendor = models.CharField(verbose_name='厂商', choices=VENDOR_CHOICES, max_length=50, default='H3C')
    category = models.CharField(verbose_name='类型', choices=CATEGORY_CHOICES, max_length=50, default='交换机')
    pattern = models.CharField(verbose_name='模式', choices=MATCH_CHOICES, max_length=50, default='match-compliance')
    regex = models.TextField(verbose_name='表达式', null=False, default='', blank=False)
    is_repair = models.BooleanField(verbose_name="是否修正", null=False, default=False, blank=False)
    repair_cmds = models.TextField(verbose_name='修复命令', null=False, default='', blank=False)
    datetime = models.DateTimeField(auto_now=True, verbose_name='创建日期')

    def __str__(self):
        return '%s-%s-%s' % (self.name, self.vendor, self.category)

    class Meta:
        verbose_name_plural = '配置合规表'
        verbose_name = '配置合规表'
        db_table = 'config_compliance'  # 通过db_table自定义数据表名
        indexes = [models.Index(fields=['vendor', ]),
                   models.Index(fields=['category', ]),
                   models.Index(fields=['datetime', ])]


# 配置模板表
class ConfigTemplate(models.Model):
    vendor = models.CharField(verbose_name="厂商", choices=SupportVendor.CHOICES, default='H3C', max_length=100)
    name = models.CharField(verbose_name='配置项名称', max_length=100, null=False, unique=True)
    config_yaml = models.TextField(verbose_name='yaml内容', null=False, blank=True, default='')
    config_jinja2 = models.TextField(verbose_name='jinja2内容', null=False, blank=True, default='')
    config_text = models.TextField(verbose_name='配置命令', null=False, blank=True, default='')
    datetime = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    def __str__(self):
        return "{}-{}".format(self.vendor, self.name)

    class Meta:
        unique_together = (('vendor', 'name'),)
        verbose_name_plural = '配置片段表'
        verbose_name = '配置片段表'
        db_table = 'config_template'  # 通过db_table自定义数据表名
        indexes = [models.Index(fields=['name', 'vendor'])]


# TTP模板表
class TTPTemplate(models.Model):
    vendor = models.CharField(verbose_name="厂商", choices=SupportVendor.CHOICES, default='H3C', max_length=100)
    name = models.CharField(verbose_name='名称', max_length=100, null=False, unique=True)
    ttp_content = models.TextField(verbose_name='模板内容', null=False, blank=True, default='')
    datetime = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    def __str__(self):
        return "{}-{}".format(self.vendor, self.name)

    class Meta:
        unique_together = (('vendor', 'name'),)
        verbose_name_plural = '配置片段表'
        verbose_name = '配置片段表'
        db_table = 'ttp_template'  # 通过db_table自定义数据表名
        indexes = [models.Index(fields=['name', 'vendor'])]
