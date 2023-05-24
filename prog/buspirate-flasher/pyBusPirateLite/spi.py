#!/usr/bin/env python
# encoding: utf-8
"""
Created by Sean Nelson on 2009-10-14.
Copyright 2009 Sean Nelson <audiohacked@gmail.com>

This file is part of pyBusPirate.

pyBusPirate is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

pyBusPirate is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with pyBusPirate.  If not, see <http://www.gnu.org/licenses/>.
"""

import time
from enum import auto, IntFlag, IntEnum
from . import bit_bang


class SPI(bit_bang.BitBang):
    class Speed(IntEnum):
        _30KHZ = 0
        _125KHZ = auto()
        _250KHZ = auto()
        _1MHZ = auto()
        _2MHZ = auto()
        _2_6MHZ = auto()
        _4MHZ = auto()
        _8MHZ = auto()

    class Cfg(IntFlag):
        SAMPLE = auto()
        CLK_EDGE = auto()
        IDLE = auto()
        OUT_TYPE = auto()

    class OutType(IntEnum):
        HIZ = 0
        _3V3 = auto()

    bulk_read = None

    def cs_low(self):
        self.port.write(b'\x02')
        return self.expect(b'\x01')

    def cs_high(self):
        self.port.write(b'\x03')
        return self.expect(b'\x01')

    def write_then_read(self, write_data, read_len, no_cs=False):
        buf = b'\x05' if no_cs else b'\x04'
        buf += len(write_data).to_bytes(2)
        buf += read_len.to_bytes(2)
        buf += write_data
        self.port.write(buf)
        if not self.expect(b'\x01'):
            return b''
        return self.port.read(read_len)

    def bulk_transfer(self, nibble):
        nibble = ((nibble-1)&0x0F)
        self.port.write((0x10 | nibble).to_bytes())
        return self.expect(b'\x01')

    def low_nibble(self, nibble):
        self.port.write((0x20 | nibble).to_bytes())
        return self.port.read(1)

    def high_nibble(self, nibble):
        self.port.write((0x30 | nibble).to_bytes())
        return self.port.read(1)

    def cfg_spi(self, spi_cfg):
        self.port.write((0x80 | spi_cfg).to_bytes())
        return self.expect(b'\x01')

    def read_spi_cfg(self):
        self.port.write(b'\x90')
        return self.port.read(1)

