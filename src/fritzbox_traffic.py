#!/usr/bin/env python3
"""
  fritzbox_traffic - A munin plugin for Linux to monitor AVM Fritzbox WAN traffic
  Copyright (C) 2015 Christian Stade-Schuldt
  Author: Christian Stade-Schuldt
  Like Munin, this plugin is licensed under the GNU GPL v2 license
  http://www.opensource.org/licenses/GPL-2.0
  This plugin requires the fritzconnection plugin. To install it using pip:
  pip install fritzconnection

  Add the following section to your munin-node's plugin configuration:

  [fritzbox_*]
  env.fritzbox_ip [ip address of the fritzbox]
  env.traffic_remove_max [0|1]

  This plugin supports the following munin configuration parameters:
  #%# family=auto contrib
  #%# capabilities=autoconf
"""

import os
import sys
from fritzconnection.lib.fritzstatus import FritzStatus
from fritzconnection.core.exceptions import FritzConnectionException
from fritzbox_config import FritzboxConfig
from fritzbox_munin_plugin_interface import MuninPluginInterface


class FritzboxTraffic(MuninPluginInterface):
  __connection = None

  def __init__(self, fritzstatus_connection: FritzStatus):
    self.__connection = fritzstatus_connection

  def print_stats(self):
    transmission_rate = self.__connection.transmission_rate
    print(f"down.value {transmission_rate[1]}")
    print(f"up.value {transmission_rate[0]}")

    if not os.environ.get('traffic_remove_max') or "false" in os.environ.get('traffic_remove_max'):
      max_traffic = self.__connection.max_bit_rate
      print(f"maxdown.value {max_traffic[1]}")
      print(f"maxup.value {max_traffic[0]}")

  def print_config(self):
    max_traffic = self.__connection.max_bit_rate

    print("graph_title WAN traffic")
    print("graph_args --base 1000")
    print("graph_vlabel bit in (-) / out (+) per ${graph_period}")
    print("graph_category network")
    print("graph_order down up maxdown maxup")
    print("down.label received")
    print("down.type DERIVE")
    print("down.graph no")
    print("down.cdef down,8,*")
    print("down.min 0")
    print(f"down.max {max_traffic[1]}")
    print("up.label bps")
    print("up.type DERIVE")
    print("up.draw LINE")
    print("up.cdef up,8,*")
    print("up.min 0")
    print(f"up.max {max_traffic[0]}")
    print("up.negative down")
    print("up.info Traffic of the WAN interface.")
    if not os.environ.get('traffic_remove_max') or "false" in os.environ.get('traffic_remove_max'):
      print("maxdown.label received")
      print("maxdown.type GAUGE")
      print("maxdown.graph no")
      print("maxup.label MAX")
      print("maxup.type GAUGE")
      print("maxup.negative maxdown")
      print("maxup.draw LINE1")
      print("maxup.info Maximum speed of the WAN interface.")


if __name__ == "__main__":
  config = FritzboxConfig()
  try:
    traffic = FritzboxTraffic(FritzStatus(address=config.server, user=config.user, password=config.password, use_tls=config.use_tls))
  except FritzConnectionException as connection_exception:
    sys.exit("Couldn't get traffic: " + str(connection_exception))

  if len(sys.argv) == 2 and sys.argv[1] == 'config':
    traffic.print_config()
  elif len(sys.argv) == 2 and sys.argv[1] == 'autoconf':
    print("yes")  # Some docs say it'll be called with fetch, some say no arg at all
  elif len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == 'fetch'):
    traffic.print_stats()
