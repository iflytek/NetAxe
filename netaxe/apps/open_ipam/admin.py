import csv
import sys
from collections import OrderedDict
from functools import update_wrapper

from django import forms
from django.contrib import admin, messages

# Register your models here.
from django.contrib.admin.models import LogEntry
from django.db.models import TextField
from django.db.models.functions import Cast
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import re_path, path, reverse

from .models import Subnet, IpAddress, CsvImportException, TagsModel
from import_export.admin import ImportExportModelAdmin
from django.utils.translation import gettext_lazy as _

# from reversion.admin import VersionAdmin
from .tools.forms import IpAddressImportForm
from .views import HostsSet


@admin.register(Subnet)
class AdminSubnetModel(ImportExportModelAdmin):
    """自定义网段显示字段"""
    list_display = ['subnet', 'subnet_id', 'mask', 'description', 'master_subnet']
    list_filter = ['subnet', 'subnet_id', 'mask', 'description', 'master_subnet']
    # Related Field got invalid lookup: icontains
    # 这个错误一般是由于你在admin.py文件里的search_fields使用了外键，而没有指定具体的字段。
    search_fields = ['subnet', 'subnet_id', 'mask', 'description', 'master_subnet__id']
    autocomplete_fields = ['master_subnet']
    # list_select_related = ['master_subnet']
    change_form_template = 'admin/openwisp-ipam/subnet/change_form.html'
    change_list_template = 'admin/openwisp-ipam/subnet/change_list.html'
    app_label = 'open_ipam'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        instance = self.get_object(request, object_id)
        print("网段实例", instance)
        if instance is None:
            # This is an internal Django method that redirects the
            # user to the admin index page with a message that points
            # out that the requested object does not exist.
            return self._get_obj_does_not_exist_redirect(
                request, self.model._meta, object_id
            )
        ipaddress_add_url = 'admin:{0}_ipaddress_add'.format(self.app_label)
        ipaddress_change_url = 'admin:{0}_ipaddress_change'.format(self.app_label)
        subnet_change_url = 'admin:{0}_subnet_change'.format(self.app_label)
        if request.GET.get('_popup'):
            return super().change_view(request, object_id, form_url, extra_context)
        # Find root master_subnet for subnet tree
        instance_root = instance
        while instance_root.master_subnet:
            instance_root = instance_root.master_subnet
        # Get instances for all subnets for root master_subnet
        instance_subnets = Subnet.objects.filter(
            subnet=instance_root.subnet
        ).values('master_subnet', 'pk', 'name', 'subnet')
        # Make subnet tree
        collection_depth = 0
        subnet_tree = [instance_subnets]
        while instance_subnets:
            instance_subnets = Subnet.objects.none()
            for slave_subnet in subnet_tree[collection_depth]:
                instance_subnets = instance_subnets | Subnet.objects.filter(
                    master_subnet=slave_subnet['pk']
                ).values('master_subnet', 'pk', 'name', 'subnet')
            subnet_tree.append(instance_subnets)
            collection_depth += 1
        subnet_ip_address_usage_list = list(instance.ipaddress_set.values())
        # free = len([i for i in subnet_ip_address_usage_list if i['tag'] == 0])
        has_allocated_and_used = len([i for i in subnet_ip_address_usage_list if i['tag'] == 2])
        reserve = len([i for i in subnet_ip_address_usage_list if i['tag'] == 3])
        not_allocated_but_used = len([i for i in subnet_ip_address_usage_list if i['tag'] == 4])
        has_allocated_not_used = len([i for i in subnet_ip_address_usage_list if i['tag'] == 6])
        self_not_used = len([i for i in subnet_ip_address_usage_list if i['tag'] == 7])
        # print(instance.ipaddress_set.values())
        # HasAllocatedAndUsed = instance.ipaddress_set.count()

        # Storing UUID corresponding to respective IP address in a dictionary
        ip_id_list = (
            IpAddress.objects.filter(subnet=instance)
                .annotate(str_id=Cast('id', output_field=TextField()))
                .values_list('ip_address', 'str_id')
        )

        # Converting UUIdField to String and then modifying to convert back to uuid form
        ip_id_list = OrderedDict(ip_id_list)
        ip_uuid = {}
        for ip_addr, Ip in ip_id_list.items():
            # ip_uuid[ip_addr] = f'{Ip[0:8]}-{Ip[8:12]}-{Ip[12:16]}-{Ip[16:20]}-{Ip[20:]}'
            # TODO 修复ip_uuid 自带‘----’ bug
            ip_uuid[ip_addr] = f'{Ip[0:8]}{Ip[8:12]}{Ip[12:16]}{Ip[16:20]}{Ip[20:]}'
        free = HostsSet(
            instance).count() - has_allocated_and_used - not_allocated_but_used - has_allocated_not_used - reserve

        labels = ['空闲', '已分配已使用', '保留', '未分配已使用', '已分配未使用', '自定义空闲']
        # print('已分配已使用', has_allocated_and_used)
        # print('空闲', free)
        # print('未分配已使用', not_allocated_but_used)
        # print('已分配未使用', has_allocated_not_used)
        # print('保留', reserve)
        values = [free, has_allocated_and_used, reserve, not_allocated_but_used, has_allocated_not_used, self_not_used]
        extra_context = {
            'labels': labels,
            'values': values,
            'original': instance,
            'ip_uuid': ip_uuid,
            'ipaddress_add_url': ipaddress_add_url,
            'ipaddress_change_url': ipaddress_change_url,
            'subnet_change_url': subnet_change_url,
            'subnet_tree': subnet_tree,
        }
        return super().change_view(request, object_id, form_url, extra_context)

    # save_on_top = True

    def _check_perm(self, view, perm):
        admin_site = self.admin_site

        def inner(request, *args, **kwargs):
            if not request.user.has_perm(f'{self.app_label}.{perm}'):
                return redirect(
                    reverse('admin:index', current_app=admin_site.name),
                )
            return view(request, *args, **kwargs)

        return update_wrapper(inner, view)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            re_path(
                r'^(?P<subnet_id>[^/]+)/export-subnet/',
                self._check_perm(self.export_view, 'change_subnet'),
                name='ipam_export_subnet',
            ),
            path(
                'import-subnet/',
                self._check_perm(self.import_view, 'add_subnet'),
                name='ipam_import_subnet',
            ),
        ]
        return custom_urls + urls

    def export_view(self, request, subnet_id):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="subnet.csv"'
        writer = csv.writer(response)
        Subnet().export_csv(subnet_id, writer)
        return response

    def import_view(self, request):
        form = IpAddressImportForm()
        form_template = 'admin/openwisp-ipam/subnet/import.html'
        subnet_list_url = f'admin:{self.app_label}_{Subnet._meta.model_name}_changelist'
        context = {
            'form': form,
            'subnet_list_url': subnet_list_url,
            'has_permission': True,
        }
        if request.method == 'POST':
            form = IpAddressImportForm(request.POST, request.FILES)
            context['form'] = form
            if form.is_valid():
                file = request.FILES['csvfile']
                # try:
                #     self.assert_organization_permissions(request)
                # except Exception as e:
                #     messages.error(request, str(e))
                #     return redirect(reverse(context['subnet_list_url']))
                if not file.name.endswith(('.csv', '.xls', '.xlsx')):
                    messages.error(request, _('File type not supported.'))
                    return render(request, form_template, context)
                try:
                    Subnet().import_csv(file)
                except CsvImportException as e:
                    messages.error(request, str(e))
                    return render(request, form_template, context)
                messages.success(request, _('Successfully imported data.'))
                return redirect(reverse(context['subnet_list_url']))
        return render(request, form_template, context)

    class Media:
        js = (
            'admin/js/jquery.init.js',
            'admin/js/SelectBox.js',
            'openwisp-ipam/js/subnet.js',
            'openwisp-ipam/js/minified/jstree.min.js',
            'openwisp-ipam/js/minified/plotly.min.js',
        )
        css = {
            'all': (
                'openwisp-ipam/css/admin.css',
                'openwisp-ipam/css/minified/jstree.min.css',
            )
        }


