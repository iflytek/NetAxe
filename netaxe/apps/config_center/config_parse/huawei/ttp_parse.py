# -*- coding: utf-8 -*-


ttp_template = """
<macro>
def check(data):
    ##print(data) ## 这里可以直接打印用于方法调试
    if 'results' in data[0].keys():
        return data[0]['results']
    return data
</macro>
<group name = "results">
<group name = "ssh">
 ssh server enable {{ enable | set(True) }}
 ssh server acl {{ acl | to_int }}
</group>
<group name = "acl">
acl basic {{ name | _start_ }}
<group name = "rule.{{ rule_id }}">
 rule {{ rule_id }} {{ action }} vpn-instance {{ vpn-instance }} source {{ source | re("\d+.\d+.\d+.\d+\s\d+.\d+.\d+.\d+")}}
</group>
</group>
<group name = "ntp-service">
 ntp-service enable {{ enable | set(True) }}
 ntp-service unicast-server {{ server }} vpn-instance {{ vpn-instance }} source {{ source-interface}}
</group>
<group name = "system">
 stp global enable {{ stp_global_enable | set(True) }}
</group>
<group name = "info-center">
 info-center loghost source {{ source_interface }}
<group name = "loghost.{{ loghost }}">
 info-center loghost vpn-instance {{ vpn-instance }} {{ loghost }}
</group>
</group>
<group name = "system">
 sysname {{ name }}
 clock timezone {{ clock_timezone | re(".*")}}
 clock protocol {{ clock_protocol }}
</group>
<group name = "hwtacacs">
{{ ignore("\s*") }}hwtacacs server template {{ template | re(".*") }}
{{ ignore("\s*") }}hwtacacs server authentication {{ primary | re("\d+.\d+.\d+.\d+") }} vpn-instance {{ vpn-instance | re("\S+") }}
{{ ignore("\s*") }}hwtacacs server authentication {{ secondary | re("\d+.\d+.\d+.\d+") }} vpn-instance {{ vpn-instance | re("\S+") }} secondary
{{ ignore("\s*") }}hwtacacs server authorization {{ primary | re("\d+.\d+.\d+.\d+") }} vpn-instance {{ vpn-instance | re("\S+") }}
{{ ignore("\s*") }}hwtacacs server authorization {{ secondary | re("\d+.\d+.\d+.\d+") }} vpn-instance {{ vpn-instance | re("\S+") }} secondary
{{ ignore("\s*") }}hwtacacs server accounting {{ primary | re("\d+.\d+.\d+.\d+") }} vpn-instance {{ vpn-instance | re("\S+") }}
{{ ignore("\s*") }}hwtacacs server accounting {{ secondary | re("\d+.\d+.\d+.\d+") }} vpn-instance {{ vpn-instance | re("\S+") }} secondary
{{ ignore("\s*") }}hwtacacs server shared-key cipher {{ key | re(".*") }}
{{ ignore("\s*") }}hwtacacs server user-name {{ user-name | re(".*") }}
</group>
<group name = "interfaces.{{ interface }}">
## 接口配置解析
interface {{ interface | re(".*") | _start_ }}
 description {{ description }}
 port link-type {{ link-type | re("\S+") }}
 port trunk permit vlan {{ permit-vlan | re(".*") }}
 undo port trunk permit vlan {{ no-permit-vlan | re("\d+") }}
 port access vlan {{ vlan-id | re("\d+") | to_int }}
 stp edged-port {{ edged-port | set(True) }}
 port link-aggregation group {{ aggregation-group | re("\d+") | to_int }}
 link-aggregation mode  {{ aggregation-mode | re("\S+") }}
 ip address {{ ip | re("\d+\d+\d+\d+") }} {{ mask | re("\d+\d+\d+\d+") }}
 ip binding vpn-instance {{ vpn-instance | re("\S+") }}
 shutdown {{ enabled | set(False) }}
## {{ ignore("\s*") }}interface {{ name | re(".*") | _start_ }}
## {{ interface | lstrip() | to_list | _line_ | joinmatches }}
## {{ interface | lstrip() | _line_ }}
# {{ _end_ }}
</group>
<group name = "snmp">
## snmp配置解析
 snmp-agent {{ _start_ }}
 snmp-agent community read cipher {{ read-cipher }} acl {{ acl-number | re("\d+") | to_int}}
 snmp-agent community write cipher {{ read-cipher }} acl {{ acl-number | re("\d+") | to_int}}
 snmp-agent sys-info contact {{ contact }}
 snmp-agent sys-info location {{ location }}
 snmp-agent sys-info version {{ version | re("\S+(\s\S+)?") }}
 snmp-agent target-host trap address udp-domain {{ trap-host | re("\d+\d+\d+\d+") }} vpn-instance {{ trap-vpn-instance }} params securityname {{ trap-key }} {{ trap-version}}
 snmp-agent trap enable {{ trap_enable }}
##{{ snmp-agent | lstrip() | _line_ }}
# {{ _end_ }}
</group>
</group>
<output macro="check"/>
"""
