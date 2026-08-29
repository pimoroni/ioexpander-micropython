import time

from machine import I2C, Pin

from ioexpander import IOExpander

PIN_A = 12
PIN_B = 3
PIN_C = 11

i2c = I2C(0, sda=Pin(20), scl=Pin(21))

ioe = IOExpander(i2c)
ioe.enable_interrupt_out(True)
ioe.setup_rotary_encoder(1, PIN_A, PIN_B, pin_c=PIN_C)

count = 0

while True:
    if ioe.get_interrupt_flag():
        count = ioe.read_rotary_encoder(1)
        ioe.clear_interrupt_flag()
        print(count)
    time.sleep(0.01)
