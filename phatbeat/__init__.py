# Raspberry Pi pHat Beat library 
# $Id: __init__.py,v 1.2 2023/01/22 10:09:28 bob Exp $
#
# Adapted from the Pimoroni Python3 pHat library. All button functions removed as
# these handled in the button_class.py 
#
# Author: Pimoroni (https://shop.pimoroni.com)
# Amended by: Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#
#
import atexit
import time
from threading import Thread
from sys import exit

try:
    import RPi.GPIO as GPIO
except ImportError:
    raise ImportError("This library requires the RPi.GPIO module\nInstall with: sudo pip install RPi.GPIO")


__version__ = '1.0'

DAT = 23
CLK = 24
NUM_PIXELS = 16
CHANNEL_PIXELS = 8
BRIGHTNESS = 7

pixels = [[0,0,0,BRIGHTNESS]] * NUM_PIXELS

_use_threading = False

_is_setup = False
_clear_on_exit = True

def _exit():
    if _clear_on_exit:
        clear()
        show()
    GPIO.cleanup()

def use_threading(value=True):
    global _use_threading
    setup()
    _use_threading = value

def set_brightness(brightness, channel = None):
    """Set the brightness of all pixels

    :param brightness: Brightness: 0.0 to 1.0

    """

    setup()

    if brightness < 0 or brightness > 1:
        raise ValueError("Brightness should be between 0.0 and 1.0")

    if channel is None or channel == 0:
        for x in range(CHANNEL_PIXELS):
            pixels[x][3] = int(31.0 * brightness) & 0b11111

    if channel is None or channel == 1:
        for x in range(CHANNEL_PIXELS):
            pixels[x + (CHANNEL_PIXELS)][3] = int(31.0 * brightness) & 0b11111

def clear(channel = None):
    """Clear the pixel buffer"""

    setup()

    if channel is None or channel == 0:
        for x in range(CHANNEL_PIXELS):
            pixels[x][0:3] = [0,0,0]

    if channel is None or channel == 1:
        for x in range(CHANNEL_PIXELS):
            pixels[x + (CHANNEL_PIXELS)][0:3] = [0,0,0]

def _write_byte(byte):
    for x in range(8):
        GPIO.output(DAT, byte & 0b10000000)
        GPIO.output(CLK, 1)
        time.sleep(0.0000005)
        byte <<= 1
        GPIO.output(CLK, 0)
        time.sleep(0.0000005)

# Emit exactly enough clock pulses to latch the small dark die APA102s which are weird
# for some reason it takes 36 clocks, the other IC takes just 4 (number of pixels/2)
def _eof():
    GPIO.output(DAT, 1)
    for x in range(32):
        GPIO.output(CLK, 1)
        time.sleep(0.0000005)
        GPIO.output(CLK, 0)
        time.sleep(0.0000005)

def _sof():
    GPIO.output(DAT,0)
    for x in range(32):
        GPIO.output(CLK, 1)
        time.sleep(0.0000005)
        GPIO.output(CLK, 0)
        time.sleep(0.0000005)

def show():
    """Output the buffer to the displays"""

    setup()

    _sof()

    for pixel in pixels:
        r, g, b, brightness = pixel
        _write_byte(0b11100000 | brightness)
        _write_byte(b)
        _write_byte(g)
        _write_byte(r)

    _eof()

def set_all(r, g, b, brightness=None, channel=None):
    """Set the RGB value and optionally brightness of all pixels

    If you don't supply a brightness value, the last value set for each pixel be kept.

    :param r: Amount of red: 0 to 255
    :param g: Amount of green: 0 to 255
    :param b: Amount of blue: 0 to 255
    :param brightness: Brightness: 0.0 to 1.0 (default around 0.2)
    :param channel: Optionally specify which bar to set: 0 or 1

    """

    setup()

    if channel is None or channel == 0:
        for x in range(CHANNEL_PIXELS):
            set_pixel(x, r, g, b, brightness)

    if channel is None or channel == 1:
        for x in range(CHANNEL_PIXELS):
            set_pixel(x + (CHANNEL_PIXELS), r, g, b, brightness)

def set_pixel(x, r, g, b, brightness=None, channel=None):
    """Set the RGB value, and optionally brightness, of a single pixel
    
    If you don't supply a brightness value, the last value will be kept.

    :param x: The horizontal position of the pixel: 0 to 7
    :param r: Amount of red: 0 to 255
    :param g: Amount of green: 0 to 255
    :param b: Amount of blue: 0 to 255
    :param brightness: Brightness: 0.0 to 1.0 (default around 0.2)
    :param channel: Optionally specify which bar to set: 0 or 1

    """

    setup()

    if brightness is None:
        brightness = pixels[x][3]
    else:
        brightness = int(31.0 * brightness) & 0b11111

    if channel in [0, 1]:
        if x >= CHANNEL_PIXELS:
            raise ValueError("Index should be < {} when displaying on a specific channel".format(CHANNEL_PIXELS))

        x += channel * (CHANNEL_PIXELS)
        
    if x >= CHANNEL_PIXELS:
        x = NUM_PIXELS - 1 - (x - CHANNEL_PIXELS)

    pixels[x] = [int(r) & 0xff,int(g) & 0xff,int(b) & 0xff,brightness]


def set_clear_on_exit(value=True):
    """Set whether the displays should be cleared upon exit

    By default the displays will turn off on exit, but calling::

        phatbeat.set_clear_on_exit(False)

    Will ensure that it does not.

    :param value: True or False (default True)

    """

    global _clear_on_exit
    setup()
    _clear_on_exit = value


def setup():
    global _is_setup

    if _is_setup:
        return True

    atexit.register(_exit)

    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup([DAT,CLK],GPIO.OUT)

    _is_setup = True

