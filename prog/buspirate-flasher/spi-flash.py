#/usr/bin/env python3

# this script is an improved implementation of the crazyradio recovery flasher.
# https://github.com/koolatron/buspirate_nrf24lu1p/blob/master/flasher.pl

import argparse
import time
from enum import auto, IntEnum, IntFlag
from pyBusPirateLite.spi import SPI

class Nrf24(SPI):
    class Cmd(IntEnum):
        WRSR = auto()
        PROGRAM = auto()
        READ = auto()
        WRDIS = auto()
        RDSR = auto()
        WREN = auto()
        ERASE_PAGE = 0x52
        ERASE_ALL = 0x62
        RDISIP = 0x84
        RDISMB = auto()
        ENDEBUG = auto()
        RDFPCR = 0x89

    class FSR(IntFlag):
        RDISIP = 0x02
        RDISMB = auto()
        INFEN = auto()
        RDYN = auto()
        WEN = auto()
        STP = auto()
        DBG = auto()

    PAGE_SIZE = 512
    WRITE_SIZE = 256

    # Bus Pirate    CrazyRadio
    # ========================
    # MOSI (8)   -> MOSI  (6)
    # MISO (10)  -> MISO  (8)
    # SCK  (7)   -> SCK   (4)
    # CS   (9)   -> CS    (10)
    # AUX  (6)   -> PROG  (2)
    # 3V3  (2)   -> 3V3   (5)
    # GND  (1)   -> GND   (9)

    # Clock polarity idle low (default)
    # Clock edge active to idle (default)
    # Sample phase middle (default)
    # CS active low (default)
    # Output type High = 3.3v

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bit_bang_mode()
        self.enter_spi()

        # Enable necessary pins.
        self.cfg_pins(Nrf24.PinCfg.CS | Nrf24.PinCfg.AUX | Nrf24.PinCfg.POWER)

        # TODO: Fix read failures at speeds above 250khz.
        self.set_speed(Nrf24.Speed._250KHZ)
        self.cfg_spi(Nrf24.Cfg.CLK_EDGE | Nrf24.Cfg.OUT_TYPE)

        # We have to wait at least 1.5ms after setting AUX/PROG high.
        time.sleep(0.0015)

    def wait_write(self):
        # Wait for a write operation to complete.
        while True:
            status = self.read_flash_status()
            if not (status[0] & Nrf24.FSR.RDYN):
                break

    def transfer(self, data):
        # We can only send 16 bytes at a time.
        count = len(data)

        if not self.bulk_transfer(count):
            raise RuntimeError('failed to start bulk transfer')

        self.port.write(data)
        return self.port.read(count)

    def write_enable(self):
        self.cs_low()
        self.transfer(Nrf24.Cmd.WREN.to_bytes())
        self.cs_high()
        status = self.read_flash_status()
        if not status[0] & Nrf24.FSR.WEN:
            raise RuntimeError('failed to enable writing')

    def write_disable(self):
        self.cs_low()
        self.transfer(Nrf24.Cmd.WRDIS.to_bytes())
        self.cs_high()
        status = self.read_flash_status()
        if status[0] & Nrf24.FSR.WEN:
            raise RuntimeError('failed to disable writing')

    def read_flash_status(self):
        self.cs_low()
        status = self.transfer(Nrf24.Cmd.RDSR.to_bytes() + b'\x00')
        self.cs_high()
        return status[-1:]

    def write_flash_status(self, data):
        self.cs_low()
        status = self.transfer(Nrf24.Cmd.WRSR.to_bytes() + data)
        self.cs_high()

    def read_flash(self, count=1, addr=0):
        data = b''

        for _ in range(0, count, Nrf24.WRITE_SIZE):
            print(hex(addr))
            buf = Nrf24.Cmd.READ.to_bytes()
            buf += addr.to_bytes(2)
            addr += Nrf24.WRITE_SIZE
            data += self.write_then_read(buf, Nrf24.WRITE_SIZE)

        return data[0:count]

    def write_flash(self, data, addr=0):
        for i in range(0, len(data), Nrf24.WRITE_SIZE):
            print(hex(addr))
            buf = Nrf24.Cmd.PROGRAM.to_bytes()
            buf += addr.to_bytes(2)
            addr += Nrf24.WRITE_SIZE
            chunk = data[i:i + Nrf24.WRITE_SIZE]

            # Skip writes that only contain '\xFF' since it won't effect flash.
            if all(x == b'\xFF' for x in chunk):
                continue

            buf += chunk
            self.write_enable()
            self.write_then_read(buf, 0)
            self.wait_write()

    def erase_page(self, page=0):
        self.write_enable()
        self.cs_low()
        self.transfer(Nrf24.Cmd.ERASE_PAGE.to_bytes() + page.to_bytes())
        self.cs_high()
        self.wait_write()

    def erase_all(self):
        self.write_enable()
        self.cs_low()
        self.transfer(Nrf24.Cmd.ERASE_ALL.to_bytes())
        self.cs_high()
        self.wait_write()

