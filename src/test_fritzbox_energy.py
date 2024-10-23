#!/usr/bin/env python3
"""
  Unit tests for energy module
"""

from unittest.mock import Mock
import os
import unittest
import pytest
from fritzbox_energy import FritzboxEnergy
from fritzbox_interface import FritzboxInterface


@unittest.mock.patch.dict(os.environ, {
  "energy_modes": "power devices uptime INVALID",
  "energy_product": "DSL"
})
@pytest.mark.parametrize("fixture_version", ["7590-7.28", "7530ax-7.80"], indirect=True)
class TestFritzboxEnergy():

  @unittest.mock.patch.dict(os.environ, {
    "energy_modes": "INVALID",
    "energy_product": "DSL"
  })
  def test_config_with_invalid_modes_only(self, fixture_version: str, capsys): # pylint: disable=unused-argument
    ecostat = FritzboxEnergy(FritzboxInterface())
    ecostat.print_config()

    assert capsys.readouterr().out == ""

  @unittest.mock.patch.dict(os.environ, {
    "energy_modes": "INVALID",
    "energy_product": "INVALID"
  })
  def test_config_with_invalid_type(self, fixture_version: str): # pylint: disable=unused-argument
    energy = FritzboxEnergy(FritzboxInterface())

    pytest.raises(Exception, energy.print_config)

  def test_config(self, fixture_version: str, capsys): # pylint: disable=unused-argument
    energy = FritzboxEnergy(FritzboxInterface())
    energy.print_config()

    assert capsys.readouterr().out == """multigraph power
graph_title Power Consumption
graph_vlabel %
graph_args --lower-limit 0 --upper-limit 100 --rigid
graph_category system
graph_order system cpu wifi dsl ab usb
system.label system
system.type GAUGE
system.graph LINE1
system.min 0
system.max 100
system.info Fritzbox overall power consumption
cpu.label cpu
cpu.type GAUGE
cpu.graph LINE1
cpu.min 0
cpu.max 100
cpu.info Fritzbox central processor power consumption
wifi.label wifi
wifi.type GAUGE
wifi.graph LINE1
wifi.min 0
wifi.max 100
wifi.info Fritzbox wifi power consumption
dsl.label dsl
dsl.type GAUGE
dsl.graph LINE1
dsl.min 0
dsl.max 100
dsl.info Fritzbox dsl power consumption
ab.label ab
ab.type GAUGE
ab.graph LINE1
ab.min 0
ab.max 100
ab.info Fritzbox analog phone ports power consumption
usb.label usb
usb.type GAUGE
usb.graph LINE1
usb.min 0
usb.max 100
usb.info Fritzbox usb devices power consumption
multigraph devices
graph_title Connected Devices
graph_vlabel Number of devices
graph_args --base 1000
graph_category network
wifi.type GAUGE
wifi.graph LINE1
wifi.label wifi
wifi.info Wifi Connections on 2.4 & 5 Ghz
lan.type GAUGE
lan.graph LINE1
lan.label lan
lan.info LAN Connections
multigraph uptime
graph_title Uptime
graph_vlabel uptime in days
graph_args --base 1000 -l 0
graph_scale no
graph_category system
uptime.label uptime
uptime.draw AREA
"""

  def test_print_energy_stats(self, fixture_version: str, capsys): # pylint: disable=unused-argument
    energy = FritzboxEnergy(FritzboxInterface())
    energy.print_stats()

    assert capsys.readouterr().out == """multigraph power
system.value 24
cpu.value 67
wifi.value 57
dsl.value 100
ab.value 0
usb.value 0
multigraph devices
wifi.value 55
lan.value 40
multigraph uptime
uptime.value 66.25
"""
