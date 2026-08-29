import time

from micropython import const

__version__ = "0.0.1"

DEFAULT_ADDRESS = const(0x18)

CHIP_ID = const(0xE26A)
CHIP_VERSION = const(2)

NUM_PINS = const(14)

LOW = const(0)
HIGH = const(1)

# The PxM1 and PxM2 registers encode the GPIO mode as two bits:
# 00 quasi-bidirectional, 01 push-pull, 10 input-only, 11 open-drain.
# Bits 2 and 3 select IO, PWM or ADC. Bit 4 is the initial output state.
PIN_MODE_IO = const(0b00000)
PIN_MODE_QB = const(0b00000)
PIN_MODE_PP = const(0b00001)
PIN_MODE_IN = const(0b00010)
PIN_MODE_PU = const(0b10000)
PIN_MODE_OD = const(0b00011)
PIN_MODE_PWM = const(0b00101)
PIN_MODE_ADC = const(0b01010)

IN = PIN_MODE_IN
IN_PULL_UP = PIN_MODE_PU
IN_PU = PIN_MODE_PU
OUT = PIN_MODE_PP
OD = PIN_MODE_OD
PWM = PIN_MODE_PWM
ADC = PIN_MODE_ADC

TYPE_IO = const(0b00)
TYPE_PWM = const(0b01)
TYPE_ADC = const(0b10)
TYPE_ADC_OR_PWM = const(0b11)

CLOCK_FREQ = const(24000000)
MAX_PERIOD = const((1 << 16) - 1)
MAX_DIVIDER = const(1 << 7)

REG_INT_MASK_P0 = const(0x00)
REG_INT_MASK_P1 = const(0x01)
REG_INT_MASK_P3 = const(0x03)

REG_ENC_EN = const(0x04)
REG_ENC_CFG = (0x05, 0x07, 0x09, 0x0B)
REG_ENC_COUNT = (0x06, 0x08, 0x0A, 0x0C)

REG_P0 = const(0x40)
REG_P1 = const(0x50)
REG_P2 = const(0x60)
REG_P3 = const(0x70)

REG_P3M1 = const(0x6C)
REG_P3M2 = const(0x6D)
REG_P0M1 = const(0x71)
REG_P0M2 = const(0x72)
REG_P1M1 = const(0x73)
REG_P1M2 = const(0x74)

# Page 1 registers, reassigned to avoid collisions
REG_P3S = const(0xC0)
REG_P0S = const(0xC2)
REG_P1S = const(0xC4)
REG_PWM4H = const(0xC7)
REG_PWM5H = const(0xC8)
REG_PIOCON1 = const(0xC9)
REG_PWM4L = const(0xCA)
REG_PWM5L = const(0xCB)

REG_ADCRL = const(0x82)
REG_ADCRH = const(0x83)
REG_ADCCON1 = const(0xA1)
REG_ADCCON0 = const(0xA8)
REG_AINDIDS = const(0xB6)

REG_PWMPH = const(0x91)
REG_PWMPL = const(0x99)
REG_PWMCON0 = const(0x98)
REG_PWMCON1 = const(0x9F)
REG_PNP = const(0x96)
REG_PIOCON0 = const(0x9E)

REG_USER_FLASH = const(0xD0)
REG_INT = const(0xF9)
REG_CHIP_ID_L = const(0xFA)
REG_CHIP_ID_H = const(0xFB)
REG_VERSION = const(0xFC)
REG_ADDR = const(0xFD)
REG_CTRL = const(0xFE)

BIT_INT_TRIGD = const(0)
BIT_INT_OUT_EN = const(1)
BIT_INT_PIN_SWAP = const(2)

MASK_CTRL_SLEEP = const(0x01)
MASK_CTRL_RESET = const(0x02)
MASK_CTRL_FREAD = const(0x04)
MASK_CTRL_FWRITE = const(0x08)
MASK_CTRL_ADDRWR = const(0x10)

BIT_ADDRESSED_REGS = (REG_P0, REG_P1, REG_P2, REG_P3)

