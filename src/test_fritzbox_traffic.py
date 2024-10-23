#!/usr/bin/env python3
"""
  Unit tests for traffic module
"""

from unittest.mock import MagicMock
from fritzbox_traffic import FritzboxTraffic

def get_fritzstatus_mock() -> MagicMock:
  mock_fritzstatus = MagicMock()
  mock_fritzstatus.max_bit_rate = [182, 1]
  mock_fritzstatus.transmission_rate = [1024, 4373]

  return mock_fritzstatus

class TestFritzboxTraffic():
  maxDiff = None

  def test_config(self, capsys):
    traffic = FritzboxTraffic(get_fritzstatus_mock())
    traffic.print_config()

    assert capsys.readouterr().out == """graph_title WAN traffic
graph_args --base 1000
graph_vlabel bit in (-) / out (+) per ${graph_period}
graph_category network
graph_order down up maxdown maxup
down.label received
down.type DERIVE
down.graph no
down.cdef down,8,*
down.min 0
down.max 1
up.label bps
up.type DERIVE
up.draw LINE
up.cdef up,8,*
up.min 0
up.max 182
up.negative down
up.info Traffic of the WAN interface.
maxdown.label received
maxdown.type GAUGE
maxdown.graph no
maxup.label MAX
maxup.type GAUGE
maxup.negative maxdown
maxup.draw LINE1
maxup.info Maximum speed of the WAN interface.
"""

  def test_traffic(self, capsys):
    traffic = FritzboxTraffic(get_fritzstatus_mock())
    traffic.print_stats()

    assert capsys.readouterr().out == """down.value 4373
up.value 1024
maxdown.value 1
maxup.value 182
"""
