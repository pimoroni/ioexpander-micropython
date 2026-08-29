"""A fake IO Expander on the far end of a fake i2c bus."""

REG_P0 = 0x40
REG_P1 = 0x50
REG_P2 = 0x60
REG_P3 = 0x70
BIT_ADDRESSED = (REG_P0, REG_P1, REG_P2, REG_P3)

REG_ADCCON0 = 0xA8
REG_ADCRL = 0x82
REG_ADCRH = 0x83
REG_PWMCON0 = 0x98
REG_USER_FLASH = 0xD0
REG_CHIP_ID_L = 0xFA
REG_CHIP_ID_H = 0xFB
REG_ENC_COUNT = (0x06, 0x08, 0x0A, 0x0C)


class FakeIOE:
    def __init__(self, chip_id=0xE26A):
        self.registers = bytearray(256)
        self.registers[REG_CHIP_ID_L] = chip_id & 0xFF
        self.registers[REG_CHIP_ID_H] = chip_id >> 8
        self.registers[REG_USER_FLASH] = 0x78
        self.adc_value = 0
        self.writes = []

    def readfrom_mem(self, address, register, length):
        return bytes(self.registers[register:register + length])

    def writeto_mem(self, address, register, buf):
        self.writes.append((register, bytes(buf)))

        if register in BIT_ADDRESSED and len(buf) == 1:
            # Port registers are bit addressed: 0b1000 | bit sets, bit alone clears
            bit = buf[0] & 0b111
            if buf[0] & 0b1000:
                self.registers[register] |= 1 << bit
            else:
                self.registers[register] &= ~(1 << bit)
            return

        for offset, value in enumerate(buf):
            self.registers[register + offset] = value

        if register == REG_PWMCON0:
            self.registers[REG_PWMCON0] &= ~(1 << 6)  # The load bit self clears
            self.registers[REG_PWMCON0] &= ~(1 << 4)  # As does the clear bit

        if register == REG_ADCCON0 and buf[0] & (1 << 6):
            # Starting a conversion completes it, and latches the result
            self.registers[REG_ADCCON0] |= 1 << 7
            self.registers[REG_ADCRH] = (self.adc_value >> 4) & 0xFF
            self.registers[REG_ADCRL] = self.adc_value & 0x0F

    def set_encoder_count(self, channel, count):
        self.registers[REG_ENC_COUNT[channel - 1]] = count & 0xFF

    def set_port_bit(self, register, bit, state):
        if state:
            self.registers[register] |= 1 << bit
        else:
            self.registers[register] &= ~(1 << bit)

    def written_to(self, register):
        return [value for reg, value in self.writes if reg == register]
