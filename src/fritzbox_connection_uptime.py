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

import os
import sys
from fritzconnection.lib.fritzstatus import FritzStatus
from FritzboxConfig import FritzboxConfig

class FritzboxConnectionUptime:
  __connection = None

  def __init__(self):
    config = FritzboxConfig()
    try:
      self.__connection = FritzStatus(address=config.server, user=config.user, password=config.password, use_tls=config.useTls)
    except Exception as e:
      sys.exit("Couldn't get connection uptime: " + str(e))

  def printUptime(self):
    print('connUptime.value %.2f' % (int(self.__connection.uptime) / 3600.0))

  def printConfig(self):
    print("graph_title Connection Uptime")
    print("graph_args --base 1000 -l 0")
    print("graph_vlabel uptime in hours")
    print("graph_scale no")
    print("graph_category network")
    print("connUptime.label uptime")
    print("connUptime.type  GAUGE")
    print("connUptime.draw AREA")
    print("graph_info The uptime in hours after the last disconnect.<br />Public IP address (ipv4): " + self.__connection.external_ip + ", Public IP address (ipv6): " + self.__connection.external_ipv6)

if __name__ == "__main__":
  uptime = FritzboxConnectionUptime()
  if len(sys.argv) == 2 and sys.argv[1] == 'config':
    uptime.printConfig()
  elif len(sys.argv) == 2 and sys.argv[1] == 'autoconf':
    print("yes")  # Some docs say it'll be called with fetch, some say no arg at all
  elif len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == 'fetch'):
    try:
      uptime.printUptime()
    except Exception as e:
      sys.exit("Couldn't retrieve fritzbox connection uptime: " + str(e))
