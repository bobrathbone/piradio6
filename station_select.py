#!/usr/bin/env python3
# Raspberry Pi Select radio station button interface
# Experimental code for station selection using buttons
# $Id: station_select.py,v 1.3 2025/06/26 09:52:12 bob Exp $
#
# Author: Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#
#

import os,sys
import time
import RPi.GPIO as GPIO
import threading
import pdb
import signal
from constants import *
from button_class import Button

GPIO.setmode(GPIO.BCM)
from config_class import Configuration
config = Configuration()

from log_class import Log
log = Log()
log.init("radio")
run = True
tDelay = 2 # Delay between button depressions in seconds
now = time.time()
pressTime = 0

# Button to station mapping <GPIO>:<station id> Modify as required
buttons = {
            2:1,
            3:2,
            4:10,
            17:8,
            27:9,
          }

def buttonPressed(gpio):
    global now,pressTime
    now = time.time()
    if now > pressTime + tDelay: 
        try:
            print("Button pressed on GPIO", gpio)
            station = buttons[gpio]
            cmd = "mpc play " + str(station)
            print(cmd)
            execCommand(cmd)
            pressTime = time.time()
        except Exception as e:
            print(str(e))
            pass

# Execute system command
def execCommand(cmd):
    try:
        p = os.popen(cmd)
        result =  p.readline().rstrip('\n')
    except Exception as e:
        msg = "execCommand: " + str(cmd)
        print(str(e))
        result = ""
    return result

def signalHandler(signal,frame):
    print("\nReceived signal", signal, "Exiting")
    run = False
    sys.exit(0)

signal.signal(signal.SIGHUP,signalHandler)
signal.signal(signal.SIGTERM,signalHandler)

pid = os.getpid()
print("Station selection running, pid", pid)

# Print button settings
for button in buttons:
    station = buttons[button]
    print("Button",button,"station",station)

# Set up button GPIOs
for button in buttons:
    Button(button, buttonPressed, log, UP)

print("Press station selection button")
try:
    while run:
        time.sleep(0.2)
    sys.exit(0)

except KeyboardInterrupt:
    print(" Stopped")
    GPIO.cleanup()
    sys.exit(0)

# End of script

# set tabstop=4 shiftwidth=4 expandtab
# retab

