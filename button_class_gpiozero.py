#!/usr/bin/env python3
# Raspberry Pi Button Push Button Class using gpiozero interface
# $Id: button_class_gpiozero.py,v 1.3 2025/02/16 12:17:08 bob Exp $
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
import threading
import pdb
from constants import *
from gpiozero import Button

class ButtonClass:
    buttonobj = None

    def __init__(self,button,callback,log,pull_up_down):
        self.button = button
        self.callback = callback
        self.pull_up_down = pull_up_down
        self.log = log

        t = threading.Thread(target=self._run,args=(button,callback,log,pull_up_down,))
        t.daemon = True
        t.start()

    def _run(self,button,callback,log,pull_up_down):
        self.button = button
        self.callback = callback
        self.pull_up_down = pull_up_down
        self.log = log

        if self.button > 0:
            if pull_up_down == DOWN:
                pull_up = False
            else:
                pull_up = True
            try:
                # The following lines enable the internal pull-up resistor
                push_button = Button(self.button,bounce_time=0.01,pull_up=True)

                # Add event detection to the GPIO inputs
                push_button.when_pressed = self.button_down_event
                push_button.when_released = self.button_up_event

            except Exception as e:
                log.message("Button GPIO " + str(self.button)\
                         + " initialise error: " + str(e), log.ERROR)
                sys.exit(1)
         
    # Button DOWN event
    def button_down_event(self,buttonobj):
        if self.buttonobj == None:
            self.buttonobj = buttonobj
        event = self.button
        self.callback(event)

    # Button UP event
    def button_up_event(self,buttonobj):
        if self.buttonobj == None:
            self.buttonobj = buttonobj
        event = self.button
        self.callback(event)

    # Was a button pressed (goes from 0 to 1 or 1 to 0 depending upon pull_up_down )
    def pressed(self):
        return self.buttonobj.is_pressed

# End of Button Class

### Test routine ###

if __name__ == "__main__":

    from config_class import Configuration

    # Button events call this routine
    def button_event(gpio):
        print("Button pressed on GPIO", gpio)
        return

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

    ButtonClass(left_switch, button_event, log, config.pull_up_down)
    ButtonClass(right_switch, button_event, log, config.pull_up_down)
    ButtonClass(mute_switch, button_event, log, config.pull_up_down)
    ButtonClass(down_switch, button_event, log, config.pull_up_down)
    ButtonClass(up_switch, button_event, log, config.pull_up_down)
    ButtonClass(menu_switch, button_event, log, config.pull_up_down)
    ButtonClass(record_switch, button_event, log, UP) # Always resistors pulled high

    try:
        while True:
            time.sleep(0.2)

    except KeyboardInterrupt:
        print(" Stopped")
        sys.exit(0)

# End of script

# set tabstop=4 shiftwidth=4 expandtab
# retab

