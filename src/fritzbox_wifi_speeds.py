#!/usr/bin/env python3
"""
  fritzbox_wifi_speed - A munin plugin for Linux to monitor Wifi Speeds of a AVM Fritzbox Mesh
  Copyright (C) 2023 Ernst Martin Witte
  Author: Ernst Martin Witte
  Like Munin, this plugin is licensed under the GNU GPL v2 license
  http://www.opensource.org/licenses/GPL-2.0

  Add the following section to your munin-node's plugin configuration:

  [fritzbox_*]
  env.fritzbox_ip [ip address of the fritzbox]
  env.fritzbox_password [fritzbox password]
  env.fritzbox_user [fritzbox user, set any value if not required]

  This plugin supports the following munin configuration parameters:
  #%# family=auto contrib
  #%# capabilities=autoconf dirtyconfig
"""

import os
import re
import sys
import pprint
from   FritzboxInterface import FritzboxInterface
import argparse





def getWifiSpeeds(debug = False):
  
  devicesByBands = {}

  if debug :
    pp = pprint.PrettyPrinter(indent=4)
  # end if 


  
  if debug:
    print("requesting data through postPageWithLogin")
  # end if        
        

  # download the graphs
  PARAMS  = {
    'xhr':         1,
    'lang':        'de',
    'page':        'homeNet',
    'xhrId':       'all',
    'useajax':     1,
    'no_sidrenew': None
  }
  jsondata = FritzboxInterface().postPageWithLogin('data.lua',
                                                   data = PARAMS)

  if debug:
    pp.pprint(jsondata)
  # end if
  
  raw_devices  = jsondata["data"]["devices"]

  for dev in raw_devices:

    if debug:
      pp.pprint({ "device_under_investigation": dev})
    # end if

    
    connInfo = dev["conninfo"]

    # if dev["conninfo" is empty, then
    # we have the master Fritz!Box device entry
    # ==> ignore it here
    if (len(connInfo) == 0):      
      continue
    #
    
    connType = connInfo["kind"]
    devName  = dev["nameinfo"]["name"]
    devUID   = dev["UID"]

    if connType == "wlan" and "bandinfo" in connInfo:

      for band in connInfo["bandinfo"]:
        bandDesc = band["desc"]
        bandID   = band["band"]
        rx       = band["speed_rx"]
        tx       = band["speed_tx"]
        
        if bandID not in devicesByBands:
          devicesByBands[bandID] = { "devices": [],
                                     "desc":    bandDesc,
                                     "id":      bandID,
                                    }
        # end if
      
        devicesByBands[bandID]["devices"].append( { "name":                 devName,
                                                    "uid":                  devUID,
                                                    "rxSpeed_inMBitPerSec": rx,
                                                    "txSpeed_inMBitPerSec": tx,
                                                    "ds_name":              f"dev_{devUID}"
                                                   })
      # end for each band
    # end if wlan
    
  # end for each device
  
  if debug:
    pp.pprint({ "devicesByBands": devicesByBands } )
  # end if

  return devicesByBands
  
# end getWifiSpeeds
    



def getGraphName(band):
  bandID = band["id"]
  return f"wifiDeviceSpeed_{bandID}"
# end getGraphName


def printConfig(devicesByBands, debug = False):

  for band in devicesByBands.values():
    devices       = band["devices"]
    bandDesc      = band["desc"]
    bandID        = band["id"]
    graphName     = getGraphName(band)    
    sortedDevices = sorted(devices, key = lambda x: x["name"])
    dsNames       = [x["ds_name"] for x in sortedDevices];
    
    print(f"multigraph {graphName}_rx")
    print(f"graph_title Wifi Device Speeds (RX {bandDesc})")
    print("graph_vlabel MBit/s")
    print("graph_args --logarithmic")
    print("graph_category network")

    print("graph_order " + " ".join(dsNames))
    for dev in sortedDevices:
      ds    = dev["ds_name"]
      label = dev['name']
        
      print(f"{ds}.label {label}")
      print(f"{ds}.type GAUGE")
      print(f"{ds}.min 0")
    # end for each device

    
    print(f"multigraph {graphName}_tx")
    print(f"graph_title Wifi Device Speeds (TX {bandDesc})")
    print("graph_vlabel MBit/s")
    print("graph_args --logarithmic")
    print("graph_category network")

    print("graph_order " + " ".join(dsNames))
    for dev in sortedDevices:
      ds    = dev["ds_name"]
      label = dev['name']
        
      print(f"{ds}.label {label}")
      print(f"{ds}.type GAUGE")
      print(f"{ds}.min 0")
    # end for each device
  # end for each band
# end  printConfig



def printValues(devicesByBands, debug = False):

  for band in devicesByBands.values():
    devices       = band["devices"]
    bandDesc      = band["desc"]
    bandID        = band["id"]
    graphName     = getGraphName(band)    
    sortedDevices = sorted(devices, key = lambda x: x["name"])
    dsNames       = [x["ds_name"] for x in sortedDevices];
    
    print(f"multigraph {graphName}_rx")
    
    for dev in sortedDevices:
      ds    = dev["ds_name"]
      print(f"{ds}.value   {dev['rxSpeed_inMBitPerSec']}")
    # end for each device
    
    print(f"multigraph {graphName}_tx")
    
    for dev in sortedDevices:
      ds    = dev["ds_name"]
      print(f"{ds}.value   {dev['txSpeed_inMBitPerSec']}")
    # end for each device
  # end for each band
   
#end printValues



def main():

  parser = argparse.ArgumentParser(description='Munin Statistics for Fritz!Box Wifi Device Speeds')

  parser.add_argument('--debug', '-d', action = 'store_true',
                      help     = "enable debug output")

  parser.add_argument('requests', nargs = '*');

  args = parser.parse_args()


  requests = list(args.requests)
  if (len(requests) == 0):
    requests.append("fetch")
  # end if

  devByBands = None
  if "config" in requests or "fetch" in requests or "debug" in requests:
    devByBands = getWifiSpeeds(debug = args.debug or "debug" in requests)
  # end if

  
  for request in requests:
    if (request == "config"):
    
      printConfig(devByBands)
    
      if "MUNIN_CAP_DIRTYCONFIG" in os.environ and os.environ["MUNIN_CAP_DIRTYCONFIG"] == "1":
        print("")
        printValues(devByBands)
      # end if DIRTY CONFIG

    elif (request == "suggest"):
      pass
    elif (request == "autoconf"):
      print("yes")
    elif (request == "fetch"):
      printValues(devByBands)
    elif (request == "debug"):
      printValues(devByBands, debug = True)
    else:
      raise Exception(f"ERROR: unknown request type \"{args.request}\"");
    # end if
    
  # end for each request
  
# end main()


if __name__ == "__main__":
  main();
