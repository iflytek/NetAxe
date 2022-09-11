from typing import Any, Dict, Type, List

from nornir.core.inventory import (
    Inventory,
    Groups,
    Host,
    Hosts,
    Defaults,
    ConnectionOptions,
    HostOrGroup,
)
from nornir.core.plugins.inventory import InventoryPlugin


def _get_connection_options(data: Dict[str, Any]) -> Dict[str, ConnectionOptions]:
    cp = {}
    for cn, c in data.items():
        cp[cn] = ConnectionOptions(
            hostname=c.get("hostname"),
            port=c.get("port"),
            username=c.get("username"),
            password=c.get("password"),
            platform=c.get("platform"),
            extras=c.get("extras"),
        )
    return cp


def _get_netops_options(data: Dict[str, Any], platform: str) -> Dict[str, ConnectionOptions]:
    scrapli_platform = ['hp_comware', 'huawei_vrp']
    # extra_opts = {}
    netmiko_options = {
        'netmiko': {
            'extras': {
                'conn_timeout': 20,
            }
        }
    }
    if platform in scrapli_platform:
        scrapli_option = {
            'scrapli': {
                'platform': platform,
                'extras': {
                    'ssh_config_file': True,
                    'auth_strict_key': False
                }
            }
        }
        return _get_connection_options(scrapli_option)
    else:
        return _get_connection_options(netmiko_options)


def _get_defaults(data: Dict[str, Any]) -> Defaults:
    return Defaults(
        hostname=data.get("hostname"),
        port=data.get("port"),
        username=data.get("username"),
        password=data.get("password"),
        platform=data.get("platform"),
        data=data.get("data"),
        connection_options=_get_connection_options(data.get("connection_options", {})),
    )


def _get_inventory_element(
        typ: Type[HostOrGroup], data: Dict[str, Any], name: str, defaults: Defaults
) -> HostOrGroup:
    return typ(
        # name="{}({})".format(name, data['hostname']),
        name=data['hostname'],
        hostname=data['hostname'],
        port=data['port'],
        username=data.get("username"),
        password=data.get("password"),
        platform=data.get("platform"),
        groups=data.get("groups"),
        data=data.get("data"),
        # groups=data.get(
        #     "groups"
        # ),  # this is a hack, we will convert it later to the correct type
        defaults=defaults,
        connection_options=_get_netops_options(data.get("connection_options", {}), data.get("platform", '')),
    )


class CMDBInventory(InventoryPlugin):
    def __init__(self, devices: List[dict], *args: Any, **kwargs: Any) -> None:
        """
        根据devices的字典列表加载所有网络主机
        Args:

          devices: 网络设备信息字典的列表，形如 [
                    {'ip': '192.168.1.1',
                    'username': 'admin',
                    'password': '1!',
                    'port': 8181,
                    platform': 'cisco_nxos',
                    'vendor':'cisco',
                    'region': '北京XX园区'
                    }
            ]
        """
        # 将host_info中的字段的数据保留，其他的都放到整形后的dict数据的data字段中去。
        super().__init__(*args, **kwargs)
        key_mapping = dict(
            manage_ip='hostname',
            username='username',
            password='password',
            port='port',
            vendor__alias='platform',
        )
        vendor_mapping = dict(
            H3C='hp_comware',
            Huawei='huawei',
            Mellanox='mellanox',
            Ruijie='ruijie_os',
            centec='cisco_ios',
            inspur='cisco_ios',
            Hillstone='ruijie_os',
            Maipu='ruijie_os'
        )
        # 对数据进行整形，将整形的数据放到reshape_devices中去。
        reshape_devices = []
        for device in devices:
            # 初始化一个整形后的数据
            reshape_device = {
                'data': {}
            }
            for k, v in device.items():
                # 数据在mapping.values中，则保留，对platform做一下处理，netmiko中是device_type，所以兼容了一下这个字段，将其转为platform
                if k in key_mapping.keys():
                    if k == 'vendor__alias':
                        reshape_device['platform'] = vendor_mapping[v]
                        reshape_device['data'][k] = v  # 我需要取vendor__alias 用于后期的判断
                    else:
                        reshape_device[key_mapping[k]] = v
                # 数据不在mapping.values中，则放到data中去
                else:
                    reshape_device['data'][k] = v
            if 'telnet' in device['protocol']:
                reshape_device['platform'] += '_telnet'
            reshape_devices.append(reshape_device)
        # 完成初始化，self.devices后续构建inventory对象
        self.devices = reshape_devices

    def load(self) -> Inventory:
        # 初始化三个对象，分别是Hosts、Groups和Defaults的实例
        hosts = Hosts()
        groups = Groups()
        defaults = Defaults()
        # 我们本例只使用了hosts，大家如果真有需要，按需去添加其他两个对象的属性
        # 从原生的inventory我们实际能看出，inventory的hosts是一个类似dict的对象，所以我们通过dict的方式构建或添加设备。
        # 所以我们将原有的列表进行了一层转化，用ip作为每个host的name，在这段就是用ip作为字典的key值，value是之前构建的字典
        hosts_dict = {i['data']['name']: i for i in self.devices}
        # hosts_dict = {i['hostname']: i for i in self.devices}
        # self.devices
        # {'data': {'id': 1134, 'serial_num': '210235A2BBH186000836', 'name': 'B3.PO.YJJH.LF.X01M1', 'vendor__name': '华三', 'soft_version': None, 'category__name': '交换机', 'framework__name': '三层', 'model__name': 'S6800-54QF', 'patch_version': None, 'status': 0, 'idc__name': '合肥B3', 'plan_id': None, 'ha_status': 0, 'chassis': 0, 'slot': 1, 'bind_ip__ipaddr': None, 'netconf_username': 'netops@network.local', 'netconf_password': 'BfLgQVs#5Y27f@SZ', 'netconf_port': 830, 'protocol': ['netconf', 'ssh']}, 'hostname': '10.254.23.156', 'platform': 'hp_comware', 'username': 'netops@network.local', 'password': 'BfLgQVs#5Y27f@SZ', 'port': 22}
        # for i in self.devices:
        #     print(i)
        # print(hosts_dict)
        # 以上这行代码等于以下三行代码
        # hosts_dict = {}
        # for i in self.deivces:
        #     hosts_dict[i['ip']] = i
        # 我们准备好了添加网络设备的字典，然后在hosts中添加每个
        for name, host_dict in hosts_dict.items():
            print(Host, host_dict, name, defaults)
            hosts[name] = _get_inventory_element(Host, host_dict, name, defaults)
        return Inventory(hosts=hosts, groups=groups, defaults=defaults)
