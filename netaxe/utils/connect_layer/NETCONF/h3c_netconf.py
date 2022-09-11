#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import division
import logging
import re

from .netconf_connect import XmlToDict, H3CNetconf

logger = logging.getLogger("ncclient")


class H3CinfoCollection(H3CNetconf):

    def __init__(self, *args, **kwargs):
        super(H3CinfoCollection, self).__init__(*args, **kwargs)
        self.device_type = kwargs.get("device_type", '')

    @staticmethod
    def get_method():
        return [func for func in dir(H3CinfoCollection) if
                callable(getattr(H3CinfoCollection, func)) and not func.startswith("__")]

    def collection_vrf_list(self):
        data_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <L3vpn>
        <L3vpnVRF> 
            <VRF>
                <VRF></VRF>
                <VrfIndex></VrfIndex>
                <Description></Description>
                <RD></RD>
                <CreationTime></CreationTime>
                <AssociatedInterfaceCount></AssociatedInterfaceCount>
                <Ipv4RoutingLimit>
                <Ipv4MaxRoutes></Ipv4MaxRoutes>
                <Ipv4RouteThreshold></Ipv4RouteThreshold>
                <Ipv4SimplyAlert></Ipv4SimplyAlert>
                </Ipv4RoutingLimit>
                <Ipv6RoutingLimit>
                <Ipv6MaxRoutes></Ipv6MaxRoutes>
                <Ipv6RouteThreshold></Ipv6RouteThreshold>
                <Ipv6SimplyAlert></Ipv6SimplyAlert>
                </Ipv6RoutingLimit>
                <ExportRoutePolicy></ExportRoutePolicy>
                <EVPNExportRoutePolicy></EVPNExportRoutePolicy>
                <Ipv4ExportRoutePolicy></Ipv4ExportRoutePolicy>
                <Ipv6ExportRoutePolicy></Ipv6ExportRoutePolicy>
                <ImportRoutePolicy></ImportRoutePolicy>
                <Ipv4ImportRoutePolicy></Ipv4ImportRoutePolicy>
                <EVPNImportRoutePolicy></EVPNImportRoutePolicy>
                <Ipv6ImportRoutePolicy></Ipv6ImportRoutePolicy>
            </VRF>
            </L3vpnVRF>
        </L3vpn>
        </top>
        '''
        request_arplist = self.netconf_get(data_xml)["top"]['L3vpn']['L3vpnVRF']['VRF']
        return request_arplist

    def collection_l2vpn_vsis(self):
        data_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <L2VPN> 
        <VSIs> 
        <VSI> 
            <VsiName></VsiName>
            <HubSpoke></HubSpoke>
            <VsiIndex></VsiIndex>
            <VxlanID></VxlanID>
            <NvgreID></NvgreID>
            <ArpSuppression></ArpSuppression>
            <MacLearning></MacLearning>
            <MacLimit></MacLimit>
            <Flooding></Flooding> 
            <FloodType></FloodType>
            <VsiInterfaceID></VsiInterfaceID> 
            <Statistics></Statistics>
            <Description></Description>
            <Bandwidth></Bandwidth>
            <BroadcastRestrain></BroadcastRestrain>
            <MulticastRestrain></MulticastRestrain>
            <UnknownUnicastRestrain></UnknownUnicastRestrain>
            <AdminStatus></AdminStatus>
            <Status></Status>
            <LocMacCnt></LocMacCnt>
        </VSI>
        </VSIs>
        <ACs> 
            <AC>
            <IfIndex></IfIndex>
            <SrvID></SrvID> 
            <VsiName></VsiName> 
            <AccessMode></AccessMode>
            <Hub></Hub>
            <Statistics></Statistics>
            <Bandwidth></Bandwidth>
            <LearningMode></LearningMode>
            </AC>
        </ACs>
        <SRVs> 
            <SRV>
            <IfIndex></IfIndex>
            <SrvID></SrvID> 
            <Encap></Encap> 
            <SVlanRange></SVlanRange> 
            <CVlanRange></CVlanRange> 
            </SRV>
        </SRVs>
        </L2VPN>
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
        req = self.netconf_get(data_xml)['top']
        if req:
            vsis = req['L2VPN']['VSIs']['VSI']
            # print(req['L2VPN'].keys())
            ACs = req['L2VPN']['ACs']['AC']
            ifmgrlist = req['Ifmgr']['Interfaces']['Interface']
            # SRVs = req['L2VPN']['SRVs']['SRV']
            for a in vsis:
                for b in ACs:
                    if a['VsiName'] == b['VsiName']:
                        a.update(IfIndex=b['IfIndex'], SrvID=b['SrvID'])
            for a in vsis:
                for b in ifmgrlist:
                    if 'IfIndex' in a.keys():
                        if a['IfIndex'] == b['IfIndex']:
                            a.update(Name=b['Name'])
            return vsis
        else:
            return []

    def collection_test_mac(self):
        '''
        构建XML，获取设备单薄MAC地址表
        :return:
        '''
        xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <MAC>
        <MacUnicastTable>
        <Unicast>
          <VLANID>160</VLANID>
          <MacAddress>38-D5-47-CA-2C-53</MacAddress>
          <PortIndex></PortIndex>
          <Status></Status>
          <Aging></Aging>
        </Unicast>
        </MAC>
        </top>
        '''

        res = self.netconf_get(xml)['top']
        return res

    def collection_mac_over_evpn(self):
        xml = '''
            <top xmlns="http://www.h3c.com/netconf/data:1.0">
            <L2VPN> 
                <LocalMACs> 
                <MAC> 
                <VsiName></VsiName> 
                <MacAddr></MacAddr> 
                <IfIndex></IfIndex> 
                <SrvID></SrvID>
                <Type></Type>
                </MAC>
                </LocalMACs>
            </L2VPN>
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
        res = self.netconf_get(xml)
        if 'top' in res:
            res = res['top']
            if 'L2VPN' not in res.keys():
                return []
            mac_list = res['L2VPN']['LocalMACs']['MAC']
            # 接口索引和name对应
            ifmgrlist = res['Ifmgr']['Interfaces']['Interface']
            # 两个表格合并，将name加入arp表格
            if isinstance(mac_list, dict):
                mac_list = [mac_list]
            for a in mac_list:
                for b in ifmgrlist:
                    if a['IfIndex'] == b.get('IfIndex'):
                        a.update(PortName=b['Name'])
            return mac_list
        else:
            return []

    def collection_arp_over_evpn(self):
        data_xml = '''
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
        <L2VPN> 
            <LocalMACs> 
            <MAC> 
            <VsiName></VsiName> 
            <MacAddr></MacAddr> 
            <IfIndex></IfIndex> 
            <SrvID></SrvID>
            <Type></Type>
            </MAC>
            </LocalMACs>
        </L2VPN>
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
        res = self.netconf_get(data_xml)['top']
        if res:
            if 'L2VPN' not in res.keys():
                return []
            arplist = res['ARP']['ArpTable']['ArpEntry']
            mac_list = res['L2VPN']['LocalMACs']['MAC']
            # 接口索引和name对应
            ifmgrlist = res['Ifmgr']['Interfaces']['Interface']
            # 两个表格合并，将name加入arp表格
            if isinstance(arplist, dict):
                arplist = [arplist]
            if isinstance(mac_list, dict):
                mac_list = [mac_list]
            for a in arplist:
                for b in mac_list:
                    if a['MacAddress'] == b.get('MacAddr'):
                        a['IfIndex'] = b['IfIndex']
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
        else:
            return []

    def collection_ipv4_routetable(self):
        '''
        构建XML，获取ipv4路由表
        :return:
        '''
        xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <Route>
            <Ipv4Routes>
              <RouteEntry>
               <VRF></VRF>
               <Topology></Topology>
               <Ipv4>
                 <Ipv4Address></Ipv4Address>
                 <Ipv4PrefixLength></Ipv4PrefixLength>
               </Ipv4>
               <Nexthop></Nexthop>
               <IfIndex></IfIndex>
               <Protocol>
                 <ProtocolID></ProtocolID>
                 <SubProtocolID></SubProtocolID>
               </Protocol>
               <ProcessID></ProcessID>
               <Age></Age>
               <Preference></Preference>
               <Metric></Metric>
               <Tag></Tag>
               <Neighbor></Neighbor>
               <ASNumber>
                 <OriginAS></OriginAS>
                 <LastAS></LastAS>
               </ASNumber>
               <BackupPathAttribute>
                 <BackupIfIndex></BackupIfIndex>
                 <BackupNexthop></BackupNexthop>
               </BackupPathAttribute>
              </RouteEntry>
            </Ipv4Routes>
        </Route>
        </top>
        '''
        request_info = self.netconf_get(xml)
        if request_info != 'None':
            request_info = request_info['top']['Route']['Ipv4Routes']['RouteEntry']
        return request_info

    def collection_running_config(self):
        '''
        通过get-config方法获取设备配置
        :return:
        '''
        request_info = self.netconfig_get_config()
        return request_info['top']

    def collection_interface_info(self):
        """请求的XML_CLI命令
        Execution 在用户视图下执行命令
        """
        obtain_h3c_display_interface_xml = '''
        <Execution>
        display interface GigabitEthernet
        display interface Ten-GigabitEthernet
        </Execution>
        '''

        request_info = self.netconf_cli(obtain_h3c_display_interface_xml)
        response_info = [x for x in str(request_info).strip().splitlines() if x != ''
                         if x != '<ncclient-test>display interface GigabitEthernet'
                         if x != '<ncclient-test>display interface Ten-GigabitEthernet']
        # 排序
        cnt = 0
        index_port_name_lst = []
        interface_info_dict = {}
        for i in response_info:
            result_1 = re.match('(GigabitEthernet|Ten-GigabitEthernet)(.*)', i, re.IGNORECASE)
            if result_1:
                index_port_name_lst.append(cnt)
            cnt += 1
        else:
            index_port_name_lst.append(-1)
        index_range_lst = [list(x) for x in zip(index_port_name_lst[:-1], index_port_name_lst[1:])]
        if self.device_type == "switch":
            for i in index_range_lst:
                # 判断当前接口状态：UP or DOWN
                if response_info[i[0]:i[1]][1].split('state:')[1].strip() == 'UP':
                    dict_key = ''
                    dict_values = []
                    input_info = []
                    output_info = []
                    for j in response_info[i[0]:i[1]]:
                        j = str(j).strip()
                        if re.match('(GigabitEthernet|Ten-GigabitEthernet)(.*)', j, re.IGNORECASE):
                            dict_key = j
                        elif re.match('(Current state:)(.*)', j, re.IGNORECASE):
                            dict_values.append(j)
                        elif re.match('(Link speed type is)(.*)', j, re.IGNORECASE):
                            dict_values.append(j.split(', ')[0].strip())
                            dict_values.append(j.split(', ')[1].strip())
                        elif re.match('\\d(.*)(speed mode,)(.*)', j, re.IGNORECASE):
                            dict_values.append(j.split(', ')[0].strip())
                            dict_values.append(j.split(', ')[1].strip())
                        elif re.match('Input:(.*)', j, re.IGNORECASE):
                            input_info.extend(j.split('Input:')[1].strip().split(', '))
                        elif re.match('\\d(.*)CRC,(.*)', j, re.IGNORECASE):
                            input_info.extend(j.split(', '))
                        elif re.match('(.*)ignored,(.*)', j, re.IGNORECASE):
                            input_info.extend(j.split(', '))
                        elif re.match('Output:', j, re.IGNORECASE):
                            output_info.extend(j.split('Output:')[1].strip().split(', '))
                        elif re.match('\\d(.*)aborts', j, re.IGNORECASE):
                            output_info.extend(j.strip().split(', '))
                        elif re.match('\\d(.*)lost carrier', j, re.IGNORECASE):
                            output_info.extend(j.strip().split(', '))
                    dict_values.append({'Input_Error': input_info})
                    dict_values.append({'Output_Error': output_info})
                    interface_info_dict[dict_key] = dict_values
                else:
                    continue
        else:
            for i in index_range_lst:
                # 判断当前接口状态：UP or DOWN
                if response_info[i[0]:i[1]][1].split('state:')[1].strip() == 'UP':
                    dict_key = ''
                    dict_values = []
                    input_info = []
                    output_info = []
                    for j in response_info[i[0]:i[1]]:
                        j = str(j).strip()
                        if re.match('(GigabitEthernet|Ten-GigabitEthernet)(.*)', j, re.IGNORECASE):
                            dict_key = j
                        elif re.match('(Current state:)(.*)', j, re.IGNORECASE):
                            dict_values.append(j)
                        elif re.match(r'\d+Mbps, .*link type is .*', j):
                            dict_values.append(j.split(",")[0])
                            dict_values.append(j.split(",")[1])
                            dict_values.append(j.split(",")[2])
                        elif re.match('Input:(.*)', j, re.IGNORECASE):
                            input_info.extend(j.split('Input:')[1].strip().split(', '))
                        elif re.match('\\d(.*)CRC,(.*)', j, re.IGNORECASE):
                            input_info.extend(j.split(', '))
                        elif re.match('(.*)ignored,(.*)', j, re.IGNORECASE):
                            input_info.extend(j.split(', '))
                        elif re.match('Output:', j, re.IGNORECASE):
                            output_info.extend(j.split('Output:')[1].strip().split(', '))
                        elif re.match('\\d(.*)aborts', j, re.IGNORECASE):
                            output_info.extend(j.strip().split(', '))
                        elif re.match('\\d(.*)lost carrier', j, re.IGNORECASE):
                            output_info.extend(j.strip().split(', '))
                    dict_values.append({'Input_Error': input_info})
                    dict_values.append({'Output_Error': output_info})
                    interface_info_dict[dict_key] = dict_values
                else:
                    continue
        return interface_info_dict

    def collection_filesystem_info(self):
        """请求的XML命令"""
        obtain_h3c_file_system_info_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <FileSystem>
        <Partitions>
        <Partition>
        <Name></Name>
        <Total></Total>
        <Used></Used>
        <Free></Free>
        <Bootable></Bootable>
        <MountState></MountState>
        </Partition>
        </Partitions>
        </FileSystem> 
        </top>
        '''
        obtain_h3c_dir_xml = '''
        <Execution>
        dir
        </Execution>
        '''
        if self.device_type == 'switch':
            request_info = self.netconf_get(obtain_h3c_file_system_info_xml)
            request_info = request_info["top"]["FileSystem"]["Partitions"]["Partition"]
        else:
            request_info = self.netconf_cli(obtain_h3c_dir_xml)

        return request_info

    def collection_startup_file__info(self):
        obtain_h3c_startup_file_info_xml = '''
        <Execution>
            display startup
        </Execution>
        '''
        request_info = self.netconf_cli(obtain_h3c_startup_file_info_xml)
        return request_info

    def collection_ntp_status_info(self):
        """
        请求的XML命令
        """
        obtain_h3c_ntp_enable_info_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <NTP>
        <Service>
        <NTPEnable></NTPEnable>
        <SNTPEnable></SNTPEnable>
        <NTPAuthEnable></NTPAuthEnable>
        <SNTPAuthEnable></SNTPAuthEnable>
        <NTPSource></NTPSource>
        </Service>
        </NTP>
        </top>
        '''
        obtain_h3c_ntp_sync_status_info_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <NTP>
        <Status>
        <NTPSynchronized></NTPSynchronized>
        <SNTPSynchronized></SNTPSynchronized>
        </Status>
        </NTP>
        </top>
        '''
        obtain_h3c_device_local_time_info_xml = '''
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
        '''

        request_ntp_enable = self.netconf_get(obtain_h3c_ntp_enable_info_xml)["top"]['NTP']['Service']['NTPEnable']
        request_ntp_sync_status = self.netconf_get(obtain_h3c_ntp_sync_status_info_xml)
        request_ntp_sync_status = request_ntp_sync_status["top"]['NTP']['Status']['NTPSynchronized']
        request_device_local_time = self.netconf_get(obtain_h3c_device_local_time_info_xml)
        request_device_local_time = str(request_device_local_time["top"]['Device']['Base']['LocalTime']).replace('T',
                                                                                                                 ' ')
        request_ntp_info = [request_ntp_enable] + [request_ntp_sync_status] + [request_device_local_time]
        return request_ntp_info

    def collection_address_number_info(self):
        """请求的XML_CLI命令"""
        obtain_h3c_display_interface_xml = '''
        <Execution>
        display mac-address statistics
        dis arp static count
        dis arp dynamic count
        display ip routing-table statistics
        </Execution>
        '''

        obtain_h3c_route_display_interface_xml = '''
        <Execution>
        dis mac-address static count
        dis mac-address dynamic count
        dis mac-address multicast count
        dis arp static count
        dis arp dynamic count
        display ip routing-table statistics
        </Execution>
        '''

        results = []
        a = 0
        b = 0
        if self.device_type == 'switch':
            request_info = str(self.netconf_cli(obtain_h3c_display_interface_xml)).splitlines()
            for i in request_info:
                # 活跃单播MAC地址统计
                if re.match(r'Total\sUnicast\sMAC\sAddresses\sIn\sUse:', i, re.IGNORECASE):
                    results.append(int(i.split(':')[1].strip()))
                # 单播MAC地址最大可用限制
                elif re.match(r'Total\sUnicast\sMAC\sAddresses\sAvailable:', i, re.IGNORECASE):
                    results.append(int(i.split(':')[1].strip()))
                # 组播MAC地址数统计
                elif re.match(r'Multicast\sand\sMultiport\sMAC\sAddress\sCount:', i, re.IGNORECASE):
                    a = int(i.split(':')[1].strip())
                # 静态组播MAC地址数统计
                elif re.match(r'Static Multicast and Multiport MAC Address (.*) Count: ', i, re.IGNORECASE):
                    b = int(i.split(':')[1].strip())
                # 组播MAC地址最大可用限制
                elif re.match(r'Total Multicast and Multiport MAC Addresses Available:', i, re.IGNORECASE):
                    results.append(a + b)
                    results.append(int(i.split(':')[1].strip()))
                # ARP静态地址数量
                elif re.match(r'Total\snumber\sof\sstatic\sentries:', str(i).strip(), re.IGNORECASE):
                    results.append(int(i.split()[-1]))
                # ARP动态地址数量
                elif re.match(r'Total\snumber\sof\sdynamic\sentries:', str(i).strip(), re.IGNORECASE):
                    results.append(int(i.split()[-1]))
                # 活跃路由表数量
                elif re.search(r'Total\s.*Active\sprefixes:\s\d+', i, re.IGNORECASE):
                    results.append(int(i.split('Active prefixes:')[1].strip()))
        else:
            request_info = str(self.netconf_cli(obtain_h3c_route_display_interface_xml)).splitlines()
            for i in request_info:
                # MAC地址数统计
                match_mac_cnt = re.match(r'(\d+\smac\saddress.*\sfound.)', i.strip(), re.I)
                if match_mac_cnt:
                    # 格式：静态MAC,动态MAC,组播MAC
                    results.append(match_mac_cnt.group().split()[0])
                # ARP地址数量
                match_arp_cnt = re.match(r'Total\snumber\sof\s.*\sentries:\s+\d+', i.strip(), re.I)
                if match_arp_cnt:
                    # 格式：静态ARP,动态ARP
                    results.append(match_arp_cnt.group().split()[-1])
                # 活跃路由表数量
                match_route_cnt = re.match(r'(Total(\s+\d+).*)', i.strip(), re.I)
                if match_route_cnt:
                    results.append(match_route_cnt.group().split()[2])
        return results

    def collection_acl_resource_info(self):
        """请求的XML_CLI命令"""
        obtain_h3c_display_qos_acl_resource_xml = '''
        <Execution>
        display qos-acl resource
        </Execution>
        '''
        request_info = str(self.netconf_cli(obtain_h3c_display_qos_acl_resource_xml)).splitlines()
        request_info_dict = dict()
        key_name = None
        acl_resource_use_info = None
        for i in request_info:
            if re.match('Interfaces:.*', i.strip(), re.IGNORECASE):
                request_info_dict[i] = ''
                key_name = i
            elif re.match('IFP ACL.*%$', i.strip(), re.IGNORECASE):
                acl_resource_use_info = [i.strip().split()[-1]]
            elif re.match('EFP ACL.*%$', i.strip(), re.IGNORECASE):
                acl_resource_use_info += [i.strip().split()[-1]]
            if key_name is not None:
                request_info_dict[key_name] = acl_resource_use_info
        return request_info_dict

    def collection_http_https_status_info(self):
        """请求的XML_CLI命令"""
        obtain_h3c_display_http_https_status_xml = '''
        <Execution>
        display ip http
        display ip https
        </Execution>
        '''
        request_info = str(self.netconf_cli(obtain_h3c_display_http_https_status_xml)).splitlines()
        return request_info

    def collection_stp_status_info(self):
        """请求的XML_CLI命令"""
        obtain_h3c_display_stp_brief_status_xml = '''
        <Execution>
        display stp brief
        </Execution>
        '''
        request_info = str(self.netconf_cli(obtain_h3c_display_stp_brief_status_xml)).splitlines()
        return request_info

    def collection_ftp_status_info(self):
        """请求的XML_CLI命令"""
        obtain_h3c_display_ftp_status_xml = '''
        <Execution>
        display ftp-server
        </Execution>
        '''
        request_info = str(self.netconf_cli(obtain_h3c_display_ftp_status_xml)).splitlines()
        return request_info

    def collection_snmp_version_info(self):
        """请求的XML_CLI命令"""
        obtain_h3c_display_snmp_running_version_xml = '''
        <Execution>
        display snmp-agent sys-info version
        </Execution>
        '''
        request_info = str(self.netconf_cli(obtain_h3c_display_snmp_running_version_xml)).splitlines()
        return request_info

    def collection_local_user_hash_info(self):
        """请求的XML_CLI命令"""
        obtain_h3c_display_local_user_hash_xml = '''
        <Execution>
        display current-configuration configuration local-user
        </Execution>
        '''
        request_info = str(self.netconf_cli(obtain_h3c_display_local_user_hash_xml)).splitlines()
        lst = []
        user_info = None
        for i in request_info:
            if i == '' or i == '#' or i == 'return':
                continue
            else:
                i = i.strip().split()
                if i[0] == 'local-user':
                    user_info = i[1]
                elif i[0] == 'password':
                    lst.append((user_info, i[1]))
        return lst

    def collection_irf_info(self):
        """请求的XML命令"""
        obtain_h3c_irf_bfd_info_xml = '''
        <Execution>
        display bfd session discriminator 3001
        </Execution>
        '''
        obtain_h3c_irf_info_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <IRF>
        <Members>
        <Member>
        <MemberID></MemberID>
        <NewMemberID></NewMemberID>
        <Description></Description>
        <Priority></Priority>
        <CPUMac></CPUMac>
        <Board>
        <Chassis></Chassis>
        <Slot></Slot>
        <Role></Role>
        </Board> 
        </Member>
        </Members>
        </IRF>
        </top>
        '''
        # obtain_h3c_irf_link_info_xml = '''
        # <top xmlns="http://www.h3c.com/netconf/data:1.0">
        # <IRF>
        # <IRFPorts>
        # <IRFPort>
        # <MemberID></MemberID>
        # <Port></Port>
        # <Neighbor></Neighbor>
        # <State></State>
        # <Interface>
        # <IfName></IfName>
        # <MDCName></MDCName>
        # <Mode></Mode>
        # <LinkState></LinkState>
        # </Interface>
        # <LinkStateInMDC>
        # <MDCName></MDCName>
        # <State></State>
        # </LinkStateInMDC>
        # </IRFPort>
        # </IRFPorts>
        # </IRF>
        # </top>
        # '''
        role_map = {'1': 'Master', '2': 'Standby', '3': 'Loading', '4': 'Other'}
        req = self.netconf_get(obtain_h3c_irf_info_xml)
        if req:
            request_irf_info = req["top"]['IRF']['Members']['Member']
            if isinstance(request_irf_info, list):
                for i in request_irf_info:
                    if isinstance(i['Board'], list):
                        for _i in i['Board']:
                            _i['Role'] = role_map[_i['Role']]
                    elif isinstance(i['Board'], dict):
                        i['Board']['Role'] = role_map[i['Board']['Role']]
                return request_irf_info
            else:
                if 'Board' in request_irf_info.keys():
                    request_irf_info['Board']['Role'] = role_map[request_irf_info['Board']['Role']]
                    return [request_irf_info]
                else:
                    return []
        else:
            return []

        # request_irf_bfd_info = str(self.netconf_cli(obtain_h3c_irf_bfd_info_xml)).splitlines()
        # request_irf_bfd_info = [x.strip() for x in request_irf_bfd_info
        #                         if re.match(r'(Session.*:\s(Down|Up)|Protocol:.*)', x.strip(), re.I)]
        # request_irf_link_info = request_info.netconf_get(obtain_h3c_irf_link_info_xml)

    def collection_logbuffer_summary_info(self):
        """请求的XML_CLI命令"""
        obtain_h3c_display_logbuffer_summary_xml = '''
        <Execution>
        display logbuffer summary
        </Execution>
        '''
        request_info = self.netconf_cli(obtain_h3c_display_logbuffer_summary_xml)
        return request_info

    def colleciton_interfaceinfo(self):
        """
        请求的XML命令
        """
        obtain_h3c_interfaceinfo_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <Ifmgr>
        <Interfaces>
        <Interface>
        </Interface>
        </Interfaces>
        </Ifmgr>
        </top>
        '''
        request_info = self.netconf_get(obtain_h3c_interfaceinfo_xml)['top']['Ifmgr']['Interfaces']['Interface']
        return request_info

    def collection_yang_info(self):
        yang_xml = '''
            <netconf-state xmlns='urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring'>
            <schemas/>
            </netconf-state>
            '''
        request_info = self.netconf_get(yang_xml)['netconf-state']['schemas']['schema']
        return request_info

    def save_running_config(self):
        request_info = self.save_config()
        return request_info

    def rollback_config(self):
        request_info = self.rollback()
        return request_info

    def collection_ipv4staticroute(self):
        xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <StaticRoute>
             <Ipv4StaticRouteConfigurations>
               <RouteEntry>
                  <DestVrfIndex></DestVrfIndex>
                  <DestTopologyIndex></DestTopologyIndex>
                  <Ipv4Address></Ipv4Address>
                  <Ipv4PrefixLength></Ipv4PrefixLength>
                  <NexthopVrfIndex></NexthopVrfIndex>
                  <NexthopIpv4Address></NexthopIpv4Address>
                  <IfIndex></IfIndex>
                  <Tag></Tag>
                  <Preference></Preference>
                  <Description></Description>
                  <Permanent></Permanent>
                  <BackupPathAttribute>
                    <BackupIfIndex></BackupIfIndex>
                    <BackupNexthopIpv4Address></BackupNexthopIpv4Address> 
                  </BackupPathAttribute>
                  <BfdAttribute>
                    <BfdWorkMode></BfdWorkMode>
                    <BfdSourceIpv4Address></BfdSourceIpv4Address>
                  </BfdAttribute>
               </RouteEntry>
             </Ipv4StaticRouteConfigurations>
          </StaticRoute>
        </top>
        '''
        request = self.netconf_get(xml)["top"]['StaticRoute']['Ipv4StaticRouteConfigurations']['RouteEntry']
        return request

    def collection_snmpconfig(self):
        system_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
         <SNMP>
          <System>
            <AgentStatus></AgentStatus>
            <Version>
              <V1></V1>
              <V2C></V2C>
              <V3></V3>
            </Version>
            <Location></Location>
            <Contact></Contact>
          </System>
         </SNMP>
         </top>
        '''
        snmp_agent_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
         <SNMP>
          <Agent>
            <LocalEngineId></LocalEngineId>
            <AgentUdpPort></AgentUdpPort>
            <PacketMaxSize></PacketMaxSize>
            <GetLog></GetLog>
            <SetLog></SetLog>
            <NotificationLog></NotificationLog>
          </Agent>
         </SNMP>
         </top>
        '''
        Communities_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <SNMP>
          <Communities>
            <Community>
              <Name></Name>
              <Type></Type>
              <Role></Role>
              <MIBView></MIBView>
              <IPv4BasicACL>
               <Number></Number>
              </IPv4BasicACL>
              <IPv6BasicACL>
               <Number></Number>
              </IPv6BasicACL>
              <Context></Context>
            </Community>
          </Communities>
        </SNMP>
        </top>
        '''
        request = self.netconf_get(system_xml)["top"]['SNMP']['System']
        return request

    def collection_BGP_config(self):

        instance_xml = '''
          <Instances>
            <Instance>
              <Name></Name>
              <ASNumber></ASNumber>
              <NSR></NSR>
              <SendDelayTime></SendDelayTime>
              <SendDelayPrefix></SendDelayPrefix>
              <SendStartupTime></SendStartupTime>
              <StartupPolicyMed></StartupPolicyMed>
            </Instance>
          </Instances>
        '''
        vrfs_xml = '''
        <VRFs>
            <VRF>
              <Name></Name>
              <VRF></VRF>
              <RouterId></RouterId>
              <Timer>
               <KeepAlive></KeepAlive>
               <HoldTime></HoldTime>
              </Timer>
              <BestRouteIgpMetricIgnore></BestRouteIgpMetricIgnore>
            </VRF>
        </VRFs>
        '''

        CfgSessionGroups_xml = '''
        <CfgSessionGroups>
            <CfgSessionGroup>
              <Name></Name>
              <VRF></VRF>
              <GroupName></GroupName>
              <Type></Type>
              <ASNumber></ASNumber>
              <ConnectInterface></ConnectInterface>
              <UpdateInterval></UpdateInterval>
              <PasswordType></PasswordType>
              <Password></Password>
              <BfdType></BfdType>
              <EbgpMaxHop></EbgpMaxHop>
              <Ignore></Ignore>
            </CfgSessionGroup>
          </CfgSessionGroups>
        '''

        CfgSessions_xml = '''
        <CfgSessions>
            <CfgSession>
              <Name></Name>
              <VRF></VRF>
              <SessAF></SessAF>
              <IpAddress></IpAddress>
              <Mask></Mask>
              <ASNumber></ASNumber>
              <GroupName></GroupName>
              <ConnectInterface></ConnectInterface>
              <UpdateInterval></UpdateInterval>
              <PasswordType></PasswordType>
              <Password></Password>
              <BfdType></BfdType>
              <EbgpMaxHop></EbgpMaxHop>
              <Ignore></Ignore>
            </CfgSession>
          </CfgSessions>
        '''
        Sessions_xml = '''
          <Sessions>
            <Session>
              <Name></Name>
              <VRF></VRF>
              <AF></AF>
              <IpAddress></IpAddress>
              <ASNumber></ASNumber>
              <State></State>
            </Session>
          </Sessions>
        '''

        head_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <BGP>
        '''
        tail_xml = '''
        </BGP>
        </top>
        '''
        xml = head_xml + instance_xml + vrfs_xml + CfgSessionGroups_xml + CfgSessions_xml + Sessions_xml + tail_xml
        res = self.netconf_get(xml)["top"]['BGP']
        # print('instance*******')
        tmp = res['Instances']['Instance']
        for key, value in tmp.items():
            print('{key}:{value}'.format(key=key, value=value))
        print('VRPs*******')
        tmp = res['VRFs']['VRF']
        for key, value in tmp.items():
            print('{key}:{value}'.format(key=key, value=value))
        print('CfgSessions*******')
        tmp = res['CfgSessions']['CfgSession']
        for i in tmp:
            print(i)
        print('Sessions*******')
        tmp = res['Sessions']['Session']
        for i in tmp:
            print(i)
        return res

    def collection_ACL_config(self):

        Capability_xml = '''
        <ACL>
          <Capability>
            <UserAclL2>
              <L2MaxOffset></L2MaxOffset>
              <L2MaxLen></L2MaxLen>
            </UserAclL2><UserAclL4>
              <L4MaxOffset></L4MaxOffset>
              <L4MaxLen></L4MaxLen>
            </UserAclL4>
            <UserAclIPv4>
              <IPv4MaxOffset></IPv4MaxOffset>
              <IPv4MaxLen></IPv4MaxLen>
            </UserAclIPv4>
            <UserAclIPv6>
              <IPv6MaxOffset></IPv6MaxOffset>
              <IPv6MaxLen></IPv6MaxLen>
            </UserAclIPv6>
          </Capability>
         </ACL>
        '''
        head_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <BGP>
        '''
        tail_xml = '''
        </BGP>
        </top
        '''

        xml = head_xml + Capability_xml + tail_xml
        re = self.netconf_get(xml)["top"]['BGP']

    def collection_arp_vsi(self):
        xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <L2VPN> 
        <VSIIpv4Subnets> 
        <Ipv4Subnet> 
        <VsiName></VsiName> 
        <SubnetAddress></SubnetAddress>
        <WildCardMask></WildCardMask> 
        <VsiInterfaceID></VsiInterfaceID>
        </Ipv4Subnet>
        </VSIIpv4Subnets>
        </L2VPN> 
        </top>
        '''
        res = self.netconf_get(xml)
        # print(res)
        if res:
            return res["top"]['L2VPN']['VSIIpv4Subnets']['Ipv4Subnet']
        else:
            return False

    def patch_version(self):
        """
        type : {'0': 'bin', '1': 'patch'}
        指定type类型为1，获取补丁版本回填
        :return:
        """
        data_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <Package>
        <ImageLists> <ImageList>
        <FileName></FileName> <Model></Model>
        <Type>1</Type>
        <Service></Service>
        <FilePlatVersion></FilePlatVersion>
        <FileProductVersion></FileProductVersion>
        </ImageList>
        </ImageLists>
        </Package>
        </top>
        '''
        # data_xml = '''
        # <top xmlns="http://www.h3c.com/netconf/data:1.0">
        # <Package>
        # <BootLoaderList>
        # <BootList>
        # <DeviceNode>
        # <Chassis></Chassis>
        # <Slot></Slot>
        # <CPUID></CPUID>
        # </DeviceNode>
        # <BootType>0</BootType>
        # <ImageFiles>
        # <FileName></FileName>
        # </ImageFiles>
        # </BootList>
        # </BootLoaderList>
        # </Package>
        # </top>
        # '''
        # type_map = {'0': 'bin', '1': 'patch'}
        # service_map = {'1': 'boot', '2': 'system', '3': 'feature'}
        # {'FileName': 'flash:/S6860-CMW710-SYSTEM-R2702H13.bin', 'Type': '1', 'Service': '2',
        # 'FilePlatVersion': 'Release 2702H13', 'FileProductVersion': 'Release 2702'}
        # BootType = {'0': 'current', '1': 'main next', '2': 'backup next'}
        res = self.netconf_get(data_xml)
        if res:
            # result = res["top"]['Package']['BootLoaderList']['BootList']
            # if isinstance(result, dict):
            return res["top"]['Package']['ImageLists']['ImageList']
        else:
            return None

    # 获取全局NAT
    def get_global_nat_policy(self, mode='DNAT', name=''):
        """
        10.254.12.100 不支持 <TransSrcIP> (<Rule>下)
        :param mode:
        :return:
        """
        if self.netconf_dict['device_params']['name'] == "hpcomware":
            return []
        # 默认获取DNAT
        if mode == 'DNAT':
            TransMode = '1'  # DNAT
        else:
            TransMode = '0'  # SNAT
        data_xml = """
        <top xmlns='http://www.h3c.com/netconf/data:1.0'>
        <NAT>
        <GlobalPolicyRuleMembers>
        <Rule>
        <RuleName>{RuleName}</RuleName>
        <Description/>
        <TransMode>{TransMode}</TransMode>
        <SrcObjGrpList>
        <SrcIpObjGroup/>
        </SrcObjGrpList>
        <SrcIPList>
        <SrcIP/>
        </SrcIPList>
        <DstObjGrpList>
        <DstIpObjGroup/>
        </DstObjGrpList>
        <DstIPList>
        <DstIP/>
        </DstIPList>
        <SrvObjGrpList>
        <ServiceObjGroup/>
        </SrvObjGrpList>
        <SrcZoneList>
        <SrcZone/>
        </SrcZoneList>
        <DstZoneList>
        <DstZone/>
        </DstZoneList>
        <TransSrcType/>
        <TransSrcAddrType/>
        <TransAddrGroupNumber/>
        <TransAddrGroupName/>
        <TransReversible/>
        <TransPortPreserved/>
        <TransDstType/>
        <TransDstIP/>
        <TransDstPort/>
        <Disable/>
        <Counting/>
        <MatchingCount/>
        <RuleTotalCount/>
        </Rule>
        </GlobalPolicyRuleMembers>
        </NAT>
        </top>
        """.format(RuleName=name, TransMode=TransMode)
        res = self.netconf_get_bulk(data_xml)
        if res:
            # print(res)
            if 'NAT' in res['top'].keys():
                trans_mode_map = {
                    '0': 'SNAT',
                    '1': 'DNAT',
                }
                return res['top']['NAT']['GlobalPolicyRuleMembers']['Rule']
        return []

    # 获取NAT地址池 很多型号不支持
    def get_netaddr_pool(self):
        data_xml = '''
                <top xmlns="http://www.h3c.com/netconf/data:1.0">
                <NAT> 
                <AddrPoolAlloc> 
                <AddrBlock> 
                    <AddrPoolName></AddrPoolName>
                    <VxLanID></VxLanID>
                    <DPAddress></DPAddress>
                    <StartIpv4Address></StartIpv4Address>
                    <EndIpv4Address></EndIpv4Address>
                </AddrBlock>
                </AddrPoolAlloc>
                </NAT>
                </top>
                '''
        res = self.netconf_get(data_xml)
        return res

    def nat_dynamic_rules(self):
        data_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <NAT> 
        <InboundDynamicRules> 
            <Interface> 
            <IfIndex></IfIndex> <ACLNumber></ACLNumber>
            <AddrGroupNumber></AddrGroupNumber>
            <VRF></VRF>
            <NoPAT></NoPAT> <Reversible></Reversible>
            <AutoAddRoute></AutoAddRoute>
            <RuleName></RuleName> <RulePriority></RulePriority>
            <MatchingCount></MatchingCount>
            <Counting></Counting>
            </Interface>
        </InboundDynamicRules>
        <OutboundDynamicRules> 
          <Interface> 
          <IfIndex></IfIndex> 
          <ACLNumber></ACLNumber> 
          <AddrGroupNumber></AddrGroupNumber>
          <VRF></VRF>
          <NoPAT></NoPAT> 
          <Reversible></Reversible> 
          <PortPreserved></PortPreserved> 
          <RuleName></RuleName> 
          <RulePriority></RulePriority>
          <MatchingCount></MatchingCount>
          <Counting></Counting>
          </Interface>
          </OutboundDynamicRules>
        </NAT>
        </top>
        '''
        res = self.netconf_get(data_xml)
        return res

    def nat_static_mapping(self):
        data_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <NAT>
        <InboundStaticMappings>
        <Mapping>
        <GlobalInfo>
        <GlobalVRF></GlobalVRF>
        <StartIpv4Address></StartIpv4Address> <EndIpv4Address></EndIpv4Address>
        </GlobalInfo>
        <LocalInfo>
        <LocalVRF></LocalVRF>
        <Ipv4Address></Ipv4Address>
        <Ipv4PrefixLength></Ipv4PrefixLength>
        </LocalInfo>
        <ACLNumber></ACLNumber>
        <Reversible></Reversible>
        <RuleName></RuleName> <RulePriority></RulePriority> <MatchingCount></MatchingCount> <Counting></Counting>
        </Mapping>
        </InboundStaticMappings>
        </NAT>
        </top>
        '''
        res = self.netconf_get(data_xml)
        return res

    # 获取全局下nat policy  无效
    def nat_policy(self):
        data_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <NAT>
        <NatPolicy>
            <Policy></Policy>
        </NatPolicy>
        <PolicyRules>
        <Rule>
            <RuleName></RuleName>
        </Rule>
        </PolicyRules>
        <PolicyRuleMembers>
        <Rule>
            <RuleName></RuleName>
            <Description></Description>
            <OutboundInterface></OutboundInterface>
            <SrcObjGrpList>
            <SrcIpObjGroup></SrcIpObjGroup>
            </SrcObjGrpList>
            <DstObjGrpList>
            <DstIpObjGroup></DstIpObjGroup>
            </DstObjGrpList>
            <SrvObjGrpList>
            <ServiceObjGroup></ServiceObjGroup>
            </SrvObjGrpList>
            <Action></Action>
            <AddrGroupNumber></AddrGroupNumber>
            <AddrGroupName></AddrGroupName>
            <Reversible></Reversible>
            <PortPreserved></PortPreserved>
            <Disable></Disable>
            <Counting></Counting>
            <MatchingCount></MatchingCount>
        </Rule>
        </PolicyRuleMembers>
        </NAT>
        </top>
        '''
        res = self.netconf_get(data_xml)
        return res

    def nat_server_group(self):
        data_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <NAT> <ServerGroups> <ServerGroup> <GroupNumber></GroupNumber>
        </ServerGroup>
        </ServerGroups>
        </NAT>
        </top>
        '''
        res = self.netconf_get(data_xml)
        return res

    def nat_object_server(self):
        data_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <NAT>
        <ObjServer>
        <Rule>
        <RuleName></RuleName>
        <IfIndex></IfIndex> <DstObjGrpList>
        <DstObjGrp></DstObjGrp>
        </DstObjGrpList>
        <SrvObjGrpList>
        <SrvObjGrp></SrvObjGrp>
        </SrvObjGrpList>
        <Action></Action>
        <LocalInfo> <LocalIP></LocalIP> <LocalPort></LocalPort>
        </LocalInfo>
        <Disable></Disable>
        <Counting></Counting> <MatchingCount></MatchingCount> <TotalCount></TotalCount>
        </Rule>
        </ObjServer>
        </NAT>
        </top>
        '''
        res = self.netconf_get(data_xml)
        return res

    # 获取安全策略
    def get_sec_policy(self):
        """
        <top xmlns='http://www.h3c.com/netconf/data:1.0'>
        <SecurityPolicies>
        <GetRules web:count='25'>
        <Rule web:filter = "Location 1">
        <ID/>
        <Type/>
        <Name/>
        <Action/>
        <SrcZoneList>
        <SrcZoneItem/>
        </SrcZoneList>
        <DestZoneList>
        <DestZoneItem/>
        </DestZoneList>
        <SrcAddrList>
        <SrcAddrItem/>
        </SrcAddrList>
        <SrcMacAddrList>
        <SrcMacAddrItem/>
        </SrcMacAddrList>
        <DestAddrList>
        <DestAddrItem/>
        </DestAddrList>
        <ServGrpList>
        <ServGrpItem/>
        </ServGrpList>
        <AppList>
        <AppItem/>
        </AppList>
        <AppGrpList>
        <AppGrpItem/>
        </AppGrpList>
        <UserList>
        <UserItem/>
        </UserList>
        <UserGrpList>
        <UserGrpItem/>
        </UserGrpList>
        <SrcSimpleAddrList>
        <SrcSimpleAddrItem/>
        </SrcSimpleAddrList>
        <DestSimpleAddrList>
        <DestSimpleAddrItem/>
        </DestSimpleAddrList>
        <ServObjList>
        <ServObjItem/>
        </ServObjList>
        <TimeRange/>
        <VRF/>
        <Profile/>
        <Enable/>
        <Log/>
        <Counting/>
        <Count/>
        <Byte/>
        <SessAgingTimeSw/>
        <SessAgingTime/>
        <SessPersistAgingTimeSw/>
        <SessPersistAgingTime/>
        <AllRulesCount/>
        <Comment/>
        </Rule>
        </GetRules>
        </SecurityPolicies>
        </top>

        :return:
        """
        data_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <SecurityPolicies>
        <GetRules>
            <Rule>
            <Type></Type>
            <ID></ID>
            <Name></Name>
            <Action></Action>
            <SrcZoneList>
            <SrcZoneItem></SrcZoneItem>
            </SrcZoneList>
            <DestZoneList>
            <DestZoneItem></DestZoneItem>
            </DestZoneList>
            <SrcAddrList>
            <SrcAddrItem></SrcAddrItem>
            </SrcAddrList>
            <DestAddrList>
            <DestAddrItem></DestAddrItem>
            </DestAddrList>
            <SrcMacAddrList>
            <SrcMacAddrItem></SrcMacAddrItem>
            </SrcMacAddrList>
            <ServGrpList>
            <ServGrpItem></ServGrpItem>
            </ServGrpList>
            <AppList>
            <AppItem></AppItem>
            </AppList>
            <AppGrpList>
            <AppGrpItem></AppGrpItem>
            </AppGrpList>
            <UserList>
            <UserItem></UserItem>
            </UserList>
            <UserGrpList>
            </UserGrpList>
            <SrcSimpleAddrList>
            <SrcSimpleAddrItem/>
            </SrcSimpleAddrList>
            <DestSimpleAddrList>
            <DestSimpleAddrItem/>
            </DestSimpleAddrList>
            <ServObjList>
            <ServObjItem/>
            </ServObjList>
            <TimeRange></TimeRange>
            <VRF></VRF>
            <Profile></Profile>
            <Enable></Enable>
            <Log></Log>
            <Counting></Counting>
            <Count></Count>
            <Byte></Byte>
            <SessAgingTimeSw></SessAgingTimeSw>
            <SessAgingTime></SessAgingTime>
            <SessPersistAgingTimeSw></SessPersistAgingTimeSw>
            <SessPersistAgingTime></SessPersistAgingTime>
            <AllRulesCount></AllRulesCount>
            </Rule>
        </GetRules>
        </SecurityPolicies>
        </top>
        '''
        try:
            res = self.netconf_get(data_xml)['top']
        except Exception as e:
            print(e)
            data_xml = '''
                    <top xmlns="http://www.h3c.com/netconf/data:1.0">
                    <SecurityPolicies> 
                    <GetRules>
                        <Rule>
                        <Type></Type>
                        <ID></ID>
                        <Name></Name>
                        <Action></Action>
                        <SrcZoneList>
                        <SrcZoneItem></SrcZoneItem>
                        </SrcZoneList>
                        <DestZoneList>
                        <DestZoneItem></DestZoneItem>
                        </DestZoneList>
                        <SrcAddrList>
                        <SrcAddrItem></SrcAddrItem>
                        </SrcAddrList>
                        <DestAddrList>
                        <DestAddrItem></DestAddrItem>
                        </DestAddrList>
                        <SrcMacAddrList>
                        <SrcMacAddrItem></SrcMacAddrItem>
                        </SrcMacAddrList>
                        <ServGrpList>
                        <ServGrpItem></ServGrpItem>
                        </ServGrpList>
                        <AppList>
                        <AppItem></AppItem>
                        </AppList>
                        <AppGrpList>
                        <AppGrpItem></AppGrpItem>
                        </AppGrpList>
                        <UserList>
                        <UserItem></UserItem>
                        </UserList>
                        <UserGrpList>
                        </UserGrpList>
                        <TimeRange></TimeRange>
                        <VRF></VRF>
                        <Profile></Profile>
                        <Enable></Enable>
                        <Log></Log>
                        <Counting></Counting>
                        <Count></Count>
                        <Byte></Byte>
                        <SessAgingTimeSw></SessAgingTimeSw>
                        <SessAgingTime></SessAgingTime>
                        <SessPersistAgingTimeSw></SessPersistAgingTimeSw>
                        <SessPersistAgingTime></SessPersistAgingTime>
                        <AllRulesCount></AllRulesCount>
                        <Comment></Comment>
                        </Rule>
                    </GetRules>
                    </SecurityPolicies>
                    </top>
                    '''
            res = self.netconf_get(data_xml)
            if not res:
                return False
            else:
                res = res['top']
        if 'SecurityPolicies' not in res.keys():
            return False
        if res:
            type_map = {'1': 'IPv4', '2': 'IPv6'}
            action_map = {'1': 'Deny', '2': 'Permit'}
            result = res['SecurityPolicies']['GetRules']['Rule']
            if isinstance(result, dict):
                result = [result]
            for i in result:
                i['Type'] = type_map[i['Type']]
                i['Action'] = action_map[i['Action']]
            return result
        else:
            return False

    # 获取地址组
    def get_ipv4_group(self, name=""):
        data_xml = """
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <OMS>
            <IPv4Groups>
                <Group>
                <Name>{name}</Name>
                <Description></Description>
                <ObjNum></ObjNum> 
                <InUse></InUse>
                <SecurityZone></SecurityZone>
                </Group>
            </IPv4Groups>
        </OMS>
        </top>
        """.format(name=name)
        res = self.netconf_get(data_xml)['top']
        if res:
            if isinstance(res['OMS']['IPv4Groups']['Group'], dict):
                return [res['OMS']['IPv4Groups']['Group']]
            elif isinstance(res['OMS']['IPv4Groups']['Group'], list):
                return res['OMS']['IPv4Groups']['Group']
        return []

    # 获取地址对象
    def get_ipv4_objs(self, name=""):
        data_xml = """
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <OMS>
            <IPv4Objs>
            <Obj>
                <Group>{name}</Group>
                <ID></ID>
                <Type></Type>
                <SubnetIPv4Address></SubnetIPv4Address>
                <IPv4Mask></IPv4Mask>
                <StartIPv4Address></StartIPv4Address>
                <EndIPv4Address></EndIPv4Address>
                <HostIPv4Address></HostIPv4Address>
                <HostName></HostName>
                <NestedGroup></NestedGroup>
            </Obj>
            </IPv4Objs>
        </OMS>
        </top>
        """.format(name=name)
        res = self.netconf_get(data_xml)['top']
        # type 0—Nested group.
        # • 1—Subnet.
        # • 2—Range.
        # • 3—Host address.
        # • 4—Host name.
        # type_map = {
        #     "1": "subnet",
        #     "2": "range",
        #     # "3": "Host address",
        #     "3": "ip",
        #     # "4": "Host name"
        #     "4": "HostName"
        # }
        if res:
            # for i in res['OMS']['IPv4Objs']['Obj']:
            #     i['Type'] = type_map[i['Type']]
            return res['OMS']['IPv4Objs']['Obj']
        else:
            return []

    def get_ipv4_paging(self, name="", map=True):
        data_xml = """
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <OMS> 
        <IPv4Paging> 
        <Group>
        <Name>{name}</Name>
        <Description></Description>
        <ObjNum></ObjNum> 
        <InUse></InUse> 
        <SecurityZone></SecurityZone> 
        <ObjList>
        <ID></ID> 
        <Type></Type> 
        <SubnetIPv4Address></SubnetIPv4Address> 
        <IPv4Mask></IPv4Mask> 
        <IPv4WildcardAddress></IPv4WildcardAddress> 
        <IPv4WildcardMask></IPv4WildcardMask> 
        <StartIPv4Address></StartIPv4Address> 
        <EndIPv4Address></EndIPv4Address> 
        <HostIPv4Address></HostIPv4Address> 
        <HostName></HostName> 
        <NestedGroup></NestedGroup> 
        <User></User> 
        <UserDomain></UserDomain> 
        <UserGroup></UserGroup> 
        <UserGroupDomain></UserGroupDomain> 
        <ExcludeIPv4Address></ExcludeIPv4Address> 
        </ObjList> 
        <AllGroupsCount></AllGroupsCount>
        </Group>
        </IPv4Paging>
        </OMS>
        </top>
        """.format(name=name)
        res = self.netconf_get(data_xml)
        # type 0—Nested group.
        # • 1—Subnet.
        # • 2—Range.
        # • 3—Host address.
        # • 4—Host name.
        type_map = {
            "0": "Nested group.",
            "1": "subnet",
            "2": "range",
            # "3": "Host address",
            "3": "ip",
            # "4": "Host name"
            "4": "HostName",
            "5": "User",
            "6": "UserGroup",
            "7": "Wildcard",
        }
        if res:
            if isinstance(res['top']['OMS']['IPv4Paging']['Group'], dict):
                res['top']['OMS']['IPv4Paging']['Group'] = [res['top']['OMS']['IPv4Paging']['Group']]
            for i in res['top']['OMS']['IPv4Paging']['Group']:
                if 'ObjList' in i.keys():
                    if isinstance(i['ObjList'], dict):
                        i['ObjList'] = [i['ObjList']]
                        if map:
                            for _t in i['ObjList']:
                                _t['Type'] = type_map[_t['Type']]
                    elif isinstance(i['ObjList'], list):
                        if map:
                            for _t in i['ObjList']:
                                _t['Type'] = type_map[_t['Type']]
            return res['top']['OMS']['IPv4Paging']['Group']
        else:
            return []

    # 获取安全域
    def get_sec_zone(self):
        xml = """
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <SecurityZone>
        <Zones> 
            <Zone> 
                <Name></Name> 
                <ID></ID>
            </Zone>
        </Zones>
        </SecurityZone>
        </top>
        """
        res = self.netconf_get(xml)['top']
        return res['SecurityZone']['Zones']['Zone']

    # 获取服务组
    def get_server_groups(self, name=""):
        if name:
            data_xml = """
                    <top xmlns='http://www.h3c.com/netconf/data:1.0' >
                    <OMS>
                    <ServGroups>
                        <Group>
                        <Name>{name}</Name>
                        <Description/>
                        <ObjNum/>
                        <InUse/>
                        </Group>
                    </ServGroups>
                    <ServObjs>
                        <Obj>
                        <Group/>
                        <ID/>
                        <Type/>
                        <Protocol/>
                        <StartSrcPort/>
                        <EndSrcPort/>
                        <StartDestPort/>
                        <EndDestPort/>
                        <ICMPType/>
                        <ICMPCode/>
                        <NestedGroup/>
                        </Obj>
                    </ServObjs>
                    </OMS>
                    </top>
                    """.format(name=name)
        else:
            data_xml = """
            <top xmlns='http://www.h3c.com/netconf/data:1.0' >
            <OMS>
            <ServGroups>
                <Group>
                <Name/>
                <Description/>
                <ObjNum/>
                <InUse/>
                </Group>
            </ServGroups>
            <ServObjs>
                <Obj>
                <Group/>
                <ID/>
                <Type/>
                <Protocol/>
                <StartSrcPort/>
                <EndSrcPort/>
                <StartDestPort/>
                <EndDestPort/>
                <ICMPType/>
                <ICMPCode/>
                <NestedGroup/>
                </Obj>
            </ServObjs>
            <SysServGroups>
                <Group>
                <Name/>
                <Description/>
                <ObjNum/>
                <InUse/>
                </Group>
            </SysServGroups>
            </OMS>
            </top>
            """
        res = self.netconf_get(data_xml)['top']
        if res:
            service_set = []
            groups = []
            service_result = dict()
            # 系统内置服务组
            if 'SysServGroups' in res['OMS'].keys():
                groups += res['OMS']['SysServGroups']['Group']
            # 用户定义服务组
            if 'ServGroups' in res['OMS'].keys():
                if isinstance(res['OMS']['ServGroups']['Group'], dict):
                    groups += [res['OMS']['ServGroups']['Group']]
                elif isinstance(res['OMS']['ServGroups']['Group'], list):
                    groups += res['OMS']['ServGroups']['Group']
            for i in groups:
                service_result[i['Name']] = i
            serv_objs = res['OMS']['ServObjs']['Obj']
            for i in serv_objs:
                if i['Group'] in service_result.keys():
                    if service_result[i['Group']].get('items'):
                        service_result[i['Group']]['items'].append(i)
                    else:
                        service_result[i['Group']]['items'] = [i]
            for i in service_result.keys():
                service_set.append(service_result[i])
            return service_set

        return []


