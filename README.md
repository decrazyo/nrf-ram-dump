
# nRF24LU1+ RAM Dumper

This project serves as reverse engineering utility to dump RAM on Nordic Semiconductor nRF24LU1+ chips.
This will replace the bootloader of a proprietary firmware image in order to hijack execution and copy the contents of RAM to flash memory for later analysis.

## Dependencies
- make
- sdcc
- binutils
- srecord
- python

## Hardware

- CrazyRadio PA (with 32k of flash)

## Initialize the submodule

```
git submodule init
git submodule update
```

## Build

```
make
```

## Program Flash

```
python prog/buspirate-flasher/spi-flash.py -p bin/patched.bin
```

## Dump RAM to Flash

```
python tools/dump.py
```

## Read Flash

```
python prog/buspirate-flasher/spi-flash.py -r dump.bin
```
