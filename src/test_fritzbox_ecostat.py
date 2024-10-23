#!/usr/bin/env python3
"""
  Unit tests for ecostat module
"""

from unittest.mock import Mock
import os
import unittest
import pytest
from fritzbox_ecostat import FritzboxEcostat
from fritzbox_interface import FritzboxInterface


@unittest.mock.patch.dict(os.environ, {
  "ecostat_modes": "cpu temp ram INVALID"
})
@pytest.mark.parametrize("fixture_version", ["7590-7.28", "7530ax-7.80"], indirect=True)
class TestFritzboxEcostat():

  @unittest.mock.patch.dict(os.environ, {
    "ecostat_modes": "INVALID"
  })
  def test_config_with_invalid_modes_only(self, fixture_version: str, capsys): # pylint: disable=unused-argument
    ecostat = FritzboxEcostat(FritzboxInterface())
    ecostat.print_config()

    assert capsys.readouterr().out == ""

  def test_config(self, fixture_version: str, capsys): # pylint: disable=unused-argument
    dsl = FritzboxEcostat(FritzboxInterface())
    dsl.print_config()

    assert capsys.readouterr().out == """multigraph cpuload
graph_title CPU usage
graph_vlabel %
graph_category system
graph_order cpu
graph_scale no
load.label system
load.type GAUGE
load.graph LINE1
load.min 0
load.info Fritzbox CPU usage
multigraph cputemp
graph_title CPU temperature
graph_vlabel degrees Celsius
graph_category sensors
graph_order tmp
graph_scale no
temp.label CPU temperature
temp.type GAUGE
temp.graph LINE1
temp.min 0
temp.info Fritzbox CPU temperature
multigraph ramusage
graph_title Memory
graph_vlabel %
graph_args --base 1000 -r --lower-limit 0 --upper-limit 100
graph_category system
graph_order strict cache free
graph_info This graph shows what the Fritzbox uses memory for.
graph_scale no
strict.label strict
strict.type GAUGE
strict.draw AREASTACK
cache.label cache
cache.type GAUGE
cache.draw AREASTACK
free.label free
free.type GAUGE
free.draw AREASTACK
"""

  def test_print_system_stats(self, fixture_version: str, capsys): # pylint: disable=unused-argument
    ecostat = FritzboxEcostat(FritzboxInterface())
    ecostat.print_stats()

    assert capsys.readouterr().out == """multigraph cpuload
load.value 10
multigraph cputemp
temp.value 71
multigraph ramusage
strict.value 17
cache.value 32.9
free.value 50.1
"""
