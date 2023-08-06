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
  # Path where to store the persistent wifi device information (bands seen).

  # VARIABLE  env.wifi_speeds_dev_info_storage_path
  #
  # NOTE: We need the information, which device was connected in the past to which wifi band 
  #       (2.4 GHz or 5 GHz... or Ethernet), particularly for those devices which are currently not connected.
  #       Otherwise, disconnected devices will vanish from the munin plots.
  # 
  #       However, if a device is currently not connected, the FritzBox does not tell us in which 
  #       band the box was connected to so far. ... well not exactly: The FritzBox tells us this
  #       information for its "own" the wifi connections, but not for those of the repeaters.
  #       
  #       You may ask why then not directly asking the repeaters for the wifi connection 
  #       information of "currenty not connected devices".
  #       Unfortunately, on my setup (Fritz!Repeater 1750E and Fritz!Repeater 3000), 
  #       I'm not able to login with anything else than the master password, not with my munin stats key.      
  #
  #       Alternatively, we could create plot entries/curves for each combination of MAC addresses and bands.
  #       But this would cause pollution of the plots, e.g. ethernet-only devices in the wifi 
  #       plots, 2.4GHz-Interface MACs (typically MACs on 2.4 GHz and 5 GHz are different) listed 
  #       in 5 GHz plots and so on.
  #
  # Q:    Why not simply using a single aggregated data rate per device?
  # A:    In my stats I'd like to ...
  #       - identify, when 2.4 GHz or 5 GHz was used
  #       - to see separate stats for 2.4 GHz and 5 GHz bands for the repeaters
  # 
  # Q:    Hmm... why are you not using the "UID"s (e.g. "landevice1234") or names instead of MACs 
  #       for device identification?
  # A:    Because I observed that the uid changes over time for the same MAC/wifi device, particularly 
  #       in the guest network and when switching the wifi connection between repeaters/boxes.
  #       ==> Therefore, I consider device names and UUIDs as not suitable for device identification.
  # 
  # Q:    Ok... but for a Fritz!Repeater the FritzBox does only show one MAC in the "netDev" page 
  #       (used here in this script) and two other MACs in the "wSet" page. ... and in the ARP cache 
  #       the repeater shows up with yet another MAC.
  # A:    Seems that the netDev page shows the single globally/"universally" administered MAC of the 
  #       repeater. The Ethernet/2.4 GHz/5GHz MACs are "generated, locally administered" MAC addresses, 
  #       derived from the universal/global MAC.
  #       Therefore, I believe, the MAC is also suitable for identification of devices with multiple 
  #       concurrently used wifi bands.
  #
  # Default: $MUNIN_PLUGSTATE/fritzbox_wifi_speed_device_info.json
  #
  # NOTE for SSDs:
  #   In case you made the "normal" munin plugin state directory to reside on a tmpfs in order 
  #   to not write your SSD to death by munin (fine for most plugins), you should put this
  #   plugin state to some persistent storage. This is recommended since the wifi device information
  #   might change very slowly such that it takes ages after the munin server reboot until 
  #   all devices have been seen connected.
  #
  #   This plugin ensures that your SSD is not written to death: It only writes the file if 
  #   the list of known devices and their (rarely changing) connection types really changed. 
  #   The frequently changing "current wifi speeds" are not stored in this state file!
  #
  env.wifi_speeds_dev_info_storage_path  /path/to/json-file-with-persistent-device-info.json

  This plugin supports the following munin configuration parameters:
  #%# family=auto contrib
  #%# capabilities=autoconf dirtyconfig
