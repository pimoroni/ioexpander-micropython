import time

from machine import I2C, Pin

from ioexpander import ADC, IOExpander

ADC_PIN = 14

i2c = I2C(0, sda=Pin(20), scl=Pin(21))

ioe = IOExpander(i2c)
ioe.set_adc_vref(3.3)
ioe.set_mode(ADC_PIN, ADC)

while True:
    print(f"{ioe.input_as_voltage(ADC_PIN):.3f}V ({ioe.input(ADC_PIN)})")
    time.sleep(0.5)
