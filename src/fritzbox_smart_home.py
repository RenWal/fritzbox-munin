#!/usr/bin/env python3
"""
  fritzbox_smart_home - A munin plugin for Linux to monitor AVM Fritzbox SmartHome values

  @see https://avm.de/fileadmin/user_upload/Global/Service/Schnittstellen/x_homeauto.pdf
"""

from fritzconnection.lib.fritzhomeauto import FritzHomeAutomation
from fritzbox_config import FritzboxConfig
from fritzbox_munin_plugin_interface import MuninPluginInterface,main_handler,print_debug


class FritzboxSmartHome(MuninPluginInterface):
  __connection = None

  def __init__(self, fritzbox_connection: FritzHomeAutomation):
    self.__connection = fritzbox_connection

  def print_stats(self):
    smart_home_data = self.__connection.get_device_information_list()
    print_debug('got result from fritzbox:')
    print_debug(smart_home_data)

    print("multigraph temperatures")
    for data in smart_home_data:
      if 'NewTemperatureIsValid' in data and data['NewTemperatureIsValid'] == 'VALID':
        print(f"t{data['NewDeviceId']}.value {float(data['NewTemperatureCelsius']) / 10}")
    print("multigraph energy")
    for data in smart_home_data:
      if 'NewMultimeterIsValid' in data and  data['NewMultimeterIsValid'] == 'VALID':
        print(f"e{data['NewDeviceId']}.value {data['NewMultimeterEnergy']}")
    print("multigraph powers")
    for data in smart_home_data:
      if 'NewMultimeterIsValid' in data and data['NewMultimeterIsValid'] == 'VALID':
        print(f"p{data['NewDeviceId']}.value {float(data['NewMultimeterPower']) / 100}")
    print("multigraph states")
    for data in smart_home_data:
      if 'NewSwitchIsValid' in data and data['NewSwitchIsValid'] == 'VALID':
        state = 1
        if 'NewSwitchState' in data and data['NewSwitchState'] == 'OFF':
          state = 0
        print(f"s{data['NewDeviceId']}.value {state}")

  def print_config(self):
    smart_home_data = self.__connection.get_device_information_list()
    print("multigraph temperatures")
    print("graph_title Smart Home temperature")
    print("graph_vlabel degrees Celsius")
    print("graph_category sensors")
    print("graph_scale no")

    for data in smart_home_data:
      if 'NewTemperatureIsValid' in data and data['NewTemperatureIsValid'] == 'VALID':
        print(f"t{data['NewDeviceId']}.label {data['NewDeviceName']}")
        print(f"t{data['NewDeviceId']}.type GAUGE")
        print(f"t{data['NewDeviceId']}.graph LINE")
        print(f"t{data['NewDeviceId']}.info Temperature [{data['NewProductName']}], Offset: {float(data['NewTemperatureOffset']) / 10}°C")

    print("multigraph energy")
    print("graph_title Smart Home energy consumption")
    print("graph_vlabel Wh")
    print("graph_category sensors")
    print("graph_scale no")
    print("graph_period hour")
    for data in smart_home_data:
      if 'NewMultimeterIsValid' in data and data['NewMultimeterIsValid'] == 'VALID':
        print(f"e{data['NewDeviceId']}.label {data['NewDeviceName']}")
        print(f"e{data['NewDeviceId']}.type DERIVE")
        print(f"e{data['NewDeviceId']}.graph LINE")
        print(f"e{data['NewDeviceId']}.info Energy consumption (Wh) [{data['NewProductName']}]")

    print("multigraph powers")
    print("graph_title Smart Home powers")
    print("graph_vlabel W")
    print("graph_category sensors")
    print("graph_scale no")
    for data in smart_home_data:
      if 'NewMultimeterIsValid' in data and data['NewMultimeterIsValid'] == 'VALID':
        print(f"p{data['NewDeviceId']}.label {data['NewDeviceName']}")
        print(f"p{data['NewDeviceId']}.type GAUGE")
        print(f"p{data['NewDeviceId']}.graph LINE")
        print(f"p{data['NewDeviceId']}.info Power (W) [{data['NewProductName']}]")

    print("multigraph states")
    print("graph_title Smart Home switch states")
    print("graph_vlabel State")
    print("graph_category sensors")
    print("graph_scale no")
    for data in smart_home_data:
      if 'NewSwitchIsValid' in data and data['NewSwitchIsValid'] == 'VALID':
        print(f"s{data['NewDeviceId']}.label {data['NewDeviceName']}")
        print(f"s{data['NewDeviceId']}.type GAUGE")
        print(f"s{data['NewDeviceId']}.graph LINE")
        print(f"s{data['NewDeviceId']}.info Switch state [{data['NewProductName']}]")


if __name__ == '__main__':
  config = FritzboxConfig()
  main_handler(FritzboxSmartHome(FritzHomeAutomation(address=config.server, user=config.user, password=config.password, use_tls=config.use_tls)))
