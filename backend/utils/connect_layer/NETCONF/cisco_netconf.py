#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import division
from .netconf_connect import CiscoNetconfConnect


class CiscoSoftwareConfig(CiscoNetconfConnect):

    def __init__(self, *args, **kwargs):
        super(CiscoSoftwareConfig, self).__init__(*args, **kwargs)
        self.device_type = kwargs.get("device_type")
        self.netconf_dict = {
            "device_params": {"name": "nexus"},
            "host": self.host,
            "port": 22,
            "timeout": kwargs.get("timeout") if kwargs.get("timeout") else 30,
            "username": self.user,
            "password": self.password,
            "hostkey_verify": False,
            "allow_agent": False,
            "look_for_keys": False
        }
        self.exec_conf_prefix = """
        <nc:config xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <configure xmlns="http://www.cisco.com/nxos:1.0:vlan_mgr_cli">
        <__XML__MODE__exec_configure>
        """
        self.exec_conf_postfix = """
        </__XML__MODE__exec_configure>
        </configure>
        </nc:config>
        """

    def enablevlan(self,vlanid,vlanname):
        xml = '''
        <vlan>
        <vlan-id-create-delete>
        <__XML__PARAM_value>%s</__XML__PARAM_value>
        <__XML__MODE_vlan>
        <name>
        <vlan-name>%s</vlan-name>
        </name>
        <state>
        <vstate>active</vstate>
        </state>
        <no>
        <shutdown/>
        </no>
        </__XML__MODE_vlan>
        </vlan-id-create-delete>
        </vlan>
        '''% (vlanid, vlanname)
        res = self.edit_config(self.exec_conf_prefix + xml + self.exec_conf_postfix)
        print(res)
        return res

    def enable_vlan_on_trunk_int(self, interface, vlanid):
        xml = """
        <interface>
        <ethernet>
        <interface>%s</interface>
        <__XML__MODE_if-ethernet-switch>
        <switchport>
        <trunk>
        <allowed>
        <vlan>
        <add>
        <__XML__BLK_Cmd_switchport_trunk_allowed_allow-vlans>
        <add-vlans>%s</add-vlans>
        </__XML__BLK_Cmd_switchport_trunk_allowed_allow-vlans>
        </add>
        </vlan>
        </allowed>
        </trunk>
        </switchport>
        </__XML__MODE_if-ethernet-switch>
        </ethernet>
        </interface>
        """% (interface, vlanid)
        res = self.edit_config(self.exec_conf_prefix + xml + self.exec_conf_postfix)
        print(res)
        return res

    def disable_vlan_on_trunk_int(self, interface, vlanid):
        xml = '''
        <nc:config xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <configure xmlns="http://www.cisco.com/nxos:1.0:vlan_mgr_cli">
        <__XML__MODE__exec_configure>
        <interface>
        <ethernet>
        <interface>%s</interface>
        <__XML__MODE_if-ethernet-switch>
        <switchport>
        <trunk>
        <allowed>
        <vlan>
        <remove>
        <__XML__BLK_Cmd_switchport_trunk_allowed_allow-vlans>
        <remove-vlans>%s</remove-vlans>
        </__XML__BLK_Cmd_switchport_trunk_allowed_allow-vlans>
        </remove>
        </vlan>
        </allowed>
        </trunk>
        </switchport>
        </__XML__MODE_if-ethernet-switch>
        </ethernet>
        </interface>
        </__XML__MODE__exec_configure>
        </configure>
        </nc:config>
        '''% (interface, vlanid)
        res = self.edit_config(self.exec_conf_prefix + xml + self.exec_conf_postfix)
        print(res)
        return res

    def enable_vlan_on_access_int(self, interface, vlanid):
        xml = '''
        <nc:config xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <configure xmlns:m1="http://www.cisco.com/nxos:7.0.3.I7.1.:configure__if-ethernet-all">
        <__XML__MODE__exec_configure>
        <interface>
        <__XML__PARAM__interface>
        <__XML__value>Ethernet1/25</__XML__value>
        <m1:switchport>
        <m1:access>
        <m1:vlan>
        <m1:__XML__PARAM__vlan-id-access>
        <m1:__XML__value>5</m1:__XML__value>
        </m1:__XML__PARAM__vlan-id-access>
        </m1:vlan>
        </m1:access>
        </m1:switchport>
        </__XML__PARAM__interface>
        </interface>
        </__XML__MODE__exec_configure>
        </configure>
        </nf:config>
        '''
        res = self.edit_config(xml)
        print(res)
        return res


