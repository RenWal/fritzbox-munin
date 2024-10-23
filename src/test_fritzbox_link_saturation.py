#!/usr/bin/env python3
"""
  Unit tests for link saturation module
"""

from unittest.mock import MagicMock
import pytest
from fritzbox_link_saturation import FritzboxLinkSaturation


@pytest.mark.parametrize("connection", ["7590-7.57", "7530ax-7.80"], indirect=True)
class TestFritzboxLinkSaturation():
  def test_config(self, connection: MagicMock, capsys):
    sut = FritzboxLinkSaturation(connection)
    sut.print_config()

    assert capsys.readouterr().out == """multigraph saturation_up
graph_title Uplink saturation
graph_vlabel bits out per ${graph_period}
graph_category network
graph_args --base 1000 --lower-limit 0
graph_order realtime high default low maxdown
up_realtime.label realtime
up_realtime.type GAUGE
up_realtime.draw AREASTACK
up_realtime.cdef up_realtime,8,*
up_high.label high
up_high.type GAUGE
up_high.draw AREASTACK
up_high.cdef up_high,8,*
up_default.label default
up_default.type GAUGE
up_default.draw AREASTACK
up_default.cdef up_default,8,*
up_low.label low
up_low.type GAUGE
up_low.draw AREASTACK
up_low.cdef up_low,8,*
maxup.label MAX
maxup.type GAUGE
maxup.graph LINE1
maxup.cdef maxup,8,*
multigraph saturation_down
graph_title Downlink saturation
graph_vlabel bits in per ${graph_period}
graph_category network
graph_args --base 1000 --lower-limit 0
graph_order internet iptv maxup
dn_internet.label internet
dn_internet.type GAUGE
dn_internet.draw AREASTACK
dn_internet.cdef dn_internet,8,*
dn_iptv.label iptv
dn_iptv.type GAUGE
dn_iptv.draw AREASTACK
dn_iptv.cdef dn_iptv,8,*
maxdown.label MAX
maxdown.type GAUGE
maxdown.graph LINE1
maxdown.cdef maxdown,8,*
"""

  def test_saturation(self, connection: MagicMock, capsys):
    sut = FritzboxLinkSaturation(connection)
    sut.print_stats()

    assert capsys.readouterr().out == """multigraph saturation_up
up_realtime.value 6081.25
up_high.value 379.55
up_default.value 11141.8
up_low.value 0
maxup.value 1555375
multigraph saturation_down
dn_internet.value 23105.35
dn_iptv.value 0
maxdown.value 7716500
"""