"""

import os
import re
import sys
import pprint
from   FritzboxInterface import FritzboxInterface
from   FritzboxConfig    import FritzboxConfig
import argparse
import warnings
import requests
import copy
import json


key_ghz24 = "ghz24"
key_ghz5  = "ghz5"
key_eth   = "eth"



def makeKnownBandDescriptor(id, descr, is_symmetric) -> dict:
  return {
    "id":           id,
    "descr":        descr,
    "is_symmetric": is_symmetric
  }
# end makeKnownBandDescriptor



knownBands = { key_ghz24: makeKnownBandDescriptor(id           = key_ghz24,
                                                  descr        = "Wifi 2.4 GHz",
                                                  is_symmetric = 0),
               key_ghz5:  makeKnownBandDescriptor(id           = key_ghz5,
                                                  descr        = "Wifi 5 GHz",
                                                  is_symmetric = 0),
               key_eth:   makeKnownBandDescriptor(id           = key_eth,
                                                  descr        = "Ethernet",
                                                  is_symmetric = 1),
              }




def getConcurrentBandsKey(bandKeyList):
  return "-".join(sorted(bandKeyList))
# end getConcurrentBandsKey
                

def createPersistentDeviceInfoStruct(name, mac, bandKeyList):
    
  info = {
    "name":                name,
    "mac":                 mac,    
    "bandsSeen":           {},
    "concurrentBandsSeen": { getConcurrentBandsKey(bandKeyList): sorted(bandKeyList) }
  }
  
  for key in knownBands.keys():
    info["bandsSeen"][key] = (key in bandKeyList)
  # end for each band
  
  return info
# end createPersistentDeviceInfoStruct



def updatePersistentDeviceInfoStruct(name,
                                     mac,
                                     bandKeyList,
                                     currentPersistentDeviceInfo,
                                     storedPersistentDeviceInfo
                                     ):

  
  if mac not in currentPersistentDeviceInfo:
    if (mac in storedPersistentDeviceInfo):
      currentPersistentDeviceInfo[mac] = copy.deepcopy(storedPersistentDeviceInfo[mac])
    else:
      # do not create new entries for not-yet-connected devices!
      if (len(bandKeyList) <= 0):
        return
      # end if
      currentPersistentDeviceInfo[mac] = createPersistentDeviceInfoStruct(name, mac, bandKeyList)
    # end if
  # end if

  
  for bandKey in bandKeyList:
    currentPersistentDeviceInfo[mac]["bandsSeen"][bandKey] = 1
  # end for each bandKey

  # only record "concurrent bands seen" if the list is not empty
  if (len(bandKeyList) <= 0):
    currentPersistentDeviceInfo[mac]["concurrentBandsSeen"][getConcurrentBandsKey(bandKeyList)] = sorted(bandKeyList)

  # update the name if needed
  currentPersistentDeviceInfo[mac]["name"] = name

# end updatePersistentDeviceInfoStruct




def getPersisentDeviceInfoPath() -> str:
  munin_config_setting_path = os.getenv('wifi_speeds_dev_info_storage_path')
  munin_pluginstate_path    = os.getenv('MUNIN_PLUGSTATE') + '/fritzbox_wifi_speed_device_info.json'
  if (munin_config_setting_path is None or munin_config_setting_path == ""):
    return munin_pluginstate_path
  else:
    return munin_config_setting_path
# end getPersisentDeviceInfoPath


def loadPersistentDeviceInfo(debug = False) -> dict:
  
  fname = getPersisentDeviceInfoPath()
  
  if (debug):
    pp = pprint.PrettyPrinter(indent=4)
    print(f"Loading persistent device info from: {fname}")
  # end if debug
    
  if (os.path.isfile(fname)):
    fh    = open(fname, 'r')
    data  = json.load(fh)
    fh.close()
  else:
    data  = {}
  # end if
  
  if (debug):
    pp.pprint({"storedInfo":  data,
               "file":        fname
               })
  # end if debug
  
  return data

# end loadPersistentDeviceInfo


def storePersistentDeviceInfo(currentInfo,
                              storedInfo,
                              debug = False):
  fname       = getPersisentDeviceInfoPath()
  needsUpdate = currentInfo != storedInfo

  if (debug):
    pp = pprint.PrettyPrinter(indent=4)
    print("Storing persistent device info:")
    pp.pprint({"currentInfo":       currentInfo,
               "storedInfo":        storedInfo,
               "needsUpdateOnDisk": needsUpdate,
               "file":              fname
               })
  # end if debug               
  
  if (needsUpdate):
    fh    = open(fname, 'w')
    json.dump(currentInfo, fh)
    fh.close()
  # end if
  
# end storePersistentDeviceInfo



  
def getWifiSpeeds(oneFritzBoxInterface,
                  debug = False):

  devicesByBands   = {}
  for key in knownBands.keys():
    devicesByBands[key] = []
  # end for each known band


  storedPersistentDeviceInfo  = loadPersistentDeviceInfo(debug = debug)
  currentPersistentDeviceInfo = {}
  
  if debug :
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint({"FritzboxInterface.config": vars(oneFritzBoxInterface.config)})
    pp.pprint({ "storedPersistentDeviceInfo": storedPersistentDeviceInfo})
  # end if 


  
  if debug:
    print(f"requesting data through postPageWithLogin from {oneFritzBoxInterface.config.server}")
  # end if        
        

  # download the graphs
  PARAMS  = {
    'xhr':         1,
    'lang':        'de',
    'page':        'netDev',
    'xhrId':       'all',
    'useajax':     1,
    'no_sidrenew': None
  }
  jsondata = oneFritzBoxInterface.postPageWithLogin('data.lua',
                                                    data = PARAMS)

  if debug:
    pp.pprint(jsondata)
  # end if

  
  active_devices   = jsondata["data"]["active"]
  passive_devices  = jsondata["data"]["passive"]
  all_devices      = active_devices + passive_devices

  # example:       "LAN 1 mit 1 Gbit/s "
  ethSpeedRegEx    = re.compile(r'\b(\d+([\.,]\d+)?)\s*([GM])bit(/s)?', re.IGNORECASE)

  # example:       "2,4 GHz, 144 / 1 Mbit/s"
  wifiSpeedRegEx   = re.compile(r'\b(\d+([\.,]\d+)?)\s*GHz,?\s*(\d+([\.,]\d+)?)\s*/\s*(\d+([\.,]\d+)?)\s*([GMk])bit(/s)?', re.IGNORECASE)

  wifi24GHzRegex   = re.compile(r'\b2[,\.]4\s*GHz\b', re.IGNORECASE)
  wifi5GHzRegex    = re.compile(r'\b5\s*GHz\b',       re.IGNORECASE)

  for dev in all_devices:

    if debug:
      pp.pprint({ "device_under_investigation": dev})
    # end if

    
    devName  = dev["name"]
    connType = dev["type"]
    mac      = dev["mac"]
    props    = dev["properties"]
    port     = dev["port"]
    
    # NOTE: We store the uid (something like "landevice1234") for completeness.
    #       But we do not use it for identification, because the uid changes over time for the same MAC/wifi device.
    #       ... at least when switching the wifi connection between repeaters/boxes,
    #       but also looks like on a single box/repeater the uid is not stable!
    devUID   = dev["UID"]

    currentSpeeds   = {}
    if mac in storedPersistentDeviceInfo:
      bandsSeenInThePast = storedPersistentDeviceInfo[mac]["bandsSeen"]
      
      for band in [key for key in bandsSeenInThePast.keys() if bandsSeenInThePast[key]]:        
        currentSpeeds[band] = { "ds": 0,
                                "us": 0
                              }
      # end for each band seen in the past
    # end if

    if (debug):
      pp.pprint({"currentSpeeds before update": currentSpeeds })
    # end if debug
    
    concurrentBands = []
    
    if (connType == "ethernet"):
      
      match = ethSpeedRegEx.search(port)
      value = 0.0
      scale = 1.0
      if (match):
        value = float(match.group(1).replace(",", "."))
        unit  = match.group(3)
        scale = 1 if unit == "M" else 1000
      # end if
      currentSpeeds[key_eth] = { "ds": value * scale,
                                 "us": value * scale
                               }
      concurrentBands.append(key_eth)
      
    elif (connType == "wlan"):
      currentBands = []
      for prop in props:
        propString   = prop["txt"]
        match = wifiSpeedRegEx.search(propString)
        if (match):
          downstream = match.group(3)
          upstream   = match.group(5)
          unit       = match.group(7)
          scale      = 1 if unit == "M" else (1000 if unit == "G" else 1.0/1000.0)
          
          if (wifi24GHzRegex.search(propString)):
            band_key = key_ghz24
          elif (wifi5GHzRegex.search(propString)):
            band_key = key_ghz5
          else:
            band_key = None
          # end if band key selection

          currentSpeeds[band_key] = { "ds": downstream * scale,
                                      "us": upstream   * scale }

          concurrentBands.append(band_key)          
          
        # end if propString matches wifi band info
      # end for each property
    elif (connType == "unknown"):
      # do nothing:
      #   - known speeds from the past are kept at 0.0 MBit/s
      #   - no connected band is recorded
      #   - if not yet seen in the past: do not create a new entry in the "seen in the past" table
      pass
    # end if
    

    if (debug):
      pp.pprint({"currentSpeeds after update":   currentSpeeds,
                 "concurrentBands after update": concurrentBands
                 })
    # end if debug    

    
    # update the persistent table of known device/bands
    # (only updated for already known devices and if we have currently a connection)
    updatePersistentDeviceInfoStruct(devName,
                                     mac,
                                     concurrentBands,
                                     currentPersistentDeviceInfo,
                                     storedPersistentDeviceInfo)

    mac4dsName = re.sub(r'[^\w]', '', mac).lower()

    for bandKey in currentSpeeds.keys():
      deviceEntry  = { "name":                 devName,
                       "uid":                  devUID,
                       "mac":                  mac,
                       "rxSpeed_inMBitPerSec": currentSpeeds[bandKey]["ds"],
                       "txSpeed_inMBitPerSec": currentSpeeds[bandKey]["us"],
                       "ds_name":              f"dev_{mac4dsName}"
                     }

      devicesByBands[bandKey].append(deviceEntry)
    # end for each band
    
    if debug:
      pp.pprint({ "currentPersistentDeviceInfo after update": currentPersistentDeviceInfo})
    # end if
    
  # end for each device
  
  if debug:
    pp.pprint({ "devicesByBands": devicesByBands } )
  # end if


  storePersistentDeviceInfo(currentPersistentDeviceInfo,
                            storedPersistentDeviceInfo,
                            debug = debug)
  

  return devicesByBands
  
# end getWifiSpeeds
    



def getGraphName(bandKey):
  bandID = knownBands[bandKey]["id"]
  return f"wifiDeviceSpeed_{bandID}"
# end getGraphName


def getRxTxConfigParams(bandKey):
  isSymmetric   = knownBands[bandKey]["is_symmetric"]

  return {
    "rx_suffix" : "" if isSymmetric else '_rx',
    "rx_prefix" : "" if isSymmetric else 'RX ',
    "tx_suffix" : "" if isSymmetric else '_tx',
    "tx_prefix" : "" if isSymmetric else 'TX ',
    "show_rx"   : 1,
    "show_tx"   : 0  if isSymmetric else 1,
  }

# end getRxTxConfigParams


def printConfig(devicesByBands, debug = False):

  for bandKey,devices in devicesByBands.items():
    bandDescr     = knownBands[bandKey]["descr"]
    graphName     = getGraphName(bandKey)
    sortedDevices = sorted(devices, key = lambda x: x["name"])
    dsNames       = [x["ds_name"] for x in sortedDevices];

    rxtxCfg = getRxTxConfigParams(bandKey)

    if (rxtxCfg['show_rx']):
      print(f"multigraph {graphName}{rxtxCfg['rx_suffix']}")
      print(f"graph_title Device Speeds ({rxtxCfg['rx_prefix']}{bandDescr})")
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
    # end if show_rx

    
    if (rxtxCfg['show_tx']):
      print(f"multigraph {graphName}{rxtxCfg['tx_suffix']}")
      print(f"graph_title Device Speeds ({rxtxCfg['tx_prefix']}{bandDescr})")
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
    # end if show_tx
    
  # end for each band
  
# end  printConfig



def printValues(devicesByBands, debug = False):

  if debug :
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint({"printValues with devicesByBands": devicesByBands})
  # end if
  
  for bandKey,devices in devicesByBands.items():

    if debug :
      pp.pprint({"printing band": { "bandKey": bandKey, "devices": devices}})
    # end if
    
    bandDescr     = knownBands[bandKey]["descr"]
    graphName     = getGraphName(bandKey)
    sortedDevices = sorted(devices, key = lambda x: x["name"])
    dsNames       = [x["ds_name"] for x in sortedDevices];
   
    rxtxCfg = getRxTxConfigParams(bandKey)
    
    if (rxtxCfg['show_rx']):
      print(f"multigraph {graphName}{rxtxCfg['rx_suffix']}")
    
      for dev in sortedDevices:
        ds    = dev["ds_name"]
        print(f"{ds}.value   {dev['rxSpeed_inMBitPerSec']}")
      # end for each device
    # end if show_rx
    
    if (rxtxCfg['show_tx']):
      print(f"multigraph {graphName}{rxtxCfg['tx_suffix']}")
    
      for dev in sortedDevices:
        ds    = dev["ds_name"]
        print(f"{ds}.value   {dev['txSpeed_inMBitPerSec']}")
      # end for each device
    # end if show_tx
    
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
    devByBands = getWifiSpeeds(FritzboxInterface(),
                               debug = args.debug or "debug" in requests)
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
