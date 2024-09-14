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
import sys
import json
from FritzboxInterface import FritzboxInterface

PAGE = 'data.lua'
PARAMS = {'xhr':1, 'lang':'de', 'page':'ecoStat', 'xhrId':'all', 'useajax':1, 'no_sidrenew':None}
RAMLABELS = ['strict', 'cache', 'free']

def get_modes():
  return os.getenv('ecostat_modes').split(' ')

def print_simple_series(data, name, graph, low=None, high=None):
  """print last value of first json data series"""
  print_multi_series(data, [name], graph, low, high)

def print_multi_series(data, names, graph, low=None, high=None):
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

def print_system_stats():
  """print the current system statistics"""

  modes = get_modes()

  # download the graphs
  jsondata = FritzboxInterface().postPageWithLogin(PAGE, data=PARAMS)['data']
  
  # print(json.dumps(jsondata, indent = 4))

  if 'cpu' in modes:
    cpuload_data = jsondata['cpuutil']
    print_simple_series(cpuload_data, 'load', 'cpuload')

  if 'temp' in modes:
    cputemp_data = jsondata['cputemp']
    print_simple_series(cputemp_data, 'temp', 'cputemp', low=0, high=120)

  if 'ram' in modes:
    ramusage_data = jsondata['ramusage']
    print_multi_series(ramusage_data, RAMLABELS, 'ramusage')

def print_config():
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
  if len(sys.argv) == 2 and sys.argv[1] == 'config':
    print_config()
  elif len(sys.argv) == 2 and sys.argv[1] == 'autoconf':
    print("yes")  # Some docs say it'll be called with fetch, some say no arg at all
  elif len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == 'fetch'):
    try:
      print_system_stats()
    except Exception as e:
      sys.exit("Couldn't retrieve fritzbox system stats: " + str(e))
