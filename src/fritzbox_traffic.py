#!/usr/bin/env python3
"""
  fritzbox_traffic - A munin plugin for Linux to monitor AVM Fritzbox WAN traffic
  Copyright (C) 2015 Christian Stade-Schuldt
  Author: Christian Stade-Schuldt
  Like Munin, this plugin is licensed under the GNU GPL v2 license
  http://www.opensource.org/licenses/GPL-2.0

  Add the following section to your munin-node's plugin configuration:

  [fritzbox_*]
  env.fritzbox_ip [ip address of the fritzbox]
  env.traffic_remove_max [0|1]

  This plugin supports the following munin configuration parameters:
  #%# family=auto contrib
  #%# capabilities=autoconf
"""

import os
from fritzconnection.lib.fritzstatus import FritzStatus
from fritzbox_config import FritzboxConfig
from fritzbox_munin_plugin_interface import MuninPluginInterface,main_handler


class FritzboxTraffic(MuninPluginInterface):
  __connection = None
  __is_show_max = True

  def __init__(self, fritzstatus_connection: FritzStatus):
    self.__connection = fritzstatus_connection
    self.__is_show_max = not os.environ.get('traffic_remove_max') or os.environ.get('traffic_remove_max') != '1'

  def print_stats(self):
    [tr_up, tr_down] = self.__connection.transmission_rate
    print(f"down.value {tr_down}")
    print(f"up.value {tr_up}")

    if self.__is_show_max:
      [max_up, max_down] = self.__connection.max_bit_rate
      print(f"maxdown.value {max_down}")
      print(f"maxup.value {max_up}")

  def print_config(self):
    [max_up, max_down] = self.__connection.max_bit_rate

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
    print(f"down.max {max_down}")
    print("up.label bps")
    print("up.type DERIVE")
    print("up.draw LINE")
    print("up.cdef up,8,*")
    print("up.min 0")
    print(f"up.max {max_up}")
    print("up.negative down")
    print("up.info Traffic of the WAN interface.")

    if self.__is_show_max:
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
  traffic = FritzboxTraffic(FritzStatus(address=config.server, user=config.user, password=config.password, use_tls=config.use_tls))
  main_handler(traffic)
