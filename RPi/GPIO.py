#!/usr/bin/env python3
#
# Raspberry Pi RPi.GPIO interception package
# $Id: GPIO.py,v 1.14 2002/01/03 14:41:25 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This package intercepts RPi.GPIO calls and redirects them to the lgpio package
# calls specifically used for the Raspberry Pi model 5 or Bookworm 
# See: https://abyz.me.uk/lg/py_lgpio.html
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#         The authors shall not be liable for any loss or damage however caused.
#

import lgpio
import time
import re
import pdb

IGNORE_WARNINGS = True  # Set to False for debugging GPIO code. See GPIO.setwarnings

# RPi.GPIO definitions (Note: they are different to LGPIO variables)
BOARD = 10
BCM = 11 
HIGH = 1
LOW = 0
OUT = 0
IN = 1

PUD_OFF = 20
PUD_DOWN = 21
PUD_UP = 22

RISING = 31
FALLING = 32
BOTH = 33

mode_board = False    # Mode is GPIO.BCM (GPIO numbering) or GPIO.BOARD (Pin numbering)
# pins is the mapping between GPIO.BOARD and GPIO.BCM. Format Pin:GPIO
pins = { 
         3:2, 5:3, 7:4, 8:14, 10:15, 11:17, 12:18, 13:27, 15:22, 16:23, 18:24, 19:10,
         21:9, 22:25, 23:11, 24:8, 26:7, 27:0, 28:1, 29:5, 31:6, 32:12, 33:13, 35:19,
         36:16, 37:26, 38:20, 40:21,
       }
        
# LGPIO Flags
LGPIO_PULL_UP = 32
LGPIO_PULL_DOWN = 64
LGPIO_PULL_OFF = 128

# A dictionary containing line event callbacks accessed using GPIO number
callbacks = {}
edges = ['NONE','RISING_EDGE','FALLING_EDGE','BOTH_EDGES']

# The Raspberry Pi Model 5 uses the RP1 chip (4). Try to open first
try:
    chip = lgpio.gpiochip_open(4)
except Exception as e:
    pass

# Earlier Raspberry Pi 4b,3B etc uses SOC chip  for I/O (0). 
try:
    chip = lgpio.gpiochip_open(0)
except Exception as e:
    print ("Fatal error: %s" % (str(e)))
    exit(1) 

# Set mode BCM (GPIO numbering) or BOARD (Pin numbering)
def setmode(mode=BCM):
    global mode_board
    if mode == BOARD:
        mode_board = True
    else:
        mode_board = False

# Get the pin or GPIO depending upon the mode (BCM or BOARD)
def _get_gpio(line):
    global mode_board
    pin = line 
    if mode_board:
        try:
            pin = pins[line]
        except:
            pass
    return pin     

# The lgpio package does not have the equivalent of GPIO.setwarnings
# so the setwarnings can eitherbe ignored or be used to enable/disable lgpio exceptions
# Set IGNORE_WARNINGS to True at the beginning of this program to prevent warnings/exceptions
def setwarnings(boolean=True):
    if not IGNORE_WARNINGS:
        lgpio.exceptions = boolean
    return

# Setup GPIO line for INPUT or OUTPUT and set internal Pull Up/Down resistors
def setup(gpio,mode=OUT,pull_up_down=PUD_OFF):
    gpio = _get_gpio(gpio)
    if mode == IN:
        # Set up pull up/down resistors
        if pull_up_down == PUD_UP:
            pullupdown = LGPIO_PULL_UP
        elif pull_up_down == PUD_DOWN:
            pullupdown = LGPIO_PULL_DOWN
        elif pull_up_down == PUD_OFF:
            pullupdown = LGPIO_PULL_OFF
        lgpio.gpio_claim_input(chip,gpio,pullupdown)

    elif mode == OUT:
        lgpio.gpio_claim_output(chip, gpio)

# Convert LGPIO event to a GPIO event and call user callback
# Level values (Not used by our callback but could be)
# 0: change to low (a falling edge)
# 1: change to high (a rising edge)
# 2: no level change (a watchdog timeout)
def _gpio_event(chip,gpio,level,flags):
    gpio = _get_gpio(gpio)
    try:
        callbacks[gpio](gpio)
    except Exception as e:
        print(str(e)) 

# Add event detection - Converts GPIO add_event_detect call to LGPIO 
def add_event_detect(gpio,edge,callback=None,bouncetime=0):
    gpio = _get_gpio(gpio)
    callbacks[gpio] = callback 
    if edge ==  RISING:
        detect = lgpio.RISING_EDGE
    elif edge ==  FALLING:
        detect = lgpio.FALLING_EDGE
    else:
        detect = lgpio.BOTH_EDGES
    try:
        lgpio.callback(chip, gpio, detect,_gpio_event)
        lgpio.gpio_claim_alert(chip, gpio, 1, lFlags=detect, notify_handle=None)
        lgpio.gpio_set_debounce_micros(chip, gpio, bouncetime)

    except Exception as e:
        print(str(e)) 

# Read a GPIO input 
def input(gpio):
    gpio = _get_gpio(gpio)
    level = None
    try:
        level=lgpio.gpio_read(chip, gpio)
    except Exception as e:
        print(str(e)) 
    return level

# Output to a GPIO pin
def output(gpio,level=LOW):
    gpio = _get_gpio(gpio)
    try:
        lgpio.gpio_write(chip, gpio, level)
    except Exception as e:
        print(str(e)) 

def get_info():
    return 

def cleanup():
    lgpio.gpiochip_close(chip)

# Get the Raspberry pi board version from /proc/cpuinfo
def getBoardRevision():
    revision = 1
    with open("/proc/cpuinfo") as f:
        cpuinfo = f.read()
    rev_hex = re.search(r"(?<=\nRevision)[ |:|\t]*(\w+)", cpuinfo).group(1)
    rev_int = int(rev_hex,16)
    if rev_int > 3:
        revision = 2
    return revision

RPI_REVISION = getBoardRevision()

# Create PWM object
def PWM(gpio, frequency):  
    gpio = _get_gpio(gpio)
    return PWMInstance(gpio, frequency)  # Return a PWM object

# PWMInstance Class
class PWMInstance: 
    def __init__(self, gpio, frequency):
        self.gpio = gpio
        self.frequency = frequency
        self.duty_cycle = 0  # Initialize

    def start(self, duty_cycle):
        self.ChangeDutyCycle(duty_cycle)

    def ChangeDutyCycle(self, duty_cycle):
        self.duty_cycle = duty_cycle
        lgpio.tx_pwm(chip, self.gpio, self.frequency, duty_cycle)

    def stop(self):
        lgpio.tx_pwm(chip, self.gpio, 0, 0)

# LGPIO information 
if __name__ == '__main__':
    gpio=4
    info = lgpio.gpio_get_chip_info(chip)
    print("Chip",hex(chip),info)
    line_info = lgpio.gpio_get_line_info(chip, gpio)
    print("Line",gpio,line_info)

    # See https://abyz.me.uk/lg/py_lgpio.html#gpio_get_mode 
    mode = lgpio.gpio_get_mode(chip, gpio)
    print("GPIO",gpio,"mode",mode)

    setmode(BOARD)
    gpio = _get_gpio(7)
    print(BOARD,7,gpio)
    lgpio.gpiochip_close(chip)

# set tabstop=4 shiftwidth=4 expandtab
# retab

