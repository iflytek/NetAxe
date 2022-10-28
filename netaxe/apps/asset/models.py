from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils import timezone
from utils.crypt_pwd import CryptPwd
# Create your models here.


class Idc(models.Model):
    """
    数据中心表
    """
    name = models.CharField(
        verbose_name='机房名称',
        max_length=50,
        null=False,
        unique=True)
    address = models.CharField(
        verbose_name='机房地址',
        max_length=100,
        null=False, default='')
    tel = models.CharField(verbose_name='机房电话', max_length=30, null=False, default='')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '数据中心表'
        db_table = 'asset_idc'
        indexes = [models.Index(fields=['name', ])]


class NetZone(models.Model):
    """网络区域表"""
    name = models.CharField(
        verbose_name='区域名',
        max_length=20, unique=True,
        null=False, default='')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '网络区域表'
        db_table = 'asset_netzone'  # 通过db_table自定义数据表名
        indexes = [models.Index(fields=['name', ])]


class Role(models.Model):
    """设备角色表"""
    name = models.CharField(
        verbose_name='设备角色',
        max_length=30, unique=True,
        null=False, default='')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '设备角色表'
        db_table = 'asset_role'  # 通过db_table自定义数据表名
        indexes = [models.Index(fields=['name', ])]


class IdcModel(models.Model):
    """
    机房模块表
    """
    name = models.CharField(
        verbose_name='模块名',
        max_length=30,
        null=False, default='')
    floor = models.CharField(
        verbose_name='楼层号',
        max_length=30,
        null=False, default='')
    area = models.CharField(
        verbose_name='区域号',
        max_length=30,
        null=False, default='')
    idc = models.ForeignKey(
        "Idc",
        verbose_name='所属机房',
        on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = (("name", "idc"),)
        verbose_name_plural = '机房模块表'
        db_table = 'asset_idc_model'  # 通过db_table自定义数据表名
        indexes = [models.Index(fields=['name', ])]


class Rack(models.Model):
    """机柜信息"""
    name = models.CharField(
        verbose_name='机柜编号',
        max_length=30,
        null=False, default='')
    rack_row = models.CharField(verbose_name='机柜排', max_length=30, null=False, default='')
    idc_model = models.ForeignKey("IdcModel", verbose_name='关联模块', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.name

    def get_idc_model_name(self):
        return self.idc_model.name

    class Meta:
        unique_together = (("name", "idc_model"),)
        verbose_name_plural = '机柜表'
        db_table = 'rack'  # 通过db_table自定义数据表名
        indexes = [models.Index(fields=['name', ])]


class Vendor(models.Model):
    """设备供应商"""
    name = models.CharField(
        verbose_name='供应商',
        max_length=30,
        null=False,
        unique=True)

    alias = models.CharField(
        verbose_name='别名',
        max_length=30,
        null=False, default='',
        unique=True)

    def __str__(self):
        return "{}({})".format(self.name, self.alias)

    class Meta:
        verbose_name_plural = '设备供应商表'
        db_table = 'asset_vendor'  # 通过db_table自定义数据表名
        indexes = [models.Index(fields=['name', ])]


class Category(models.Model):
    """设备类型"""
    name = models.CharField(
        verbose_name='设备类型',
        max_length=30,
        null=False, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '设备类型表'
        db_table = 'asset_category'  # 通过db_table自定义数据表名
        indexes = [models.Index(fields=['name', ])]


class Model(models.Model):
    """
    设备硬件型号
    """
    name = models.CharField(
        verbose_name='硬件型号',
        max_length=30,
        null=False,
        unique=True)
    vendor = models.ForeignKey(
        "Vendor",
        verbose_name='供应商',
        on_delete=models.CASCADE,
        blank=True)

    def __str__(self):
        return self.name

    class Meta:
        unique_together = (("name", "vendor"),)
        verbose_name_plural = '硬件型号表'
        db_table = 'asset_model'  # 通过db_table自定义数据表名
        indexes = [models.Index(fields=['name', ])]


class Attribute(models.Model):
    """
    设备网络属性
    """
    name = models.CharField(
        verbose_name='网络属性',
        max_length=30,
        null=False,
        unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '网络属性表'
        db_table = 'asset_attribute'  # 通过db_table自定义数据表名
        indexes = [models.Index(fields=['name', ])]


class Framework(models.Model):
    """
    设备网络架构
    """
    name = models.CharField(
        verbose_name='网络架构',
        max_length=50,
        null=False,
        unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = '网络架构表'
        db_table = 'asset_framework'  # 通过db_table自定义数据表名
        indexes = [models.Index(fields=['name', ])]


class AssetIpInfo(models.Model):
    """IP信息表"""
    name = models.CharField(verbose_name='标识名', max_length=200, null=True, blank=True)
    device = models.ForeignKey("NetworkDevice", verbose_name='关联设备',
                               related_name='bind_ip', null=True, blank=True,
                               on_delete=models.CASCADE)
    ipaddr = models.GenericIPAddressField(verbose_name='IP', null=False)

    def __str__(self):
        return "{}-{}".format(self.name, self.ipaddr)

    class Meta:
        unique_together = (("name", "device"),)
        verbose_name_plural = '设备关联IP表'
        db_table = 'asset_ip'  # 通过db_table自定义数据表名
        indexes = [models.Index(fields=['name', ])]


class AssetAccount(models.Model):
    """
    设备管理账户表
    """
    protocol_choices = (
        ('ssh', 'ssh'),
        ('telnet', 'telnet'),
        ('netconf', 'netconf'),
    )
    name = models.CharField(
        verbose_name='管理账户',
        max_length=50,
        default='',
        unique=True)
    username = models.CharField(
        verbose_name='登录用户名',
        max_length=50,
        default='',
        null=True,
        blank=True)
    password = models.CharField(
        verbose_name='登录密码',
        max_length=200,
        default='',
        null=True,
        blank=True)
    protocol = models.CharField(
        verbose_name='协议名',
        max_length=20, choices=protocol_choices,
        null=False, default='ssh')
    port = models.IntegerField(verbose_name='端口号', default=22)
    role = models.CharField(verbose_name='用户角色', max_length=20, choices=(
        ('3', '超级管理员'), ('2', '管理员'), ('1', '普通用户'), ('0', '查看')), default=3)

    en_pwd = models.CharField(
        verbose_name='特权密码',
        max_length=20,
        default='', blank=True,
        null=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        _encrypt = True
        if self.pk:
            old_password = AssetAccount.objects.get(id=self.id)
            _encrypt = False if old_password.password == self.password else True
        if _encrypt:
            crypt = CryptPwd()
            self.password = crypt.encrypt_pwd(self.password)
        super(AssetAccount, self).save(*args, **kwargs)

    @property
    def decode_password(self):
        crypt = CryptPwd()
        return crypt.decrypt_pwd(self.password)

    class Meta:
        verbose_name_plural = '设备管理账户'
        db_table = 'asset_account'  # 通过db_table自定义数据表名
        indexes = [models.Index(fields=['name', ])]


class NetworkDevice(models.Model):
    """网络设备模型"""

    status_choices = ((0, '在线'), (1, '下线'), (2, '挂牌'), (3, '备用'))
    ha_choices = ((1, '主设备'), (2, '从设备'), (0, '独立设备'))
    serial_num = models.CharField(
        verbose_name='序列号',
        max_length=200,
        null=False, unique=True)
    manage_ip = models.GenericIPAddressField(verbose_name='管理地址', null=False, default='0.0.0.0')
    name = models.CharField(
        verbose_name='资产名称',
        max_length=100,
        null=False, default='')
    vendor = models.ForeignKey(
        "Vendor",
        verbose_name='供应商',
        related_name='vendor_asset',
        on_delete=models.CASCADE,
        null=True,
        blank=True)
    idc = models.ForeignKey(
        "Idc",
        related_name='idc_asset',
        verbose_name='所属机房',
        on_delete=models.CASCADE,
        null=True,
        blank=True)
    category = models.ForeignKey(
        "Category",
        verbose_name='设备类型',
        related_name='category_asset',
        on_delete=models.CASCADE,
        null=True,
        blank=True)
    model = models.ForeignKey(
        "Model",
        verbose_name='硬件型号',
        related_name='model_asset',
        on_delete=models.CASCADE,
        null=True,
        blank=True)
    soft_version = models.CharField(
        verbose_name='软件版本',
        max_length=200,
        default='',
        null=False)
    patch_version = models.CharField(
        verbose_name='补丁版本',
        max_length=200,
        default='',
        null=True)
    role = models.ForeignKey(
        "Role",
        verbose_name='设备角色',
        related_name='role_asset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True)
    attribute = models.ForeignKey(
        "Attribute",
        verbose_name='网络属性',
        related_name='attribute_asset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True)
    framework = models.ForeignKey(
        "Framework",
        verbose_name='网络架构',
        related_name='framework_asset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True)
    zone = models.ForeignKey(
        "NetZone",
        verbose_name='网络区域',
        related_name='zone_asset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True)
    rack = models.ForeignKey(
        "Rack",
        verbose_name='机柜编号',
        related_name='rack_asset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True)
    idc_model = models.ForeignKey(
        "IdcModel",
        verbose_name='模块',
        related_name='idc_model_asset',
        on_delete=models.SET_NULL,
        null=True,
        blank=True)
    u_location_start = models.IntegerField(
        verbose_name='机架位起始', default=0, validators=[MaxValueValidator(50), MinValueValidator(1)])
    u_location_end = models.IntegerField(
        verbose_name='机架位结束', default=0, validators=[MaxValueValidator(50), MinValueValidator(1)])
    uptime = models.DateField(verbose_name='上线时间', null=True, default=timezone.now)
    expire = models.DateField(verbose_name='维保日期', null=True, blank=True)
    memo = models.TextField(verbose_name='备注', null=True, default='')
    status = models.PositiveSmallIntegerField(
        verbose_name='状态', choices=status_choices, default=0)
    ha_status = models.PositiveSmallIntegerField(
        verbose_name='HA状态', choices=ha_choices, default=0)
    chassis = models.IntegerField(verbose_name='机框编号', default=0)
    slot = models.IntegerField(verbose_name='槽位编号', default=0)
    auto_enable = models.BooleanField(verbose_name="自动化纳管", null=False, default=True)
    account = models.ManyToManyField('AssetAccount', verbose_name='管理账户', blank=True)
    plan = models.ForeignKey("automation.CollectionPlan", verbose_name='采集方案',
                             blank=True, null=True, related_name='releate_device', on_delete=models.SET_NULL)
    bgbu = models.ManyToManyField("users.BgBu", verbose_name='BGBU', blank=True)

    def __str__(self):
        return '{}_{}_{}'.format(self.manage_ip, self.name, self.idc.name)

    def account_list(self):
        return ','.join([i.name for i in self.account.all()])

    class Meta:
        unique_together = (("rack", "u_location_start", "u_location_end"),)
        verbose_name = '网络设备表'
        verbose_name_plural = '网络设备表'
        db_table = 'asset_networkdevice'  # 通过db_table自定义数据表名
        indexes = [models.Index(fields=['manage_ip', ]),
                   models.Index(fields=['serial_num', ]),
                   models.Index(fields=['name', ]),
                   models.Index(fields=['soft_version', ]),
                   models.Index(fields=['patch_version', ]),
                   models.Index(fields=['uptime', ]),
                   models.Index(fields=['expire', ]),
                   models.Index(fields=['status', ]),
                   ]
        index_together = ['manage_ip', 'name']


class AdminRecord(models.Model):
    record_modes = (
        ('ssh', 'ssh'),
        ('guacamole', 'guacamole')
    )

    admin_login_user = models.ForeignKey(
        'users.UserProfile',
        verbose_name='用户',
        related_name='admin_record',
        on_delete=models.CASCADE)
    admin_server = models.CharField(max_length=32, verbose_name='登录主机')
    admin_remote_ip = models.GenericIPAddressField(verbose_name='远程地址')
    admin_start_time = models.CharField(max_length=64, verbose_name='开始时间')
    admin_login_status_time = models.CharField(
        max_length=16, verbose_name='登录时长')
    admin_record_file = models.CharField(max_length=256, verbose_name='操作记录')
    admin_record_mode = models.CharField(
        max_length=10,
        choices=record_modes,
        verbose_name='登录协议',
        default='ssh')

    class Meta:
        db_table = 'asset_admin_record'
        verbose_name = '登录管理用户记录表'
        verbose_name_plural = '登录管理用户记录表'