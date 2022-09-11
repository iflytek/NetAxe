#!/usr/bin/env python
# -*- coding:utf-8 -*-

import base64
import json
import re
import xmltodict
from xml.dom.minidom import parseString
from ncclient import manager
from ncclient.operations import RPCError
from netaddr import IPAddress


class H3CNetconf(object):
    """H3C设备netconf专用连接类"""

    def __init__(self, *args, **kwargs):
        self.host = kwargs.get("host")
        self.user = kwargs.get("user")
        self.password = kwargs.get("password")
        self.netconf_dict = {
            "device_params": {"name": kwargs.get("device_params") if kwargs.get("device_params") else "h3c"},
            "host": self.host,
            "port": 830,
            "timeout": kwargs.get("timeout") if kwargs.get("timeout") else 3600,
            "username": self.user,
            "password": self.password,
            "hostkey_verify": False,
            "allow_agent": False,
            "look_for_keys": False
        }
        self.netconf_session = manager.connect(**self.netconf_dict)
        self.server_capabilities = self.netconf_session.server_capabilities
        self.client_capabilities = self.netconf_session.client_capabilities

    def get_schema(self, name):
        return self.netconf_session.get_schema(name, version='1.0')

    def closed(self):
        return self.netconf_session.close_session()

    def netconf_get(self, data):
        res = self.netconf_session.get(('subtree', data))
        mxl = json.dumps(xmltodict.parse(parseString(str(res.xml)).toprettyxml()))
        result = json.loads(mxl)["rpc-reply"]["data"]
        return result

    def netconf_get_bulk(self, data):
        res = self.netconf_session.get_bulk(('subtree', data))
        mxl = json.dumps(xmltodict.parse(parseString(str(res.xml)).toprettyxml()))
        result = json.loads(mxl)["rpc-reply"]["data"]
        return result

    def netconf_get_schema(self, identifier, version=None, format=None):
        #  schema_res = device.netconf_get_schema(identifier='comware-top-config', version='2014-10-12', format='yang')
        res = self.netconf_session.get_schema(identifier, version=version, format=format)
        mxl = json.dumps(xmltodict.parse(parseString(str(res.xml)).toprettyxml()))
        result = json.loads(mxl)["rpc-reply"]["data"]
        return result

    def get_capabilities(self):
        # with manager.connect(**self.netconf_dict) as netconf_session:
        #     return netconf_session.client_capabilities
        data = """
         <netconf-state xmlns='urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring'>
                  <capabilities/>
         </netconf-state>
         """
        res = self.netconf_get(data=data)
        # print(res['netconf-state']['capabilities'].keys())
        return res['netconf-state']['capabilities']['capability']

    def lock(self):
        res = self.netconf_session.locked(target='running')
        xml_str = parseString(str(res))
        if xml_str.toprettyxml().find('<ok/>') != -1:
            return True
        else:
            return False, xml_str.toprettyxml()

    def netconf_cli(self, data):
        res = self.netconf_session.cli(data)
        mxl = json.dumps(xmltodict.parse(parseString(str(res.xml)).toprettyxml()))
        result = json.loads(mxl)["rpc-reply"]["CLI"]["Execution"]
        return result

    def netconfig_get_config(self):
        res = self.netconf_session.get_config(source='running')
        # res = self.netconf_session.get_config(('running', data))
        mxl = json.dumps(xmltodict.parse(parseString(str(res.xml)).toprettyxml()))
        result = json.loads(mxl)["rpc-reply"]["data"]
        return result

    def edit_config(self, xml_data):
        try:
            res = self.netconf_session.edit_config(target='running', config=xml_data)
            xml_str = parseString(str(res))
            if xml_str.toprettyxml().find('<ok/>') != -1:
                return True
            else:
                return False, xml_str.toprettyxml()
        except Exception as e:
            return False, 'Exception:{}'.format(e)

    def save_config(self):
        try:
            res = self.netconf_session.save(file='test.cfg')
            xml_str = parseString(str(res))
            if xml_str.toprettyxml().find('<ok/>') != -1:
                return True
            else:
                return False, xml_str.toprettyxml()
        except Exception as e:
            return False, 'Exception:{}'.format(e)

    def _action(self, data):
        '''
        下发动作
        :param data:
        :return:
        '''
        try:
            res = self.netconf_session.action(data)
            xml_str = parseString(str(res))
            if xml_str.toprettyxml().find('<ok/>') != -1:
                return True
            else:
                return False, xml_str.toprettyxml()
        except Exception as e:
            return False, 'Exception:{}'.format(e)

    def rollback(self):
        '''
        配置在线回滚
        :return:
        '''
        try:
            res = self.netconf_session.rollback(file='test.cfg')
            xml_str = parseString(str(res))
            if xml_str.toprettyxml().find('<ok/>') != -1:
                return True
            else:
                return False, xml_str.toprettyxml()
        except Exception as e:
            return False, 'Exception:{}'.format(e)

    def colleciton_arp_list(self):
        """
        采集ARP表
        请求的XML命令
        """
        obtain_h3c_arp_info_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <ARP>
            <ArpTable>
                <ArpEntry>
                    <IfIndex></IfIndex>
                    <Ipv4Address></Ipv4Address>
                    <MacAddress></MacAddress>
                    <VLANID></VLANID>
                    <PortIndex></PortIndex>
                    <VrfIndex></VrfIndex>
                    <ArpType></ArpType>
                </ArpEntry>
            </ArpTable>
        </ARP>
        <Ifmgr>
            <Interfaces>
                <Interface>
                    <IfIndex></IfIndex>
                    <Name></Name>
                    <PortIndex></PortIndex>
                </Interface>
            </Interfaces>
        </Ifmgr>
        </top>
        '''
        request_arplist = self.netconf_get(obtain_h3c_arp_info_xml)["top"]
        # 截取ARP列表
        arplist = request_arplist['ARP']['ArpTable']['ArpEntry']
        # 接口索引和name对应
        ifmgrlist = request_arplist['Ifmgr']['Interfaces']['Interface']
        # for i in ifmgrlist:
        #     print(i)
        # 两个表格合并，将name加入arp表格
        if isinstance(arplist, dict):
            arplist = [arplist]
        for a in arplist:
            for b in ifmgrlist:
                if a['IfIndex'] == b['IfIndex']:
                    a.update(Name=b['Name'])
        for a in arplist:
            for b in ifmgrlist:
                if a.get('PortIndex'):
                    if a['PortIndex'] == b.get('PortIndex'):
                        a['Name'] = b['Name']

        return arplist

    def colleciton_interface_list(self):
        """
        请求的XML_
        """
        obtain_interfaces_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <Ifmgr>
          <Interfaces>
           <Interface>
             <IfIndex></IfIndex>
             <Name></Name>
             <AbbreviatedName></AbbreviatedName>
             <PortIndex></PortIndex>
             <ifTypeExt></ifTypeExt>
             <ifType></ifType>
             <Description></Description>
             <AdminStatus></AdminStatus>
             <OperStatus></OperStatus>
             <ConfigSpeed></ConfigSpeed>
             <ActualSpeed></ActualSpeed>
             <ConfigDuplex></ConfigDuplex>
             <ActualDuplex></ActualDuplex>
             <LinkType></LinkType>
             <PVID></PVID>
             <InetAddressIPV4></InetAddressIPV4>
             <InetAddressIPV4Mask></InetAddressIPV4Mask>
             <PhysicalIndex></PhysicalIndex>
             <MAC></MAC>
             <PortLayer></PortLayer>
             <ForwardingAttributes></ForwardingAttributes>
             <Loopback></Loopback>
             <MDI></MDI>
             <ConfigMTU></ConfigMTU>
             <ActualMTU></ActualMTU>
             <ConfigBandwidth></ConfigBandwidth>
             <ActualBandwidth></ActualBandwidth>
             <SubPort></SubPort>
             <ForceUP></ForceUP>
           </Interface>
          </Interfaces>
        </Ifmgr>
        </top>
        '''
        res = self.netconf_get(obtain_interfaces_xml)['top']
        if res:
            oper_status_map = {'1': 'up', '2': 'down', '3': 'testing', '4': 'unknown',
                               '5': 'dormant', '6': 'notPresent', '7': 'lowerLayerDown'}
            admin_status_map = {'1': 'admin up', '2': 'admin down'}
            interface_list = res['Ifmgr']['Interfaces']['Interface']
            config_duplex_map = {'1': 'full', '2': 'half', '3': 'auto'}
            actual_duplex_map = {'1': 'full', '2': 'half', '3': 'auto'}
            port_layer_map = {'1': 'layer 2', '2': 'layer 3'}
            # link_type_map = {'1': 'access', '2': 'trunk', '3': 'hybrid'}

            if isinstance(interface_list, list):
                for i in interface_list:
                    i['OperStatus'] = oper_status_map[i['OperStatus']]
                    i['AdminStatus'] = admin_status_map[i['AdminStatus']]
                    if 'ConfigDuplex' in i.keys():
                        i['ConfigDuplex'] = config_duplex_map[i['ConfigDuplex']] \
                            if i['ConfigDuplex'] in [x for x in config_duplex_map.keys()] else i['ConfigDuplex']
                    if 'ActualDuplex' in i.keys():
                        i['ActualDuplex'] = actual_duplex_map[i['ActualDuplex']] \
                            if i['ActualDuplex'] in [x for x in actual_duplex_map.keys()] else i['ActualDuplex']
                    if 'PortLayer' in i.keys():
                        i['PortLayer'] = port_layer_map[i['PortLayer']]
                    if 'ActualSpeed' in i.keys():
                        i['ActualSpeed'] = str(int(int(i['ActualSpeed']) / 1000))
                return interface_list

        return []

    def colleciton_lagg_list(self):
        """
        采集链路聚合信息colleciton_lagg
        其中 聚合组片段中，不支持irf参数，MemberList和SelectedMemberList都是乱码不可用
        LinkMode 1—Static 2—Dynamic
        GroupId: 无符号整数.
            • Layer 2 aggregation group: 1 to 16384.
            • Layer 3 aggregation group: 16385 to 32768.
            • Blade aggregation group: 32769 to 36864.
            • S-channel bundle group: 36865 to 40960.
        """
        obtain_h3c_arp_info_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <LAGG>
            <LAGGGroups>
                <LAGGGroup>
                <GroupId></GroupId>
                <LinkMode></LinkMode>
                <IfIndex></IfIndex>
                </LAGGGroup>
            </LAGGGroups>
            <LAGGMembers>
                <LAGGMember>
                <IfIndex></IfIndex>
                <GroupId></GroupId>
                <SelectedStatus></SelectedStatus> 
                <UnSelectedReason></UnSelectedReason> 
                <LacpEnable></LacpEnable> 
                <LacpMode></LacpMode>
                </LAGGMember>
            </LAGGMembers>
        </LAGG>
        <Ifmgr>
            <Interfaces>
                <Interface>
                    <IfIndex></IfIndex>
                    <Name></Name>
                </Interface>
            </Interfaces>
        </Ifmgr>
        </top>
        '''
        back_obtain_h3c_arp_info_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <LAGG>
            <LAGGGroups>
                <LAGGGroup>
                <GroupId></GroupId>
                <LinkMode></LinkMode>
                <IfIndex></IfIndex>
                </LAGGGroup>
            </LAGGGroups>
            <LAGGMembers>
                <LAGGMember>
                <IfIndex></IfIndex>
                <GroupId></GroupId>
                </LAGGMember>
            </LAGGMembers>
        </LAGG>
        <Ifmgr>
            <Interfaces>
                <Interface>
                    <IfIndex></IfIndex>
                    <Name></Name>
                </Interface>
            </Interfaces>
        </Ifmgr>
        </top>
        '''
        try:
            res = self.netconf_get(obtain_h3c_arp_info_xml)
        except:
            res = self.netconf_get(back_obtain_h3c_arp_info_xml)
        group_list = []
        if res:
            # print(1,res)
            link_mode = {'1': 'Static', '2': 'Dynamic'}
            SelectedStatus_map = {'1': 'Selected.', '2': 'Unselected.', '3': 'Individual.'}
            intf_list = res['top']['Ifmgr']['Interfaces']['Interface']
            if 'LAGGGroups' not in res['top']['LAGG'].keys():
                return []
            group_list = res['top']['LAGG']['LAGGGroups']['LAGGGroup']
            member_list = res["top"]['LAGG']['LAGGMembers']['LAGGMember']
            if isinstance(group_list, dict):
                group_list = [group_list]
            for a in member_list:
                for b in intf_list:
                    if a['IfIndex'] == b['IfIndex']:
                        a.update(Name=b['Name'])
            for a in group_list:
                for b in member_list:
                    if a['GroupId'] == b['GroupId']:
                        if 'SelectedStatus' in b.keys():
                            b['SelectedStatus'] = SelectedStatus_map[b['SelectedStatus']]
                        if 'Memberlist' in a.keys():
                            a['Memberlist'].append(b)
                        else:
                            a['Memberlist'] = [b]
                for b in intf_list:
                    if a['IfIndex'] == b['IfIndex']:
                        a.update(Name=b['Name'])
                a['LinkMode'] = link_mode[a['LinkMode']]
                if int(a['GroupId']) < 16384:
                    a['attr'] = 'Layer 2 aggregation group'
                elif 16385 < int(a['GroupId']) < 32768:
                    a['attr'] = 'Layer 3 aggregation group'
                elif 32769 < int(a['GroupId']) < 36864:
                    a['attr'] = 'Blade aggregation group'
                elif 36865 < int(a['GroupId']) < 40960:
                    a['attr'] = 'S-channel bundle group'
                else:
                    a['attr'] = ''
        return group_list

    def collection_device_PhysicalEntities(self, class_flag=3):
        '''
        构建XML，指定class 类型为3 ，获取软硬件信息
        防护期class 类型为9
        :return:
        '''
        xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <Device>
          <PhysicalEntities>
            <Entity>
              <PhysicalIndex></PhysicalIndex>
              <Chassis></Chassis>
              <Slot></Slot>
              <SubSlot></SubSlot>
              <Description></Description>
              <VendorType></VendorType>
              <ContainedIn></ContainedIn>
              <Class>{class_flag}</Class>
              <ParentRelPos></ParentRelPos>
              <Name></Name>
              <HardwareRev></HardwareRev>
              <FirmwareRev></FirmwareRev>
              <SoftwareRev></SoftwareRev>
              <SerialNumber></SerialNumber>
              <MfgName></MfgName>
              <Model></Model>
              <Alias></Alias>
              <AssetID></AssetID>
              <FRU></FRU>
              <MfgDate></MfgDate>
              <Uris></Uris>
            </Entity>
          </PhysicalEntities>
        </Device>
        </top>
        '''.format(class_flag=class_flag)
        req = self.netconf_get(xml)
        if req:
            res = req["top"]['Device']['PhysicalEntities']['Entity']
            return res
        else:
            return False

    def collection_device_base(self):
        xml = """
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
         <Device>
          <Base>
            <Uptime></Uptime>
            <HostName></HostName>
            <HostDescription></HostDescription>
            <HostOid></HostOid>
            <MinChassisNum></MinChassisNum>
            <MaxChassisNum></MaxChassisNum>
            <MinSlotNum></MinSlotNum>
            <MaxSlotNum></MaxSlotNum>
            <MinCPUIDNum></MinCPUIDNum>
            <MaxCPUIDNum></MaxCPUIDNum>
            <LocalTime></LocalTime>
            <ClockProtocol>
              <Protocol></Protocol>
              <MDCID></MDCID>
            </ClockProtocol>
            <TimeZone>
              <Zone></Zone>
              <ZoneName></ZoneName>
            </TimeZone>
          </Base>
         </Device>
         </top>
        """
        req = self.netconf_get(xml)
        if req:
            res = req["top"]['Device']['Base']
            return res
        else:
            return False

    # 获取全量的硬件信息
    def collection_secpath_slot_info(self):
        xml = """
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <Device>
        <Base>
            <HostName/>
            <MinChassisNum/>
            <MaxChassisNum/>
            <MinSlotNum/>
            <MaxSlotNum/>
        </Base>
        <PhysicalEntities>
            <Entity>
                <PhysicalIndex/>
                <Chassis/>
                <Slot/>
                <Class/>
                <VendorType/>
                <ContainedIn/>
                <HardwareRev/>
                <FirmwareRev/>
                <SoftwareRev/>
                <SerialNumber/>
                <Name/>
            </Entity>
        </PhysicalEntities>
        <Boards>
            <Board>
                <DeviceNode>
                <Chassis/>
                <Slot/>
                <CPUID/>
                </DeviceNode>
                <PhysicalIndex/>
                <Role/>
            </Board>
        </Boards>
        </Device>
        </top>
        """
        req = self.netconf_get(xml)
        if req:
            res = req["top"]['Device']['PhysicalEntities']['Entity']
            return res
        else:
            return False

    def collection_ipv4address_list(self):
        """
        获取接口IP地址信息
        :return:
        """
        xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <IPV4ADDRESS>
          <Ipv4Addresses>
            <Ipv4Address>
              <IfIndex></IfIndex>
              <Ipv4Address></Ipv4Address>
              <Ipv4Mask></Ipv4Mask>
              <AddressOrigin></AddressOrigin>
            </Ipv4Address>
          </Ipv4Addresses>
         </IPV4ADDRESS>
         <Ifmgr>
            <Interfaces>
                <Interface>
                    <IfIndex></IfIndex>
                    <Name></Name>
                </Interface>
            </Interfaces>
        </Ifmgr>
        </top>
        '''
        # AddressOrigin: • 0—Other. • 1—Manual. • 2—Manual - sub. • 3—DHCP. • 4—BOOTP. • 5—Negotiate. • 6—Unnumbered.
        # • 7—VRRP. • 8—Cellular. • 9—MAD.
        req = self.netconf_get(xml)["top"]

        arp_list = req['IPV4ADDRESS']['Ipv4Addresses']['Ipv4Address']
        # 截图接口索引和name对应
        ifmgrlist = req['Ifmgr']['Interfaces']['Interface']
        type_map = {'1': 'Primary', '2': 'Sub'}
        # 两个表格合并，将name加入arp表格
        if isinstance(arp_list, dict):
            arp_list = [arp_list]
        if isinstance(arp_list, list) and arp_list:
            for a in arp_list:
                try:
                    a['type'] = type_map[a['AddressOrigin']]
                except Exception as e:
                    a['type'] = a['AddressOrigin']
                for b in ifmgrlist:
                    if a['IfIndex'] == b['IfIndex']:
                        a.update(Name=b['Name'])
            return arp_list

        return []

    def collection_ipv6address_list(self):
        xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <IPV6ADDRESS> 
        <Ipv6Addresses> 
        <AddressEntry>
        <IfIndex></IfIndex>
        <Ipv6Address></Ipv6Address> 
        <AddressOrigin></AddressOrigin> 
        <Ipv6PrefixLength></Ipv6PrefixLength> 
        <AnycastFlag></AnycastFlag>
        </AddressEntry>
        </Ipv6Addresses>
        </IPV6ADDRESS>
        <Ifmgr>
        <Interfaces>
        <Interface>
        <IfIndex></IfIndex>
        <Name></Name>
        </Interface>
        </Interfaces>
        </Ifmgr>
        </top>
        '''
        # AddressOrigin:
        # • 0—Other. • 1—Manual. • 2—Manual - sub. • 3—DHCP. • 4—BOOTP. • 5—Negotiate. • 6—Unnumbered. • 7—VRRP. • 8—Cellular. • 9—MAD.
        req = self.netconf_get(xml)['top']
        ipv6_list = req['IPV6ADDRESS']['Ipv6Addresses']['AddressEntry'] if 'IPV6ADDRESS' in req.keys() else []
        # 截图接口索引和name对应
        ifmgrlist = req['Ifmgr']['Interfaces']['Interface']
        address_origin_map = {'1': 'AssignedIP', '2': 'AssignedEUI64IP', '3': 'LinklocalIP', '4': 'AssignedAutoIP',
                              '5': 'DHCPv6'}
        # 两个表格合并，将name加入arp表格
        if isinstance(ipv6_list, dict):
            ipv6_list = [ipv6_list]
        if isinstance(ipv6_list, list) and ipv6_list:
            for a in ipv6_list:
                a['AddressOrigin'] = address_origin_map[a['AddressOrigin']]
                for b in ifmgrlist:
                    if a['IfIndex'] == b['IfIndex']:
                        a.update(Name=b['Name'])
            return ipv6_list

        return []

    def collection_mac_unicasttable(self):
        '''
        构建XML，获取设备单薄MAC地址表
        :return:
        '''
        xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <MAC>
          <MacUnicastTable>
            <Unicast>
              <VLANID></VLANID>
              <MacAddress></MacAddress>
              <PortIndex></PortIndex>
              <NickName></NickName>
              <Status></Status>
              <Aging></Aging>
            </Unicast>
          </MacUnicastTable>
        </MAC>
        <Ifmgr>
            <Interfaces>
                <Interface>
                    <IfIndex></IfIndex>
                    <Name></Name>
                    <PortIndex></PortIndex>
                </Interface>
            </Interfaces>
        </Ifmgr>
        </top>
        '''

        """
        <Ifmgr>
            <Interfaces>
                <Interface>
                    <IfIndex></IfIndex>
                    <Name></Name>
                    <PortIndex></PortIndex>
                </Interface>
            </Interfaces>
        </Ifmgr>
        """
        res = self.netconf_get(xml)['top']
        if res:
            if 'MAC' not in res.keys():
                return []
            mac_list = res['MAC']['MacUnicastTable']['Unicast']
            # 接口索引和name对应
            ifmgrlist = res['Ifmgr']['Interfaces']['Interface']
            # 两个表格合并，将name加入arp表格
            if isinstance(mac_list, dict):
                mac_list = [mac_list]
            for a in mac_list:
                for b in ifmgrlist:
                    if a['PortIndex'] == b.get('IfIndex'):
                        a.update(PortName=b['Name'])
            return mac_list
        else:
            return []

    def collection_lldp_info(self):
        data_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <LLDP> 
        <LLDPNeighbors>
            <LLDPNeighbor>
                <TimeMark></TimeMark>
                <IfIndex></IfIndex>
                <NeighborIndex></NeighborIndex>
                <SystemName></SystemName>
                <ChassisId></ChassisId>
                <PortId></PortId>
            </LLDPNeighbor>
        </LLDPNeighbors>
        <NbManageAddresses>
            <ManageAddress>
                <TimeMark></TimeMark>
                <IfIndex></IfIndex>
                <AgentID></AgentID>
                <NeighborIndex></NeighborIndex>
                <SubType></SubType>
                <Address></Address>
                <InterfaceType></InterfaceType>
                <InterfaceID></InterfaceID>
            </ManageAddress>
        </NbManageAddresses>
        </LLDP>
        <Ifmgr>
            <Interfaces>
                <Interface>
                    <IfIndex></IfIndex>
                    <Name></Name>
                    <PortIndex></PortIndex>
                </Interface>
            </Interfaces>
        </Ifmgr>
        </top>
        '''
        request_info = self.netconf_get(data_xml)
        # {'TimeMark': '4423895', 'IfIndex': '48', 'NeighborIndex': '1', 'SystemName': 'JD.NET.INT.DS.001', 'ChassisId': '0440-a9e7-3f89', 'PortId': 'Ten-GigabitEthernet2/0/11'}
        if request_info:
            SubType_map = {
                '0': 'other',
                '1': 'ipv4',
                '2': 'ipv6',
                '3': 'NSAP',
                '4': 'HDLC',
                '5': 'BBN1822',
                '6': 'all802',
                '7': 'e163',
            }
            # print(request_info['top']['LLDP']['NbManageAddresses'])
            LLDPNeighbor = request_info['top']['LLDP']['LLDPNeighbors']['LLDPNeighbor']
            lldpnbaddr = request_info['top']['LLDP']['NbManageAddresses']['ManageAddress']
            ifmgrlist = request_info['top']['Ifmgr']['Interfaces']['Interface']
            # 两个表格合并，将name加入arp表格
            if isinstance(LLDPNeighbor, dict):
                LLDPNeighbor = [LLDPNeighbor]
            if isinstance(lldpnbaddr, dict):
                lldpnbaddr = [lldpnbaddr]
            for a in LLDPNeighbor:
                for b in ifmgrlist:
                    if a['IfIndex'] == b['IfIndex']:
                        a.update(LocalPort=b['Name'])
            import codecs
            for i in lldpnbaddr:
                try:
                    tmp_hex = base64.b64decode(i['Address'])
                    hex_str = codecs.encode(tmp_hex, 'hex').decode('ascii')
                    ip_str = []
                    if len(hex_str) == 8:
                        for k in range(len(hex_str)):
                            if k % 2 == 0:
                                ip_str.append(str((int(("0x" + (hex_str[k] + hex_str[k + 1])), 16))))
                                # 获取的是邻居IP地址
                        if ip_str:
                            # print("获取的是邻居的IP地址:{}".format('.'.join(ip_str)))
                            i['Address'] = '.'.join(ip_str)
                    elif len(hex_str) == 12:
                        # print("获取的是邻居的MAC地址:{}".format(hex_str))
                        i['Address'] = hex_str
                    # ipv6地址判断
                    elif len(hex_str) == 32:
                        # print("获取的是邻居的ipv6地址:{}".format(hex_str))
                        _tmp_v6 = ':'.join([hex_str[k:k + 4] for k in range(0, len(hex_str), 4)])
                        _tmp = IPAddress(_tmp_v6)
                        i['Address'] = _tmp.format().upper()
                except Exception as e:
                    print(e)
            for a in LLDPNeighbor:
                for b in lldpnbaddr:
                    if a['IfIndex'] == b['IfIndex']:
                        a.update(Address=b['Address'], SubType=SubType_map[b['SubType']])
            return LLDPNeighbor
        else:
            return None

    def collection_vrrp_info(self):
        obtain_h3c_vrrp_info_xml = """
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <VRRP>
        <VRRPOper>
        <Operation>
        <AddressType></AddressType>
        <IfIndex></IfIndex>
        <VrID></VrID>
        <OperState></OperState>
        <PriorityConfig></PriorityConfig>
        <PriorityRun></PriorityRun>
        <IpAddressCount></IpAddressCount>
        <MasterIpAddress></MasterIpAddress>
        <AuthTypeConfig></AuthTypeConfig>
        <AuthTypeRun></AuthTypeRun>
        <AdverInterval></AdverInterval>
        <PreemptMode></PreemptMode>
        <PreemptDelay></PreemptDelay>
        </Operation>
        </VRRPOper>
        <VRRPAssoIpAddress>
        <AssoIpAddr>
        <AddressType></AddressType>
        <IfIndex></IfIndex>
        <VrID></VrID>
        <IpAddress></IpAddress>
        <LinkLocal></LinkLocal>
        </AssoIpAddr>
        </VRRPAssoIpAddress>
        </VRRP>
        <Ifmgr>
            <Interfaces>
                <Interface>
                    <IfIndex></IfIndex>
                    <Name></Name>
                    <PortIndex></PortIndex>
                </Interface>
            </Interfaces>
        </Ifmgr>
        </top>
        """
        req = self.netconf_get(obtain_h3c_vrrp_info_xml)["top"]
        if req:
            if 'VRRP' in req.keys():
                oper_state_map = {
                    "0": "Inactive",
                    "1": "Initialize",
                    "2": "Backup",
                    "3": "Master",
                }
                Operation = req['VRRP']['VRRPOper']['Operation']
                AssoIpAddr = req['VRRP']['VRRPAssoIpAddress']['AssoIpAddr']
                ifmgrlist = req['Ifmgr']['Interfaces']['Interface']
                # 两个表格合并，将name加入arp表格
                if isinstance(Operation, dict):
                    Operation = [Operation]
                if isinstance(AssoIpAddr, dict):
                    AssoIpAddr = [AssoIpAddr]
                for a in Operation:
                    for b in AssoIpAddr:
                        if a['IfIndex'] == b['IfIndex']:
                            a.update(**b)
                for a in Operation:
                    a['OperState'] = oper_state_map[a['OperState']]
                    for b in ifmgrlist:
                        if a['IfIndex'] == b['IfIndex']:
                            a.update(Name=b['Name'])
                return Operation
            return []
        return []


class HuaweiyangNetconfConnect(object):
    """
    Huawe设备netconf专用连接类
    """

    def __init__(self, *args, **kwargs):
        self.host = kwargs.get("host")
        self.user = kwargs.get("user")
        self.password = kwargs.get("password")
        self.netconf_dict = {
            "device_params": {"name": "huaweiyang"},
            "host": self.host,
            "port": 830,
            "timeout": kwargs.get("timeout") if kwargs.get("timeout") else 1000,
            "username": self.user,
            "password": self.password,
            "hostkey_verify": False,
            "allow_agent": False,
            "look_for_keys": False
        }
        self.netconf_session = manager.connect(**self.netconf_dict)
        # self.netconf_session = manager.connect(**self.netconf_dict)

    def closed(self):
        return self.netconf_session.close_session()

    def netconf_get(self, data):
        # with manager.connect(**self.netconf_dict) as netconf_session:
        try:
            res = self.netconf_session.get(('subtree', data))
            mxl = json.dumps(xmltodict.parse(parseString(str(res.xml)).toprettyxml()))
            result = json.loads(mxl)["rpc-reply"]["data"]
            return result
        except RPCError as e:
            return False, 'RPCError:{}'.format(e.message)

    def _netconf_get(self, data):
        try:
            res = self.netconf_session.get(('subtree', data))
            mxl = json.dumps(xmltodict.parse(parseString(str(res.xml)).toprettyxml()))
            result = json.loads(mxl)["rpc-reply"]["data"]
            return True, result
        except RPCError as e:
            return False, 'RPCError:{}'.format(e.message)

    def netconf_cli(self, data):
        # with manager.connect(**self.netconf_dict) as netconf_session:
        res = self.netconf_session.cli(data)
        mxl = json.dumps(xmltodict.parse(parseString(str(res.xml)).toprettyxml()))
        result = json.loads(mxl)["rpc-reply"]["CLI"]["Execution"]
        return result

    def netconfig_get_config(self, data=None):
        # with manager.connect(**self.netconf_dict) as netconf_session:
        if data:
            res = self.netconf_session.get_config(source='running', filter=data)
        else:
            res = self.netconf_session.get_config(source='running')
        mxl = json.dumps(xmltodict.parse(parseString(str(res.xml)).toprettyxml()))
        result = json.loads(mxl)["rpc-reply"]["data"]
        return result

    def edit_config(self, xml_data):
        try:
            # with manager.connect(**self.netconf_dict) as netconf_session:
            res = self.netconf_session.edit_config(target='running', config=xml_data)
            xml_str = parseString(str(res))
            if xml_str.toprettyxml().find('<ok/>') != -1:
                return True
            else:
                return False, xml_str.toprettyxml()
        except Exception as e:
            return False, 'Exception:{}'.format(e)

    def rpc(self, obj):
        # 测试不通过 本来想测测华为USG的RPC调用功能
        try:
            with manager.connect(**self.netconf_dict) as netconf_session:
            # resp = netconf_session.dispatch(to_ele(obj))
                resp = netconf_session.rpc(obj)
                return resp.data_xml if hasattr(resp, 'data_xml') else resp.xml
            # xml_str = parseString(str(res))
            # if xml_str.toprettyxml().find('<ok/>') != -1:
            #     return True
            # else:
            #     return False, xml_str.toprettyxml()
        except RPCError as e:
            msg = e.xml
            return False, 'Exception:{}'.format(msg)

    def save_config(self):
        try:
            with manager.connect(**self.netconf_dict) as netconf_session:
                res = netconf_session.save(file='test.cfg')
                xml_str = parseString(str(res))
                if xml_str.toprettyxml().find('<ok/>') != -1:
                    return True
                else:
                    return False, xml_str.toprettyxml()
        except Exception as e:
            return False, 'Exception:{}'.format(e)

    def action(self,data):
        '''
        下发动作
        :param data:
        :return:
        '''
        try:
            # with manager.connect(**self.netconf_dict) as netconf_session:
            res = self.netconf_session.action(data)
            xml_str = parseString(str(res))
            if xml_str.toprettyxml().find('<ok/>') != -1:
                return True
            else:
                return False, xml_str.toprettyxml()
        except Exception as e:
            return False, 'Exception:{}'.format(e)

    def rollback(self):
        '''
        配置在线回滚
        :return:
        '''
        try:
            # with manager.connect(**self.netconf_dict) as netconf_session:
            res = self.netconf_session.rollback(file='test.cfg')
            xml_str = parseString(str(res))
            if xml_str.toprettyxml().find('<ok/>') != -1:
                return True
            else:
                return False, xml_str.toprettyxml()
        except Exception as e:
            return False, 'Exception:{}'.format(e)


class HuaweiNetconfConnect(object):
    """
    Huawe设备netconf专用连接类
    """

    def __init__(self, *args, **kwargs):
        self.host = kwargs.get("host")
        self.user = kwargs.get("user")
        self.password = kwargs.get("password")
        self.netconf_dict = {
            "device_params": {"name": "huawei"},
            "host": self.host,
            "port": 830,
            "timeout": kwargs.get("timeout") if kwargs.get("timeout") else 30,
            "username": self.user,
            "password": self.password,
            "hostkey_verify": False,
            "allow_agent": False,
            "look_for_keys": False,
        }

    def netconf_get(self, data):
        with manager.connect(**self.netconf_dict) as netconf_session:
            res = netconf_session.get(('subtree', data))
            mxl = json.dumps(xmltodict.parse(parseString(str(res.xml)).toprettyxml()))
            result = json.loads(mxl)["rpc-reply"]["data"]
            return result

    def netconf_cli(self, data):
        with manager.connect(**self.netconf_dict) as netconf_session:
            res = netconf_session.cli(data)
            mxl = json.dumps(xmltodict.parse(parseString(str(res.xml)).toprettyxml()))
            result = json.loads(mxl)["rpc-reply"]["CLI"]["Execution"]
            return result

    def netconfig_get_config(self):
        with manager.connect(**self.netconf_dict) as netconf_session:
            res = netconf_session.get_config(source='running')
            mxl = json.dumps(xmltodict.parse(parseString(str(res.xml)).toprettyxml()))
            result = json.loads(mxl)["rpc-reply"]["data"]
            return result

    def edit_config(self,xml_data):
        try:
            with manager.connect(**self.netconf_dict) as netconf_session:
                res = netconf_session.edit_config(target='running', config=xml_data)
                xml_str = parseString(str(res))
                if xml_str.toprettyxml().find('<ok/>') != -1:
                    return True
                else:
                    return False ,xml_str.toprettyxml()
        except Exception as e:
            return False, 'Exception:{}'.format(e)

    def save_config(self):
        try:
            with manager.connect(**self.netconf_dict) as netconf_session:
                res = netconf_session.save(file='test.cfg')
                xml_str = parseString(str(res))
                if xml_str.toprettyxml().find('<ok/>') != -1:
                    return True
                else:
                    return False, xml_str.toprettyxml()
        except Exception as e:
            return False, 'Exception:{}'.format(e)

    def action(self,data):
        '''
        下发动作
        :param data:
        :return:
        '''
        try:
            with manager.connect(**self.netconf_dict) as netconf_session:
                res = netconf_session.action(data)
                xml_str = parseString(str(res))
                if xml_str.toprettyxml().find('<ok/>') != -1:
                    return True
                else:
                    return False, xml_str.toprettyxml()
        except Exception as e:
            return False, 'Exception:{}'.format(e)

    def rollback(self):
        '''
        配置在线回滚
        :return:
        '''
        try:
            with manager.connect(**self.netconf_dict) as netconf_session:
                res = netconf_session.rollback(file='test.cfg')
                xml_str = parseString(str(res))
                if xml_str.toprettyxml().find('<ok/>') != -1:
                    return True
                else:
                    return False, xml_str.toprettyxml()
        except Exception as e:
            return False, 'Exception:{}'.format(e)

    def ceshi(self):
        with manager.connect(**self.netconf_dict) as netconf_session:
            res = netconf_session.__dict__.items()
            for i in res:
                print(i)
            return res


class CiscoNetconfConnect(object):
    """
    思科设备专用netconf连接类
    """

    def __init__(self, *args, **kwargs):
        self.host = kwargs.get("host")
        self.user = kwargs.get("user")
        self.password = kwargs.get("password")
        self.netconf_dict = {
            "device_params": {"name": "nexus"},
            "host": self.host,
            "port": 830,
            "timeout": kwargs.get("timeout") if kwargs.get("timeout") else 30,
            "username": self.user,
            "password": self.password,
            "hostkey_verify": False,
            "allow_agent": False,
            "look_for_keys": False
        }

    def netconf_get(self, data):
        with manager.connect(**self.netconf_dict) as netconf_session:
            res = netconf_session.get(('subtree', data))
            mxl = json.dumps(xmltodict.parse(parseString(str(res.xml)).toprettyxml()))
            result = json.loads(mxl)["rpc-reply"]["data"]
            return result

    def netconf_cli(self, data):
        with manager.connect(**self.netconf_dict) as netconf_session:
            res = netconf_session.cli(data)
            mxl = json.dumps(xmltodict.parse(parseString(str(res.xml)).toprettyxml()))
            result = json.loads(mxl)["rpc-reply"]["CLI"]["Execution"]
            return result

    def netconfig_get_config(self):
        with manager.connect(**self.netconf_dict) as netconf_session:
            res = netconf_session.get_config(source='running')
            mxl = json.dumps(xmltodict.parse(parseString(str(res.xml)).toprettyxml()))
            result = json.loads(mxl)["rpc-reply"]["data"]
            return result

    def edit_config(self,xml_data):
        try:
            with manager.connect(**self.netconf_dict) as netconf_session:
                res = netconf_session.edit_config(target='running', config=xml_data)
                xml_str = parseString(str(res))

                if xml_str.toprettyxml().find('<ok/>') != -1:
                    return True
                else:
                    return False ,xml_str.toprettyxml()
        except Exception as e:
            return False, 'Exception:{}'.format(e)

    def save_config(self):
        try:
            with manager.connect(**self.netconf_dict) as netconf_session:
                res = netconf_session.exec_command({'copy running-config startup-config'})
                # xml_str = parseString(str(res))
                # if xml_str.toprettyxml().find('<ok/>') != -1:
                #     return True
                # else:
                #     return False, xml_str.toprettyxml()
                if (res.ok):
                    return ('Running Configuration Saved to Startup Successfully')
        except Exception as e:
            return False, 'Exception:{}'.format(e)

    def action(self,data):
        '''
        下发动作
        :param data:
        :return:
        '''
        try:
            with manager.connect(**self.netconf_dict) as netconf_session:
                res = netconf_session.action(data)
                xml_str = parseString(str(res))
                if xml_str.toprettyxml().find('<ok/>') != -1:
                    return True
                else:
                    return False, xml_str.toprettyxml()
        except Exception as e:
            return False, 'Exception:{}'.format(e)

    def rollback(self):
        '''
        配置在线回滚
        :return:
        '''
        try:
            with manager.connect(**self.netconf_dict) as netconf_session:
                res = netconf_session.rollback(file='test.cfg')
                xml_str = parseString(str(res))
                if xml_str.toprettyxml().find('<ok/>') != -1:
                    return True
                else:
                    return False, xml_str.toprettyxml()
        except Exception as e:
            return False, 'Exception:{}'.format(e)

    def build_xml(self, cmd):
        """
        用于nexus设备执行command命令构建xml格式
        show version 转换后格式为<show><version></version></show>
        build Netconf XML for a basic command, this should work pretty good for most
        show commands
        """

        args = cmd.split(' ')
        xml = ""
        for a in reversed(args):
            xml = """<%s>%s</%s>""" % (a, xml, a)
        return xml

    def run_cmd(self, cmd):
        '''
        用于nexus设备执行command命令
        :param cmd:
        :return:
        '''
        xml = self.build_xml(cmd)
        with manager.connect(**self.netconf_dict) as netconf_session:
            res = netconf_session.get(('subtree', xml))
            mxl = json.dumps(xmltodict.parse(parseString(str(res.xml)).toprettyxml()))
            result = json.loads(mxl)["rpc-reply"]["data"]
            return result['mod:show']
        # ncdata = str(self.manager.get(('subtree', xml)))
        # try:
        #     # we return valid XML
        #     root = ET.fromstring(ncdata)
        #     return root
        #
        # except:
        #     # somthing f'd up we'll return it as a we got it back
        #     return ncdata

    def exec_command(self,cmd):
        '''
        调用exec_command方法执行命令下发和信息收集
        :param cmd:
        :return:
        '''
        with manager.connect(**self.netconf_dict) as netconf_session:
            res = netconf_session.exec_command({cmd})
            mxl = json.dumps(xmltodict.parse(parseString(str(res.xml)).toprettyxml()))
            result = json.loads(mxl)["rpc-reply"]
            # print(result)
            if (res.ok):
                return True

    def foo(self):
        with manager.connect(**self.netconf_dict) as netconf_session:
            print(netconf_session)
            for capability in netconf_session.server_capabilities:
                print(capability)


class XmlToDict(object):
    def get_dict(self, xml):
        """xml to dict"""
        return xmltodict.parse(xml_input=xml, encoding="utf-8")

    def get_xml_content(self, orderdict):
        for i in orderdict:
            print(orderdict[str(i)])

    def get_content(self,xml):
        first_title = re.match(r"<.*>", xml).group()[1:-1]
        orderdict = self.get_dict(xml)
        orderdict=orderdict[first_title]
        self.get_xml_content(orderdict)

    def dicttoxml(self, dict):
        """dict to xml"""
        return xmltodict.unparse(dict, encoding="utf-8")


if __name__ == '__main__':
    pass