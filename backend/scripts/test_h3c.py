from napalm import get_network_driver

driver = get_network_driver("h3c_comware")
driver = driver("10.254.1.1", "aaaaaaaaaaaa", "aaaaaaaaaaa",)
driver.open()
# you can use any options that supported by netmiko.send_command
# ret = driver.send_command("display clock", use_textfsm=True)
# print(ret)
ret = driver.is_alive()
print(ret)
get_facts = driver.get_facts()
print(get_facts)
driver.close()