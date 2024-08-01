#!/usr/bin/env python3
# Raspberry Pi RGB I2C Rotary Encoder Class
# $Id: rgb_dual_i2c.py,v 1.9 2024/06/13 16:05:41 bob Exp $
#
# Author : Bob Rathbone and Lubos Ruckl (Czech republic)
# Site   : http://www.bobrathbone.com
#
# This class is the driver for the Pimoroni I2C RGB Rotary Encoder 
# See https://shop.pimoroni.com/products/rgb-encoder-breakout 
# 
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.
#
# Default I2C addresses
# - 0x0F Volume Rotary Encoder
# - 0x1F Channel Rotary Encoder

import time,sys,os
import colorsys
from rotary_class_rgb_i2c import RGB_I2C_RotaryEncoder
from button_class import Button
from config_class import Configuration
from constants import *
import pdb

config = Configuration()

# Define callbacks
def volume_callback(event):
    print("Volume rotary encoder event", RGB_I2C_RotaryEncoder.sEvents[event])
    handleEvent(event)

def channel_callback(event):
    print("Channel rotary encoder event", RGB_I2C_RotaryEncoder.sEvents[event])
    handleEvent(event)

def mute_event(event):
    print("Mute switch pressed (GPIO %s)" % event)

def menu_event(event):
    print("Menu switch pressed (GPIO %s)" % event)

# Handle event if other actions required 
def handleEvent(event):
    return  

# Set to default adresses or change for addresses in use
volume_i2c = 0x0F
channel_i2c = 0x1F

if __name__ == "__main__":

    print("RGB I2C Dual Rotary Encoder Test")
    print("Volume rotary encoder I2C address %s" % hex(volume_i2c))
    print("Channel rotary encoder I2C address %s" % hex(channel_i2c))
    
    mute_switch = config.getSwitchGpio("mute_switch")
    menu_switch = config.getSwitchGpio("menu_switch")
    print("Mute switch GPIO", mute_switch)
    print("Menu switch GPIO", menu_switch)

    volume_encoder = RGB_I2C_RotaryEncoder(volume_i2c,mute_switch,volume_callback)
    channel_encoder = RGB_I2C_RotaryEncoder(channel_i2c,menu_switch,channel_callback)

    cycle=True # Cycle colours when encoder knob turned
    channel_encoder.run(cycle)
    volume_encoder.run(cycle)
    
    colors = [(255,0,0),(255,255,0),(255,255,255),(0,255,0),(0,255,255),
              (255,0,255),(0,0,255),(255,64,64),(64,64,255),(255,0,0)]

    try:
        print("Started")
        while True:
            for color in colors:
                time.sleep(5)
                volume_encoder.setColor(color)
                channel_encoder.setColor(color)

    except KeyboardInterrupt:
        print(" Stopped")
        sys.exit(0)

# End of script
# set tabstop=4 shiftwidth=4 expandtab
# retab
