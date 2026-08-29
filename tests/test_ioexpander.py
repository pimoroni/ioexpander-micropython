import pytest
from fake_ioe import FakeIOE


def test_setup():
    from ioexpander import IOExpander

    ioe = IOExpander(FakeIOE())

    assert ioe.address == 0x18
    assert ioe.get_chip_id() == 0xE26A
    assert len(ioe.pins) == 14


def test_setup_invalid_chip_id():
    from ioexpander import IOExpander

    with pytest.raises(RuntimeError):
        IOExpander(FakeIOE(chip_id=0x0000))


def test_setup_skip_chip_id_check():
    from ioexpander import IOExpander

    IOExpander(FakeIOE(chip_id=0x0000), skip_chip_id_check=True)


def test_setup_with_reset():
    from ioexpander import IOExpander

    i2c = FakeIOE()
    IOExpander(i2c, perform_reset=True)

    assert i2c.registers[0xFE] & 0b10  # The reset bit of CTRL


def test_reset_timeout():
    from ioexpander import IOExpander

    i2c = FakeIOE()
    i2c.registers[0xD0] = 0x00  # Never reports the reset as complete

    with pytest.raises(RuntimeError):
        IOExpander(i2c, perform_reset=True)


def test_pin_out_of_range():
    from ioexpander import OUT, IOExpander

    ioe = IOExpander(FakeIOE())

    with pytest.raises(ValueError):
        ioe.set_mode(0, OUT)

    with pytest.raises(ValueError):
        ioe.set_mode(15, OUT)


def test_bit_addressed_registers():
    from ioexpander import REG_P0, IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)

    ioe.set_bit(REG_P0, 3)
    assert i2c.registers[REG_P0] == 0b1000

    ioe.clr_bit(REG_P0, 3)
    assert i2c.registers[REG_P0] == 0

    # Bit addressed writes carry the bit number, not a mask
    assert (REG_P0, bytes([0b1011])) in i2c.writes
    assert (REG_P0, bytes([0b0011])) in i2c.writes


def test_plain_registers_read_modify_write():
    from ioexpander import REG_PNP, IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)

    ioe.set_bit(REG_PNP, 2)
    ioe.set_bit(REG_PNP, 5)
    assert i2c.registers[REG_PNP] == 0b00100100

    ioe.clr_bit(REG_PNP, 2)
    assert i2c.registers[REG_PNP] == 0b00100000


def test_set_mode_output():
    from ioexpander import OUT, IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)

    # Pin 5 is port 0, pin 0
    ioe.set_mode(5, OUT)

    assert ioe.get_mode(5) == OUT
    assert i2c.registers[0x71] & 0b1 == 0  # P0M1
    assert i2c.registers[0x72] & 0b1 == 1  # P0M2, push-pull is 0b01


def test_set_mode_input_pull_up():
    from ioexpander import IN_PU, IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)

    # Pin 1 is port 1, pin 5
    ioe.set_mode(1, IN_PU)

    # Pull up is quasi-bidirectional with the output driven high
    assert i2c.registers[0x73] & (1 << 5) == 0  # P1M1
    assert i2c.registers[0x74] & (1 << 5) == 0  # P1M2
    assert i2c.registers[0x50] & (1 << 5)       # P1, driven high


def test_set_mode_schmitt_trigger():
    from ioexpander import IN, IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)

    ioe.set_mode(1, IN, schmitt_trigger=True)
    assert i2c.registers[0xC4] & (1 << 5)  # P1S


def test_set_mode_pwm_inverted():
    from ioexpander import PWM, IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)

    # Pin 1 is PWM channel 5 on PIOCON1
    ioe.set_mode(1, PWM, invert=True)

    assert i2c.registers[0xC9] & (1 << 5)  # PIOCON1
    assert i2c.registers[0x96] & (1 << 5)  # PNP, inverted
    assert i2c.registers[0x98] & (1 << 7)  # PWMCON0, PWMRUN


def test_set_mode_rejects_unsupported():
    from ioexpander import ADC, PWM, IOExpander

    ioe = IOExpander(FakeIOE())

    with pytest.raises(ValueError):
        ioe.set_mode(1, ADC)  # Pin 1 is PWM only

    with pytest.raises(ValueError):
        ioe.set_mode(10, PWM)  # Pin 10 is ADC only


