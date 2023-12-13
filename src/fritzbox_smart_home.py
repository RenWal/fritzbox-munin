#!/usr/bin/env python3
"""
  fritzbox_smart_home - A munin plugin for Linux to monitor AVM Fritzbox SmartHome values

  @see https://avm.de/fileadmin/user_upload/Global/Service/Schnittstellen/x_homeauto.pdf
"""

from fritzconnection import FritzConnection
from fritzbox_config import FritzboxConfig
from fritzbox_munin_plugin_interface import MuninPluginInterface,main_handler


class FritzboxSmartHome(MuninPluginInterface):
  __connection = None

  def __init__(self, fritzbox_connection: FritzConnection):
    self.__connection = fritzbox_connection

  def __retrieve_smart_home(self) -> []:
    smart_home_data = []

    for i in range(0, 20):
      try:
        data = self.__connection.call_action('X_AVM-DE_Homeauto1', 'GetGenericDeviceInfos', arguments={'NewIndex': i})
        smart_home_data.append(data)
      except Exception:
        # smart home device index does not exist, so we stop here
        break

    return smart_home_data

  def print_stats(self):
    smart_home_data = self.__retrieve_smart_home()

    print("multigraph temperatures")
    for data in smart_home_data:
      if data['NewTemperatureIsValid'] == 'VALID':
        print (f"t{data['NewDeviceId']}.value {float(data['NewTemperatureCelsius']) / 10}")
    print("multigraph energy")
    for data in smart_home_data:
      if data['NewMultimeterIsValid'] == 'VALID':
        print (f"e{data['NewDeviceId']}.value {data['NewMultimeterEnergy']}")
    print("multigraph powers")
    for data in smart_home_data:
      if data['NewMultimeterIsValid'] == 'VALID':
        print (f"p{data['NewDeviceId']}.value {float(data['NewMultimeterPower']) / 100}")
    print("multigraph states")
    for data in smart_home_data:
      if data['NewSwitchIsValid'] == 'VALID':
        state = 1
        if data['NewSwitchState'] == 'OFF':
          state = 0
        print (f"s{data['NewDeviceId']}.value {state}")

  def print_config(self):
    smart_home_data = self.__retrieve_smart_home()
    print("multigraph temperatures")
    print("graph_title Smart Home temperature")
    print("graph_vlabel degrees Celsius")
    print("graph_category sensors")
    print("graph_scale no")

    for data in smart_home_data:
      if data['NewTemperatureIsValid'] == 'VALID':
        print (f"t{data['NewDeviceId']}.label {data['NewDeviceName']}")
        print (f"t{data['NewDeviceId']}.type GAUGE")
        print (f"t{data['NewDeviceId']}.graph LINE")
        print (f"t{data['NewDeviceId']}.info Temperature [{data['NewProductName']}], Offset: {float(data['NewTemperatureOffset']) / 10} C")

    print("multigraph energy")
    print("graph_title Smart Home energy consumption")
    print("graph_vlabel Wh")
    print("graph_category sensors")
    print("graph_scale no")
    print("graph_period hour")
    for data in smart_home_data:
      if data['NewMultimeterIsValid'] == 'VALID':
        print (f"e{data['NewDeviceId']}.label {data['NewDeviceName']}")
        print (f"e{data['NewDeviceId']}.type DERIVE")
        print (f"e{data['NewDeviceId']}.graph LINE")
        print (f"e{data['NewDeviceId']}.info Energy consumption (Wh) [{data['NewProductName']}]")

    print("multigraph powers")
    print("graph_title Smart Home powers")
    print("graph_vlabel W")
    print("graph_category sensors")
    print("graph_scale no")
    for data in smart_home_data:
      if data['NewMultimeterIsValid'] == 'VALID':
        print (f"p{data['NewDeviceId']}.label {data['NewDeviceName']}")
        print (f"p{data['NewDeviceId']}.type GAUGE")
        print (f"p{data['NewDeviceId']}.graph LINE")
        print (f"p{data['NewDeviceId']}.info Power (W) [{data['NewProductName']}]")

    print("multigraph states")
    print("graph_title Smart Home switch states")
    print("graph_vlabel State")
    print("graph_category sensors")
    print("graph_scale no")
    for data in smart_home_data:
      if data['NewSwitchIsValid'] == 'VALID':
        print (f"s{data['NewDeviceId']}.label {data['NewDeviceName']}")
        print (f"s{data['NewDeviceId']}.type GAUGE")
        print (f"s{data['NewDeviceId']}.graph LINE")
        print (f"s{data['NewDeviceId']}.info Switch state [{data['NewProductName']}]")


if __name__ == '__main__':
  config = FritzboxConfig()
  main_handler(FritzboxSmartHome(FritzConnection(address=config.server, user=config.user, password=config.password, use_tls=config.use_tls)))
