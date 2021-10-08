#!/usr/bin/env python3
"""
  Unit tests for connection uptime module
"""

from unittest.mock import Mock
import unittest
import sys
from fritzbox_connection_uptime import FritzboxConnectionUptime

def get_fritzstatus_mock():
  mock_fritzstatus = Mock()
  mock_fritzstatus.external_ip = '127.0.0.1'
  mock_fritzstatus.external_ipv6 = '0000::0000::0000::0000'
  mock_fritzstatus.uptime = 18720

  return mock_fritzstatus

class TestFritzboxConnectionUptime(unittest.TestCase):
  def test_config(self):
    uptime = FritzboxConnectionUptime(get_fritzstatus_mock())
    uptime.print_config()

    # pylint: disable=no-member
    output = sys.stdout.getvalue().strip()
    self.assertEqual(output, "graph_title Connection Uptime\ngraph_args --base 1000 -l 0\ngraph_vlabel uptime in hours\ngraph_scale no\ngraph_category network\nuptime.label uptime\nuptime.draw AREA\ngraph_info The uptime in hours after the last disconnect.<br />Public IP address (ipv4): 127.0.0.1, Public IP address (ipv6): 0000::0000::0000::0000")

  def test_uptime(self):
    uptime = FritzboxConnectionUptime(get_fritzstatus_mock())
    uptime.print_uptime()

    # pylint: disable=no-member
    output = sys.stdout.getvalue().strip()
    self.assertEqual(output, 'uptime.value 5.20')

if __name__ == '__main__':
  unittest.main(module=__name__, buffer=True, exit=False)
