
#include <stdint.h>

#define RAM_DUMP_ADDRESS 0x7800
#define RAM_ADDRESS 0x8000
#define PAGE_SIZE 512
#define RAM_SIZE 2048

// Flash Command Register.
// nRF24LU1+ Product Spec Section 17.3.6
__sfr __at (0xFA) FCR;

// Flash Status Register (FSR).
// nRF24LU1+ Product Spec Section 17.3.6
__sbit __at (0xFD) WEN;  // Bit 5. Write enable.
__sbit __at (0xFC) RDYN; // Bit 4. Flash interface ready.

// Interrupt Enable 0 Register (IEN0).
// nRF24LU1+ Product Spec Section 22.4.1
__sbit __at (0xAF) EA; // Bit 7. Enable interrupts.

inline void enable_write(void) {
    // nRF24LU1+ Product Spec Section 17.5.1
    FCR = 0xAA;
    FCR = 0x55;
    WEN = 1;
}

void erase_page(uint8_t page) {
    // Set page to erase.
    FCR = page;
    // Wait for the write to finish.
    while(RDYN == 1);
}

void write_flash(uint16_t addr, uint8_t data) {
    // Write data.
    uint8_t __xdata* ptr = (uint8_t __xdata*) addr;
    *ptr = data;
    // Wait for the write to finish.
    while(RDYN == 1);
}

void erase_ram_dump(void) {
    // Erase flash where we want to dump RAM.
    for(uint8_t i = 0; i < RAM_SIZE / PAGE_SIZE; i++) {
        erase_page((RAM_DUMP_ADDRESS / PAGE_SIZE) + i);
    }
}

void write_ram_dump(void) {
    // Dump RAM to flash.
    uint8_t* ptr = (uint8_t __xdata*) RAM_ADDRESS;
    for(uint16_t i = 0; i < RAM_SIZE; i++) {
        write_flash(RAM_DUMP_ADDRESS + i, *ptr);
        ptr++;
    }
}

void main(void) {
    // Disable interrupts.
    EA = 0;
    enable_write();
    erase_ram_dump();
    write_ram_dump();
    // Disable writing.
    WEN = 0;
}