# 防火墙自动化
class H3CSecPath(H3CNetconf):

    def __init__(self, *args, **kwargs):
        super(H3CSecPath, self).__init__(*args, **kwargs)
        self.device_type = kwargs.get("device_type")

    @staticmethod
    def get_method():
        return [func for func in dir(H3CSecPath) if
                callable(getattr(H3CSecPath, func)) and not func.startswith("__")]

    def get_boards(self):
        xml = """
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
              <Class></Class>
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
        """
        req = self.netconf_get(xml)
        if req:
            return req["top"]['Device']['PhysicalEntities']['Entity']
        return []

    def get_secpath_physical(self, class_flag=3):
        '''
        构建XML，指定class 类型为3 ，获取软硬件信息
        防火墙 class 类型为9? 不正确，9是slot板卡，有主控板
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
            # Boards = req["top"]['Device']['Boards']['Board']
            PhysicalEntities = req["top"]['Device']['PhysicalEntities']['Entity']
            # if isinstance(Boards, dict):
            #     Boards = [Boards]
            # BoardslIndex = [x['PhysicalIndex'] for x in Boards]
            # res = [x for x in PhysicalEntities if x['PhysicalIndex'] in BoardslIndex]
            return PhysicalEntities
        else:
            return False

    def get_ipv4_oms(self, name):
        data_xml = """
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <OMS>
        <GetIPv4ObjData>
        <Obj>
        <Group>{name}</Group>
        <ID/>
        <Type/>
        <SubnetIPv4Address/>
        <IPv4Mask/>
        <IPv4WildcardAddress/>
        <IPv4WildcardMask/>
        <StartIPv4Address/>
        <EndIPv4Address/>
        <HostIPv4Address/>
        <HostName/>
        <NestedGroup/>
        <User/>
        <UserDomain/>
        <UserGroup/>
        <UserGroupDomain/>
        <ExcludeIPv4Address/>
        </Obj>
        </GetIPv4ObjData>
        </OMS>
        </top>
        """.format(name=name)
        res = self.netconf_get(data_xml)
        return res['top']['OMS']['GetIPv4ObjData']['Obj']

    def get_ipv4_paging(self, name="", map=True):
        data_xml = """
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <OMS> 
        <IPv4Paging> 
        <Group>
        <Name>{name}</Name>
        <Description></Description>
        <ObjNum></ObjNum> 
        <InUse></InUse> 
        <SecurityZone></SecurityZone> 
        <ObjList>
        <ID></ID> 
        <Type></Type> 
        <SubnetIPv4Address></SubnetIPv4Address> 
        <IPv4Mask></IPv4Mask> 
        <IPv4WildcardAddress></IPv4WildcardAddress> 
        <IPv4WildcardMask></IPv4WildcardMask> 
        <StartIPv4Address></StartIPv4Address> 
        <EndIPv4Address></EndIPv4Address> 
        <HostIPv4Address></HostIPv4Address> 
        <HostName></HostName> 
        <NestedGroup></NestedGroup> 
        <User></User> 
        <UserDomain></UserDomain> 
        <UserGroup></UserGroup> 
        <UserGroupDomain></UserGroupDomain> 
        <ExcludeIPv4Address></ExcludeIPv4Address> 
        </ObjList> 
        <AllGroupsCount></AllGroupsCount>
        </Group>
        </IPv4Paging>
        </OMS>
        </top>
        """.format(name=name)
        res = self.netconf_get(data_xml)
        # type 0—Nested group.
        # • 1—Subnet.
        # • 2—Range.
        # • 3—Host address.
        # • 4—Host name.
        type_map = {
            "0": "Nested group.",
            "1": "subnet",
            "2": "range",
            # "3": "Host address",
            "3": "ip",
            # "4": "Host name"
            "4": "HostName",
            "5": "User",
            "6": "UserGroup",
            "7": "Wildcard",
        }
        if res:
            if isinstance(res['top']['OMS']['IPv4Paging']['Group'], dict):
                res['top']['OMS']['IPv4Paging']['Group'] = [res['top']['OMS']['IPv4Paging']['Group']]
            # step1 把object格式统一list类型
            for i in res['top']['OMS']['IPv4Paging']['Group']:
                if 'ObjList' in i.keys():
                    if isinstance(i['ObjList'], dict):
                        i['ObjList'] = [i['ObjList']]
            # step2 判断有没有因为page分页问题没有显示全的条目，如果有就继续补充
            for i in res['top']['OMS']['IPv4Paging']['Group']:
                if 'ObjList' in i.keys():
                    if len(i['ObjList']) != int(i['ObjNum']):
                        ext_items = self.get_ipv4_oms(name=i['Name'])
                        if ext_items:
                            i['ObjList'] += ext_items
            # step3 格式化type
            for i in res['top']['OMS']['IPv4Paging']['Group']:
                if 'ObjList' in i.keys():
                    if map:
                        for _t in i['ObjList']:
                            _t['Type'] = type_map[_t['Type']]
            return res['top']['OMS']['IPv4Paging']['Group']
        else:
            return []

    # 获取NAT地址组
    def get_nataddr_group(self) -> list:
        data_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <NAT> 
        <AddrGroups> 
            <AddrGroup> 
                <GroupNumber></GroupNumber>
                <PortBlockSize></PortBlockSize>
                <ExtendedBlockNumber></ExtendedBlockNumber>
                <StartPort></StartPort>
                <EndPort></EndPort>
            </AddrGroup>
        </AddrGroups>
        <AddrGroupMembers> 
            <GroupMember> 
            <GroupNumber></GroupNumber> 
            <StartIpv4Address></StartIpv4Address>
            <EndIpv4Address></EndIpv4Address>
            </GroupMember>
        </AddrGroupMembers>
        </NAT>
        </top>
        '''
        res = self.netconf_get(data_xml)
        if res:
            addr_groups = res["top"]["NAT"]['AddrGroups']['AddrGroup']
            addr_group_members = res["top"]["NAT"]['AddrGroupMembers']['GroupMember']
            if isinstance(addr_groups, dict):
                addr_groups = [addr_groups]
            if isinstance(addr_group_members, dict):
                addr_group_members = [addr_group_members]
            for a in addr_groups:
                for b in addr_group_members:
                    if a['GroupNumber'] == b['GroupNumber']:
                        a.update(b)
            # {'GroupNumber': '1', 'StartPort': '1', 'EndPort': '65535', 'StartIpv4Address': '10.103.1.11',
            # 'EndIpv4Address': '10.103.1.30'}
            return addr_groups
        else:
            return []

    # 获取服务组
    def get_server_groups(self, name=""):
        if name:
            data_xml = """
                    <top xmlns='http://www.h3c.com/netconf/data:1.0' >
                    <OMS>
                    <ServGroups>
                        <Group>
                        <Name>{name}</Name>
                        <Description/>
                        <ObjNum/>
                        <InUse/>
                        </Group>
                    </ServGroups>
                    <ServObjs>
                        <Obj>
                        <Group/>
                        <ID/>
                        <Type/>
                        <Protocol/>
                        <StartSrcPort/>
                        <EndSrcPort/>
                        <StartDestPort/>
                        <EndDestPort/>
                        <ICMPType/>
                        <ICMPCode/>
                        <NestedGroup/>
                        </Obj>
                    </ServObjs>
                    </OMS>
                    </top>
                    """.format(name=name)
        else:
            data_xml = """
            <top xmlns='http://www.h3c.com/netconf/data:1.0' >
            <OMS>
            <ServGroups>
                <Group>
                <Name/>
                <Description/>
                <ObjNum/>
                <InUse/>
                </Group>
            </ServGroups>
            <ServObjs>
                <Obj>
                <Group/>
                <ID/>
                <Type/>
                <Protocol/>
                <StartSrcPort/>
                <EndSrcPort/>
                <StartDestPort/>
                <EndDestPort/>
                <ICMPType/>
                <ICMPCode/>
                <NestedGroup/>
                </Obj>
            </ServObjs>
            <SysServGroups>
                <Group>
                <Name/>
                <Description/>
                <ObjNum/>
                <InUse/>
                </Group>
            </SysServGroups>
            </OMS>
            </top>
            """
        res = self.netconf_get(data_xml)['top']
        if res:
            service_set = []
            groups = []
            service_result = dict()
            # 系统内置服务组
            if 'SysServGroups' in res['OMS'].keys():
                groups = res['OMS']['SysServGroups']['Group']
            # 用户定义服务组
            if 'ServGroups' in res['OMS'].keys():
                if isinstance(res['OMS']['ServGroups']['Group'], dict):
                    groups += [res['OMS']['ServGroups']['Group']]
                elif isinstance(res['OMS']['ServGroups']['Group'], list):
                    groups += res['OMS']['ServGroups']['Group']
            for i in groups:
                service_result[i['Name']] = i
            serv_objs = res['OMS']['ServObjs']['Obj']
            for i in serv_objs:
                if i['Group'] in service_result.keys():
                    if service_result[i['Group']].get('items'):
                        service_result[i['Group']]['items'].append(i)
                    else:
                        service_result[i['Group']]['items'] = [i]
            for i in service_result.keys():
                service_set.append(service_result[i])
            return service_set

        return []

    # 删除安全策略
    def delete_sec_policy(self, method, rule_id):
        """
        <config>
        <top xmlns='http://www.h3c.com/netconf/config:1.0' web:operation='remove'>
        <SecurityPolicies>
        <IPv4Rules>
        <Rule>
        <ID>4</ID>
        </Rule>
        </IPv4Rules>
        </SecurityPolicies>
        </top>
        </config>
        :param method:
        :param rule_id:
        :return:
        """
        data_xml = """
        <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <top xmlns='http://www.h3c.com/netconf/config:1.0'>
                <SecurityPolicies  xc:operation="{method}">
                <IPv4Rules>
                <Rule>
                <ID>{rule_id}</ID>
                </Rule>
                </IPv4Rules>
                </SecurityPolicies>
            </top>
        </config>
        """.format(method=method, rule_id=rule_id)
        request_info = self.edit_config(xml_data=data_xml)
        if isinstance(request_info, tuple):
            return request_info[0], request_info[1]
        return request_info, ''

    # 配置安全策略 step1
    def config_ipv4_rule(self, **kwargs):
        # action 1 deny  2 permit
        # enable true(defalut) false disable
        # log true enable   false  disable(default)
        # counting true enable false  disable(default)
        # comment Description
        # Profile
        # SessAgingTimeSw true enable false  disable(default)
        # SessPersistAgingTime value range 0 to 2000000 seconds
        # SessPersistAgingTimeSw true enable false  disable(default)
        # SessPersistAgingTime  value range 0 to 24000 hours
        # RuleGroupName
        """
        默认源和目的安全域为Any， 服务也为Any， 地址Any
        <VRF></VRF>
        <RuleGroupName></RuleGroupName>
        <TimeRange></TimeRange>
        <Profile></Profile>
        <SessAgingTime></SessAgingTime>
        <SessPersistAgingTime></SessPersistAgingTime>
        Comment 描述
        :return:
        """
        # action_map = {
        #     "deny": "1",
        #     "permit": "2"
        # }
        data_xml = """
        <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <top xmlns="http://www.h3c.com/netconf/config:1.0">
        <SecurityPolicies xmlns="http://www.h3c.com/netconf/config:1.0" xc:operation="{method}"> 
        <IPv4Rules> 
        <Rule> 
            <ID>{ID}</ID> 
            <RuleName>{name}</RuleName> 
            <Action>{action}</Action>  
            <Enable>{enable}</Enable> 
            <Log>{log}</Log> 
            <Counting>{counting}</Counting> 
            <Comment>{description}</Comment>
            <SessAgingTimeSw>false</SessAgingTimeSw>
            <SessPersistAgingTimeSw>false</SessPersistAgingTimeSw>
        </Rule>
        </IPv4Rules> 
        </SecurityPolicies>
        </top>
        </config>
        """.format(**kwargs)
        request_info = self.edit_config(xml_data=data_xml)
        if isinstance(request_info, tuple):
            return request_info[0], request_info[1]
        return request_info, ''

    # 编辑安全策略
    def edit_ipv4_rule(self, **kwargs):
        """
        <config>
        <top xmlns='http://www.h3c.com/netconf/config:1.0' web:operation='replace'>
        <SecurityPolicies>
        <IPv4Rules>
        <Rule>
        <ID>4</ID>
        <RuleName>test123</RuleName>
        <Action>2</Action>
        <Enable>true</Enable>
        <Log>false</Log>
        <Counting>false</Counting>
        <Comment>111222</Comment>
        <SessAgingTimeSw>false</SessAgingTimeSw>
        <SessPersistAgingTimeSw>false</SessPersistAgingTimeSw>
        </Rule></IPv4Rules>
        </SecurityPolicies>
        </top>
        </config>
        <config>
        <top xmlns='http://www.h3c.com/netconf/config:1.0' web:operation='merge'>
        <SecurityPolicies>
        <IPv4ServObj web:operation='merge'>
        <ServObj>
        <ID>4</ID>
        <SeqNum/>
        <IsIncrement>false</IsIncrement>
        <ServObjList>
        <ServObjItem>{&#34;Type&#34;:&#34;0&#34;,&#34;StartSrcPort&#34;:&#34;0&#34;,&#34;EndSrcPort&#34;:&#34;65535&#34;,&#34;StartDestPort&#34;:&#34;80&#34;,&#34;EndDestPort&#34;:&#34;80&#34;}</ServObjItem>
        <ServObjItem>{&#34;Type&#34;:&#34;0&#34;,&#34;StartSrcPort&#34;:&#34;0&#34;,&#34;EndSrcPort&#34;:&#34;65535&#34;,&#34;StartDestPort&#34;:&#34;443&#34;,&#34;EndDestPort&#34;:&#34;443&#34;}</ServObjItem>
        </ServObjList>
        </ServObj>
        </IPv4ServObj>
        </SecurityPolicies>
        <SecurityPolicies>
        <IPv4SrcAddr web:operation='merge'>
        <SrcAddr>
        <ID>4</ID>
        <SeqNum/>
        <IsIncrement>false</IsIncrement>
        <NameList><NameItem>10.1.154.0/24</NameItem>
        <NameItem>10.103.101.0/24</NameItem>
        </NameList></SrcAddr>
        </IPv4SrcAddr>
        </SecurityPolicies>
        </top></config>
        :param kwargs:
        :return:
        """
        data_xml = """
                <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
                <top xmlns="http://www.h3c.com/netconf/config:1.0">
                <SecurityPolicies> 
                <IPv4Rules> 
                <Rule> 
                    <ID>65535</ID> 
                    <RuleName>{name}</RuleName> 
                    <Action>{action}</Action>  
                    <Enable>{enable}</Enable> 
                    <Log>{log}</Log> 
                    <Counting>{counting}</Counting> 
                    <Comment>{description}</Comment>
                    <SessAgingTimeSw>false</SessAgingTimeSw>
                    <SessPersistAgingTimeSw>false</SessPersistAgingTimeSw>
                </Rule>
                </IPv4Rules> 
                </SecurityPolicies>
                </top>
                </config>
                """.format(**kwargs)
        request_info = self.edit_config(xml_data=data_xml)
        if isinstance(request_info, tuple):
            return request_info[0], request_info[1]
        return request_info, ''

    # 配置安全策略 step2
    def config_sec_policy(self, SecurityPolicies):
        """
        <config>
        <top xmlns='http://www.h3c.com/netconf/config:1.0' web:operation='merge'>
            <SecurityPolicies>
            <IPv4SrcSimpleAddr web:operation='merge'>
            <SrcSimpleAddr>
            <ID>5</ID>
            <SeqNum/>
            <IsIncrement>false</IsIncrement>
            <SimpleAddrList>
            <SimpleAddrItem>1.1.1.1</SimpleAddrItem>
            <SimpleAddrItem>2.2.2.2</SimpleAddrItem>
            <SimpleAddrItem>3.3.3.3-3.3.3.10</SimpleAddrItem>
            </SimpleAddrList>
            </SrcSimpleAddr>
            </IPv4SrcSimpleAddr>
            </SecurityPolicies>
            <SecurityPolicies>
            <IPv4DestSimpleAddr web:operation='merge'>
            <DestSimpleAddr>
            <ID>5</ID>
            <SeqNum/>
            <IsIncrement>false</IsIncrement>
            <SimpleAddrList>
            <SimpleAddrItem>1.1.1.1</SimpleAddrItem>
            <SimpleAddrItem>2.2.2.2</SimpleAddrItem>
            <SimpleAddrItem>3.3.3.3-3.3.3.10</SimpleAddrItem>
            </SimpleAddrList>
            </DestSimpleAddr>
            </IPv4DestSimpleAddr>
            </SecurityPolicies>
        </top>
        </config>

        <config>
        <top xmlns='http://www.h3c.com/netconf/config:1.0' web:operation='merge'>
        <SecurityPolicies><IPv4SrcSecZone web:operation='merge'>
        <SrcSecZone>
        <ID>4</ID>
        <SeqNum/>
        <IsIncrement>false</IsIncrement>
        <NameList>
        <NameItem>Local</NameItem>
        </NameList>
        </SrcSecZone>
        </IPv4SrcSecZone>
        </SecurityPolicies>
        <SecurityPolicies>
        <IPv4DestSecZone web:operation='merge'>
        <DestSecZone>
        <ID>4</ID>
        <SeqNum/>
        <IsIncrement>false</IsIncrement>
        <NameList>
        <NameItem>Trust</NameItem>
        <NameItem>DMZ</NameItem>
        </NameList>
        </DestSecZone>
        </IPv4DestSecZone>
        </SecurityPolicies><SecurityPolicies>
        <IPv4SrcAddr web:operation='merge'>
        <SrcAddr>
        <ID>4</ID>
        <SeqNum/>
        <IsIncrement>false</IsIncrement>
        <NameList>
        <NameItem>10.103.101.0/24</NameItem>
        </NameList></SrcAddr></IPv4SrcAddr>
        </SecurityPolicies><SecurityPolicies>
        <IPv4DestAddr web:operation='merge'>
        <DestAddr>
        <ID>4</ID>
        <SeqNum/>
        <IsIncrement>false</IsIncrement>
        <NameList><NameItem>10.103.101.0/24</NameItem>
        </NameList></DestAddr>
        </IPv4DestAddr>
        </SecurityPolicies>
        <SecurityPolicies><IPv4ServGrp web:operation='merge'>
        <ServGrp>
        <ID>4</ID>
        <SeqNum/>
        <IsIncrement>false</IsIncrement>
        <NameList>
        <NameItem>ICMP</NameItem>
        </NameList>
        </ServGrp>
        </IPv4ServGrp>
        </SecurityPolicies>
        </top>
        </config>
        """
        # 新建策略ID 值必须为65535  这样系统会自动分配
        dict_data = {
            'config':
                {
                    '@xmlns:xc': 'urn:ietf:params:xml:ns:netconf:base:1.0',
                    'top':
                        {
                            '@xmlns': 'http://www.h3c.com/netconf/config:1.0',
                            '@xc:operation': 'merge',
                            'SecurityPolicies': SecurityPolicies['SecurityPolicies']
                        }
                }
        }
        res = XmlToDict().dicttoxml(dict=dict_data)
        data_xml = res.split('\n')[1]
        # print(data_xml)
        request_info = self.edit_config(xml_data=data_xml)
        # print(request_info)
        if isinstance(request_info, tuple):
            return request_info[0], request_info[1]
        return request_info, ''

    # 查询指定安全策略
    def get_sec_policy_name(self, name):
        """
        <RuleGroupName></RuleGroupName>
        :return:
        """
        data_xml = '''
                <top xmlns="http://www.h3c.com/netconf/data:1.0">
                <SecurityPolicies> 
                <GetRules>
                    <Rule>
                    <Type></Type>
                    <ID></ID>
                    <Name>{name}</Name>
                    <Action></Action>
                    <SrcZoneList>
                    <SrcZoneItem></SrcZoneItem>
                    </SrcZoneList>
                    <DestZoneList>
                    <DestZoneItem></DestZoneItem>
                    </DestZoneList>
                    <SrcAddrList>
                    <SrcAddrItem></SrcAddrItem>
                    </SrcAddrList>
                    <DestAddrList>
                    <DestAddrItem></DestAddrItem>
                    </DestAddrList>
                    <SrcMacAddrList>
                    <SrcMacAddrItem></SrcMacAddrItem>
                    </SrcMacAddrList>
                    <ServGrpList>
                    <ServGrpItem></ServGrpItem>
                    </ServGrpList>
                    <AppList>
                    <AppItem></AppItem>
                    </AppList>
                    <AppGrpList>
                    <AppGrpItem></AppGrpItem>
                    </AppGrpList>
                    <UserList>
                    <UserItem></UserItem>
                    </UserList>
                    <UserGrpList>
                    </UserGrpList>
                    <TimeRange></TimeRange>
                    <VRF></VRF>
                    <Profile></Profile>
                    <Enable></Enable>
                    <Log></Log>
                    <Counting></Counting>
                    <Count></Count>
                    <Byte></Byte>
                    <SessAgingTimeSw></SessAgingTimeSw>
                    <SessAgingTime></SessAgingTime>
                    <SessPersistAgingTimeSw></SessPersistAgingTimeSw>
                    <SessPersistAgingTime></SessPersistAgingTime>
                    <AllRulesCount></AllRulesCount>
                    <Comment></Comment>
                    </Rule>
                </GetRules>
                </SecurityPolicies>
                </top>
                '''.format(name=name)
        res = self.netconf_get(data_xml)['top']
        if 'SecurityPolicies' not in res.keys():
            return False
        if res:
            # type_map = {'1': 'IPv4', '2': 'IPv6'}
            # action_map = {'1': 'Deny', '2': 'Permit'}
            result = res['SecurityPolicies']['GetRules']['Rule']
            # for i in result:
            #     i['Type'] = type_map[i['Type']]
            #     i['Action'] = action_map[i['Action']]
            return result
        else:
            return False

    # 获取安全策略
    def get_sec_policy(self):
        """
        <RuleGroupName></RuleGroupName>
        :return:
        """
        # <Comment></Comment> 被取消
        data_xml = '''
                        <top xmlns="http://www.h3c.com/netconf/data:1.0">
                        <SecurityPolicies> 
                        <GetRules>
                            <Rule>
                            <Type></Type>
                            <ID></ID>
                            <Name></Name>
                            <Action></Action>
                            <SrcZoneList>
                            <SrcZoneItem></SrcZoneItem>
                            </SrcZoneList>
                            <DestZoneList>
                            <DestZoneItem></DestZoneItem>
                            </DestZoneList>
                            <SrcAddrList>
                            <SrcAddrItem></SrcAddrItem>
                            </SrcAddrList>
                            <DestAddrList>
                            <DestAddrItem></DestAddrItem>
                            </DestAddrList>
                            <SrcMacAddrList>
                            <SrcMacAddrItem></SrcMacAddrItem>
                            </SrcMacAddrList>
                            <ServGrpList>
                            <ServGrpItem></ServGrpItem>
                            </ServGrpList>
                            <AppList>
                            <AppItem></AppItem>
                            </AppList>
                            <AppGrpList>
                            <AppGrpItem></AppGrpItem>
                            </AppGrpList>
                            <UserList>
                            <UserItem></UserItem>
                            </UserList>
                            <UserGrpList>
                            </UserGrpList>
                            <SrcSimpleAddrList>
                            <SrcSimpleAddrItem/>
                            </SrcSimpleAddrList>
                            <DestSimpleAddrList>
                            <DestSimpleAddrItem/>
                            </DestSimpleAddrList>
                            <ServObjList>
                            <ServObjItem/>
                            </ServObjList>
                            <TimeRange></TimeRange>
                            <VRF></VRF>
                            <Profile></Profile>
                            <Enable></Enable>
                            <Log></Log>
                            <Counting></Counting>
                            <Count></Count>
                            <Byte></Byte>
                            <SessAgingTimeSw></SessAgingTimeSw>
                            <SessAgingTime></SessAgingTime>
                            <SessPersistAgingTimeSw></SessPersistAgingTimeSw>
                            <SessPersistAgingTime></SessPersistAgingTime>
                            <AllRulesCount></AllRulesCount>
                            </Rule>
                        </GetRules>
                        </SecurityPolicies>
                        </top>
                        '''
        res = self.netconf_get(data_xml)['top']
        if 'SecurityPolicies' not in res.keys():
            return False
        if res:
            type_map = {'1': 'IPv4', '2': 'IPv6'}
            action_map = {'1': 'Deny', '2': 'Permit'}
            result = res['SecurityPolicies']['GetRules']['Rule']
            for i in result:
                i['Type'] = type_map[i['Type']]
                i['Action'] = action_map[i['Action']]
            return result
        else:
            return False

    # 移动安全策略
    def move_ipv4_rule(self, **kwargs):
        if kwargs.get('rule_id') and kwargs.get('target_id') and kwargs.get('insert'):
            # 1 head  2 before  3 after  4 tail
            if kwargs['insert'] == 'before':
                move_type = 2
            elif kwargs['insert'] == 'after':
                move_type = 3
            else:
                return False
            params = dict(id=kwargs['rule_id'], dest_id=kwargs['target_id'], move_type=move_type)
            xml = """
                    <top xmlns="http://www.h3c.com/netconf/action:1.0">
                    <SecurityPolicies> 
                    <MoveIPv4Rule> 
                    <Rule> 
                    <ID>{id}</ID> 
                    <MoveType>{move_type}</MoveType> 
                    <DestID>{dest_id}</DestID>
                    </Rule>
                    </MoveIPv4Rule> 
                    </SecurityPolicies>
                    </top>
                    """.format(**params)
            request_info = self._action(xml)
            return request_info
        elif kwargs.get('rule_id') and kwargs.get('insert'):
            if kwargs['insert'] == 'first':
                move_type = '1'
            elif kwargs['insert'] == 'bottom':
                move_type = '4'
            else:
                return False
            params = dict(id=kwargs['rule_id'], move_type=move_type)
            xml = """
                <top xmlns="http://www.h3c.com/netconf/action:1.0">
                <SecurityPolicies> 
                <MoveIPv4Rule> 
                <Rule> 
                <ID>{id}</ID> 
                <MoveType>{move_type}</MoveType> 
                </Rule>
                </MoveIPv4Rule> 
                </SecurityPolicies>
                </top>
                """.format(**params)
            request_info = self._action(xml)
            return request_info
        return False

        # params = dict(id=id, dest_id=dest_id, move_type=move_type)

    # 获取源安全域和目的安全域
    def get_sec_zone(self):
        xml = """
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <SecurityZone>
        <Zones> 
            <Zone> 
                <Name></Name> 
                <ID></ID>
            </Zone>
        </Zones>
        </SecurityZone>
        </top>
        """
        res = self.netconf_get(xml)['top']
        return res['SecurityZone']['Zones']['Zone']

    # 获取安全策略包含地址对象
    def get_ipv4_addr(self):
        data_xml = """
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <SecurityPolicies> 
        <IPv4SrcAddr> 
            <SrcAddr>
            <ID></ID>
            <SeqNum></SeqNum> 
            <IsIncrement></IsIncrement> 
            <NameList>
            <NameItem></NameItem>
            </NameList>
            </SrcAddr>
        </IPv4SrcAddr>
        <IPv4DestAddr> 
            <DestAddr>
            <ID></ID>
            <SeqNum></SeqNum>
            <IsIncrement></IsIncrement>
            <NameList>
            <NameItem></NameItem>
            </NameList>
            </DestAddr>
        </IPv4DestAddr>
        </SecurityPolicies> 
        </top>
        """
        res = self.netconf_get(data_xml)['top']
        if res:
            return dict(src=res['SecurityPolicies']['IPv4SrcAddr']['SrcAddr'],
                        dst=res['SecurityPolicies']['IPv4DestAddr']['DestAddr'])
        else:
            return []

    # 查询关联服务组
    def query_server_groups(self, name):
        data_xml = """
                <top xmlns='http://www.h3c.com/netconf/data:1.0' >
                <OMS>
                <ServGroups>
                    <Group>
                    <Name>{name}</Name>
                    <Description/>
                    <ObjNum/>
                    <InUse/>
                    </Group>
                </ServGroups>
                <ServObjs>
                <Obj>
                <Group/>
                <ID/>
                <Type/>
                <Protocol/>
                <StartSrcPort/>
                <EndSrcPort/>
                <StartDestPort/>
                <EndDestPort/>
                <ICMPType/>
                <ICMPCode/>
                <NestedGroup/>
                </Obj>
                </ServObjs>
                <SysServGroups>
                <Group>
                <Name/>
                <Description/>
                <ObjNum/>
                <InUse/>
                </Group>
                </SysServGroups>
                </OMS>
                </top>
                """.format(name=name)

        res = self.netconf_get(data_xml)
        if res:
            return res['top']['OMS']['ServGroups']['Group']

        return []

    # 查询指定安全策略
    def get_sec_policy_id(self, rule_id):
        data_xml = '''
                <top xmlns="http://www.h3c.com/netconf/data:1.0">
                <SecurityPolicies> 
                <GetRules>
                    <Rule>
                    <Type></Type>
                    <ID>{rule_id}</ID>
                    <Name></Name>
                    <Action></Action>
                    <SrcZoneList>
                    <SrcZoneItem></SrcZoneItem>
                    </SrcZoneList>
                    <DestZoneList>
                    <DestZoneItem></DestZoneItem>
                    </DestZoneList>
                    <SrcAddrList>
                    <SrcAddrItem></SrcAddrItem>
                    </SrcAddrList>
                    <SrcSimpleAddrList>
                    <SrcSimpleAddrItem></SrcSimpleAddrItem>
                    </SrcSimpleAddrList>
                    <DestAddrList>
                    <DestAddrItem></DestAddrItem>
                    </DestAddrList>
                    <DestSimpleAddrList>
                    <DestSimpleAddrItem></DestSimpleAddrItem>
                    </DestSimpleAddrList>
                    <SrcMacAddrList>
                    <SrcMacAddrItem></SrcMacAddrItem>
                    </SrcMacAddrList>
                    <ServGrpList>
                    <ServGrpItem></ServGrpItem>
                    </ServGrpList>
                    <ServObjList>
                    <ServObjItem/>
                    </ServObjList>
                    <AppList>
                    <AppItem></AppItem>
                    </AppList>
                    <AppGrpList>
                    <AppGrpItem></AppGrpItem>
                    </AppGrpList>
                    <UserList>
                    <UserItem></UserItem>
                    </UserList>
                    <UserGrpList>
                    </UserGrpList>
                    <TimeRange></TimeRange>
                    <VRF></VRF>
                    <Profile></Profile>
                    <Enable></Enable>
                    <Log></Log>
                    <Counting></Counting>
                    <Count></Count>
                    <Byte></Byte>
                    <SessAgingTimeSw></SessAgingTimeSw>
                    <SessAgingTime></SessAgingTime>
                    <SessPersistAgingTimeSw></SessPersistAgingTimeSw>
                    <SessPersistAgingTime></SessPersistAgingTime>
                    <AllRulesCount></AllRulesCount>
                    <Comment></Comment>
                    </Rule>
                </GetRules>
                </SecurityPolicies>
                </top>
                '''.format(rule_id=rule_id)
        res = self.netconf_get(data_xml)['top']
        if 'SecurityPolicies' not in res.keys():
            return False
        if res:
            result = res['SecurityPolicies']['GetRules']['Rule']
            return result
        else:
            return False

    # 获取接口下NATserver
    def get_server_on_policy(self):
        data_xml = '''
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <NAT> 
        <ServerOnInterfaces> 
            <Interface> 
                <IfIndex></IfIndex>
                <ProtocolType></ProtocolType>
                <GlobalInfo> 
                <GlobalVRF></GlobalVRF>
                <GlobalStartIpv4Address></GlobalStartIpv4Address> 
                <GlobalEndIpv4Address></GlobalEndIpv4Address> 
                <GlobalStartPortNumber></GlobalStartPortNumber> 
                <GlobalEndPortNumber></GlobalEndPortNumber> 
                <GlobalIfIndex></GlobalIfIndex>
                </GlobalInfo> <LocalInfo> <LocalVRF></LocalVRF> 
                <LocalStartIpv4Address></LocalStartIpv4Address> 
                <LocalEndIpv4Address></LocalEndIpv4Address> 
                <LocalStartPortNumber>
                </LocalStartPortNumber> 
                <LocalEndPortNumber></LocalEndPortNumber>
                <LocalSrvGroupNumber>
                </LocalSrvGroupNumber> 
                </LocalInfo> 
                <ACLNumber></ACLNumber> 
                <Reversible></Reversible>
                <MatchingCount></MatchingCount>
                <Counting></Counting>
                <RuleName></RuleName>
                <RulePriority></RulePriority>
            </Interface>
        </ServerOnInterfaces>
        </NAT>
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
        res = self.netconf_get(data_xml)['top']
        if 'NAT' not in res.keys():
            return False
        if res:
            # 截取natinterface列表
            natinterface_res = res['NAT']['ServerOnInterfaces']['Interface']
            # 接口索引和name对应
            ifmgrlist = res['Ifmgr']['Interfaces']['Interface']
            if isinstance(natinterface_res, dict):
                natinterface_res = [natinterface_res]
            for a in natinterface_res:
                for b in ifmgrlist:
                    if a['IfIndex'] == b['IfIndex']:
                        a.update(Name=b['Name'])
            type_map = {
                '1': "icmp",
                '6': "tcp",
                '17': "udp",
            }
            return natinterface_res
        else:
            return False

    # 获取服务对象
    def get_service_objs(self):
        data_xml = """
                <top xmlns="http://www.h3c.com/netconf/data:1.0">
                <OMS> 
                    <ServObjs>
                    <Obj>
                    <Group></Group>
                    <ID></ID>
                    <Type></Type>
                    <Protocol></Protocol>
                    <StartSrcPort></StartSrcPort>
                    <StartDestPort></StartDestPort> <EndDestPort></EndDestPort>
                    <ICMPType></ICMPType>
                    <ICMPCode></ICMPCode>
                    <NestedGroup></NestedGroup>
                    </Obj>
                    </ServObjs>
                </OMS>
                </top>
                """
        res = self.netconf_get(data_xml)['top']
        type_map = {
            "0": "Nested group",
            "1": "Protocol",
            "2": "ICMP",
            "3": "TCP",
            "4": "UDP",
            "5": "ICMPv6",
        }
        if res:
            for x in res['OMS']['ServObjs']['Obj']:
                x['Type'] = type_map[x['Type']]
            return res['OMS']['ServObjs']['Obj']
        else:
            return []

    def get_ipv4_group(self):
        """
        :return:
        """
        data_xml = """
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <OMS>
            <IPv4Groups>
                <Group>
                <Name></Name>
                <Description></Description>
                <ObjNum></ObjNum> 
                <InUse></InUse>
                <SecurityZone></SecurityZone>
                </Group>
            </IPv4Groups>
        </OMS>
        </top>
        """
        res = self.netconf_get(data_xml)['top']
        if res:
            return res['OMS']['IPv4Groups']['Group']
        else:
            return []

    # 新建/修改地址组
    def create_ipv4_group(self, method="create", name="", description=""):
        if not name:
            return False
        if description:
            data_xml = """
            <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <top xmlns="http://www.h3c.com/netconf/config:1.0">
            <OMS xmlns="http://www.h3c.com/netconf/config:1.0" xc:operation="{method}">
            <IPv4Groups>
            <Group>
            <Name>{name}</Name>
            <Description>{description}</Description>
            </Group>
            </IPv4Groups>
            </OMS>
            </top>
            </config>
            """.format(method=method, name=name, description=description)
            request_info = self.edit_config(xml_data=data_xml)
            if isinstance(request_info, tuple):
                return request_info[0]
            return request_info
        else:
            data_xml = """
            <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <top xmlns="http://www.h3c.com/netconf/config:1.0">
            <OMS xmlns="http://www.h3c.com/netconf/config:1.0" xc:operation="{method}">
            <IPv4Groups>
            <Group>
            <Name>{name}</Name>
            </Group>
            </IPv4Groups>
            </OMS>
            </top>
            </config>
            """.format(method=method, name=name)
            request_info = self.edit_config(xml_data=data_xml)
            if isinstance(request_info, tuple):
                return request_info[0]
            return request_info

    # 删除地址组
    def delete_ipv4_group(self, name):
        data_xml = """
        <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <top xmlns="http://www.h3c.com/netconf/config:1.0">
            <OMS xmlns="http://www.h3c.com/netconf/config:1.0" xc:operation="remove">
                <IPv4Groups>
                    <Group>
                    <Name>{name}</Name>
                    </Group>
                </IPv4Groups>
            </OMS>
        </top>
        </config>
        """.format(name=name)
        request_info = self.edit_config(xml_data=data_xml)
        if isinstance(request_info, tuple):
            return request_info[0]
        return request_info

    # 删除服务组
    def delete_server_groups(self, name):
        data_xml = """
                <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
                <top xmlns="http://www.h3c.com/netconf/config:1.0">
                    <OMS xmlns="http://www.h3c.com/netconf/config:1.0" xc:operation="remove">
                        <ServGroups>
                            <Group>
                            <Name>{name}</Name>
                            </Group>
                        </ServGroups>
                    </OMS>
                </top>
                </config>
                """.format(name=name)
        request_info = self.edit_config(xml_data=data_xml)
        if isinstance(request_info, tuple):
            return request_info[0]
        return request_info

    # 配置OMS对象
    def config_oms_objs(self, OMS):
        """
        这是修改地址组某一个条目案例
        <top xmlns='http://www.h3c.com/netconf/config:1.0' web:operation='replace'>
        <OMS>
        <IPv4Objs web:operation='remove'>
        <Obj>
        <Group>12.101测试</Group>
        <ID>10</ID>
        </Obj>
        </IPv4Objs>
        </OMS>
        <OMS>
        <IPv4Objs web:operation='create'>
        <Obj>
        <Group>12.101测试</Group>
        <ID>4294967295</ID>
        <Type>1</Type>
        <SubnetIPv4Address>1.1.1.1</SubnetIPv4Address>
        <IPv4Mask>255.255.255.255</IPv4Mask>
        </Obj>
        </IPv4Objs>
        </OMS>
        </top>
        # 这是新增条目 网段形式
        <top xmlns='http://www.h3c.com/netconf/config:1.0' web:operation='replace'>
        <OMS>
        <IPv4Objs web:operation='create'>
        <Obj>
        <Group>12.101测试</Group>
        <ID>4294967295</ID>
        <Type>1</Type>
        <SubnetIPv4Address>2.2.2.2</SubnetIPv4Address>
        <IPv4Mask>255.255.255.255</IPv4Mask>
        </Obj>
        </IPv4Objs>
        </OMS>
        </top>
        # 删除条目 range
        <top xmlns='http://www.h3c.com/netconf/config:1.0' web:operation='replace'>
        <OMS>
        <IPv4Objs web:operation='remove'>
        <Obj>
        <Group>12.101测试</Group>
        <ID>0</ID>
        </Obj>
        </IPv4Objs>
        </OMS>
        </top>
        # 新增条目 range
        <top xmlns='http://www.h3c.com/netconf/config:1.0' web:operation='replace'>
        <OMS>
        <IPv4Objs web:operation='create'>
        <Obj>
        <Group>12.101测试</Group>
        <ID>4294967295</ID>
        <Type>2</Type>
        <StartIPv4Address>3.3.3.1</StartIPv4Address>
        <EndIPv4Address>3.3.3.2</EndIPv4Address>
        </Obj>
        </IPv4Objs>
        </OMS>
        </top>
        :param OMS:
        :return:
        """
        dict_data = {
            'config':
                {
                    '@xmlns:xc': 'urn:ietf:params:xml:ns:netconf:base:1.0',
                    'top':
                        {
                            '@xmlns': 'http://www.h3c.com/netconf/config:1.0',
                            'OMS': OMS
                        }
                }
        }
        res = XmlToDict().dicttoxml(dict=dict_data)
        data_xml = res.split('\n')[1]
        request_info = self.edit_config(xml_data=data_xml)
        # print(request_info)
        if isinstance(request_info, tuple):
            return request_info[0], request_info[1]
        elif isinstance(request_info, bool):
            return request_info, ''
        return False, 'netconf未捕获到预期的返回结果'

    # 新建/修改服务组
    def create_service_groups(self, method="create", name="", description=""):
        server_objs = """
        <config>
        <top xmlns='http://www.h3c.com/netconf/config:1.0' web:operation='create'>
        <OMS>
        <ServObjs web:operation='create'>
        <Obj>
        <Group>test_ser</Group>
        <ID>4294967295</ID>
        <Type>3</Type>
        <StartSrcPort>0</StartSrcPort>
        <EndSrcPort>65535</EndSrcPort>
        <StartDestPort>80</StartDestPort>
        <EndDestPort>80</EndDestPort>
        </Obj>
        <Obj>
        <Group>test_ser</Group>
        <ID>4294967295</ID>
        <Type>4</Type>
        <StartSrcPort>0</StartSrcPort>
        <EndSrcPort>65535</EndSrcPort>
        <StartDestPort>21</StartDestPort>
        <EndDestPort>21</EndDestPort>
        </Obj>
        </ServObjs>
        </OMS>
        </top>
        </config>
        """
        if not name:
            return False
        if description:
            data_xml = """
            <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <top xmlns="http://www.h3c.com/netconf/config:1.0">
            <OMS xmlns="http://www.h3c.com/netconf/config:1.0" xc:operation="{method}">
            <ServGroups>
            <Group>
            <Name>{name}</Name>
            <Description>{description}</Description>
            </Group>
            </ServGroups>
            </OMS>
            </top>
            </config>
            """.format(method=method, name=name, description=description)
            request_info = self.edit_config(xml_data=data_xml)
            if isinstance(request_info, tuple):
                return request_info[0]
            return request_info
        else:
            data_xml = """
            <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
            <top xmlns="http://www.h3c.com/netconf/config:1.0">
            <OMS xmlns="http://www.h3c.com/netconf/config:1.0" xc:operation="{method}">
            <ServGroups>
            <Group>
            <Name>{name}</Name>
            </Group>
            </ServGroups>
            </OMS>
            </top>
            </config>
            """.format(method=method, name=name)
            request_info = self.edit_config(xml_data=data_xml)
            if isinstance(request_info, tuple):
                return request_info[0]
            return request_info

    # 获取OMS对象1
    def get_oms_objs(self, OMS):
        dict_data = {
            'top':
                {
                    '@xmlns': 'http://www.h3c.com/netconf/data:1.0',
                    'OMS': OMS
                }
        }
        res = XmlToDict().dicttoxml(dict=dict_data)
        data_xml = res.split('\n')[1]
        res = self.netconf_get(data_xml)['top']
        if 'IPv4Objs' in res['OMS'].keys():
            if isinstance(res['OMS']['IPv4Objs']['Obj'], dict):
                res['OMS']['IPv4Objs']['Obj'] = [res['OMS']['IPv4Objs']['Obj']]
        if 'ServObjs' in res['OMS'].keys():
            if isinstance(res['OMS']['ServObjs']['Obj'], dict):
                res['OMS']['ServObjs']['Obj'] = [res['OMS']['ServObjs']['Obj']]
        return res['OMS']

    # 获取地址对象1
    def get_ipv4_objs(self,
                      name='', ID='', SubnetIPv4Address='', HostIPv4Address='',
                      IPv4Mask='', StartIPv4Address='', EndIPv4Address=''):
        data_xml = """
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <OMS>
            <IPv4Objs>
            <Obj>
                <Group>{name}</Group>
                <ID>{ID}</ID>
                <Type></Type>
                <SubnetIPv4Address>{SubnetIPv4Address}</SubnetIPv4Address>
                <IPv4Mask>{IPv4Mask}</IPv4Mask>
                <StartIPv4Address>{StartIPv4Address}</StartIPv4Address>
                <EndIPv4Address>{EndIPv4Address}</EndIPv4Address>
                <HostIPv4Address>{HostIPv4Address}</HostIPv4Address>
                <HostName></HostName>
                <NestedGroup></NestedGroup>
            </Obj>
            </IPv4Objs>
        </OMS>
        </top>
        """.format(name=name, ID=ID, SubnetIPv4Address=SubnetIPv4Address, HostIPv4Address=HostIPv4Address,
                   IPv4Mask=IPv4Mask, StartIPv4Address=StartIPv4Address, EndIPv4Address=EndIPv4Address)
        res = self.netconf_get(data_xml)['top']
        # type 0—Nested group.
        # • 1—Subnet.
        # • 2—Range.
        # • 3—Host address.
        # • 4—Host name.
        type_map = {
            "1": "subnet",
            "2": "range",
            # "3": "Host address",
            "3": "ip",
            # "4": "Host name"
            "4": "HostName"
        }
        if res:
            if isinstance(res['OMS']['IPv4Objs']['Obj'], dict):
                res['OMS']['IPv4Objs']['Obj'] = [res['OMS']['IPv4Objs']['Obj']]
            # for i in res['OMS']['IPv4Objs']['Obj']:
            #     i['Type'] = type_map[i['Type']]
            return res['OMS']['IPv4Objs']['Obj']
        else:
            return []

    # 获取地址对象中的OMS详细信息
    def get_ipv4_obj_data(self, name=''):
        data_xml = """
        <top xmlns="http://www.h3c.com/netconf/data:1.0">
        <OMS> 
        <GetIPv4ObjData> 
            <Obj>
                <Group>{name}</Group>
                <ID></ID> 
                <Type></Type> 
                <SubnetIPv4Address></SubnetIPv4Address> 
                <IPv4Mask></IPv4Mask> 
                <IPv4WildcardAddress></IPv4WildcardAddress> 
                <IPv4WildcardMask></IPv4WildcardMask> 
                <StartIPv4Address></StartIPv4Address> 
                <EndIPv4Address></EndIPv4Address> 
                <HostIPv4Address></HostIPv4Address> 
                <HostName></HostName> 
                <NestedGroup></NestedGroup> 
                <User></User> 
                <UserDomain></UserDomain> 
                <UserGroup></UserGroup> 
                <UserGroupDomain></UserGroupDomain> 
                <ExcludeIPv4Address></ExcludeIPv4Address>
            </Obj>
        </GetIPv4ObjData>
        </OMS>
        </top>
        """.format(name=name)
        res = self.netconf_get(data_xml)['top']
        type_map = {
            "1": "subnet",
            "2": "range",
            # "3": "Host address",
            "3": "ip",
            # "4": "Host name"
            "4": "HostName"
        }
        if res:
            return res['OMS']['GetIPv4ObjData']['Obj']
        else:
            return []

    # NAT server
    def get_nat_server(self):
        data_xml = """
        <top xmlns='http://www.h3c.com/netconf/data:1.0'>
        <NAT>
            <ServerOnInterfaces>
                <Interface>
                    <IfIndex/>
                    <ProtocolType/>
                    <GlobalInfo>
                        <GlobalVRF/>
                        <GlobalStartIpv4Address/>
                        <GlobalEndIpv4Address/>
                        <GlobalStartPortNumber/>
                        <GlobalEndPortNumber/>
                        <GlobalIfIndex/>
                    </GlobalInfo>
                    <RuleName/>
                    <ACLNumber/>
                    <Reversible/>
                    <LocalInfo>
                        <LocalVRF/>
                        <LocalStartIpv4Address/>
                        <LocalEndIpv4Address/>
                        <LocalStartPortNumber/>
                        <LocalEndPortNumber/>
                        <LocalSrvGroupNumber/>
                    </LocalInfo>
                    <Disable/>
                    <Description/>
                    <MatchingCount/>
                    <Counting/>
                </Interface>
            </ServerOnInterfaces>
            <DestinationNatOnInterfaces>
                <Interface>
                    <IfIndex/>
                    <ACLNumber/>
                    <RuleName/>
                    <LocalInfo>
                        <LocalVRF/>
                        <LocalIpv4Address/>
                        <LocalPortNumber/>
                    </LocalInfo>
                    <Disable/>
                    <Description/>
                    <MatchingCount/>
                    <Counting/>
                </Interface>
            </DestinationNatOnInterfaces>
            <ServerGroups>
                <ServerGroup>
                    <GroupNumber/>
                </ServerGroup>
            </ServerGroups>
            <ServerGroupMembers>
                <GroupMember>
                    <GroupNumber/>
                    <Ipv4Address/>
                    <PortNumber/>
                    <Weight/>
                    <Sessions/>
                </GroupMember>
            </ServerGroupMembers>
            <ObjServer>
                <Rule>
                    <RuleName/>
                    <IfIndex/>
                    <DstObjGrpList>
                        <DstObjGrp/>
                    </DstObjGrpList>
                    <SrvObjGrpList>
                        <SrvObjGrp/>
                    </SrvObjGrpList>
                    <Action/>
                    <LocalInfo>
                        <LocalIP/>
                        <LocalPort/>
                    </LocalInfo>
                    <Disable/>
                    <Counting/>
                    <Description/>
                    <MatchingCount/>
                </Rule>
            </ObjServer>
        </NAT>
        <Ifmgr>
            <Interfaces>
                <Interface>
                    <IfIndex/>
                    <AbbreviatedName/>
                    <Name/>
                    <ifTypeExt/>
                    <Description/>
                    <PortLayer>2</PortLayer>
                </Interface>
            </Interfaces>
            <InterfaceCapabilities>
                <Interface>
                    <IfIndex/>
                    <Configurable>true</Configurable>
                </Interface>
            </InterfaceCapabilities>
        </Ifmgr>
        <L3vpn>
            <L3vpnVRF>
                <VRF>
                    <VRF/>
                    <VrfIndex/>
                    <Description/>
                    <AssociatedInterfaceCount/>
                </VRF>
            </L3vpnVRF>
        </L3vpn>
        <ACL>
            <NamedGroups>
                <Group>
                    <GroupIndex/>
                    <GroupType>1</GroupType>
                    <GroupCategory/>
                    <MatchOrder/>
                    <Step/>
                    <Description/>
                    <RuleNum/>
                </Group>
            </NamedGroups>
        </ACL>
        <OMS>
            <SysServGroups>
                <Group>
                    <Name/>
                    <Description/>
                    <ObjNum/>
                    <InUse/>
                </Group>
            </SysServGroups>
        </OMS>
    </top>
        """
        res = self.netconf_get(data_xml)['top']
        if res:
            return res['NAT']['ServerOnInterfaces']['Interface']
        return []

    # nat group
    def get_nat_addr_groups(self):
        data_xml = """
        <top xmlns='http://www.h3c.com/netconf/data:1.0'>
        <NAT>
            <AddrGroups>
                <AddrGroup>
                    <GroupNumber></GroupNumber>
                    <GroupName/>
                    <PortBlockSize/>
                    <ExtendedBlockNumber/>
                    <StartPort/><EndPort/>
                    <HealthCheckStatus/>
                </AddrGroup>
            </AddrGroups>
            <AddrGroupMembers>
                <GroupMember>
                    <GroupNumber></GroupNumber>
                    <StartIpv4Address/>
                    <EndIpv4Address/>
                </GroupMember>
            </AddrGroupMembers>
            <AddrGroupHealthCheck>
                <GroupHealthCheck>
                    <GroupNumber></GroupNumber>
                    <ProbeName/>
                </GroupHealthCheck>
            </AddrGroupHealthCheck>
        </NAT>
        </top>
        """
        req = self.netconf_get(data_xml)['top']
        if req:
            # addr_groups = req['NAT']['AddrGroups'] or []
            # addr_groups_members = req['NAT']['AddrGroupMembers'] or []
            # addr_groups_health_check = req['NAT'].get('AddrGroupHealthCheck', '')
            return req['NAT']
        return []

    # SNAT
    def get_source_nat(self):
        data_xml = """
        <top xmlns='http://www.h3c.com/netconf/data:1.0'>
        <NAT>
        <PolicyRuleMembers>
        <Rule>
            <RuleName/>
            <Description/>
            <OutboundInterface/>
            <SrcObjGrpList>
                <SrcIpObjGroup/>
            </SrcObjGrpList>
            <DstObjGrpList>
                <DstIpObjGroup/>
            </DstObjGrpList>
            <SrvObjGrpList>
                <ServiceObjGroup/>
            </SrvObjGrpList>
            <Action/>
            <AddrGroupNumber/>
            <AddrGroupName/>
            <Reversible/>
            <PortPreserved/>
            <Disable/>
            <Counting/>
            <MatchingCount/>
        </Rule>
        </PolicyRuleMembers>
        </NAT>
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
        action_map = {
            '0': 'NO-PAT',
            '1': 'PAT',
            '2': 'EasyIp',
            '3': 'NO NAT'
        }
        req = self.netconf_get(data_xml)['top']
        if req:
            if 'NAT' not in req.keys():
                return []
            ifmgr_list = req['Ifmgr']['Interfaces']['Interface']
            nat_res = req['NAT']['PolicyRuleMembers']['Rule']
            # 两个表格合并，将name加入arp表格
            if isinstance(nat_res, dict):
                nat_res = [nat_res]
            for a in nat_res:
                a['Action'] = action_map[a['Action']]
                for b in ifmgr_list:
                    if a['OutboundInterface'] == b['IfIndex']:
                        a.update(OutboundInterfaceName=b['Name'])
            return nat_res
        return []

    # 获取全局NAT
    def get_global_nat_policy(self, mode='DNAT', name=''):
        """
        10.254.12.100 不支持 <TransSrcIP/>  (在Rule下)
        :param mode:
        :return:
        """
        # 默认获取DNAT
        if mode == 'DNAT':
            TransMode = '1'  # DNAT
        else:
            TransMode = '0'  # SNAT
        if name != '':
            data_xml = """
            <top xmlns='http://www.h3c.com/netconf/data:1.0'>
            <NAT>
            <GlobalPolicyRuleSrcObj>
            <Rule><RuleName>{RuleName}</RuleName>
            <SrcAddrType/>
            <SrcObjGrpList><SrcIpObj/>
            </SrcObjGrpList>
            <SrcIPList>
            <SrcIP/>
            </SrcIPList>
            </Rule>
            </GlobalPolicyRuleSrcObj>
            <GlobalPolicyRuleDstObj>
            <Rule>
            <RuleName>{RuleName}</RuleName>
            <DstAddrType/>
            <DstObjGrpList>
            <DstIpObj/>
            </DstObjGrpList>
            <DstIPList>
            <DstIP/>
            </DstIPList>
            </Rule>
            </GlobalPolicyRuleDstObj>
            <GlobalPolicyRuleSrvObj>
            <Rule>
            <RuleName>{RuleName}</RuleName>
            <SrvAddrType/>
            <SrvObjGrpList>
            <SrvObj/>
            </SrvObjGrpList>
            </Rule>
            </GlobalPolicyRuleSrvObj>
            </NAT>
            </top>
            """.format(RuleName=name)
            res = self.netconf_get(data_xml)
        else:
            data_xml = """
            <top xmlns='http://www.h3c.com/netconf/data:1.0'>
            <NAT>
            <GlobalPolicyRuleMembers>
            <Rule>
            <RuleName>{RuleName}</RuleName>
            <Description/>
            <TransMode>{TransMode}</TransMode>
            <SrcObjGrpList>
            <SrcIpObjGroup/>
            </SrcObjGrpList>
            <SrcIPList>
            <SrcIP/>
            </SrcIPList>
            <DstObjGrpList>
            <DstIpObjGroup/>
            </DstObjGrpList>
            <DstIPList>
            <DstIP/>
            </DstIPList>
            <SrvObjGrpList>
            <ServiceObjGroup/>
            </SrvObjGrpList>
            <SrcZoneList>
            <SrcZone/>
            </SrcZoneList>
            <DstZoneList>
            <DstZone/>
            </DstZoneList>
            <TransSrcType/>
            <TransSrcAddrType/>
            <TransAddrGroupNumber/>
            <TransAddrGroupName/>
            <TransReversible/>
            <TransPortPreserved/>
            <TransDstType/>
            <TransDstIP/>
            <TransDstPort/>
            <Disable/>
            <Counting/>
            <MatchingCount/>
            <RuleTotalCount/>
            </Rule>
            </GlobalPolicyRuleMembers>
            </NAT>
            </top>
            """.format(RuleName=name, TransMode=TransMode)
            res = self.netconf_get_bulk(data_xml)
        if res:
            # print(res)
            if 'NAT' in res['top'].keys():
                trans_mode_map = {
                    '0': 'SNAT',
                    '1': 'DNAT',
                }
                if name != '':
                    # print(res)
                    results = res['top']['NAT']
                else:
                    results = res['top']['NAT']['GlobalPolicyRuleMembers']['Rule']
                if isinstance(results, dict):
                    return [results]
                return results
        return []

    # 配置DNAT
    def config_nat_server(self, NAT: list, method='create'):
        """
           'config':
                {
                    '@xmlns:xc': 'urn:ietf:params:xml:ns:netconf:base:1.0',
                    'top':
                        {
                            '@xmlns': 'http://www.h3c.com/netconf/config:1.0',
                            'NAT': [
                                {'GlobalPolicyRules': {'Rule': {'RuleName': 'test'}}},
                                {'GlobalPolicyRuleMembers':
                                     {
                                         'Rule': {
                                             'RuleName': 'test',
                                             'Description': 'test_des',
                                             'TransMode': '1',
                                             'SrcZoneList': {'SrcZone': 'Untrust'},
                                             'TransDstType': '0',
                                             'TransDstIP': '10.100.160.222',
                                             'Disable': 'false',
                                             'Counting': 'true'
                                         }
                                     }
                                },
                                {'GlobalPolicyRuleSrcObj': {'Rule': {'RuleName': 'test', 'SrcAddrType': '1'}}},
                                {'GlobalPolicyRuleDstObj':
                                     {
                                         'Rule':
                                             {
                                                 'RuleName': 'test',
                                                 'DstAddrType': '1',
                                                 'DstIPList': {'DstIP': ['114.118.64.34', '114.118.64.35']}
                                             }
                                     }
                                },
                                {'GlobalPolicyRuleSrvObj':
                                     {
                                         'Rule':
                                             {
                                                 'RuleName': 'test',
                                                 'SrvAddrType': '0',
                                                 'SrvObjGrpList': {'SrvObj': 'http'}
                                             }
                                     }
                                }
                            ]
                        }
                }
        }
        :return:
        """
        dict_data = {
            'config':
                {
                    '@xmlns:xc': 'urn:ietf:params:xml:ns:netconf:base:1.0',
                    'top':
                        {
                            '@xmlns': 'http://www.h3c.com/netconf/config:1.0',
                            '@xc:operation': method if method else 'create',
                            'NAT': NAT
                        }
                }
        }
        res = XmlToDict().dicttoxml(dict=dict_data)
        data_xml = res.split('\n')[1]
        request_info = self.edit_config(xml_data=data_xml)
        # print(request_info)
        if isinstance(request_info, tuple):
            return request_info[0]
        return request_info

    # DELETE NAT
    def del_nat_server(self, RuleName):
        dict_data = {
            'top': {
                '@xmlns': 'http://www.h3c.com/netconf/config:1.0',
                '@xc:operation': 'remove',
                'NAT': {
                    'GlobalPolicyRules': {
                        'Rule': [{'RuleName': RuleName}]
                    }
                }
            }
        }
        res = XmlToDict().dicttoxml(dict=dict_data)
        data_xml = res.split('\n')[1]
        request_info = self.edit_config(xml_data=data_xml)
        # print(request_info)
        if isinstance(request_info, tuple):
            return request_info[0]
        return request_info

    # top通用配置
    def config_top(self, top):
        dict_data = {
            'config':
                {
                    '@xmlns:xc': 'urn:ietf:params:xml:ns:netconf:base:1.0',
                    'top': top
                }
        }
        res = XmlToDict().dicttoxml(dict=dict_data)
        data_xml = res.split('\n')[1]
        print(data_xml)
        request_info = self.edit_config(xml_data=data_xml)
        # print(request_info)
        if isinstance(request_info, tuple):
            return request_info[0], request_info[1]
        elif isinstance(request_info, bool):
            return request_info, ''
        return False, 'netconf未捕获到预期的返回结果'

    # action data
    def action_top(self, top):
        """
        {'top': {
        '@xmlns': 'http://www.h3c.com/netconf/action:1.0',
        'SecurityPolicies':
        {'MoveIPv4Rule': {'Rule': {'ID': '{id}', 'MoveType': '{move_type}'}}}}}
        :param dict_data:
        :return:
        """
        dict_data = {'top': top}
        res = XmlToDict().dicttoxml(dict=dict_data)
        data_xml = res.split('\n')[1]
        request_info = self._action(data=data_xml)
        # print(request_info)
        if isinstance(request_info, tuple):
            return request_info[0], request_info[1]
        elif isinstance(request_info, bool):
            return request_info, ''
        return False, 'netconf未捕获到预期的返回结果'

    def config_snat_test(self):
        data_xml = """
        <config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0">
        <top xmlns='http://www.h3c.com/netconf/config:1.0' xc:operation='create'>
        <NAT>
            <PolicyRules xc:operation='create'>
                <Rule>
                    <RuleName>test123</RuleName>
                </Rule>
            </PolicyRules>
        </NAT>
        <NAT>
            <PolicyRuleMembers xc:operation='create'>
                <Rule>
                    <RuleName>test123</RuleName>
                    <OutboundInterface>159</OutboundInterface>
                    <Action>1</Action>
                    <AddrGroupNumber>10</AddrGroupNumber>
                    <Reversible>false</Reversible>
                    <PortPreserved>true</PortPreserved>
                    <Disable>true</Disable>
                </Rule>
            </PolicyRuleMembers>
        </NAT>
        <NAT>
            <PolicyRuleMemberSrcObj xc:operation='merge'>
                <Rule>
                    <RuleName>test123</RuleName>
                    <SrcObjGrpList>
                        <SrcIpObj>test1</SrcIpObj>
                    </SrcObjGrpList>
                </Rule>
            </PolicyRuleMemberSrcObj>
        </NAT>
    </top>
    </config>
        """
        request_info = self.edit_config(xml_data=data_xml)
        # print(request_info)
        if isinstance(request_info, tuple):
            return request_info[0], request_info[1]
        elif isinstance(request_info, bool):
            return request_info, ''
        return False, 'netconf未捕获到预期的返回结果'

    def config_sec_policy_test(self):
        IPv4Rules = {
            'IPv4Rules':
                {
                    'Rule': {
                        'ID': 65535,
                        'RuleName': 'test123456',
                        'Action': 2,
                        'Enable': False,
                        'Log': False,
                        'Counting': False,
                        'SessAgingTimeSw': False,
                        'SessPersistAgingTimeSw': False,
                    }
                }
        }
        config_data = [

        ]
        data = [{
            '@xmlns': 'http://www.h3c.com/netconf/config:1.0',
            '@xc:operation': 'create',
            'SecurityPolicies': IPv4Rules
        }]
        return self.config_top(top=data)


if __name__ == '__main__':
    pass