def test_set_mode_is_a_no_op_when_unchanged():
    from ioexpander import OUT, IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)

    ioe.set_mode(5, OUT)
    writes = len(i2c.writes)
    ioe.set_mode(5, OUT)

    assert len(i2c.writes) == writes


def test_digital_output():
    from ioexpander import HIGH, LOW, OUT, IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)
    ioe.set_mode(5, OUT)

    ioe.output(5, HIGH)
    assert i2c.registers[0x40] & 0b1  # P0.0

    ioe.output(5, LOW)
    assert not i2c.registers[0x40] & 0b1


def test_digital_input():
    from ioexpander import IN, IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)
    ioe.set_mode(1, IN)  # Port 1, pin 5

    i2c.set_port_bit(0x50, 5, True)
    assert ioe.input(1) == 1

    i2c.set_port_bit(0x50, 5, False)
    assert ioe.input(1) == 0


def test_pwm_output():
    from ioexpander import PWM, IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)
    ioe.set_mode(1, PWM)  # PWM channel 5

    ioe.output(1, 0x1234)

    assert i2c.registers[0xCB] == 0x34  # PWM5L
    assert i2c.registers[0xC8] == 0x12  # PWM5H


def test_adc_input():
    from ioexpander import ADC, IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)
    ioe.set_mode(10, ADC)  # Pin 10 is ADC channel 3

    i2c.adc_value = 2048
    assert ioe.input(10) == 2048
    assert ioe.input_as_voltage(10) == pytest.approx((2048 / 4095.0) * 3.3)


def test_adc_vref():
    from ioexpander import ADC, IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)
    ioe.set_mode(10, ADC)
    ioe.set_adc_vref(5.0)

    assert ioe.get_adc_vref() == 5.0

    i2c.adc_value = 4095
    assert ioe.input_as_voltage(10) == pytest.approx(5.0)


def test_adc_channel_select():
    from ioexpander import ADC, IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)
    ioe.set_mode(11, ADC)  # Pin 11 is ADC channel 3
    ioe.input(11)

    assert i2c.registers[0xA8] & 0x0F == 3  # ADCCON0
    assert i2c.registers[0xB6] & (1 << 3)   # AINDIDS
    assert i2c.registers[0xA1] & 0b1        # ADCCON1, ADC enabled


def test_adc_timeout():
    from ioexpander import ADC, IOExpander

    class StuckADC(FakeIOE):
        def writeto_mem(self, address, register, buf):
            super().writeto_mem(address, register, buf)
            if register == 0xA8:
                self.registers[0xA8] &= ~(1 << 7)  # Never completes

    i2c = StuckADC()
    ioe = IOExpander(i2c)
    ioe.set_mode(10, ADC)

    with pytest.raises(RuntimeError):
        ioe.input(10, adc_timeout=0.01)


def test_set_pwm_control():
    from ioexpander import IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)

    ioe.set_pwm_control(64)
    assert i2c.registers[0x9F] == 0b110  # PWMCON1

    with pytest.raises(ValueError):
        ioe.set_pwm_control(3)


def test_set_pwm_period():
    from ioexpander import IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)

    ioe.set_pwm_period(0xABCD)
    assert i2c.registers[0x99] == 0xCD  # PWMPL
    assert i2c.registers[0x91] == 0xAB  # PWMPH


def test_set_pwm_frequency():
    from ioexpander import IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)

    # 24MHz clock, so 1kHz needs a period of 24000 and no division
    assert ioe.set_pwm_frequency(1000) == 24000
    assert i2c.registers[0x9F] == 0b000
    assert (i2c.registers[0x91] << 8) | i2c.registers[0x99] == 23999

    # 100Hz needs 240000, which only fits after dividing by 4
    assert ioe.set_pwm_frequency(100) == 60000
    assert i2c.registers[0x9F] == 0b010


def test_set_pwm_frequency_out_of_range():
    from ioexpander import MAX_PERIOD, IOExpander

    ioe = IOExpander(FakeIOE())

    assert ioe.set_pwm_frequency(1) == MAX_PERIOD
    assert ioe.set_pwm_frequency(24000000) == 2


