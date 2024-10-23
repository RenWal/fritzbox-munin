#!/usr/bin/env python3
"""
  Unit tests for smart home temperature module
"""

from unittest.mock import MagicMock
import pytest
from fritzbox_smart_home import FritzboxSmartHome


@pytest.mark.parametrize("connection", ["7590-7.57", "7530ax-7.80"], indirect=True)
class TestFritzboxSmartHome:
  def test_config(self, connection: MagicMock, capsys):  # pylint: disable=unused-argument
    sut = FritzboxSmartHome(connection)
    sut.print_config()

    assert capsys.readouterr().out == """multigraph temperatures
graph_title Smart Home temperature
graph_vlabel degrees Celsius
graph_category sensors
graph_scale no
t16.label Lichterkette
t16.type GAUGE
t16.graph LINE
t16.info Temperature [FRITZ!DECT 210], Offset: 0.0°C
multigraph energy
graph_title Smart Home energy consumption
graph_vlabel Wh
graph_category sensors
graph_scale no
graph_period hour
e16.label Lichterkette
e16.type DERIVE
e16.graph LINE
e16.info Energy consumption (Wh) [FRITZ!DECT 210]
multigraph powers
graph_title Smart Home powers
graph_vlabel W
graph_category sensors
graph_scale no
p16.label Lichterkette
p16.type GAUGE
p16.graph LINE
p16.info Power (W) [FRITZ!DECT 210]
multigraph states
graph_title Smart Home switch states
graph_vlabel State
graph_category sensors
graph_scale no
s16.label Lichterkette
s16.type GAUGE
s16.graph LINE
s16.info Switch state [FRITZ!DECT 210]
"""

  def test_smart_home(self, connection: MagicMock, capsys):  # pylint: disable=unused-argument
    sut = FritzboxSmartHome(connection)
    sut.print_stats()

    assert capsys.readouterr().out == """multigraph temperatures
t16.value 7.0
multigraph energy
e16.value 16770
multigraph powers
p16.value 0.0
multigraph states
s16.value 0
"""

  def test_smart_home_empty_devices(self, capsys):  # pylint: disable=unused-argument
    connection = MagicMock()
    connection.get_device_information_list.return_value = {}

    sut = FritzboxSmartHome(connection)
    sut.print_stats()

    assert capsys.readouterr().out == """multigraph temperatures
multigraph energy
multigraph powers
multigraph states
"""