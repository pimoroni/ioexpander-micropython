import time

from machine import I2C, Pin

from ioexpander import PWM, IOExpander

LED_PIN = 1

i2c = I2C(0, sda=Pin(20), scl=Pin(21))

ioe = IOExpander(i2c)

# A period of 255 gives 256 steps of brightness
ioe.set_pwm_period(255)
ioe.set_pwm_control(2)
ioe.set_mode(LED_PIN, PWM)

while True:
    for brightness in range(256):
        ioe.output(LED_PIN, brightness)
        time.sleep(0.005)
    for brightness in range(255, -1, -1):
        ioe.output(LED_PIN, brightness)
        time.sleep(0.005)
