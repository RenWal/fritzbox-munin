#!/usr/bin/env python3
"""
  fritzbox_connection_uptime - A munin plugin for Linux to monitor AVM Fritzbox connection uptime
  Copyright (C) 2015 Christian Stade-Schuldt
  Author: Christian Stade-Schuldt
  Like Munin, this plugin is licensed under the GNU GPL v2 license
  http://www.opensource.org/licenses/GPL-2.0
  This plugin requires the fritzconnection plugin. To install it using pip:
  pip install fritzconnection

  Add the following section to your munin-node's plugin configuration:

  [fritzbox_*]
  env.fritzbox_ip [ip address of the fritzbox]

  This plugin supports the following munin configuration parameters:
  #%# family=auto contrib
  #%# capabilities=autoconf
"""

from fritzconnection.lib.fritzstatus import FritzStatus
from fritzbox_config import FritzboxConfig
from fritzbox_munin_plugin_interface import MuninPluginInterface,main_handler


class FritzboxConnectionUptime(MuninPluginInterface):
  __connection = None

  def __init__(self, fritzstatus_connection: FritzStatus):
    self.__connection = fritzstatus_connection

  def print_stats(self):
    print(f"uptime.value {(int(self.__connection.connection_uptime) / 3600.0):.2f}")

  def print_config(self):
    print("graph_title Connection Uptime")
    print("graph_args --base 1000 -l 0")
    print("graph_vlabel uptime in hours")
    print("graph_scale no")
    print("graph_category network")
    print("uptime.label uptime")
    print("uptime.draw AREA")
    print("graph_info The uptime in hours after the last disconnect.<br />Public IP address (ipv4): " + self.__connection.external_ip + ", Public IP address (ipv6): " + self.__connection.external_ipv6)


if __name__ == "__main__":
  config = FritzboxConfig()
  uptime = FritzboxConnectionUptime(FritzStatus(address=config.server, user=config.user, password=config.password, use_tls=config.use_tls))

  main_handler(uptime)
