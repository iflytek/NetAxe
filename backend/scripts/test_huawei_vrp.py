from napalm import get_network_driver
driver = get_network_driver('huawei_vrp')
device = driver(hostname='10.254.1.1', username='admin', password='aaaaaaaaaaa')
device.open()

# get_facts = device.get_facts()
# print(get_facts)
#
# is_alive = device.is_alive()
# print(is_alive)
#
# arp = device.get_arp_table()
# print(arp)
get_lldp_neighbors = device.get_lldp_neighbors()
print(get_lldp_neighbors)
send_command = device.cli(['dis ver', 'dis cu'])
print(send_command)
device.close()