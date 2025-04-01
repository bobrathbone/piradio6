#!/usr/bin/env python3
# Raspberry Pi Rotary Encoder Class
# $Id: rotary_class_gpiozero.py,v 1.13 2025/02/20 19:29:30 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#         The authors shall not be liable for any loss or damage however caused.
#

# See GPIOZERO docs
# https://gpiozero.readthedocs.io/en/latest/index.html
# Rotary encoder: https://gpiozero.readthedocs.io/en/latest/api_input.html#rotaryencoder

from gpiozero import Button,RotaryEncoder

import os,sys,pwd
import time
import threading
import pdb

class RotaryEncoderClass:
    pinA = None
    pinB = None
    NOEVENT=0
    CLOCKWISE=1
    ANTICLOCKWISE=2
    BUTTONDOWN=3
    BUTTONUP=4
    buttonobj = None

    current_rotary_value = 0

    # Initialise RotaryEncoderClass in a thread
    def __init__(self, pinA, pinB,button,callback):
        t = threading.Thread(target=self._run,args=(pinA,pinB,button,callback))
        t.daemon = True
        t.start()

    # Set up rotary encoder event detection
    def _run(self,pinA,pinB,button,callback):
        self.pinA = pinA
        self.pinB = pinB
        self.button = button
        self.callback = callback

        try:
            push_button = Button(self.button,bounce_time=0.001,pull_up=True)
            push_button.when_pressed = self.button_down_event
            push_button.when_released = self.button_up_event
        except Exception as e:
            print("Rotary Encoder initialise error GPIO %s %s" % (self.button,str(e)))
            sys.exit(1)

        try:
            self.rotary_encoder = RotaryEncoder(self.pinA,self.pinB,wrap=True,max_steps=64)
            self.rotary_encoder.when_rotated_clockwise = self.rotated_clockwise
            self.rotary_encoder.when_rotated_counter_clockwise = self.rotated_counter_clockwise
        except Exception as e:
            print("Rotary Encoder initialise error",str(e))
            sys.exit(1)

    # Clockwise events
    def rotated_clockwise(self):
        self.callback(self.CLOCKWISE)

    # Counter-Clockwise events
    def rotated_counter_clockwise(self):
        self.callback(self.ANTICLOCKWISE)

    # Button DOWN event
    def button_down_event(self,buttonobj):
        if self.buttonobj == None:
            self.buttonobj = buttonobj
        #print("down value",buttonobj.is_pressed)
        event = self.BUTTONDOWN
        self.callback(event)

    # Button UP event
    def button_up_event(self,buttonobj):
        if self.buttonobj == None:
            self.buttonobj = buttonobj
        #print("up value",buttonobj.is_pressed)
        event = self.BUTTONUP
        self.callback(event)

    def buttonPressed(self,button_gpio):
        #print("active state",self.buttonobj.is_pressed)
        return self.buttonobj.is_pressed

# End of rotary class

if __name__ == "__main__":

    from config_class import Configuration
    config = Configuration()

    eventNames = ('NO_EVENT','CLOCKWISE','ANTICLOCKWISE','BUTTONDOWN','BUTTONUP')

    # Volume event 
    def volume_event(event):
        if event == volumeknob.BUTTONUP or event == volumeknob.BUTTONDOWN:
            print("Volume event",event,eventNames[event],"Mute button pressed",
                   volumeknob.buttonPressed(mute_switch))
        else:
            print("Volume event",event,eventNames[event])
        
    # Tuner event 
    def tuner_event(event):
        if event == tunerknob.BUTTONUP or event == tunerknob.BUTTONDOWN:
            print("Tuner event",eventNames[event],"Menu button pressed",
                   tunerknob.buttonPressed(menu_switch))
        else:
            print("Tuner event",eventNames[event])

    # Get configuration
    print("Test gpiozero rotary encoder Class")
    left_switch = config.getSwitchGpio("left_switch")
    right_switch = config.getSwitchGpio("right_switch")
    mute_switch = config.getSwitchGpio("mute_switch")
    down_switch = config.getSwitchGpio("down_switch")
    up_switch = config.getSwitchGpio("up_switch")
    menu_switch = config.getSwitchGpio("menu_switch")

    print("Left switch GPIO", left_switch)
    print("Right switch GPIO", right_switch)
    print("Up switch GPIO", up_switch)
    print("Down switch GPIO", down_switch)
    print("Mute switch GPIO", mute_switch)
    print("Menu switch GPIO", menu_switch)

    volumeknob = RotaryEncoderClass(left_switch,right_switch,mute_switch,volume_event)
    tunerknob = RotaryEncoderClass(down_switch,up_switch,menu_switch,tuner_event)

    print("Waiting for events")
    try:
        while True:
            time.sleep(0.2)  # Must be more than bounce time

    except KeyboardInterrupt:
        print(" Stopped")
        sys.exit(0)

# End of script
# set tabstop=4 shiftwidth=4 expandtab
# retab