def read(nrf24, start, length, file):
    if not length:
        # The chip only has 32k of flash.
        length = (1024 * 32) - start

    print('reading')
    data = nrf24.read_flash(length, start)

    with open(file, 'wb') as f:
        f.write(data)

def erase(nrf24, start, length):
    if start == 0 and length == 0:
        print('erasing all')
        nrf24.erase_all()
    else:
        print('erasing')
        if length == 0:
            # erase all following pages
            length = 64 - start

        for i in range(start, start + length):
            print(hex(i))
            nrf24.erase_page(i)

def write(nrf24, start, length, file):
    with open(file, 'rb') as f:
        data = f.read(length if length else None)

    print('writing')
    nrf24.write_flash(data, start)

def verify(nrf24, start, length, file):
    with open(file, 'rb') as f:
        file = f.read(length if length else None)

    print('reading')
    flash = nrf24.read_flash(len(file), start)

    print('validating')
    if file == flash:
        print('file/flash match')
    else:
        print('file/flash mismatch')
        print('byte\tfile\tflash')
        for i in range(len(file)):
            if file[i] != flash[i]:
                print('{}\t{}\t{}', hex(i), hex(file[i]), hex(flash[i]))

def program(nrf24, start, length, file):
    erase(nrf24, start, length)
    write(nrf24, start, length, file)
    verify(nrf24, start, length, file)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--device',
        default='/dev/bus_pirate',
        help='bus pirate device path or COM port (default: %(default)s)')
    parser.add_argument('-b', '--baud',
        default=115200,
        type=int,
        help='bus pirate baud rate (default: %(default)s)')
    parser.add_argument('-s', '--start',
        default=0,
        type=lambda x: int(x, base=0),
        help=('address to start reading/writing or page to start erasing. '
            '(default: %(default)s)'))
    parser.add_argument('-l', '--length',
        default=0,
        type=lambda x: int(x, base=0),
        help=('number of bytes to read/write or number of pages to erase. '
            '0 for all following. (default: %(default)s)'))

    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('-r', '--read',
        help='read flash to a file')
    mode.add_argument('-e', '--erase',
        action='store_true',
        help='erase flash')
    mode.add_argument('-w', '--write',
        help='write a file to flash')
    mode.add_argument('-v', '--verify',
        help='compare the contents of flash to a file')
    mode.add_argument('-p', '--program',
        help='erase all, flash, and verify')


    args = parser.parse_args()

    nrf24 = Nrf24(args.device, args.baud)

    try:
        if args.read:
            read(nrf24, args.start, args.length, args.read)
        elif args.erase:
            erase(nrf24, args.start, args.length)
        elif args.write:
            write(nrf24, args.start, args.length, args.write)
        elif args.verify:
            verify(nrf24, args.start, args.length, args.verify)
        elif args.program:
            program(nrf24, args.start, args.length, args.program)
        else:
            pass
    finally:
        nrf24.reset_bus_pirate()

if __name__ == '__main__':
    main()
