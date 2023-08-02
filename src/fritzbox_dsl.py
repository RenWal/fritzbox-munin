#!/usr/bin/env python3
"""
  fritzbox_dsl - A munin plugin for Linux to monitor AVM Fritzbox DSL link quality
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
  env.dsl_modes [capacity] [snr] [damping] [errors] [crc]

  This plugin supports the following munin configuration parameters:
  #%# family=auto contrib
  #%# capabilities=autoconf
"""

import os
import sys
import json
from lxml import html
from FritzboxInterface import FritzboxInterface

PAGE   = 'data.lua'
PARAMS = {'page': 'dslStat', 'lang': 'en', 'useajax': 1, 'xhrId': 'all', 'xhr': 1, 'no_sidrenew' : None}

TITLES = {
  'capacity': 'Link Capacity',
  'rate'    : 'Synced Rate',
  'snr'     : 'Signal-to-Noise Ratio',
  'damping' : 'Line Loss',
  'errors'  : 'Errors: Transmission',
  'crc'     : 'Errors: Checksums',
  'ecc'     : 'Errors: Corrected'
}
TYPES = {
  'capacity': 'GAUGE',
  'rate': 'GAUGE',
  'snr': 'GAUGE',
  'damping': 'GAUGE',
  'errors': 'DERIVE',
  'crc': 'GAUGE',
  'ecc': 'GAUGE'
}
VLABELS = {
  'capacity': 'bit/s',
  'rate': 'bit/s',
  'snr': 'dB',
  'damping': 'dB',
  'errors': 's',
  'crc': 'n',
  'ecc': 'n',
}

def get_modes():
  return os.getenv('dsl_modes').split(' ')

def print_graph(name, recv, send, prefix=""):
  if name:
    print("multigraph " + name)
  print(prefix + f"recv.value {recv}")
  print(prefix + f"send.value {send}")

def print_dsl_stats():
  """print the current DSL statistics"""

  modes = get_modes()

  # download the table
  data = FritzboxInterface().postPageWithLogin(PAGE, data=PARAMS)

  dslStats = data["data"]["negotiatedValues"]
  errStats = data["data"]["errorCounters"]

  if 'capacity' in modes:
    capacity_recv = float(dslStats[2]["val"][0]["ds"])
    capacity_send = float(dslStats[2]["val"][0]["us"])
    print_graph("dsl_capacity", capacity_recv, capacity_send)

  if 'rate' in modes:
    rate_recv = float(dslStats[3]["val"][0]["ds"])
    rate_send = float(dslStats[3]["val"][0]["us"])
    print_graph("dsl_rate", rate_recv, rate_send)

  if 'snr' in modes: # Störabstandsmarge
    snr_recv = float(dslStats[12]["val"][0]["ds"])
    snr_send = float(dslStats[12]["val"][0]["us"])
    print_graph("dsl_snr", snr_recv, snr_send)

  if 'damping' in modes: # Leitungsdämpfung
    damping_recv = float(dslStats[13]["val"][0]["ds"])
    damping_send = float(dslStats[13]["val"][0]["us"])
    print_graph("dsl_damping", damping_recv, damping_send)

  if 'errors' in modes:
    es_recv  = float(errStats[1]["val"][0]["ds"])
    es_send  = float(errStats[1]["val"][0]["us"])
    ses_recv = float(errStats[2]["val"][0]["ds"])
    ses_send = float(errStats[2]["val"][0]["us"])
    print_graph("dsl_errors", int(es_recv),  int(es_send),  prefix="es_")
    print_graph(None,         int(ses_recv), int(ses_send), prefix="ses_")

  if 'crc' in modes:
    crc_recv = float(errStats[6]["val"][0]["ds"])
    crc_send = float(errStats[6]["val"][0]["us"])
    print_graph("dsl_crc", crc_recv, crc_send)

  if 'ecc' in modes:
    corr_recv = float(errStats[10]["val"][0]["ds"])
    corr_send = float(errStats[10]["val"][0]["us"])
    fail_recv = float(errStats[14]["val"][0]["ds"])
    fail_send = float(errStats[14]["val"][0]["us"])
    print_graph("dsl_ecc", corr_recv, corr_send, prefix="corr_")
    print_graph(None,      fail_recv, fail_send, prefix="fail_")


def print_config():
  modes = get_modes()

  for mode in ['capacity', 'rate', 'snr', 'damping', 'crc']:
    if not mode in modes:
      continue
    print("multigraph dsl_" + mode)
    print("graph_title " + TITLES[mode])
    print("graph_vlabel " + VLABELS[mode])
    print("graph_args --lower-limit 0")
    print("graph_category network")
    for p,l in {'recv' : 'receive', 'send': 'send'}.items():
      print(p + ".label " + l)
      print(p + ".type " + TYPES[mode])
      print(p + ".graph LINE1")
      print(p + ".min 0")
      if mode in ['capacity', 'rate']:
        print(p + ".cdef " + p + ",1000,*")

  if 'errors' in modes:
    print("multigraph dsl_errors")
    print("graph_title " + TITLES['errors'])
    print("graph_vlabel " + VLABELS['errors'])
    print("graph_args --lower-limit 0")
    print("graph_category network")
    print("graph_order es_recv es_send ses_recv ses_send")
    for p,l in {'es_recv' : 'receive errored', 'es_send': 'send errored', 'ses_recv' : 'receive severely errored', 'ses_send': 'send severely errored'}.items():
      print(p + ".label " + l)
      print(p + ".type " + TYPES['errors'])
      print(p + ".graph LINE1")
      print(p + ".min -1")
      print(p + ".warning 1")

  if 'ecc' in modes:
    print("multigraph dsl_ecc")
    print("graph_title " + TITLES['ecc'])
    print("graph_vlabel " + VLABELS['ecc'])
    print("graph_args --lower-limit 0")
    print("graph_category network")
    print("graph_order corr_recv corr_send fail_recv fail_send")
    for p,l in {'corr_recv' : 'receive corrected', 'corr_send': 'send corrected', 'fail_recv' : 'receive uncorrectable', 'fail_send': 'send uncorrectable'}.items():
      print(p + ".label " + l)
      print(p + ".type " + TYPES['ecc'])
      print(p + ".graph LINE1")
      print(p + ".min 0")
      print(p + ".warning 1")

if __name__ == "__main__":
  if len(sys.argv) == 2 and sys.argv[1] == 'config':
    print_config()
  elif len(sys.argv) == 2 and sys.argv[1] == 'autoconf':
    print("yes")  # Some docs say it'll be called with fetch, some say no arg at all
  elif len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == 'fetch'):
    try:
      print_dsl_stats()
    except Exception as e:
      sys.exit("Couldn't retrieve fritzbox dsl stats: " + str(e))