RESET_TIMEOUT = 1.0
RESET_COMPLETE = const(0x78)

_PXM1 = (REG_P0M1, REG_P1M1, None, REG_P3M1)
_PXM2 = (REG_P0M2, REG_P1M2, None, REG_P3M2)
_PX = (REG_P0, REG_P1, None, REG_P3)
_PXS = (REG_P0S, REG_P1S, None, REG_P3S)
_MASK_P = (REG_INT_MASK_P0, REG_INT_MASK_P1, None, REG_INT_MASK_P3)

_PWML = (0x9A, 0x9B, 0x9C, 0x9D, REG_PWM4L, REG_PWM5L)
_PWMH = (0x92, 0x93, 0x94, 0x95, REG_PWM4H, REG_PWM5H)

# type, port, pin, adc channel, pwm channel, PIOCON register
_PIN_TABLE = (
    (TYPE_PWM, 1, 5, 0, 5, REG_PIOCON1),
    (TYPE_PWM, 1, 0, 0, 2, REG_PIOCON0),
    (TYPE_PWM, 1, 2, 0, 0, REG_PIOCON0),
    (TYPE_PWM, 1, 4, 0, 1, REG_PIOCON1),
    (TYPE_PWM, 0, 0, 0, 3, REG_PIOCON0),
    (TYPE_PWM, 0, 1, 0, 4, REG_PIOCON0),
    (TYPE_ADC_OR_PWM, 1, 1, 7, 1, REG_PIOCON0),
    (TYPE_ADC_OR_PWM, 0, 3, 6, 5, REG_PIOCON0),
    (TYPE_ADC_OR_PWM, 0, 4, 5, 3, REG_PIOCON1),
    (TYPE_ADC, 3, 0, 1, 0, 0),
    (TYPE_ADC, 0, 6, 3, 0, 0),
    (TYPE_ADC_OR_PWM, 0, 5, 4, 2, REG_PIOCON1),
    (TYPE_ADC, 0, 7, 2, 0, 0),
    (TYPE_ADC, 1, 7, 0, 0, 0),
)

PWM_DIVIDERS = {1: 0b000, 2: 0b001, 4: 0b010, 8: 0b011, 16: 0b100, 32: 0b101, 64: 0b110, 128: 0b111}


class _Pin:
    def __init__(self, type, port, pin, adc_channel, pwm_channel, reg_io_pwm):
        self.type = type
        self.mode = 0
        self.port = port
        self.pin = pin
        self.adc_channel = adc_channel
        self.pwm_channel = pwm_channel
        self.reg_io_pwm = reg_io_pwm
        self.reg_m1 = _PXM1[port]
        self.reg_m2 = _PXM2[port]
        self.reg_p = _PX[port]
        self.reg_ps = _PXS[port]
        self.reg_int_mask_p = _MASK_P[port]
        self.reg_pwml = _PWML[pwm_channel]
        self.reg_pwmh = _PWMH[pwm_channel]

    def mode_supported(self, mode):
        if mode == PIN_MODE_PWM:
            return bool(self.type & TYPE_PWM)
        if mode == PIN_MODE_ADC:
            return bool(self.type & TYPE_ADC)
        return True


