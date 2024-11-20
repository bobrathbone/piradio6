#!/usr/bin/env python3
# $Id: rotary_class_alternative.py,v 1.9 2002/01/23 15:33:05 bob Exp $
#
# Raspberry Pi Alternative Rotary Encoder Class
# Certain Rotary Encoders will not work with the current version of the Rotary class.
# For example those from TT Electronics
# To use this alternative rotary class save the standard one first and copy the alternative one
#   cp rotary_class.py rotary_class.py.orig
#   cp rotary_class.py.alternative rotary_class.py
# Restart the radio
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class uses standard rotary encoder with push switch
# 
# 
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.
#

import os,sys,pwd
import time
import RPi.GPIO as GPIO
import threading

class RotaryEncoderAlternative:

    CLOCKWISE=1
    ANTICLOCKWISE=2
    BUTTONDOWN=3
    BUTTONUP=4

    rotary_a = 0
    rotary_b = 0
    rotary_c = 0
    last_state = 0
    direction = 0

    # Initialise rotary encoder object
    def __init__(self,pinA,pinB,button,callback,ky040_r1_fitted=False):
        t = threading.Thread(target=self._run,args=(pinA,pinB,button,callback,ky040_r1_fitted))
        t.daemon = True
        t.start()

    def _run(self, pinA, pinB, button, callback, ky040_r1_fitted):
        self.pinA = pinA
        self.pinB = pinB
        self.button = button
        self.callback = callback

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        try:
            # The following lines enable the internal pull-up resistors
            # on version 2 (latest) boards
            if pinA > 0 and pinB > 0:
                GPIO.setup(self.pinA, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                GPIO.setup(self.pinB, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                # Add event detection to the GPIO inputs
                GPIO.add_event_detect(self.pinA, GPIO.BOTH, callback=self.switch_event)
                GPIO.add_event_detect(self.pinB, GPIO.BOTH, callback=self.switch_event)
            if button > 0:
                gpio = self.button
                if ky040_r1_fitted:
                    GPIO.setup(self.button, GPIO.IN, pull_up_down=GPIO.PUD_OFF)
                else:
                    GPIO.setup(self.button, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                # Add event detection to the GPIO inputs
                GPIO.add_event_detect(self.button, GPIO.BOTH, callback=self.button_event, 
                                       bouncetime=200)
            
        except Exception as e:
            print("Rotary Encoder initialise error GPIO %s %s" % (gpio,str(e)))
            sys.exit(1)

    # Call back routine called by switch events
    def switch_event(self,switch):
        if GPIO.input(self.pinA):
            self.rotary_a = 1
        else:
            self.rotary_a = 0

        if GPIO.input(self.pinB):
            self.rotary_b = 1
        else:
            self.rotary_b = 0

        self.rotary_c = self.rotary_a ^ self.rotary_b
        new_state = self.rotary_a * 4 + self.rotary_b * 2 + self.rotary_c * 1
        delta = (new_state - self.last_state) % 4
        self.last_state = new_state
        event = 0

        if delta == 1:
            if self.direction == self.CLOCKWISE:
                # print "Clockwise"
                event = self.direction
            else:
                self.direction = self.CLOCKWISE
        elif delta == 3:
            if self.direction == self.ANTICLOCKWISE:
                # print "Anticlockwise"
                event = self.direction
            else:
                self.direction = self.ANTICLOCKWISE
        if event > 0:
            self.callback(event)
        return

    # Push button down event
    def button_event(self,button):
        # Ignore Button Up events
        print("button_event",button)
        if self.buttonPressed(button):
            self.callback(self.BUTTONDOWN)
        return

    # Get a button state - returns 1 or 0
    def getButtonState(self, button):
        return  GPIO.input(button)

    def buttonPressed(self,button):
        time.sleep(0.05)
        state = self.getButtonState(button)
        if state == 1:
            pressed = False
        else:
            pressed = True
        return pressed

# End of RotaryEncoder class

### Test routine ###

Names = ['NO_EVENT', 'CLOCKWISE', 'ANTICLOCKWISE', 'BUTTONDOWN', 'BUTTONUP']

# Volume event - test only - no event generation
def volume_event(event):
        name = ''
        try:
                name = Names[event]
        except:
                name = 'ERROR'

        print("Volume event ", event, name)
        return

# Tuner event - test only - no event generation
def tuner_event(event):
        name = ''
        try:
                name = Names[event]
        except:
                name = 'ERROR'

        print("Tuner event ", event, name)
        return

if __name__ == "__main__":

    from config_class import Configuration
    config = Configuration()

    print("Test rotary encoder Class")

    # Get configuration
    left_switch = config.getSwitchGpio("left_switch")
    right_switch = config.getSwitchGpio("right_switch")
    mute_switch = config.getSwitchGpio("mute_switch")
    down_switch = config.getSwitchGpio("down_switch")
    up_switch = config.getSwitchGpio("up_switch")
    menu_switch = config.getSwitchGpio("menu_switch")

    if config.rotary_step_size:
        step_size = 'half'
    else:
        step_size = 'full'

    ky040_r1_fitted = config.ky040_r1_fitted
    if ky040_r1_fitted:
        r1_fitted = 'yes'
    else:
        r1_fitted = 'no'

    print("Left switch GPIO", left_switch)
    print("Right switch GPIO", right_switch)
    print("Up switch GPIO", up_switch)
    print("Down switch GPIO", down_switch)
    print("Mute switch GPIO", mute_switch)
    print("Menu switch GPIO", menu_switch)
    print("Rotary encoder step size =", step_size)
    print("KY040 rotary encoder R1 resistor fitted =", ky040_r1_fitted)

    volumeknob = RotaryEncoderAlternative(left_switch,right_switch,mute_switch,volume_event)
    tunerknob = RotaryEncoderAlternative(down_switch,up_switch,menu_switch,tuner_event)

    print("Waiting for events")
    try:
        while True:
            time.sleep(0.05)

    except KeyboardInterrupt:
        print(" Stopped")
        sys.exit(0)

# End of script
# set tabstop=4 shiftwidth=4 expandtab
# retab
