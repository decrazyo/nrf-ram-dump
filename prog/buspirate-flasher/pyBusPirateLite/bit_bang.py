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

import serial
import time
from enum import auto, IntFlag

"""
PICSPEED = 24MHZ / 16MIPS
"""

class BitBang:
    class PinCfg(IntFlag):
        CS = auto()
        AUX = auto()
        PULLUPS = auto()
        POWER = auto()

    class Pins(IntFlag):
        MOSI = auto()
        CLK = auto()
        MISO = auto()
        CS = auto()
        AUX = auto()
        PULLUP = auto()
        POWER = auto()

    def __init__(self, port='/dev/bus_pirate', speed=115200, timeout=1):
        self.port = serial.Serial(port, speed, timeout=timeout)

    def bit_bang_mode(self):
        self.port.reset_input_buffer();

        for i in range(20):
            self.port.write(b'\x00');

            if self.port.in_waiting:
                break;

            time.sleep(0.01)

        return self.expect(b'BBIO1')

    def reset(self):
        self.port.write(b'\x00')
        time.sleep(0.1)

    def enter_spi(self):
        self.port.read(5)
        self.port.write(b'\x01')
        time.sleep(0.1)
        return self.expect(b'SPI1')

    def enter_i2c(self):
        self.port.write(b'\x02')
        time.sleep(0.1)
        return self.expect(b'I2C1')

    def enter_uart(self):
        self.port.write(b'\x03')
        time.sleep(0.1)
        return self.expect(b'ART1')

    def enter_1wire(self):
        self.port.write(b'\x04')
        time.sleep(0.1)
        return self.expect(b'1W01')

    def enter_rawwire(self):
        self.port.write(b'\x05')
        time.sleep(0.1)
        return self.expect(b'RAW1')

    def reset_bus_pirate(self):
        self.reset()
        self.port.write(b'\x0F')
        time.sleep(0.1)
        self.port.reset_input_buffer()

    def raw_cfg_pins(self, config):
        self.port.write((0x40 | config).to_bytes())
        time.sleep(0.1)
        return self.expect(b'\x01')

    def raw_set_pins(self, pins):
        self.port.write((0x80 | config).to_bytes())
        time.sleep(0.1)
        return self.expect(b'\x01')

    def expect(self, data):
        return self.port.read(len(data)) == data

    """ Self-Test """
    def short_selftest(self):
        self.port.write(b'\x10')
        time.sleep(0.1)
        return self.port.read(1)

    def long_selftest(self):
        self.port.write(b'\x11')
        time.sleep(0.1)
        return self.port.read(1)

    """ PWM """
    def setup_pwm(self, prescaler, dutycycle, period):
        self.port.write(b'\x12')
        self.port.write(prescaler.to_bytes())
        self.port.write(((dutycycle>>8)&0xFF).to_bytes())
        self.port.write((dutycycle&0xFF).to_bytes())
        self.port.write(((period>>8)&0xFF).to_bytes())
        self.port.write((period&0xFF).to_bytes())
        time.sleep(0.1)
        return self.expect(b'\x01')

    def clear_pwm(self):
        self.port.write(b'\x13')
        time.sleep(0.1)
        return self.expect(b'\x01')

    """ ADC """
    def adc_measure(self):
        self.port.write(b'\x14')
        time.sleep(0.1)
        return self.port.read(2)

    """ General Commands for Higher-Level Modes """
    def mode_string(self):
        self.port.write(b'\x01')
        time.sleep(0.1)
        return self.expect(b'\x01')

    def bulk_trans(self, byte_count=1, byte_string=None):
        if byte_string == None: pass
        self.port.write((0x10 | (byte_count-1)).to_bytes())
        for i in range(byte_count):
            self.port.write((byte_string[i]).to_bytes())
        data = self.port.read(byte_count+1)
        return data[1:]

    def cfg_pins(self, pins=0):
        self.port.write((0x40 | pins).to_bytes())
        time.sleep(0.1)
        return self.expect(b'\x01')

    def read_pins(self):
        self.port.write(b'\x50')
        time.sleep(0.1)
        return self.port.read(1)

    def set_speed(self, spi_speed=0):
        self.port.write((0x60 | spi_speed).to_bytes())
        time.sleep(0.1)
        return self.expect(b'\x01')

    def read_speed(self):
        self.port.write(b'\x70')
        time.sleep(0.1)
        return self.port.read(1)