def test_interrupts():
    from ioexpander import IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)

    ioe.enable_interrupt_out()
    assert i2c.registers[0xF9] & 0b010
    assert not i2c.registers[0xF9] & 0b100

    ioe.enable_interrupt_out(pin_swap=True)
    assert i2c.registers[0xF9] & 0b100

    ioe.disable_interrupt_out()
    assert not i2c.registers[0xF9] & 0b010

    i2c.registers[0xF9] |= 0b1
    assert ioe.get_interrupt_flag() is True

    ioe.clear_interrupt_flag()
    assert ioe.get_interrupt_flag() is False


def test_interrupt_pin():
    from ioexpander import IOExpander

    class FakePin:
        def __init__(self, state):
            self.state = state

        def value(self):
            return self.state

    ioe = IOExpander(FakeIOE(), interrupt=FakePin(0))
    assert ioe.get_interrupt_flag() is True

    ioe.interrupt = FakePin(1)
    assert ioe.get_interrupt_flag() is False


def test_set_pin_interrupt():
    from ioexpander import IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)

    ioe.set_pin_interrupt(1, True)  # Port 1, pin 5
    assert i2c.registers[0x01] & (1 << 5)  # INT_MASK_P1

    ioe.set_pin_interrupt(1, False)
    assert not i2c.registers[0x01] & (1 << 5)


def test_setup_rotary_encoder():
    from ioexpander import IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)

    ioe.setup_rotary_encoder(1, 12, 3, pin_c=11)

    assert i2c.registers[0x05] == 12 | (3 << 4)  # ENC_1_CFG
    assert i2c.registers[0x04] & 0b01            # ENC_EN, channel 1 enabled
    assert not i2c.registers[0x04] & 0b10        # Microsteps off


def test_setup_rotary_encoder_microsteps():
    from ioexpander import IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)

    ioe.setup_rotary_encoder(1, 3, 12, count_microsteps=True)
    assert i2c.registers[0x04] & 0b11


def test_rotary_encoder_channel_out_of_range():
    from ioexpander import IOExpander

    ioe = IOExpander(FakeIOE())

    with pytest.raises(ValueError):
        ioe.setup_rotary_encoder(5, 3, 12)

    with pytest.raises(ValueError):
        ioe.read_rotary_encoder(0)

    with pytest.raises(ValueError):
        ioe.clear_rotary_encoder(5)


def test_read_rotary_encoder():
    from ioexpander import IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)
    ioe.setup_rotary_encoder(1, 3, 12)

    i2c.set_encoder_count(1, 10)
    assert ioe.read_rotary_encoder(1) == 10

    i2c.set_encoder_count(1, 0xF6)  # -10
    assert ioe.read_rotary_encoder(1) == -10


def test_read_rotary_encoder_wraps():
    from ioexpander import IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)
    ioe.setup_rotary_encoder(1, 3, 12)

    i2c.set_encoder_count(1, 120)
    assert ioe.read_rotary_encoder(1) == 120

    # The count register wraps from +127 to -128, but the total keeps climbing
    i2c.set_encoder_count(1, 0x88)  # -120
    assert ioe.read_rotary_encoder(1) == 136

    i2c.set_encoder_count(1, 120)
    assert ioe.read_rotary_encoder(1) == 120


def test_clear_rotary_encoder():
    from ioexpander import IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)
    ioe.setup_rotary_encoder(1, 3, 12)

    i2c.set_encoder_count(1, 120)
    ioe.read_rotary_encoder(1)
    i2c.set_encoder_count(1, 0x88)
    ioe.read_rotary_encoder(1)

    ioe.clear_rotary_encoder(1)
    i2c.set_encoder_count(1, 0)

    assert ioe.read_rotary_encoder(1) == 0


def test_set_address():
    from ioexpander import IOExpander

    i2c = FakeIOE()
    ioe = IOExpander(i2c)
    ioe.set_address(0x20)

    assert ioe.address == 0x20
    assert i2c.registers[0xFD] == 0x20


def test_pwm_load_timeout():
    from ioexpander import IOExpander

    class StuckLoad(FakeIOE):
        def writeto_mem(self, address, register, buf):
            super().writeto_mem(address, register, buf)
            if register == 0x98:
                self.registers[0x98] |= 1 << 6  # The load never completes

    ioe = IOExpander(StuckLoad(), timeout=0.01)

    with pytest.raises(RuntimeError):
        ioe.pwm_load()


def test_version():
    import ioexpander

    assert ioexpander.__version__ == "0.0.1"
