#!/usr/bin/env python3
# Raspberry Pi test all available GPIOs. All pins are toggled up and down
#
# $Id: toggle_gpios.py,v 1.1 2026/01/15 20:34:45 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#

import RPi.GPIO as GPIO
import sys,time 
import os

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

delay = 0.0001
pins = (2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27)

def setHigh(pin):
    GPIO.output(pin, GPIO.HIGH)

def setLow(pin):
    GPIO.output(pin, GPIO.LOW)

# Set up pins
for pin in range (0,len(pins)):
    gpio_pin = pins[pin]
    try:
        GPIO.setup(gpio_pin, GPIO.OUT)
        time.sleep(0.1)
    except Exception as e:
        print("Warning: GPIO",gpio_pin, e)     

while True:
    try:
        for pin in range (0,len(pins)):
            gpio_pin = pins[pin]
            setHigh(gpio_pin)
        time.sleep(delay)
        for pin in range (0,len(pins)):
            gpio_pin = pins[pin]
            setLow(gpio_pin)
        time.sleep(delay)

    except KeyboardInterrupt:
        print("\nEnd of GPIOs test")
        GPIO.cleanup()
        sys.exit(0)

# set tabstop=4 shiftwidth=4 expandtab
# retab
