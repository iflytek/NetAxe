# -*- coding: utf-8 -*-
import json

import yaml
from ttp import ttp

from netaxe.settings import BASE_DIR

CONFIG_PATH = BASE_DIR + '/media/device_config/current-configuration/'

ttp_template = """
<macro>
def check(data):
    ##print(data) ## 这里可以直接打印用于方法调试
    if 'results' in data[0].keys():
        return data[0]['results']
    return data
</macro>
<group name = "results">
<group name = "system">
 sysname {{ name }}
 clock timezone {{ clock_timezone | re(".*")}}
 clock protocol {{ clock_protocol }}
 ip unreachables enable {{ unreachables | set(True) }}
 ip ttl-expires enable {{ ttl-expires | set(True) }}
 vxlan tunnel mac-learning disable{{ vxlan_mac_learing | set(True) }}
 <group name = "stp">
 stp global enable{{ global_enable | set(True) }}
 </group>
 <group name = "netconf">
 netconf ssh server enable{{ enable | set(True) }}
 </group>
</group>
<group name = "vlan.{{ name }}">
vlan {{ name }}
</group>
<group name = "vsi.{{ name }}">
vsi {{ name }}
 description {{description}}
 gateway vsi-interface {{gateway}}
 vxlan {{ vxlan }}
 evpn encapsulation {{ evpn }}
  route-distinguisher {{ RD }}
  vpn-target {{ RT | re("\S+(\s\S+)?") }} {{ target | _start_ }}
# {{ _end_ }}
</group>
<group name = "vrf.{{ name }}">
ip vpn-instance {{ name }}
## 路由标识
 route-distinguisher {{ RD }}
 <group name = "address-family.{{ name }}">
 address-family {{ name }}
  vpn-target {{ RT }} {{ target | _start_ }}
 # {{ _end_ }}
 </group>
</group>
<group name = "ssh">
 ssh server enable {{ enable | set(True) }}
 ssh server acl {{ acl | to_int }}
</group>
<group name = "ACL">
acl basic {{ name | _start_ }}
acl number {{ acl_number }} name {{ name | _start_}}
 <group name = "rule">
 description {{ description }}
 rule {{ rule_id }} {{ action }} vpn-instance {{ vrf }} source {{ source | re("\d+.\d+.\d+.\d+\s\d+.\d+.\d+.\d+")}}
 </group>
</group>
<group name = "ntp_service">
 ntp-service enable {{ enable | set(True) }}
 <group name = "server">
 ntp-service unicast-server {{ ip }} vpn-instance {{ vrf }}
 ntp-service unicast-server {{ ip }} vpn-instance {{ vrf }} source {{ source-interface }}
 </group>
</group>
<group name = "info_center">
 info-center loghost source {{ source_interface }}
 <group name = "loghost.{{ loghost }}">
 info-center loghost vpn-instance {{ vrf }} {{ loghost }}
 </group>
</group>
<group name = "interfaces.{{ interface }}">
## 接口配置解析
interface {{ interface | re(".*") | _start_ }}
 <group name = "drni">
 port drni group {{ group | _start_ }}
  <group name = "service-instance">
 service-instance {{ instance }}
  encapsulation s-vid {{s-vid}}
  xconnect vsi {{vsi}}
 # {{ _end_ }}
  </group>
 </group>
 description {{ description }}
 port link-type {{ link-type | re("\S+") }}
 port trunk permit vlan {{ permit-vlan | re(".*") }}
 undo port trunk permit vlan {{ no-permit-vlan | re("\d+") }}
 port access vlan {{ vlan-id | re("\d+") | to_int }}
 stp edged-port {{ edged-port | set(True) }}
 port link-aggregation group {{ aggregation_group | re("\d+") | to_int }}
 link-aggregation mode  {{ aggregation_mode | re("\S+") }}
 ip address {{ ip | re("\d+.\d+.\d+.\d+") }} {{ mask | re("\d+.\d+.\d+.\d+") }}
 ip address dhcp-alloc {{ dhcp | set(True)}}
 port link-mode {{ mode }}
 mac-address {{ mac-address }}
 ip binding vpn-instance {{ vrf | re("\S+") }}
 distributed-gateway local {{ distributed-gateway_local | set(True) }}
 ip-prefix-route generate disable {{ disable_ip-prefix-route_generate | set(True) }}
 shutdown {{ enabled | set(False) }}
## {{ ignore("\s*") }}interface {{ name | re(".*") | _start_ }}
## {{ interface | lstrip() | to_list | _line_ | joinmatches }}
## {{ interface | lstrip() | _line_ }}
# {{ _end_ }}
</group>
<group name = "underlay">
 <group name = "route">
  <group name = "bgp.{{ as_number }}">
bgp {{ as_number }}
 graceful-restart {{ GR | set(True)}}
 router-id {{ router-id }}
   <group name = "peer.{{ peer }}">
 peer {{ peer }} as-number {{ peer_as_number }}
 peer {{ peer }} description {{ description }}
 peer {{ peer }} bfd {{ bfd }}
   </group>
   <group name = "address_family">
 address-family {{ protocol }} {{ type }}
  balance {{ balance }}
    <group name = "network">
  network {{ ip }} {{ mask }}
    </group>
    <group name = "peer">
  peer {{ peer }} {{ enable|re("enable")|let(True) }}
  peer {{ peer }} {{ enable|re("disable")|let(False) }}
    </group>
   </group>
  </group>
 </group>
</group>
<group name = "overlay">
 <group name = "route">
  <group name = "bgp.{{ as_number }}">
bgp {{ as_number }} {{ instance }} {{ name }}
 router-id {{ router-id }}
   <group name = "peer.{{ peer }}">
 peer {{ peer }} as-number {{ peer_as_number }}
 peer {{ peer }} connect-interface {{ interface }}
 peer {{ peer }} ebgp-max-hop {{ ebgp_max_hop }}
 peer {{ peer }} description {{ description }}
 peer {{ peer }} bfd {{ bfd }}
   </group>
   <group name = "address-family">
 address-family {{ protocol }} {{ type }}
  balance {{ balance }}
  vpn-route cross multipath {{ vpn-route_cross_multipath | set(True)}}
    <group name = "network">
  network {{ ip }} {{ mask }}
    </group>
    <group name = "peer">
  peer {{ peer }} {{ enable|re("enable")|let(True) }}
  peer {{ peer }} {{ enable|re("disable")|let(False) }}
    </group>
  <group name = "vrf.{{ name }}">
 ip vpn-instance {{ name }}
   <group name = "address-family">
  address-family {{ protocol }} {{ type }}
   balance {{ balance }}
   vpn-route cross multipath {{ vpn_route_cross_multipath | set(True)}}
   </group>
  </group>
   </group>
  </group>
 </group>
</group>
<group name = "VRF.{{ name }}">
ip vpn-instance {{ name }}
 route-distinguisher {{ RD }}
</group>
<group name = "LLDP">
 lldp global {{ enable|re("enable")|let(True) }}
 lldp global tlv-enable basic-tlv management-address-tlv interface {{ management_interface }}
</group>
<group name = "DRNI">
 drni auto-recovery reload-delay {{reload_delay}}
 drni role priority {{ priority }}
 drni system-mac {{ system_mac }}
 drni system-number {{ system_number }}
 drni keepalive ip destination {{keepalive_dst}} source {{keepalive_src}} vpn-instance {{vrf}}
 <group name = "mad_exclude_interface">
 drni mad exclude interface {{ interface | _start_ }}
 </group>
</group>
<group name = "snmp">
## snmp配置解析
 snmp-agent {{ _start_ }}
 snmp-agent community read cipher {{ read-cipher }} acl {{ acl-number | re("\d+") | to_int}}
 snmp-agent community write cipher {{ read-cipher }} acl {{ acl-number | re("\d+") | to_int}}
 snmp-agent sys-info contact {{ contact }}
 snmp-agent sys-info location {{ location }}
 snmp-agent sys-info version {{ version | re("\S+(\s\S+)?") }}
 snmp-agent target-host trap address udp-domain {{ trap-host | re("\d+\d+\d+\d+") }} vpn-instance {{ trap-vrf }} params securityname {{ trap-key }} {{ trap-version}}
 snmp-agent trap enable {{ trap_enable }}
##{{ snmp-agent | lstrip() | _line_ }}
# {{ _end_ }}
</group>
</group>
<output macro="check"/>
"""


