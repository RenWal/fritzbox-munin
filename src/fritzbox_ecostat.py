#!/usr/bin/env python3
"""
  fritzbox_ecostat - A munin plugin for Linux to monitor AVM Fritzbox system
  stats
  Copyright (C) 2019 Rene Walendy
  Author: Rene Walendy
  Like Munin, this plugin is licensed under the GNU GPL v2 license
  http://www.opensource.org/licenses/GPL-2.0

  Add the following section to your munin-node's plugin configuration:

  [fritzbox_*]
  env.fritzbox_ip [ip address of the fritzbox]
  env.fritzbox_password [fritzbox password]
  env.fritzbox_user [fritzbox user, set any value if not required]
  env.ecostat_modes [cpu] [temp] [ram]

  This plugin supports the following munin configuration parameters:
  #%# family=auto contrib
  #%# capabilities=autoconf
"""

import os
from fritzbox_interface import FritzboxInterface
from fritzbox_munin_plugin_interface import MuninPluginInterface,main_handler

# @todo refactor

PAGE = 'data.lua'
PARAMS = {'xhr':1, 'lang':'de', 'page':'ecoStat', 'xhrId':'all', 'useajax':1, 'no_sidrenew':None}
RAMLABELS = ['strict', 'cache', 'free']

def get_modes():
  return os.getenv('ecostat_modes').split(' ') if (os.getenv('ecostat_modes')) else []


class FritzboxEcostat(MuninPluginInterface):
  __connection = None

  def __init__(self, fritzbox_interface: FritzboxInterface):
    self.__connection = fritzbox_interface

  def __print_simple_series(self, data, name, graph, low=None, high=None):
    """print last value of first json data series"""
    self.__print_multi_series(data, [name], graph, low, high)

  def __print_multi_series(self, data, names, graph, low=None, high=None):
    """print last value of multiple json data series"""

    print("multigraph " + graph)
    series = data['series']
    for i in range(len(names)):
      s = series[i]
      n = names[i]
      val = s[-1] # last entry is latest measurement
      if (low is None or float(val) > low) and (high is None or float(val) < high):
        print(n + '.value ' + str(val))
      else:
        print("# " + str(val) + " exceeded limits " + str(low) + " - " + str(high))

  def print_stats(self):
    """print the current system statistics"""

    modes = get_modes()

    # download the graphs
    jsondata = self.__connection.post_page_with_login(PAGE, data=PARAMS)['data']

    if 'cpu' in modes:
      cpuload_data = jsondata['cpuutil']
      self.__print_simple_series(cpuload_data, 'load', 'cpuload')

    if 'temp' in modes:
      cputemp_data = jsondata['cputemp']
      self.__print_simple_series(cputemp_data, 'temp', 'cputemp', low=0, high=120)

    if 'ram' in modes:
      ramusage_data = jsondata['ramusage']
      self.__print_multi_series(ramusage_data, RAMLABELS, 'ramusage')

  def print_config(self):
    modes = get_modes()

    if 'cpu' in modes:
      print("multigraph cpuload")
      print("graph_title CPU usage")
      print("graph_vlabel %")
      print("graph_category system")
      print("graph_order cpu")
      print("graph_scale no")
      print("load.label system")
      print("load.type GAUGE")
      print("load.graph LINE1")
      print("load.min 0")
      print("load.info Fritzbox CPU usage")

    if 'temp' in modes:
      print("multigraph cputemp")
      print("graph_title CPU temperature")
      print("graph_vlabel degrees Celsius")
      print("graph_category sensors")
      print("graph_order tmp")
      print("graph_scale no")
      print("temp.label CPU temperature")
      print("temp.type GAUGE")
      print("temp.graph LINE1")
      print("temp.min 0")
      print("temp.info Fritzbox CPU temperature")

    if 'ram' in modes:
      print("multigraph ramusage")
      print("graph_title Memory")
      print("graph_vlabel %")
      print("graph_args --base 1000 -r --lower-limit 0 --upper-limit 100")
      print("graph_category system")
      print("graph_order strict cache free")
      print("graph_info This graph shows what the Fritzbox uses memory for.")
      print("graph_scale no")
      for l in RAMLABELS:
        print(l + ".label " + l)
        print(l + ".type GAUGE")
        print(l + ".draw AREASTACK")


if __name__ == "__main__":
  main_handler(FritzboxEcostat(FritzboxInterface()))