class IOExpander:
    def __init__(self, i2c, address=DEFAULT_ADDRESS, interrupt=None, timeout=1.0, skip_chip_id_check=False, perform_reset=False):
        """Initialise the IO Expander.

        :param i2c: an initialised machine.I2C instance
        :param address: i2c address of the expander
        :param interrupt: optional interrupt pin, a machine.Pin already set up as an input
        :param timeout: seconds to wait for PWM loads and ADC conversions
        :param skip_chip_id_check: skip the chip ID check, for a board that reports incorrectly
        :param perform_reset: reset the expander to a known state on startup

        """
        self.i2c = i2c
        self.address = address
        self.interrupt = interrupt
        self.timeout = timeout
        self.vref = 3.3

        self._encoder_offset = [0, 0, 0, 0]
        self._encoder_last = [0, 0, 0, 0]

        self.pins = [_Pin(*entry) for entry in _PIN_TABLE]

        if not skip_chip_id_check:
            chip_id = self.get_chip_id()
            if chip_id != CHIP_ID:
                raise RuntimeError(f"IOExpander: invalid chip ID 0x{chip_id:04x}, expected 0x{CHIP_ID:04x}")

        if perform_reset:
            self.reset()

        if self.interrupt is not None:
            self.enable_interrupt_out(True)

    def _read_u8(self, register):
        return self.i2c.readfrom_mem(self.address, register, 1)[0]

    def _write_u8(self, register, value):
        self.i2c.writeto_mem(self.address, register, bytes([value & 0xFF]))

    def get_bit(self, register, bit):
        """Return the value of one bit of a register.

        :param register: register address
        :param bit: bit position from the right

        """
        return self._read_u8(register) & (1 << bit)

    def set_bits(self, register, bits):
        """Set the given bits of a register.

        :param register: register address
        :param bits: mask of bits to set

        """
        if register in BIT_ADDRESSED_REGS:
            # The port registers are bit addressed, so that setting one pin does
            # not write the whole port and smash the i2c pins
            for bit in range(8):
                if bits & (1 << bit):
                    self._write_u8(register, 0b1000 | (bit & 0b111))
                    time.sleep_us(50)
            return

        value = self._read_u8(register)
        time.sleep_us(50)
        self._write_u8(register, value | bits)

    def set_bit(self, register, bit):
        """Set one bit of a register.

        :param register: register address
        :param bit: bit position from the right

        """
        self.set_bits(register, 1 << bit)

    def clr_bits(self, register, bits):
        """Clear the given bits of a register.

        :param register: register address
        :param bits: mask of bits to clear

        """
        if register in BIT_ADDRESSED_REGS:
            for bit in range(8):
                if bits & (1 << bit):
                    self._write_u8(register, bit & 0b111)
                    time.sleep_us(50)
            return

        value = self._read_u8(register)
        time.sleep_us(50)
        self._write_u8(register, value & ~bits)

    def clr_bit(self, register, bit):
        """Clear one bit of a register.

        :param register: register address
        :param bit: bit position from the right

        """
        self.clr_bits(register, 1 << bit)

    def change_bit(self, register, bit, state):
        """Set or clear one bit of a register.

        :param register: register address
        :param bit: bit position from the right
        :param state: True to set, False to clear

        """
        if state:
            self.set_bit(register, bit)
        else:
            self.clr_bit(register, bit)

    def get_chip_id(self):
        """Return the chip ID, which should be 0xE26A."""
        return (self._read_u8(REG_CHIP_ID_H) << 8) | self._read_u8(REG_CHIP_ID_L)

    def get_version(self):
        """Return the firmware version."""
        return self._read_u8(REG_VERSION)

    def _check_reset(self):
        try:
            return self._read_u8(REG_USER_FLASH)
        except OSError:
            return 0x00

    def reset(self):
        """Reset the expander and wait for it to come back."""
        self.set_bits(REG_CTRL, MASK_CTRL_RESET)

        deadline = time.ticks_add(time.ticks_ms(), int(RESET_TIMEOUT * 1000))
        while self._check_reset() != RESET_COMPLETE:
            if time.ticks_diff(deadline, time.ticks_ms()) < 0:
                raise RuntimeError("IOExpander: timed out waiting for reset")
            time.sleep_ms(1)

    def set_address(self, address):
        """Write a new i2c address into the expander's flash.

        :param address: the address to store

        """
        self.set_bit(REG_CTRL, 4)
        self._write_u8(REG_ADDR, address)
        self.address = address
        time.sleep_ms(250)
        self.clr_bit(REG_CTRL, 4)

    def get_adc_vref(self):
        """Return the ADC reference voltage."""
        return self.vref

    def set_adc_vref(self, vref):
        """Set the ADC reference voltage, used to scale voltage readings.

        :param vref: reference voltage in volts

        """
        self.vref = vref

    def enable_interrupt_out(self, pin_swap=False):
        """Drive the interrupt pin when an enabled input changes.

        :param pin_swap: False for the interrupt on P1.3, True for P0.0

        """
        self.set_bit(REG_INT, BIT_INT_OUT_EN)
        self.change_bit(REG_INT, BIT_INT_PIN_SWAP, pin_swap)

    def disable_interrupt_out(self):
        """Stop driving the interrupt pin."""
        self.clr_bit(REG_INT, BIT_INT_OUT_EN)

    def get_interrupt_flag(self):
        """Return True if an interrupt is pending."""
        if self.interrupt is not None:
            return self.interrupt.value() == 0
        return self.get_bit(REG_INT, BIT_INT_TRIGD) != 0

    def clear_interrupt_flag(self):
        """Clear a pending interrupt."""
        self.clr_bit(REG_INT, BIT_INT_TRIGD)

    def set_pin_interrupt(self, pin, enabled):
        """Enable or disable the interrupt for one pin.

        :param pin: pin number, 1 to 14
        :param enabled: True to interrupt on a change, False to ignore it

        """
        io_pin = self._get_pin(pin)
        self.change_bit(io_pin.reg_int_mask_p, io_pin.pin, enabled)

    def _get_pin(self, pin):
        if pin < 1 or pin > NUM_PINS:
            raise ValueError(f"IOExpander: pin should be in range 1-{NUM_PINS}")
        return self.pins[pin - 1]

    def pwm_load(self, wait_for_load=True):
        """Load the buffered PWM period and duty registers.

        :param wait_for_load: block until the load completes

        """
        self.set_bit(REG_PWMCON0, 6)

        if not wait_for_load:
            return

        deadline = time.ticks_add(time.ticks_ms(), int(self.timeout * 1000))
        while self.pwm_loading():
            if time.ticks_diff(deadline, time.ticks_ms()) < 0:
                raise RuntimeError("IOExpander: timed out waiting for PWM load")
            time.sleep_ms(1)

    def pwm_loading(self):
        """Return True if a PWM load is in progress."""
        return self.get_bit(REG_PWMCON0, 6) != 0

    def pwm_clear(self, wait_for_clear=True):
        """Clear the PWM counter.

        :param wait_for_clear: block until the clear completes

        """
        self.set_bit(REG_PWMCON0, 4)

        if not wait_for_clear:
            return

        deadline = time.ticks_add(time.ticks_ms(), int(self.timeout * 1000))
        while self.pwm_clearing():
            if time.ticks_diff(deadline, time.ticks_ms()) < 0:
                raise RuntimeError("IOExpander: timed out waiting for PWM clear")
            time.sleep_ms(1)

    def pwm_clearing(self):
        """Return True if a PWM clear is in progress."""
        return self.get_bit(REG_PWMCON0, 4) != 0

    def set_pwm_control(self, divider):
        """Set the PWM clock divider.

        :param divider: one of 1, 2, 4, 8, 16, 32, 64 or 128

        """
        try:
            pwmdiv2 = PWM_DIVIDERS[divider]
        except KeyError:
            raise ValueError(f"IOExpander: divider must be one of {tuple(PWM_DIVIDERS)}") from None

        # This also sets GP, PWMTYP and FBINEN to 0
        self._write_u8(REG_PWMCON1, pwmdiv2)

    def set_pwm_period(self, value, load=True, wait_for_load=True):
        """Set the PWM period, which is the number of steps in a cycle.

        :param value: period in clock cycles, 0 to 65535
        :param load: load the new period immediately
        :param wait_for_load: block until the load completes

        """
        value &= 0xFFFF
        self._write_u8(REG_PWMPL, value & 0xFF)
        self._write_u8(REG_PWMPH, value >> 8)

        if load:
            self.pwm_load(wait_for_load)

    def set_pwm_frequency(self, frequency, load=True, wait_for_load=True):
        """Set the PWM frequency, picking a divider and period to suit.

        Returns the period that was set, which along with the divider determines
        how many steps of resolution the duty cycle has.

        :param frequency: frequency in Hz
        :param load: load the new period immediately
        :param wait_for_load: block until the load completes

        """
        period = int(CLOCK_FREQ / frequency)
        if period // 128 > MAX_PERIOD:
            return MAX_PERIOD
        if period < 2:
            return 2

        divider = 1
        while period > MAX_PERIOD and divider < MAX_DIVIDER:
            period >>= 1
            divider <<= 1

        period = min(period, MAX_PERIOD)
        self.set_pwm_control(divider)
        self.set_pwm_period(period - 1, load, wait_for_load)

        return period

    def get_mode(self, pin):
        """Return the mode of a pin.

        :param pin: pin number, 1 to 14

        """
        return self._get_pin(pin).mode

    def set_mode(self, pin, mode, schmitt_trigger=False, invert=False):
        """Set the mode of a pin.

        :param pin: pin number, 1 to 14
        :param mode: one of IN, IN_PU, OUT, OD, PWM or ADC
        :param schmitt_trigger: enable the Schmitt trigger, inputs only
        :param invert: invert the PWM output, for a common anode LED

        """
        io_pin = self._get_pin(pin)

        gpio_mode = mode & 0b11
        io_type = (mode >> 2) & 0b11
        initial_state = mode >> 4

        if io_pin.mode == mode:
            return

        if io_type != TYPE_IO and not io_pin.mode_supported(mode):
            raise ValueError(f"IOExpander: pin {pin} does not support this mode")

        io_pin.mode = mode

        if mode == PIN_MODE_PWM:
            self.set_bit(io_pin.reg_io_pwm, io_pin.pwm_channel)
            self.change_bit(REG_PNP, io_pin.pwm_channel, invert)
            self.set_bit(REG_PWMCON0, 7)  # PWMRUN
        elif io_pin.type & TYPE_PWM:
            self.clr_bit(io_pin.reg_io_pwm, io_pin.pwm_channel)

        pm1 = self._read_u8(io_pin.reg_m1) & ~(1 << io_pin.pin)
        pm2 = self._read_u8(io_pin.reg_m2) & ~(1 << io_pin.pin)

        pm1 |= (gpio_mode >> 1) << io_pin.pin
        pm2 |= (gpio_mode & 0b1) << io_pin.pin

        self._write_u8(io_pin.reg_m1, pm1)
        self._write_u8(io_pin.reg_m2, pm2)

        if mode in (PIN_MODE_PU, PIN_MODE_IN):
            self.change_bit(io_pin.reg_ps, io_pin.pin, schmitt_trigger)

        # Bit 5 of the mode encodes the default output state
        self._write_u8(io_pin.reg_p, (initial_state << 3) | io_pin.pin)

    def _read_adc(self, io_pin, adc_timeout):
        self.clr_bits(REG_ADCCON0, 0x0F)
        self.set_bits(REG_ADCCON0, io_pin.adc_channel)
        self._write_u8(REG_AINDIDS, 0)
        self.set_bit(REG_AINDIDS, io_pin.adc_channel)
        self.set_bit(REG_ADCCON1, 0)

        self.clr_bit(REG_ADCCON0, 7)  # ADCF, the conversion complete flag
        self.set_bit(REG_ADCCON0, 6)  # ADCS, the conversion start flag

        deadline = time.ticks_add(time.ticks_ms(), int(adc_timeout * 1000))
        while not self.get_bit(REG_ADCCON0, 7):
            if time.ticks_diff(deadline, time.ticks_ms()) < 0:
                raise RuntimeError("IOExpander: timed out waiting for ADC conversion")
            time.sleep_ms(1)

        return (self._read_u8(REG_ADCRH) << 4) | self._read_u8(REG_ADCRL)

    def input(self, pin, adc_timeout=1.0):
        """Read a pin, as a 12-bit ADC count or a digital 0 or 1.

        :param pin: pin number, 1 to 14
        :param adc_timeout: seconds to wait for an ADC conversion

        """
        io_pin = self._get_pin(pin)

        if io_pin.mode == PIN_MODE_ADC:
            return self._read_adc(io_pin, adc_timeout)

        return 1 if self.get_bit(io_pin.reg_p, io_pin.pin) else 0

    def input_as_voltage(self, pin, adc_timeout=1.0):
        """Read a pin as a voltage, scaled against the ADC reference.

        :param pin: pin number, 1 to 14
        :param adc_timeout: seconds to wait for an ADC conversion

        """
        io_pin = self._get_pin(pin)

        if io_pin.mode == PIN_MODE_ADC:
            return (self._read_adc(io_pin, adc_timeout) / 4095.0) * self.vref

        return self.vref if self.get_bit(io_pin.reg_p, io_pin.pin) else 0.0

    def output(self, pin, value, load=True, wait_for_load=True):
        """Write to a pin, as a PWM duty cycle or a digital LOW or HIGH.

        :param pin: pin number, 1 to 14
        :param value: PWM duty in clock cycles, or LOW or HIGH
        :param load: load a new PWM duty immediately
        :param wait_for_load: block until the load completes

        """
        io_pin = self._get_pin(pin)

        if io_pin.mode == PIN_MODE_PWM:
            self._write_u8(io_pin.reg_pwml, value & 0xFF)
            self._write_u8(io_pin.reg_pwmh, value >> 8)
            if load:
                self.pwm_load(wait_for_load)
        elif value == LOW:
            self.clr_bit(io_pin.reg_p, io_pin.pin)
        elif value == HIGH:
            self.set_bit(io_pin.reg_p, io_pin.pin)

    def setup_rotary_encoder(self, channel, pin_a, pin_b, pin_c=None, count_microsteps=False):
        """Set up a rotary encoder on one of the four encoder channels.

        :param channel: encoder channel, 1 to 4
        :param pin_a: pin number of the encoder's A terminal
        :param pin_b: pin number of the encoder's B terminal
        :param pin_c: pin number of the encoder's common terminal, if it is wired to a pin
        :param count_microsteps: count every state change rather than every detent

        """
        if channel < 1 or channel > 4:
            raise ValueError("IOExpander: channel should be in range 1-4")
        channel -= 1

        self.set_mode(pin_a, PIN_MODE_PU, schmitt_trigger=True)
        self.set_mode(pin_b, PIN_MODE_PU, schmitt_trigger=True)

        if pin_c is not None:
            self.set_mode(pin_c, PIN_MODE_OD)
            self.output(pin_c, LOW)

        self._write_u8(REG_ENC_CFG[channel], pin_a | (pin_b << 4))
        self.change_bit(REG_ENC_EN, (channel * 2) + 1, count_microsteps)
        self.set_bit(REG_ENC_EN, channel * 2)

        self._write_u8(REG_ENC_COUNT[channel], 0x00)

    def read_rotary_encoder(self, channel):
        """Return the accumulated count of a rotary encoder channel.

        The expander counts into a signed 8-bit register, so this tracks the
        wraparound and returns a count that keeps growing.

        :param channel: encoder channel, 1 to 4

        """
        if channel < 1 or channel > 4:
            raise ValueError("IOExpander: channel should be in range 1-4")
        channel -= 1

        last = self._encoder_last[channel]
        value = self._read_u8(REG_ENC_COUNT[channel])

        if value & 0b10000000:
            value -= 256

        if last > 64 and value < -64:
            self._encoder_offset[channel] += 256
        if last < -64 and value > 64:
            self._encoder_offset[channel] -= 256

        self._encoder_last[channel] = value

        return self._encoder_offset[channel] + value

    def clear_rotary_encoder(self, channel):
        """Reset the count of a rotary encoder channel to zero.

        :param channel: encoder channel, 1 to 4

        """
        if channel < 1 or channel > 4:
            raise ValueError("IOExpander: channel should be in range 1-4")
        channel -= 1

        self._encoder_last[channel] = 0
        self._encoder_offset[channel] = 0
        self._write_u8(REG_ENC_COUNT[channel], 0)
