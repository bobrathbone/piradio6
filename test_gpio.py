#!/usr/bin/env python3
# Raspberry Pi test IR GPIO pin
# $Id: test_gpio.py,v 1.1 2021/11/16 15:38:17 bob Exp $
#
# Author: Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class uses standard rotary encoder with push switch
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#
#

import os,sys
import time
import RPi.GPIO as GPIO
ir_gpio = 16

def gpio_event(event):
    print("IR event",event)

GPIO.setmode(GPIO.BCM)

gpios = [9,16,25]

for gpio in gpios:
    print ("Setting up GPIO", gpio )
    GPIO.setup(gpio, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.add_event_detect(gpio,GPIO.BOTH,callback=gpio_event, bouncetime=1)

while True:
    time.sleep(0.1)
