import os
import json


class FritzConnectionMock: # pylint: disable=too-few-public-methods
  version: str

  def __init__(self, version):
    self.version = version

  def call_action(self, *args, **kwargs) -> {}:
    if args[0] == 'WANDSLInterfaceConfig1' and args[1] == 'GetInfo':
      return self.__get_fixture('dsl_info.json')

    index = 0
    if 'arguments' in kwargs and 'NewIndex' in kwargs['arguments']:
      index = kwargs['arguments']['NewIndex']

    json_object = self.get_device_information_list()

    return json_object[index] if len(json_object) > index else {}

  def get_device_information_list(self, *args, **kwargs) -> {}:
    return self.__get_fixture('smart_home_devices.json')

  def get_monitor_data(self) -> {}:
    return self.__get_fixture('monitor_data.json')

  def __get_fixture(self, file_name):
    file_dir = f"{os.path.dirname(__file__)}/fixtures/fritzbox{self.version}"
    with open(file_dir + "/" + file_name, "r", encoding="utf-8") as file:
      return json.load(file)