class CiscoSoftwareinfoCollection(CiscoNetconfConnect):

    def __init__(self, *args, **kwargs):
        super(CiscoSoftwareinfoCollection, self).__init__(*args, **kwargs)
        self.device_type = kwargs.get("device_type")
        self.netconf_dict = {
            "device_params": {"name": "nexus"},
            "host": self.host,
            "port": 22,
            "timeout": kwargs.get("timeout") if kwargs.get("timeout") else 30,
            "username": self.user,
            "password": self.password,
            "hostkey_verify": False,
            "allow_agent": False,
            "look_for_keys": False
        }

    def colleciton_hostname(self):
        xml = '''
        <show xmlns="http://www.cisco.com/nxos:1.0">
        <hostname>
        </hostname>
        </show>
        '''
        request = self.netconf_get(xml)
        return request

    def colleciton_arp_list(self):
        """
        采集ARP表
        请求的XML命令
        """
        arp_info_xml = '''
        <show>
        <ip>
        <arp/>
        </ip>
        </show>
        '''
        request_arplist = self.netconf_get(arp_info_xml)
        #截取ARP列表
        # arplist = request_arplist['ARP']['ArpTable']['ArpEntry']
        #截图接口索引和name对应
        # ifmgrlist = request_arplist['Ifmgr']['Interfaces']['Interface']
        #两个表格合并，将name加入arp表格

        return request_arplist

    def colleciton_ip_route(self):
        """
        采集路由表
        请求的XML命令
        """
        xml = '''
        <show>
        <ip>
          <route/>
        </ip>
        </show>
        '''
        request_routelist = self.netconf_get(xml)\
            ['mod:show']['mod:ip']['mod:route']['mod:__XML__OPT_Cmd_urib_show_ip_route_command_ip']\
            ['mod:__XML__OPT_Cmd_urib_show_ip_route_command_unicast']['mod:__XML__OPT_Cmd_urib_show_ip_route_command_topology']\
        ['mod:__XML__OPT_Cmd_urib_show_ip_route_command_l3vm-info']['mod:__XML__OPT_Cmd_urib_show_ip_route_command_rpf']\
        ['mod:__XML__OPT_Cmd_urib_show_ip_route_command_ip-addr']['mod:__XML__OPT_Cmd_urib_show_ip_route_command_protocol']\
        ['mod:__XML__OPT_Cmd_urib_show_ip_route_command_summary']['mod:__XML__OPT_Cmd_urib_show_ip_route_command_vrf']\
        ['mod:__XML__OPT_Cmd_urib_show_ip_route_command___readonly__']['mod:__readonly__']['mod:TABLE_vrf']['mod:ROW_vrf']
        vrf_name_out = request_routelist['mod:vrf-name-out']
        routetable = request_routelist['mod:TABLE_addrf']['mod:ROW_addrf']
        addrf= routetable['mod:addrf'] #res: ipv4
        TABLE_prefix = routetable['mod:TABLE_prefix']['mod:ROW_prefix']

        for i in TABLE_prefix:
            print(i)
        return TABLE_prefix

    def collection_device_info(self):
        '''
        构建XML
        :return:
        '''
        xml = '''
        <show>
          <version/>
        </show>
        '''
        res = self.netconf_get(xml)['mod:show']['mod:version']['mod:__XML__OPT_Cmd_sysmgr_show_version___readonly__']\
        ['mod:__readonly__']
        #查看key和value的值
        # for key, value in res.items():
        #     print(key, value)
        return res

    def collection_l3_interface_info(self):
        '''
        查询三层接口信息
        请求的XML
        :return:
        '''
        xml = '''
        <show>
        <ip>
        <interface>
        <brief/>
        </interface>
        </ip>
        </show>
        '''
        res = self.netconf_get(xml)['mod:show']['mod:ip']['mod:interface']['mod:__XML__BLK_Cmd_ip_show_interface_command_brief']\
        ['mod:__XML__OPT_Cmd_ip_show_interface_command_operational']['mod:__XML__OPT_Cmd_ip_show_interface_command_vrf']\
        ['mod:__XML__OPT_Cmd_ip_show_interface_command___readonly__']['mod:__readonly__']['mod:TABLE_intf']
        # 显示结果
        # for i in res:
        #     print(i)
        return res

    def collection_l2_interface_info(self):
        '''
        查询接口状态
        :return:
        '''
        xml = '''
        <show>
        <interface>
        <brief/>
        </interface>
        </show>
        '''
        res = self.netconf_get(xml)['mod:show']['mod:interface']['mod:__XML__OPT_Cmd_show_interface_brief___readonly__']\
        ['mod:__readonly__']['mod:TABLE_interface']['mod:ROW_interface']
        for i in res:
            print(i)
        return res

    def collection_maclist_info(self):
        '''
        查询maclist表项
        :return:
        '''
        xml = '''
        <show>
        <mac>
        <address-table/>
        </mac>
        </show>
        '''
        res = self.netconf_get(xml)['mod:show']['mod:mac']['mod:address-table']['mod:__XML__OPT_Cmd_show_mac_addr_tbl_static']\
        ['mod:__XML__OPT_Cmd_show_mac_addr_tbl_local']['mod:__XML__OPT_Cmd_show_mac_addr_tbl_address']\
        ['mod:__XML__OPT_Cmd_show_mac_addr_tbl___readonly__']['mod:__readonly__']
        # header = res['mod:header'] #头部解释信息，等同于show mac address-list 的头部
        mactable = res['mod:TABLE_mac_address']['mod:ROW_mac_address']
        # print(mactable)
        for key, value in mactable.items():
            print(key, value)
        return mactable

    def collection_config_info(self):
        '''
        show running-confg
        :return:
        '''
        xml = '''
        show running-config
        '''
        res = self.netconfig_get_config()
        #print(res)
        return res

    def colleciton_vlan_info(self):

        xml = '''
        <show xmlns="http://www.cisco.com/nxos:1.0">
        <vlan>
        </vlan>
        </show>
        '''
        res = self.netconf_get(xml)['vlan_mgr_cli:show']['vlan_mgr_cli:vlan']['vlan_mgr_cli:__XML__OPT_Cmd_show_vlan___readonly__']\
        ['vlan_mgr_cli:__readonly__']['vlan_mgr_cli:TABLE_vlanbrief']['vlan_mgr_cli:ROW_vlanbrief']
        for key,value in res.items():
            print(key,value)
        return res

    def command(self,command):
        '''

        :return:
        '''

        res = self.run_cmd(command)
        return res

    def collection_running_config(self):
        '''
        通过get-config方法获取设备配置
        :return:
        '''
        request_info = self.netconfig_get_config()
        return request_info


if __name__ == '__main__':
    pass