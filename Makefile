# Path to a firmware file to patch.
BASE_FIRMWARE = ./fw_updates/RQR12/RQR12.05/RQR12.05_B0028.hex
BOOTLOADER_ADDRESS = 0x7400

SDCC ?= sdcc
CFLAGS = --model-large --std-c99
LDFLAGS = --xram-loc 0x8000 --xram-size 2048 --model-large --code-loc $(BOOTLOADER_ADDRESS)
VPATH = src/
OBJS = bin/main.rel

.PHONY: all
all: bin/ bin/patched.bin

.PHONY: clean
clean:
	rm -f bin/*

bin/:
	mkdir -p bin

# Compile the memory dumper.
bin/%.rel: %.c
	$(SDCC) $(CFLAGS) -c $< -o $@

# Link the memory dumper.
bin/dumper.hex: $(OBJS)
	$(SDCC) $(LDFLAGS) $(OBJS) -o $@

# Replace the bootloader with the memory dumper.
bin/patched.hex: bin/dumper.hex
	srec_cat -disable-sequence-warning $(BASE_FIRMWARE) -Intel -Exclude $(BOOTLOADER_ADDRESS) $< -Intel -o $@ -Intel

# Create a binary that is suitable for flashing.
bin/patched.bin: bin/patched.hex
	objcopy -I ihex $< --gap-fill 255 -O binary $@
