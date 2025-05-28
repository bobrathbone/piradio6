#!/usr/bin/env python3
#
# Raspberry Pi Event class
#
# $Id: event_class.py,v 1.42 2025/05/12 19:11:08 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class is the front end to underlying  classes which generate events
# The incomming events are translated to standard events which are passed
# on to the main program for further handling.
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#

import os,sys
import time,pwd

from rotary_class import RotaryEncoder
from rotary_class_alternative import RotaryEncoderAlternative
from rotary_class_rgb import RotaryEncoderRgb
from log_class import Log
from constants import *
from rotary_switch_class import RotarySwitch
import RPi.GPIO as GPIO
import pdb

log = Log()
volumeknob = None
tunerknob = None
rotary_switch = None

# Buttons
left_button = None
right_button = None
mute_button = None
up_button = None
down_button = None
menu_button = None
record_button = None

# If no interrupt required
def no_interrupt():
        return False

class Event():
    config = None
    
    # Event definitions
    NO_EVENT = 0

    # Volume control buttons amd mute
    RIGHT_SWITCH = 1
    LEFT_SWITCH  = 2
    MUTE_BUTTON_DOWN = 3
    MUTE_BUTTON_UP = 4

    # Channnel change switches and menu
    UP_SWITCH    = 5
    DOWN_SWITCH  = 6
    MENU_BUTTON_DOWN = 7
    MENU_BUTTON_UP = 8

    # Alarm and timer events
    ALARM_FIRED = 9
    TIMER_FIRED = 10

    # Other reEvents from the IR receiever
    KEY_LANGUAGE = 11
    KEY_INFO = 12

    # Event from the retro radio rotary switch (not encoder!)
    ROTARY_SWITCH_CHANGED = 13
    
    # MP client change
    MPD_CLIENT_CHANGE = 14

    # Events from the Web interface
    LOAD_RADIO = 15     # Used by web interface v1.7
    LOAD_MEDIA = 16     #   ditto
    LOAD_PLAYLIST = 17  # Used by web interface v1.8 onwards
    LOAD_AIRPLAY = 18
    LOAD_SPOTIFY = 19

    # Playlist events
    PLAYLIST_CHANGED = 20

    # PLAY COMMAND
    PLAY = 21

    RECORD_BUTTON = 22

    # Shutdown radio
    SHUTDOWN = 23

    # Alternate event names (easier to understand code )
    VOLUME_UP = RIGHT_SWITCH
    VOLUME_DOWN = LEFT_SWITCH
    CHANNEL_UP = UP_SWITCH
    CHANNEL_DOWN = DOWN_SWITCH

    event_type = NO_EVENT
    event_triggered = False

    eventNames = ['NO_EVENT', 'RIGHT_SWITCH', 'LEFT_SWITCH', 'MUTE_BUTTON_DOWN', 
              'MUTE_BUTTON_UP', 'UP_SWITCH', 'DOWN_SWITCH', 'MENU_BUTTON_DOWN',
              'MENU_BUTTON_UP', 'ALARM_FIRED', 'TIMER_FIRED', 'KEY_LANGUAGE',
              'KEY_INFO', 'ROTARY_SWITCH_CHANGE', 'MPD_CLIENT_CHANGE', 
              'LOAD_RADIO', 'LOAD_MEDIA', 'LOAD_PLAYLIST', 'LOAD_AIRPLAY', 
              'LOAD_SPOTIFY','PLAYLIST_CHANGED','PLAY','RECORD_BUTTON','SHUTDOWN',
             ]

    encoderEventNames = [ 'NONE', 'CLOCKWISE', 'ANTICLOCKWISE',
                  'BUTTONDOWN', 'BUTTONUP']

    # Switches GPIO configuration
    left_switch = 14
    right_switch = 15
    mute_switch = 4
    up_switch = 24
    down_switch = 23
    menu_switch = 17
    record_switch = 0

    rotary_switch_value = 0

    # Configuration 
    user_interface = 0
    display_type = 0

    play_number = 0     # Play number (from remote control)

    # Initialisation routine
    def __init__(self,config):
        self.config = config
        log.init('radio')
        self.getConfiguration()
        self.setInterface()
        self.setupRotarySwitch()
        self.setRecordButton()
        return

    # Call back routine for the volume control knob
    def volume_event(self,event):
        global volumeknob
        self.event_type = self.NO_EVENT

        encoderEventName = self.getEncoderEventName(event)
        log.message("Volume event:" + str(event) + ' ' + encoderEventName, log.DEBUG)

        self.event_triggered = True

        if event == RotaryEncoder.CLOCKWISE:
            self.event_type = self.VOLUME_UP

        elif event == RotaryEncoder.ANTICLOCKWISE:
            self.event_type = self.VOLUME_DOWN

        elif event ==  RotaryEncoder.BUTTONDOWN:
            self.event_type = self.MUTE_BUTTON_DOWN

        elif event ==  RotaryEncoder.BUTTONUP:
            self.event_type = self.MUTE_BUTTON_UP

        else:
            self.event_triggered = False
        return

    # Call back routine for the tuner control 
    def tuner_event(self,event):
        global tunerknob
        self.event_type = self.NO_EVENT
        self.event_triggered = True

        encoderEventName = self.getEncoderEventName(event)
        log.message("Tuner event:" + str(event) + ' ' + encoderEventName, log.DEBUG)

        if event == RotaryEncoder.CLOCKWISE:
            self.event_type = self.CHANNEL_UP

        elif event == RotaryEncoder.ANTICLOCKWISE:
            self.event_type = self.CHANNEL_DOWN

        elif event ==  RotaryEncoder.BUTTONDOWN:
            self.event_type = self.MENU_BUTTON_DOWN

            # Holding the menu button for 3 seconds down shuts down the radio
            count = 15 
            while tunerknob.buttonPressed(self.menu_switch):
                time.sleep(0.2)
                count -= 1
                if count < 0:
                    self.event_type = self.SHUTDOWN
                    self.event_triggered = True
                    break

        elif event ==  RotaryEncoder.BUTTONUP:
            self.event_type = self.MENU_BUTTON_UP

        else:
            self.event_triggered = False

        return self.event_type

    # This is the record button to start liquidsoap
    def record_button_event(self,event):
        msg = "Record button event:" + str(event)
        log.message(msg, log.DEBUG)
        while record_button.pressed():
            time.sleep(0.1)
        time.sleep(1)
        self.event_type = self.RECORD_BUTTON
        self.event_triggered = True
        return self.event_type

    # Call back routine button events (Not rotary encoder buttons)
    def button_event(self,event):
        global up_switch,down_switch
        msg = "Button event:" + str(event)
        log.message(msg, log.DEBUG)
        self.event_triggered = True

        # Convert button event to standard events
        if event == self.right_switch:
            self.event_type = self.VOLUME_UP

        elif event == self.left_switch:
            self.event_type = self.VOLUME_DOWN

        elif event == self.mute_switch:
            self.event_type = self.MUTE_BUTTON_DOWN

        elif event == self.up_switch:
            self.event_type = self.CHANNEL_UP

        elif event == self.down_switch:
            self.event_type = self.CHANNEL_DOWN

        elif event == self.menu_switch:
            self.event_type = self.MENU_BUTTON_DOWN

            # Holding the menu button for 3 seconds down shuts down the radio
            count = 15 
            while menu_button.pressed():
                time.sleep(0.1)
                count -= 1
                if count < 0:
                    self.event_type = self.SHUTDOWN
                    self.event_triggered = True
                    break
        else:
            self.event_triggered = False
        return

    # Call back routine rotary switch events (Not rotary encoder buttons)
    def rotary_switch_event(self,event):
        log.message("Rotary switch event value:" + str(event), log.DEBUG)
        self.event_triggered = True
        time.sleep(1)   # Allow switch to settle
        self.rotary_switch_value = rotary_switch.get()
        self.set(self.ROTARY_SWITCH_CHANGED)
        return

    # Get rotary switch (not rotary encoders!)
    def getRotarySwitch(self):
        return self.rotary_switch_value

    # Set event for radio functions
    def set(self,event):
        self.event_triggered = True
        self.event_type = event
        return self.event_type

    # Check for event True or False
    def detected(self):
        return self.event_triggered

    # Get the event type  
    def getType(self):
        return self.event_type

    # Clear event an set triggered to False
    def clear(self):
        if self.event_type != self.NO_EVENT:
            sName = " " + self.getName()
            log.message("Clear event " + str(self.event_type) + sName, log.DEBUG)
        self.event_triggered = False
        self.event_type = self.NO_EVENT
        return 

    # Get the event name 
    def getName(self):
        return self.eventNames[self.event_type]

    # Get the event name 
    def getEncoderEventName(self,event):
        return self.encoderEventNames[event]

    # Repeat on volume down button 
    def leftButtonPressed(self):
        global left_button
        pressed = False
        if left_button != None:
            pressed =  left_button.pressed()
            if pressed:
                self.set(self.VOLUME_DOWN)
        return pressed

    # Repeat on volume up button 
    def rightButtonPressed(self):
        global right_button
        pressed = False
        if right_button != None:
            pressed =  right_button.pressed()
            if pressed:
                self.set(self.VOLUME_UP)
        return pressed

    def upButtonPressed(self):
        global up_button
        pressed = False
        if up_button != None:
            pressed =  up_button.pressed()
        return pressed

    def downButtonPressed(self):
        global down_button
        pressed = False
        if down_button != None:
            pressed =  down_button.pressed()
        return pressed

    # See if mute button held
    def muteButtonPressed(self):
        global mute_button
        pressed = False

        if volumeknob != None:
            pressed = volumeknob.buttonPressed(self.mute_switch)

        elif mute_button != None:
            pressed =  mute_button.pressed()

        return pressed

    # Record button
    def recordButtonPressed(self):
        global record_switch
        pressed = False
        if down_button != None:
            pressed =  record_switch.pressed()
        return pressed

    def getConfiguration(self):
        userInterfaces = ["Rotary encoders", "Buttons", "Touchscreen",
                  "Cosmic controller", "Piface CAD"]
        rotaryClasses = ["Standard", "Alternative"]
        self.user_interface = self.config.user_interface
        self.display_type = self.config.getDisplayType()
        log.message("User interface: " + userInterfaces[self.user_interface], log.DEBUG)
        return

    # Get switches GPIO configuration
    def getGPIOs(self):
        log.message("event.getGPIOs", log.DEBUG)
        self.left_switch = self.config.getSwitchGpio("left_switch")
        self.right_switch = self.config.getSwitchGpio("right_switch")
        self.mute_switch = self.config.getSwitchGpio("mute_switch")
        self.down_switch = self.config.getSwitchGpio("down_switch")
        self.up_switch = self.config.getSwitchGpio("up_switch")
        self.menu_switch = self.config.getSwitchGpio("menu_switch")
        self.record_switch = self.config.getSwitchGpio("record_switch")
        return

    # Configure rotary switch (not rotary encoders!)
    def setupRotarySwitch(self):
        global  rotary_switch
        switch1 = self.config.getMenuSwitch('menu_switch_value_1')
        switch2 = self.config.getMenuSwitch('menu_switch_value_2')
        switch4 = self.config.getMenuSwitch('menu_switch_value_4')

        if switch1 > 0 and switch2 > 0 and switch4 > 0:
            rotary_switch = RotarySwitch(switch1,switch2, \
                switch4,self.rotary_switch_event)
        return

    # Configure the user interface (either buttons or rotary encoders)
    def setInterface(self):
        log.message("event.setInterface " + str(self.user_interface), log.DEBUG)
        self.getGPIOs()     # Get GPIO configuration

        if self.user_interface == self.config.ROTARY_ENCODER:
            self.setRotaryInterface()

        # The Adafruit and Piface CAD interfaces use I2C and SPI respectively
        elif self.user_interface == self.config.BUTTONS \
                    and self.display_type != self.config.LCD_ADAFRUIT_RGB \
                    and self.display_type != self.config.PIFACE_CAD:
            self.setButtonInterface()
                
        elif self.user_interface == self.config.GRAPHICAL:
            # Log only
            log.message("event.setInterface Graphical/Touchscreen", log.DEBUG)

        elif self.user_interface == self.config.COSMIC_CONTROLLER:
            self.setCosmicInterface()


    # Set up rotary encoders interface
    def setRotaryInterface(self):
        global tunerknob
        global volumeknob

        # Internal pullup resistors can be disabled for rotary encoders (eg KY-040)
        # with their own pullup resistors. See rotary_gpio_pullup in radiod.conf

        if self.config.rotary_class == self.config.ALTERNATIVE:
            log.message("event.setInterface RotaryEncoder ALTERNATIVE", log.DEBUG)
            volumeknob = RotaryEncoderAlternative(self.left_switch, self.right_switch,
                    self.mute_switch,self.volume_event)
            tunerknob = RotaryEncoderAlternative(self.down_switch, self.up_switch,
                    self.menu_switch,self.tuner_event)

        elif self.config.rotary_class == self.config.STANDARD:
            log.message("event.setInterface RotaryEncoder STANDARD", log.DEBUG)

            volumeknob = RotaryEncoder(self.left_switch, self.right_switch,
                    self.mute_switch,self.volume_event,
                    rotary_step_size=self.config.rotary_step_size,
                    ky040_r1_fitted=self.config.ky040_r1_fitted)

            tunerknob = RotaryEncoder(self.down_switch, self.up_switch,
                    self.menu_switch,self.tuner_event, 
                    rotary_step_size=self.config.rotary_step_size,
                    ky040_r1_fitted=self.config.ky040_r1_fitted)
    
        elif self.config.rotary_class == self.config.RGB_ROTARY:
            log.message("event.setInterface RotaryEncoder RGB_ROTARY", log.DEBUG)

            volumeknob = RotaryEncoderRgb(self.left_switch, self.right_switch,
                    self.mute_switch,self.volume_event,pullup=self.config.rotary_gpio_pullup)

            tunerknob = RotaryEncoderRgb(self.down_switch, self.up_switch,
                    self.menu_switch,self.tuner_event,pullup=self.config.rotary_gpio_pullup)
    
        elif self.config.rotary_class == self.config.RGB_I2C_ROTARY:
            volume_i2c = self.config.volume_rgb_i2c
            tuner_i2c = self.config.channel_rgb_i2c
            volume_interrupt_pin = 22
            tuner_interrupt_pin = 23
            from rotary_class_rgb_i2c import RGB_I2C_RotaryEncoder

            volumeknob = RGB_I2C_RotaryEncoder(volume_i2c,self.mute_switch,
                            self.volume_event,volume_interrupt_pin)
            tunerknob = RGB_I2C_RotaryEncoder(tuner_i2c,self.menu_switch,
                        self.tuner_event,tuner_interrupt_pin)

            volumeknob.run(True)
            tunerknob.run(True)
    
        elif self.config.rotary_class == self.config.ROTARY_GPIOZERO:
            from rotary_class_gpiozero  import RotaryEncoderClass
            log.message("event.setInterface RotaryEncoder ROTARY_GPIOZERO", log.DEBUG)

            volumeknob = RotaryEncoderClass(self.left_switch, self.right_switch,
                    self.mute_switch,self.volume_event)

            tunerknob = RotaryEncoderClass(self.down_switch, self.up_switch,
                    self.menu_switch,self.tuner_event) 

        if self.config.rotary_class == self.config.RGB_I2C_ROTARY:
            msg = "Volume knob i2c address %s, mute switch %s interrupt_pin %d" \
                    % (hex(volume_i2c),self.mute_switch,volume_interrupt_pin)
            log.message(msg, log.DEBUG)
            msg = "Tuner knob i2c address %s, mute switch %s interrupt_pin %d" % \
                    (hex(tuner_i2c),self.menu_switch,tuner_interrupt_pin)
            log.message(msg, log.DEBUG)
        else:
            msg = "Volume knob", self.left_switch, self.right_switch, self.mute_switch
            log.message(msg, log.DEBUG)
            msg = "Tuner knob", self.down_switch, self.up_switch,self.menu_switch
            log.message(msg, log.DEBUG)
        return

    # Set up buttons interface
    def setButtonInterface(self):
        from button_class import Button
        global left_button,right_button,mute_button  
        global up_button,down_button,menu_button

        # Get pull up/down resistor configuration
        up_down = self.config.pull_up_down
        
        log.message("event.setInterface Push Buttons pull_up_down=" + str(up_down), 
                        log.DEBUG)
        left_button = Button(self.left_switch,self.button_event,log,pull_up_down=up_down)
        right_button = Button(self.right_switch,self.button_event,log,pull_up_down=up_down)
        down_button = Button(self.down_switch,self.button_event,log,pull_up_down=up_down)
        up_button = Button(self.up_switch,self.button_event,log,pull_up_down=up_down)
        mute_button = Button(self.mute_switch,self.button_event,log,pull_up_down=up_down)
        menu_button = Button(self.menu_switch,self.button_event,log,pull_up_down=up_down)

    # Set up the record button (This is always from high to low when pressed)
    def setRecordButton(self):
        global record_button
        if self.record_switch > 0:
            from button_class import Button
            record_button = Button(self.record_switch,self.record_button_event,log,UP)

    # Set up IQAudio cosmic controller interface
    def setCosmicInterface(self):
        from cosmic_class import Button
        global volumeknob
        global left_button,right_button,mute_button  
        global up_button,down_button,menu_button 
        log.message("event.setInterface Cosmic interface", log.DEBUG)

        # Buttons
        down_button = Button(self.down_switch,self.button_event,log)
        up_button = Button(self.up_switch,self.button_event,log)
        menu_button = Button(self.menu_switch,self.button_event,log)

        # Rotary encoder
        volumeknob = RotaryEncoder(self.left_switch, self.right_switch,
                self.mute_switch,self.volume_event)
        return

    # Get the volume knob interface
    def getVolumeKnob(self):
        return volumeknob

    # Check if menu button held down
    def menuPressed(self):
        pressed = False
        global menu_button
        if self.user_interface == self.config.BUTTONS:
            pressed = menu_button.pressed()
        elif self.user_interface == self.config.ROTARY_ENCODER:
            pressed = tunerknob.buttonPressed(self.menu_switch)
        return pressed

# End of Event class

### Main routine ###
# Creates the event object and prints event number and name
if __name__ == "__main__":

    from config_class import Configuration
    config = Configuration() 

    event = Event(config)
    print ("Waiting for events:")

    try: 
        while True:
            if event.detected():
                type = event.getType()
                name = event.eventNames[int(type)]
                if type != event.NO_EVENT:
                    print("Event %d %s" % (type,name))
                event.clear()
            else:
                time.sleep(0.01)

    except KeyboardInterrupt:
        print(" Stopped")
        sys.exit(0)


# End of script

# set tabstop=4 shiftwidth=4 expandtab
# retab

