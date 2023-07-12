#!/usr/bin/env python3
# Raspberry Pi Cosmic Controller (IQAudio) Class
# $Id: cosmic_class.py,v 1.5 2023/07/06 11:11:37 bob Exp $
#
# Author: Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class uses one standard rotary encoder with push switch
# and three push to make buttons. It also has three status LEDs and option IR sensor
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#
#

import os,sys,pwd
import time,pdb
import RPi.GPIO as GPIO

class Button:

    def __init__(self,button,callback,log):
        self.button = button
        self.callback = callback
        self.log = log

        if self.button > 0:
            msg = "Creating button for GPIO " +  str(self.button)
            log.message(msg, log.DEBUG)
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

            try:
                # The following lines enable the internal pull-up resistor
                GPIO.setup(self.button, GPIO.IN, pull_up_down=GPIO.PUD_UP)

                # Add event detection to the GPIO inputs
                GPIO.add_event_detect(self.button, GPIO.FALLING, 
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

    # Was a button pressed (goes from 1 to 0)
    def pressed(self):
        state = GPIO.input(self.button)
        if state == 0:
            pressed = True
        else:
            pressed = False
        return pressed

# End of Cosmic Button Class

### Test routines ###

statusLed = None
Names = ['NO_EVENT', 'CLOCKWISE', 'ANTICLOCKWISE', 'BUTTON DOWN', 'BUTTON UP']

# Default settings
left_switch = 23    # Rotary encoder A
right_switch = 24   # Rotary encoder B
mute_switch = 27    # Rotary encoder push switch (Mute)
down_switch = 4     # Push button 2 Channel DOWN
menu_switch = 5     # Push button 3 Menu functions
up_switch =  6      # Push button 1 Channel UP

def interrupt(gpio):
    global up_switch,down_switch,menu_switch
    print("Button pressed on GPIO", gpio)

    if gpio == down_switch:
        statusLed.set(StatusLed.LED1)
    elif gpio == menu_switch:
        statusLed.set(StatusLed.LED2)
    elif gpio == up_switch:
        statusLed.set(StatusLed.LED3)
        
        return

# Test only - No event sent
def rotary_event(event):
    name = ''
    try:
            name = Names[event]
    except:
            name = 'ERROR'

    if event == RotaryEncoder.CLOCKWISE:
        statusLed.set(StatusLed.LED3)
    elif event == RotaryEncoder.ANTICLOCKWISE:
        statusLed.set(StatusLed.LED1)
    else:
        statusLed.set(StatusLed.CLEAR)

        print("Rotary event ", event, name)
        return

# Configure RGB status LED
def statusLedInitialise(statusLed):
    rgb_red = config.getRgbLed('rgb_red')
    rgb_green = config.getRgbLed('rgb_green')
    rgb_blue = config.getRgbLed('rgb_blue')
    statusLed = StatusLed(rgb_red,rgb_green,rgb_blue)
    print("statusLed",rgb_red,rgb_green,rgb_blue)
    return statusLed

if __name__ == "__main__":

    from rotary_class import RotaryEncoder
    from status_led_class import StatusLed
    from config_class import Configuration
    from log_class import Log

    config = Configuration()
    log = Log()
    if len(log.getName()) < 1:
        log.init("radio")

    print("Test Cosmic Controller Class")
    getConfig = False
    
    # Get configuration
    if getConfig:
        left_switch = config.getSwitchGpio("left_switch")
        right_switch = config.getSwitchGpio("right_switch")
        mute_switch = config.getSwitchGpio("mute_switch")
        up_switch = config.getSwitchGpio("up_switch")
        down_switch = config.getSwitchGpio("down_switch")
        menu_switch = config.getSwitchGpio("menu_switch")

    print("Left switch GPIO", left_switch)
    print("Right switch GPIO", right_switch)
    print("Up switch GPIO", up_switch)
    print("Down switch GPIO", down_switch)
    print("Mute switch GPIO", mute_switch)
    print("Menu switch GPIO", menu_switch)

    Button(down_switch, interrupt, log)
    Button(up_switch, interrupt, log)
    Button(menu_switch, interrupt, log)

    volumeknob = RotaryEncoder(left_switch, right_switch,mute_switch,rotary_event)

    statusLed = statusLedInitialise(statusLed)
    statusLed.set(StatusLed.LED1)
    time.sleep(1)
    statusLed.set(StatusLed.LED2)
    time.sleep(1)
    statusLed.set(StatusLed.LED3)
    time.sleep(1)
    statusLed.set(StatusLed.ALL)
    time.sleep(1)
    statusLed.set(StatusLed.CLEAR)
    time.sleep(1)

    # Main wait loop
    try:
        while True:
            time.sleep(0.2)

    except KeyboardInterrupt:
            print(" Stopped")
            sys.exit(0)

# End of script
# :set tabstop=4 shiftwidth=4 expandtab
# :retab
