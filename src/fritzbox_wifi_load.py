#!/usr/bin/env python3
"""
  fritzbox_wifi_load - A munin plugin for Linux to monitor AVM Fritzbox wifi
  bandwidth usage and neighbor AP count
  Copyright (C) 2019 Rene Walendy
  Author: Rene Walendy
  Like Munin, this plugin is licensed under the GNU GPL v2 license
  http://www.opensource.org/licenses/GPL-2.0

  Add the following section to your munin-node's plugin configuration:

  [fritzbox_*]
  env.fritzbox_ip [ip address of the fritzbox]
  env.fritzbox_password [fritzbox password]
  env.fritzbox_user [fritzbox user, set any value if not required]
  env.wifi_freqs [24] [5]
  env.wifi_modes [freqs] [neighbors]

  This plugin supports the following munin configuration parameters:
  #%# family=auto contrib
  #%# capabilities=autoconf
"""

import os
import sys
import pprint
from FritzboxInterface import FritzboxInterface

PAGE = 'data.lua'
PARAMS = {'xhr':1, 'lang':'de', 'page':'chan', 'xhrId':'environment', 'useajax':1, 'no_sidrenew':None}

def average_load(datapoints):
  """ average send and receive series """
  recv = 0
  send = 0
  for d in datapoints:
    parts = d.split(u':')
    recv += int(parts[0])
    send += int(parts[1])
  datalen = len(datapoints)
  recv //= datalen
  send //= datalen
  return (recv,send)

def get_freqs():
  return os.getenv('wifi_freqs').split(' ')

def get_modes():
  return os.getenv('wifi_modes').split(' ')

def print_wifi_load(debug = False):
  """get the current wifi bandwidth usage"""

  # set up the graphs (load the 10-minute view)
  fritzboxHelper = FritzboxInterface()
  # download the graphs
  jsondata = fritzboxHelper.postPageWithLogin(PAGE, data=PARAMS)['data']

  if debug:
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(jsondata)
  # end if
  
  freqs = get_freqs()
  modes = get_modes()
  scanlist = jsondata['scanlist']

  # parse data from all available frequencies
  for freq in freqs:
    band_id = freq + 'ghz'
    freqdata = jsondata[band_id]
    if freqdata == None:
      continue
    if 'freqs' in modes:
      airtimedata = freqdata['airtimedata']
      datapoints = airtimedata.split(',')[3:303]
      average_recv, average_send = average_load(datapoints)
      print('multigraph bandwidth_' + freq + 'ghz')
      print(freq + 'ghz_recv.value ' + str(average_recv))
      print(freq + 'ghz_send.value ' + str(average_send))
    if 'neighbors' in modes:
      own_chans = freqdata['usedChannels']
      sameChan = 0
      otherChans = 0
      for ap in scanlist:
        # only count APs on the current band
        if ap['bandId'] != band_id: continue
        # don't count the FritzBox's own AP
        if not ap.get('isEnvNet', False): continue
        chan = ap['channel']
        if chan in own_chans:
          sameChan+=1
        else:
          otherChans+=1
      print('multigraph neighbors_' + freq + 'ghz')
      print(freq + 'ghz_samechan.value ' + str(sameChan))
      print(freq + 'ghz_otherchans.value ' + str(otherChans))

def print_config():
  freqs = get_freqs()
  modes = get_modes()
  for freq in freqs:
    if 'freqs' in modes:
      print("multigraph bandwidth_" + freq + 'ghz')
      print("graph_title WIFI " + freq + "GHz bandwidth usage")
      print("graph_vlabel percent")
      print("graph_category network")
      print("graph_args --lower-limit 0 --upper-limit 100 --rigid")
      print("graph_order " + freq + "ghz_recv " + freq + "ghz_send")
      for p,l in {'recv' : 'receive', 'send': 'send'}.items():
        multiP = freq + 'ghz_' + p
        print(multiP + '.label ' + l)
        print(multiP + '.type GAUGE')
        print(multiP + '.draw AREASTACK')
    if 'neighbors' in modes:
      print("multigraph neighbors_" + freq + 'ghz')
      print("graph_title WIFI " + freq + "GHz neighbor APs")
      print("graph_vlabel number of APs")
      print("graph_category network")
      print("graph_args --lower-limit 0")
      print("graph_order " + freq + "ghz_samechan " + freq + "ghz_otherchans")
      for p,l in {'samechan' : 'same channel', 'otherchans': 'other channels'}.items():
        multiP = freq + 'ghz_' + p
        print(multiP + '.label ' + l)
        print(multiP + '.type GAUGE')
        print(multiP + '.draw AREASTACK')

if __name__ == "__main__":
  if (len(sys.argv) == 1):
    request = "fetch"
  else:
    request = sys.argv[1]
  # end if
  
  if (request == "config"):
    print_config()
  elif (request == 'autoconf'):
    print("yes")  # Some docs say it'll be called with fetch, some say no arg at all
  elif (request == 'fetch' or request == 'debug'):
    try:
      print_wifi_load(request == 'debug')
    except Exception as e:
      sys.exit("Couldn't retrieve fritzbox wifi load: " + str(e))
