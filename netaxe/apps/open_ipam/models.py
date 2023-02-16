import csv
import json
import sys
import time
from io import StringIO

from ipaddress import ip_address

import openpyxl
from django.db import models

from cidrfield.models import IPNetworkField
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError

# from users.models import OpLogs


class CsvImportException(Exception):
    pass


class Subnet(models.Model):
    subnet_id = models.IntegerField(default=0, verbose_name='网段ID')
    name = models.CharField(max_length=100, db_index=True, verbose_name='名称')
    subnet = IPNetworkField(db_index=True, verbose_name='子网段')
    mask = models.IntegerField(default=24, verbose_name='掩码')
    freehosts_percent = models.FloatField(verbose_name='空闲率', blank=True, null=True, default=0)
    description = models.CharField(max_length=300, blank=True, verbose_name='描述', null=True)

    master_subnet = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='child_subnet_set',
        verbose_name='上一级子网段'
    )

    class Meta:
        # abstract = True
        ordering = ['subnet']
        db_table = 'ipam_subnet'  # 通过db_table自定义数据表名
        indexes = [
            models.Index(fields=['subnet'], name='subnet_idx'),
            models.Index(fields=['name'], name='name'),
        ]
        verbose_name = _('子网网段表')
        verbose_name_plural = _('子网网段表')

    def __str__(self):
        return f' {self.subnet}'

    def _read_row(self, reader):
        value = next(reader)
        if len(value) > 0:
            return value[0].strip()
        return None

    def clean(self):
        if not self.subnet:
            return

        self._validate_multitenant_unique_child_subnet()

    def _validate_multitenant_unique_child_subnet(self):

        qs = self._meta.model.objects.exclude(id=self.pk).filter(subnet=self.subnet)
        if qs.exists():
            raise ValidationError(
                {
                    'subnet': _(
                        'This subnet is already exists'
                    )
                }
            )

    def _get_csv_reader(self, file):
        if file.name.endswith(('.xlsx')):
            book = openpyxl.load_workbook(filename=file)
            sheet = book.worksheets[0]
            reader = sheet.values
        else:
            reader = csv.reader(StringIO(file.read().decode('utf-8')), delimiter=',')
        return reader

    def import_csv(self, file):
        reader = self._get_csv_reader(file)
        self._read_subnet_import_data(reader)
        # next(reader)
        # next(reader)
        # self._read_ipaddress_data(reader, subnet)

    # 读取subnet导入的excel
    def _read_subnet_import_data(self, reader):
        subnet_model = Subnet

        try:
            # 需要优先导入父级网段
            for row in reader:
                # print(row)
                description = str(row[3] or '').strip()
                master_subnet_name = str(row[4] or '').strip()
                # 判断不存在父级网段
                if not master_subnet_name:
                    if not subnet_model.objects.filter(
                            subnet=row[0].strip(),
                    ).exists():
                        # 如果不存在则创建新的实例
                        instance = subnet_model(
                            subnet=row[0].strip(),
                            name=row[0].strip(),
                            mask=row[2].strip(),
                            description=description,
                        )

                        try:

                            instance.full_clean()
                        except ValueError as e:
                            raise CsvImportException(str(e))
                        # subnet_list.append(instance)
                        print('保存不包括父级网段', instance.subnet)
                        instance.save()
                else:
                    # 准备保存带父级网段
                    if not subnet_model.objects.filter(
                            subnet=row[0].strip(),
                    ).exists():
                        instance = subnet_model(
                            subnet=row[0].strip(),
                            name=row[0].strip(),
                            mask=row[2].strip(),
                            description=description,
                        )
                        instance.master_subnet = subnet_model.objects.filter(subnet=master_subnet_name).first()
                        try:

                            instance.full_clean()
                        except ValueError as e:
                            raise CsvImportException(str(e))
                        # subnet_list.append(instance)
                        print('保存带父级网段', instance.subnet)

                        instance.save()
        except ValidationError as e:
            raise CsvImportException(str(e))

    def export_csv(self, subnet_id, writer):
        ipaddress_model = IpAddress
        subnet = Subnet.objects.get(pk=subnet_id)
        writer.writerow([subnet.name])
        writer.writerow([subnet.subnet])
        # writer.writerow([subnet.organization.slug] if subnet.organization else '')
        writer.writerow('')
        fields = [
            ipaddress_model._meta.get_field('ip_address'),
            ipaddress_model._meta.get_field('description'),
        ]
        writer.writerow(field.name for field in fields)  # 写字段名称
        for obj in subnet.ipaddress_set.all():
            row = []
            for field in fields:
                row.append(str(getattr(obj, field.name)))
            writer.writerow(row)  # 写字段内容

    def get_next_available_ip(self):
        ipaddress_set = [ip.ip_address for ip in self.ipaddress_set.all()]
        # NOTE: Shim for Python 3.7
        # In Python < 3.8, subnet.hosts() does not include network
        # address if prefixlen of subnet is 32.
        # See https://bugs.python.org/issue28577.
        py_major_ver, py_minor_ver, _, _, _ = sys.version_info[:]
        if self.subnet.prefixlen == 32 and py_major_ver == 3 and py_minor_ver < 8:
            subnet_hosts = [self.subnet.network_address]
        else:
            subnet_hosts = self.subnet.hosts()
        for host in subnet_hosts:
            if str(host) not in ipaddress_set:
                return str(host)
        return None

    # def update(self, **kwargs):
    #     print('=====================', kwargs)
    #     return super(Subnet, self).update(**kwargs)

    # def create(self, *args, **kwargs):
    #     print('==========create', kwargs)
    #     return super().create(*args, **kwargs)

    # def save(self, *args, **kwargs):
    #     # print('==========save', *args, **kwargs)
    #     # re_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    #     # oprate_data = {
    #     #     're_time': re_time,  # 请求时间
    #     #     'access_time': 10,  # 请求时间
    #     #     're_url': "ipam/subnet",  # 请求url
    #     #     're_method': 'POST',  # 请求方法
    #     #     're_content': "测试测试测试",  # 请求参数
    #     # }
    #     # OpLogs.objects.create(**oprate_data)
    #     return super().save(*args, **kwargs)


