#!/usr/bin/env python3
"""
  Unit tests for dsl module
"""

from unittest.mock import MagicMock
import os
import unittest
import pytest
from fritzbox_dsl import FritzboxDsl
from fritzbox_interface import FritzboxInterface


@unittest.mock.patch.dict(os.environ, {
  "dsl_modes": "capacity snr damping errors crc INVALID"
})
@pytest.mark.parametrize("fixture_version", ["7590-7.57", "7530ax-7.80"], indirect=True)
@pytest.mark.parametrize("connection", ["7530ax-7.80"], indirect=True)
class TestFritzboxDsl():

  @unittest.mock.patch.dict(os.environ, {
    "dsl_modes": "INVALID"
  })
  def test_config_with_invalid_modes_only(self, connection: MagicMock, fixture_version: str, capsys): # pylint: disable=unused-argument
    dsl = FritzboxDsl(FritzboxInterface(), connection)
    dsl.print_config()

    assert capsys.readouterr().out == ""

  def test_config(self, connection: MagicMock, fixture_version: str, capsys): # pylint: disable=unused-argument
    dsl = FritzboxDsl(FritzboxInterface(), connection)
    dsl.print_config()

    assert capsys.readouterr().out == """multigraph dsl_capacity
graph_title Link Capacity
graph_vlabel bit/s
graph_args --lower-limit 0
graph_category network
recv.label receive
recv.type GAUGE
recv.graph LINE1
recv.min 0
recv.cdef recv,1000,*
send.label send
send.type GAUGE
send.graph LINE1
send.min 0
send.cdef send,1000,*
multigraph dsl_snr
graph_title Signal-to-Noise Ratio
graph_vlabel dB
graph_args --lower-limit 0
graph_category network
recv.label receive
recv.type GAUGE
recv.graph LINE1
recv.min 0
send.label send
send.type GAUGE
send.graph LINE1
send.min 0
multigraph dsl_damping
graph_title Line Loss
graph_vlabel dB
graph_args --lower-limit 0
graph_category network
recv.label receive
recv.type GAUGE
recv.graph LINE1
recv.min 0
send.label send
send.type GAUGE
send.graph LINE1
send.min 0
multigraph dsl_crc
graph_title Checksum Errors
graph_vlabel n
graph_args --lower-limit 0
graph_category network
recv.label receive
recv.type GAUGE
recv.graph LINE1
recv.min 0
send.label send
send.type GAUGE
send.graph LINE1
send.min 0
multigraph dsl_errors
graph_title Transmission Errors
graph_vlabel s
graph_args --lower-limit 0
graph_category network
graph_order es_recv es_send ses_recv ses_send
es_recv.label receive errored
es_recv.type DERIVE
es_recv.graph LINE1
es_recv.min 0
es_recv.warning 1
es_send.label send errored
es_send.type DERIVE
es_send.graph LINE1
es_send.min 0
es_send.warning 1
ses_recv.label receive severely errored
ses_recv.type DERIVE
ses_recv.graph LINE1
ses_recv.min 0
ses_recv.warning 1
ses_send.label send severely errored
ses_send.type DERIVE
ses_send.graph LINE1
ses_send.min 0
ses_send.warning 1
"""

  def test_print_dsl_stats(self, connection: MagicMock, fixture_version: str, capsys): # pylint: disable=unused-argument
    dsl = FritzboxDsl(FritzboxInterface(), connection)
    dsl.print_stats()

    assert capsys.readouterr().out == """multigraph dsl_capacity
recv.value 139083
send.value 47102
multigraph dsl_snr
recv.value 28
send.value 31
multigraph dsl_damping
recv.value 6
send.value 4
multigraph dsl_errors
es_recv.value 0
es_send.value 0
ses_recv.value 0
ses_send.value 0
multigraph dsl_crc
recv.value 0
send.value 0
"""