class IpAddressAdminForm(forms.ModelForm):
    class Meta:
        help_texts = {
            'subnet': _(
                '选择一个子网,'
                'IP地址字段会自动提示第一个可用的IP地址'
            )
        }


@admin.register(IpAddress)
class AdminIpAddressModel(ImportExportModelAdmin):
    """自定义IP地址显示字段"""
    list_display = ['ip_address', 'subnet', 'description', 'tag', 'get_bgbu', 'lastOnlineTime']
    # list_filter = ['ip_address', 'subnet', 'description', 'tag', 'lastOnlineTime']
    search_fields = ['ip_address', 'subnet__name', 'description', 'tag', 'lastOnlineTime']
    autocomplete_fields = ['subnet']
    multitenant_parent = 'subnet'
    form = IpAddressAdminForm
    change_form_template = 'admin/openwisp-ipam/ip_address/change_form.html'
    change_list_template = 'admin/openwisp-ipam/ip_address/change_list.html'
    app_label = 'open_ipam'

    # save_on_top = True

    class Media:
        js = (
            'admin/js/jquery.init.js',
            'openwisp-ipam/js/ip-request.js',
        )

    def get_bgbu(self, instance):
        return [bgbu.name for bgbu in instance.bgbu.all()]

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            # re_path(
            #     r'^(?P<subnet_id>[^/]+)/import-ip-address/',
            #     self._check_perm(self.export_view, 'change_ip_address'),
            #     name='ipam_export_ip_address',
            # ),
            path(
                'import-ip-address/',
                self._check_perm(self.import_view, 'add_ip_address'),
                name='ipam_import_ip_address',
            ),
        ]
        return custom_urls + urls

    def _check_perm(self, view, perm):
        admin_site = self.admin_site

        def inner(request, *args, **kwargs):
            if not request.user.has_perm(f'{self.app_label}.{perm}'):
                return redirect(
                    reverse('admin:index', current_app=admin_site.name),
                )
            return view(request, *args, **kwargs)

        return update_wrapper(inner, view)

    def get_extra_context(self):
        url = reverse('get_next_available_ip', args=['0000'])
        # print('url', url)
        return {'get_next_available_ip_url': url}

    def add_view(self, request, form_url='', extra_context=None):
        return super().add_view(request, form_url, self.get_extra_context())

    def change_view(self, request, object_id, form_url='', extra_context=None):
        # self.fields = ('ip_address', 'subnet__name', 'description', 'tag',)
        # self.readonly_fields = ('lastOnlineTime')
        return super().change_view(
            request, object_id, form_url, self.get_extra_context()
        )

    def response_add(self, request, *args, **kwargs):
        """
        Custom reponse to dismiss an add form popup for IP address.
        """
        response = super().response_add(request, *args, **kwargs)
        if request.POST.get('_popup'):
            return HttpResponse(
                f"""
<script type='text/javascript'>
    opener.dismissAddAnotherPopup(window, '{request.POST.get('ip_address')}');
</script>
                """
            )
        return response

    def response_change(self, request, *args, **kwargs):
        """
        Custom reponse to dismiss a change form popup for IP address.
        """
        response = super().response_change(request, *args, **kwargs)
        if request.POST.get('_popup'):
            return HttpResponse(
                """
<script type='text/javascript'>
    opener.dismissAddAnotherPopup(window);
</script>
             """
            )
        return response

    def import_view(self, request):
        form = IpAddressImportForm()
        form_template = 'admin/openwisp-ipam/ip_address/import.html'
        ip_address_list_url = f'admin:{self.app_label}_{IpAddress._meta.model_name}_changelist'
        context = {
            'form': form,
            'ip_address_list_url': ip_address_list_url,
            'has_permission': True,
        }
        if request.method == 'POST':
            form = IpAddressImportForm(request.POST, request.FILES)
            context['form'] = form
            if form.is_valid():
                file = request.FILES['csvfile']
                # try:
                #     self.assert_organization_permissions(request)
                # except Exception as e:
                #     messages.error(request, str(e))
                #     return redirect(reverse(context['subnet_list_url']))
                if not file.name.endswith(('.csv', '.xls', '.xlsx')):
                    messages.error(request, _('File type not supported.'))
                    return render(request, form_template, context)
                try:
                    IpAddress().import_csv(file)
                except CsvImportException as e:
                    messages.error(request, str(e))
                    return render(request, form_template, context)
                messages.success(request, _('Successfully imported data.'))
                return redirect(reverse(context['ip_address_list_url']))

        return render(request, form_template, context)


