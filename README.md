# IO Expander MicroPython

The [Pimoroni IO Expander Breakout](https://shop.pimoroni.com/products/io-expander) is a Nuvoton
MS51 microcontroller that gives you 14 extra pins over i2c. Eight of them can read a 12-bit ADC,
six can drive a 16-bit PWM output, and four rotary encoders can be counted in hardware.

This driver also underpins the RGB Encoder, RGB Potentiometer and Encoder Wheel breakouts, which
are all fundamentally an IO Expander with something wired to its pins.

## Installing

Install with `mip`:

```python
import mip
mip.install("github:pimoroni/ioexpander-micropython/package.json")
```

Or with Thonny, via Tools -> Manage Packages, searching for `ioexpander-micropython`.

## Getting Started

```python
from machine import I2C, Pin
from ioexpander import IOExpander

i2c = I2C(0, sda=Pin(20), scl=Pin(21))

ioe = IOExpander(i2c)
```

The breakout ships at address `0x18`. Pins are numbered 1 to 14, matching the silkscreen.

## Pin Modes

Every pin has to be told what it is before you use it:

```python
from ioexpander import ADC, IN, IN_PU, OD, OUT, PWM

ioe.set_mode(1, OUT)     # Push-pull output
ioe.set_mode(2, IN)      # Input, high impedance
ioe.set_mode(3, IN_PU)   # Input with pull-up
ioe.set_mode(4, OD)      # Open-drain output
ioe.set_mode(5, PWM)     # PWM output
ioe.set_mode(14, ADC)    # Analog input
```

Not every pin can do everything. Pins 1 to 6 are PWM only, pins 10, 11, 13 and 14 are ADC only,
and pins 7, 8, 9 and 12 can be either. Setting an unsupported mode raises a `ValueError`.

Two extra settings apply to particular modes:

```python
ioe.set_mode(2, IN, schmitt_trigger=True)  # Cleans up a noisy input
ioe.set_mode(5, PWM, invert=True)          # For a common anode LED
```

## Reading and Writing

`input()` returns a digital 0 or 1, or a 12-bit count from a pin in ADC mode:

```python
value = ioe.input(14)
volts = ioe.input_as_voltage(14)
```

Voltages are scaled against the ADC reference, which defaults to 3.3V:

```python
ioe.set_adc_vref(5.0)
```

`output()` writes a digital `LOW` or `HIGH`, or a PWM duty cycle:

```python
from ioexpander import HIGH, LOW

ioe.output(1, HIGH)
ioe.output(5, 128)
```

## PWM

All six PWM channels share one counter and the period and clock divider are global. The period
sets how many steps of duty cycle you get. The divider sets how fast the counter runs:

```python
ioe.set_pwm_period(255)   # 256 steps of duty cycle
ioe.set_pwm_control(2)    # Divide the 24MHz clock by 2
```

Or set a frequency and let the driver pick both:

```python
period = ioe.set_pwm_frequency(1000)
```

New duty cycles are buffered until a load. `output()` loads by default, which is one i2c
transaction per channel. To update several channels in step, use `load=Talse` until the last one:

```python
ioe.output(1, r, load=False)
ioe.output(7, g, load=False)
ioe.output(2, b)
```

This combines multiple transactions into one, speeding things up slightly.

## Rotary Encoders

The expander counts up to four rotary encoders in hardware, so you don't have to poll fast
enough to catch every transition:

```python
ioe.setup_rotary_encoder(1, pin_a=12, pin_b=3, pin_c=11)
count = ioe.read_rotary_encoder(1)
ioe.clear_rotary_encoder(1)
```

`pin_c` is the encoder's common terminal, if it is wired to a pin rather than to ground. Pass
`count_microsteps=True` to count every state change rather than every detent.

The expander counts into a signed 8-bit register. `read_rotary_encoder()` tracks the wraparound
for you and returns a count that keeps growing. You must read it often enough that the count doesn't
move more than 128 between reads.

## Interrupts

The expander can drive its `INT` pin when a watched input changes, so you can wait on a pin
instead of polling over i2c:

```python
from machine import Pin

interrupt = Pin(22, Pin.IN, Pin.PULL_UP)
ioe = IOExpander(i2c, interrupt=interrupt)

ioe.set_pin_interrupt(3, True)

if ioe.get_interrupt_flag():
    ...
    ioe.clear_interrupt_flag()
```

Without a pin, `get_interrupt_flag()` reads the flag over i2c instead.

## Changing the Address

`set_address()` writes a new address into the expander's flash, where it persists across power
cycles:

```python
ioe.set_address(0x20)
```