class IpAddress(models.Model):
    tag_choices = ((1, '空闲'), (2, '已分配已使用'), (3, '保留'), (4, '未分配已使用'), (6, '已分配未使用'), (7, '自定义空闲'))
    subnet = models.ForeignKey(Subnet, on_delete=models.CASCADE, verbose_name='归属子网段')

    ip_address = models.GenericIPAddressField(verbose_name='IP地址', unique=True)
    description = models.CharField(max_length=500, blank=True, verbose_name='描述信息', null=True)
    tag = models.PositiveSmallIntegerField(verbose_name='状态标签', choices=tag_choices, default=1)
    # bgbu = models.ManyToManyField("BgBu", blank=True)
    editDate = models.DateField(blank=True, auto_now=True, null=True, verbose_name='编辑时间')
    lastScan = models.DateField(blank=True, auto_now=True, null=True)
    lastDiscovery = models.DateField(blank=True, auto_now=True, null=True)
    lastOnlineTime = models.DateField(blank=True, auto_now=True, null=True, verbose_name='最近在线时间')

    class Meta:
        # abstract = True
        ordering = ['ip_address']
        indexes = [models.Index(fields=['ip_address', ]),
                   models.Index(fields=['description', ]),
                   models.Index(fields=['lastOnlineTime', ]),

                   ]
        db_table = 'ipam_ip_address'  # 通过db_table自定义数据表名
        verbose_name = _('网络地址表')
        verbose_name_plural = _('网络地址表')

    def __str__(self):
        return self.ip_address

    def import_csv(self, file):
        reader = self._get_csv_reader(file)

        # subnet =  self._read_subnet_import_data(reader)
        # next(reader)
        # next(reader)
        subnet = ''
        self._read_ipaddress_data(reader, subnet)

    def _get_csv_reader(self, file):
        if file.name.endswith(('.xlsx')):
            book = openpyxl.load_workbook(filename=file)
            sheet = book.worksheets[0]
            reader = sheet.values
        else:
            reader = csv.reader(StringIO(file.read().decode('utf-8')), delimiter=',')
        return reader

    def _read_ipaddress_data(self, reader, subnet):
        ipaddress_model = IpAddress
        # ipaddress_list = []
        for row in reader:
            # print('row', row)
            # description = json.loads(str(row[4] or '').strip())
            description = str(row[4] or '').strip()
            # if not ipaddress_model.objects.filter(
            #         ip_address=row[1].strip(),
            # ).exists():
            instance = ipaddress_model(
                ip_address=row[1].strip(),
                description=description,
                tag=row[2]
            )
            instance.subnet = Subnet.objects.filter(subnet=row[0]).first()
            instance.save()


# class BgBu(models.Model):
#     """ """
#     name = models.CharField(verbose_name='业务线名称', max_length=20, null=False, unique=True)
#
#     # def user_list(self):
#     #     return ','.join([i.username for i in self.authusers_set.all()])
#
#     def __str__(self):
#         return self.name
#
#     class Meta:
#         verbose_name = '业务线表'
#         verbose_name_plural = '业务线表'
#         db_table = 'ipam_bgbu'  # 通过db_table自定义数据表名
#         indexes = [models.Index(fields=['name', ]), ]


class TagsModel(models.Model):
    bg_color = models.CharField(max_length=100, blank=True, verbose_name='bg_color')
    compress = models.CharField(max_length=100, blank=True, verbose_name='compress')
    fg_color = models.CharField(max_length=100, blank=True, verbose_name='fgcolor')
    locked = models.CharField(max_length=100, blank=True, verbose_name='locked')
    type = models.CharField(max_length=100, blank=True, verbose_name='type')
    show_tag = models.BooleanField(verbose_name='showtag')

    class Meta:
        # abstract = True
        db_table = 'ipam_tags'  # 通过db_table自定义数据表名
        verbose_name = _('网络地址标签表')
        verbose_name_plural = _('网络地址标签表')