# admin.site.register(Subnet, AdminSubnetModel)
# admin.site.register(IpAddress, AdminIpAddressModel)

# @admin.register(BgBu)
# class AdminBgBuModel(admin.ModelAdmin):
#     """自定义BGBU显示字段"""
#     list_display = ['name']
#     list_filter = ['name']
#     search_fields = ['name']
#     # autocomplete_fields = ['name']


@admin.register(TagsModel)
class AdminTagsModel(admin.ModelAdmin):
    """自定义BGBU显示字段"""
    list_display = ['bg_color', 'compress', 'fg_color', 'locked', 'type', 'show_tag']
    list_filter = ['bg_color', 'compress', 'fg_color', 'locked', 'type', 'show_tag']
    search_fields = ['bg_color', 'compress', 'fg_color', 'locked', 'type', 'show_tag']


# 添加 admin后台操作日志
# class LogEntryAdmin(admin.ModelAdmin):
#     list_display = ['object_repr', 'object_id', 'action_flag', 'user', 'change_message', 'object_repr']
#     list_filter = ('user', 'action_flag')
#     search_fields = ['action_flag', 'user', 'change_message']
#
#
# admin.site.register(LogEntry, LogEntryAdmin)
admin.site.site_header = 'NetAxe网络运维管理系统'
admin.site.site_title = 'NetAxe网络运维管理系统'
admin.site.index_title = 'NetAxe网络运维管理后台'
