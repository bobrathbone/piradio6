#!/usr/bin/env python3
# Raspberry Pi Rotary Encoder Class
# $Id: new_rotary_class.py,v 1.5 2025/02/12 17:43:39 bob Exp $
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

from gpiozero import Button, RotaryEncoder
import os,sys,pwd
import time
import threading
import pdb

class RotaryEncoderClass:
    pinA = None
    pinB = None
    CLOCKWISE=1
    ANTICLOCKWISE=2
    BUTTONDOWN=3
    BUTTONUP=4

    eventNames = ('NO_EVENT','CLOCKWISE','ANTICLOCKWISE','BUTTONDOWN','BUTTONUP')

    current_rotary_value = 0

    def __init__(self, pinA, pinB,button,callback):
        t = threading.Thread(target=self._run,args=(pinA,pinB,button,callback))
        t.daemon = True
        t.start()

    def _run(self,pinA,pinB,button,callback):
        self.pinA = pinA
        self.pinB = pinB
        self.button = button
        self.callback = callback

        try:
            push_button = Button(self.button)
            push_button.when_pressed = button_event
            ### push_button.when_released = released
        except Exception as e:
            print("Rotary Encoder initialise error GPIO %s %s" % (self.button,str(e)))
            sys.exit(1)

        try:
            self.rotary_encoder = RotaryEncoder(self.pinA,self.pinB,wrap=True, max_steps=16)
            self.rotary_encoder.when_rotated = callback

        except Exception as e:
            print("Rotary Encoder initialise error",str(e))
            sys.exit(1)

    # Call back routine called by switch events
    def rotary_event(self, switch):
        print("rotary event",switch)

# End of rotary class


if __name__ == "__main__":

    from config_class import Configuration
    config = Configuration()

    volume_steps = 0
    tuner_steps = 0

    # Push button down event
    def button_event(button_obj):
        print("Button event",button_obj.pin)
    
    # Volume event - test only - No event generation
    def volume_event(volume_obj):
        global volume_steps
        if volumeknob.rotary_encoder.steps > volume_steps:
            event = volumeknob.CLOCKWISE
        else:
            event = volumeknob.ANTICLOCKWISE
        event_name = volumeknob.eventNames[event]
        print("Volume event",event_name)
        volume_steps = volumeknob.rotary_encoder.steps
        
    # Tuner event 
    def tuner_event(tuner_obj):
        global tuner_steps
        if tunerknob.rotary_encoder.steps > tuner_steps:
            event = tunerknob.CLOCKWISE
        else:
            event = tunerknob.ANTICLOCKWISE
        event_name = tunerknob.eventNames[event]
        print("Tuner event",event_name)
        tuner_steps = tunerknob.rotary_encoder.steps

    # Get configuration
    print("Test standard rotary encoder Class")
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
            time.sleep(0.05)

    except KeyboardInterrupt:
        print(" Stopped")
        sys.exit(0)

# End of script
# set tabstop=4 shiftwidth=4 expandtab
# retab