class H3cParse:
    def __init__(self, host, _dir):
        self._dir = _dir
        self.host = host
        self.yaml_dict = {self.host: {}}
        self.parse_res = {}
        self.ttp_template = ttp_template

    def parse(self, data_to_parse):
        parser = ttp(data=data_to_parse, template=self.ttp_template)
        parser.parse()
        results = parser.result(format='json')[0]
        self.parse_res = json.loads(results)
        # print(self.parse_res)
        if isinstance(self.parse_res, dict):
            for k in self.parse_res.keys():
                self.yaml_dict[self.host][k] = self.parse_res[k]

    def snmp(self, snmp):
        self.yaml_dict[self.host]['snmp'] = snmp

    # def interface(self, interfaces):
    #     self.yaml_dict[self.host]['interfaces'] = interfaces
    #     for interface in interfaces:
    #         if 'interface' not in interface.keys():
    #             continue
    #         # 接口FortyGigE1/0/49 因为有斜杠，系统会误判为路径，需要替换
    #         sub_path = "{}{}/{}.txt".format(
    #             CONFIG_PATH, self._dir, interface['name'].replace('/', '_'))
    #         with open(sub_path, 'w', encoding='utf8') as f:
    #             f.write(interface['interface'])
    #         # {'interface': 'port link-mode bridge', 'name': 'Ten-GigabitEthernet1/0/45'}

    def get_yaml(self):
        # 生成json
        # sub_path = "{}{}/{}-{}.json".format(
        #     CONFIG_PATH, self._dir, 'hp_comware', self.host)
        # # print(sub_path)
        # with open(sub_path, 'w', encoding='utf8') as f:
        #     f.write(json.dumps(self.yaml_dict))
        # print(self.yaml_dict)
        yaml_res = yaml.dump(self.yaml_dict)
        # print(yaml_res)
        sub_path = "{}{}/{}-{}.yaml".format(
            CONFIG_PATH, self._dir, 'hp_comware', self.host)
        # print(sub_path)
        with open(sub_path, 'w', encoding='utf8') as f:
            f.write(yaml_res)
        return

    def show_yaml(self):
        yaml_res = yaml.dump(self.yaml_dict)
        print(yaml_res)
        return yaml_res


if __name__ == "__main__":
    pass