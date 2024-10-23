import os
from unittest.mock import MagicMock


class ResponseMock: # pylint: disable=too-few-public-methods
  version: str

  def __new__(cls, *args, **kwargs):
    url = args[1]
    file_dir = f"{os.path.dirname(__file__)}/fixtures/fritzbox{cls.version}"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = ''

    if 'internet/dsl_stats_tab.lua' in url:
      with open(file_dir + "/dsl_stats_tab_lua.html", "r", encoding="utf-8") as file:
        mock_response.text = file.read()

    if 'login_sid.lua?version=2' in url:
      with open(file_dir + "/login_sid_lua.xml", "rb") as file:
        mock_response.content = file.read()

    file_name = None
    if 'internet/inetstat_monitor.lua' in url:
      file_name = "inetstat_monitor_lua.json"
    elif 'data.lua' in url and kwargs['data']['page'] == 'ecoStat':
      file_name = "ecostat_data_lua.json"
    elif 'data.lua' in url and kwargs['data']['page'] == 'energy':
      file_name = "energy_data_lua.json"
    elif 'data.lua' in url and kwargs['data']['page'] == 'dslStat':
      file_name = "dsl_data_lua.json"
    elif 'data.lua' in url:
      mock_response.text = "{'data': {}}"

    if file_name is not None:
      with open(file_dir + "/" + file_name, "r", encoding="utf-8") as file:
        mock_response.text = file.read()

    return mock_response
