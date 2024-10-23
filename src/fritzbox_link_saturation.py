#!/usr/bin/env python3
"""
  fritzbox_link_saturation - A munin plugin for Linux to monitor AVM Fritzbox
  WAN link saturation with QoS stats
  Copyright (C) 2019 Rene Walendy
  Author: Rene Walendy
  Like Munin, this plugin is licensed under the GNU GPL v2 license
  http://www.opensource.org/licenses/GPL-2.0

  Add the following section to your munin-node's plugin configuration:

  [fritzbox_*]
  env.fritzbox_ip [ip address of the fritzbox]
  env.fritzbox_password [fritzbox password]
  env.fritzbox_user [fritzbox user, set any value if not required]

  This plugin supports the following munin configuration parameters:
  #%# family=auto contrib
  #%# capabilities=autoconf
"""

from statistics import mean
from fritzconnection.lib.fritzstatus import FritzStatus
from fritzbox_config import FritzboxConfig
from fritzbox_munin_plugin_interface import MuninPluginInterface,main_handler,print_debug


LABELS_UP = ['realtime', 'high', 'default', 'low']
LABELS_DN = ['internet', 'iptv']


class FritzboxLinkSaturation(MuninPluginInterface):
  __connection = None

  def __init__(self, fritzstatus_connection: FritzStatus):
    self.__connection = fritzstatus_connection

  def print_stats(self):
    group_data = self.__connection.get_monitor_data()
    print_debug('got result from fritzbox:')
    print_debug(group_data)

    maxup = group_data['Newmax_us']
    maxdown = group_data['Newmax_ds']

    print("multigraph saturation_up")
    for i, value in enumerate(['Newprio_realtime_bps', 'Newprio_high_bps', 'Newprio_default_bps', 'Newprio_low_bps']):
      if value in group_data:
        print('up_' + LABELS_UP[i] + '.value ' + str(mean(group_data[value])))
    print("maxup.value " + str(maxup))

    print("multigraph saturation_down")
    for i, value in enumerate(['Newds_current_bps', 'Newmc_current_bps']):
      if value in group_data:
        print('dn_' + LABELS_DN[i] + '.value ' + str(mean(group_data[value])))
    print("maxdown.value " + str(maxdown))

  def print_config(self):
    print("multigraph saturation_up")
    print("graph_title Uplink saturation")
    print("graph_vlabel bits out per ${graph_period}")
    print("graph_category network")
    print("graph_args --base 1000 --lower-limit 0")
    print("graph_order " + ' '.join(LABELS_UP) + " maxdown")
    for label in LABELS_UP:
      print('up_' + label + '.label ' + label)
      print('up_' + label + '.type GAUGE')
      print('up_' + label + '.draw AREASTACK')
      print('up_' + label + '.cdef up_' + label + ',8,*')
    print("maxup.label MAX")
    print("maxup.type GAUGE")
    print("maxup.graph LINE1")
    print('maxup.cdef maxup,8,*')

    print("multigraph saturation_down")
    print("graph_title Downlink saturation")
    print("graph_vlabel bits in per ${graph_period}")
    print("graph_category network")
    print("graph_args --base 1000 --lower-limit 0")
    print("graph_order " + ' '.join(LABELS_DN) + " maxup")
    for label in LABELS_DN:
      print('dn_' + label + '.label ' + label)
      print('dn_' + label + '.type GAUGE')
      print('dn_' + label + '.draw AREASTACK')
      print('dn_' + label + '.cdef dn_' + label + ',8,*')
    print("maxdown.label MAX")
    print("maxdown.type GAUGE")
    print("maxdown.graph LINE1")
    print('maxdown.cdef maxdown,8,*')


if __name__ == "__main__":
  config = FritzboxConfig()
  main_handler(FritzboxLinkSaturation(FritzStatus(address=config.server, user=config.user, password=config.password, use_tls=config.use_tls)))
