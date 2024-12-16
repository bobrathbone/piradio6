#!/usr/bin/env python3
# Raspberry Pi Button Push Button Class
# $Id: button_class.py,v 1.14 2024/12/11 08:37:33 bob Exp $
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
from constants import *

GPIO.setmode(GPIO.BCM)

class Button:

    def __init__(self,button,callback,log,pull_up_down):
        t = threading.Thread(target=self._run,args=(button,callback,log,pull_up_down,))
        t.daemon = True
        t.start()

    def _run(self,button,callback,log,pull_up_down):
        self.button = button
        self.callback = callback
        self.pull_up_down = pull_up_down
        self.log = log

        if self.button > 0:
            GPIO.setwarnings(False)

            if pull_up_down == DOWN:
                resistor = GPIO.PUD_DOWN
                edge = GPIO.RISING
                sEdge = 'Rising'
            else:
                resistor = GPIO.PUD_UP
                edge = GPIO.FALLING
                sEdge = 'Falling'

            try:
                msg = "Creating button object for GPIO " +  str(self.button) \
                     + " edge=" +  sEdge
                log.message(msg, log.DEBUG)
                # The following lines enable the internal pull-up resistor
                GPIO.setup(self.button, GPIO.IN, pull_up_down=resistor)

                # Add event detection to the GPIO inputs
                GPIO.add_event_detect(self.button, edge, 
                            callback=self.button_event,
                            bouncetime=200)
            except Exception as e:
                log.message("Button GPIO " + str(self.button)\
                         + " initialise error: " + str(e), log.ERROR)
                sys.exit(1)
         
    # Push button event
    def button_event(self,button):
        self.log.message("Push button event GPIO " + str(button), self.log.DEBUG)
        event_button = self.button
        self.callback(event_button) # Pass button event to event class
        return

    # Was a button pressed (goes from 0 to 1 or 1 to 0 depending upon pull_up_down )
    def pressed(self):
        level = 1
        if self.pull_up_down == UP:
            level = 0
        state = GPIO.input(self.button)
        if state == level:
            pressed = True
        else:
            pressed = False
        return pressed

# End of Button Class

### Test routine ###

def interrupt(gpio):
    print("Button pressed on GPIO", gpio)
    return

if __name__ == "__main__":

    from config_class import Configuration
    from log_class import Log
    config = Configuration()
    log = Log()
    if len(log.getName()) < 1:
        log.init("radio")

    pullupdown = ['DOWN','UP'] 

    print("Test Button Class")

    # Get switch configuration
    left_switch = config.getSwitchGpio("left_switch")
    right_switch = config.getSwitchGpio("right_switch")
    mute_switch = config.getSwitchGpio("mute_switch")
    down_switch = config.getSwitchGpio("down_switch")
    up_switch = config.getSwitchGpio("up_switch")
    menu_switch = config.getSwitchGpio("menu_switch")
    record_switch = config.getSwitchGpio("record_switch")

    print("Left switch GPIO", left_switch)
    print("Right switch GPIO", right_switch)
    print("Mute switch GPIO", mute_switch)
    print("Up switch GPIO", up_switch)
    print("Down switch GPIO", down_switch)
    print("Menu switch GPIO", menu_switch)
    print("Pull Up/Down resistors", pullupdown[config.pull_up_down])
    print("Record switch GPIO", record_switch,"Pull Up")

    Button(left_switch, interrupt, log, config.pull_up_down)
    Button(right_switch, interrupt, log, config.pull_up_down)
    Button(mute_switch, interrupt, log, config.pull_up_down)
    Button(down_switch, interrupt, log, config.pull_up_down)
    Button(up_switch, interrupt, log, config.pull_up_down)
    Button(menu_switch, interrupt, log, config.pull_up_down)
    Button(record_switch, interrupt, log, UP) # Always resistors pulled high

    try:
        while True:
            time.sleep(0.2)

    except KeyboardInterrupt:
        print(" Stopped")
        GPIO.cleanup()
        sys.exit(0)

# End of script

# set tabstop=4 shiftwidth=4 expandtab
# retab

