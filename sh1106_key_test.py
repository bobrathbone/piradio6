#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# $Id: sh1106_key_test.py,v 1.1 2023/09/14 07:18:04 bob Exp $
# Author :      Waveshare team (https://www.waveshare.com/)
# Modified by : Bob Rathbone
# Site :        http://www.bobrathbone.com
#
# Modified from original Waveshare SH1106 driver code
# See: https://files.waveshare.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#          The authors shall not be liable for any loss or damage however caused.
#

import time
#import config
import sh1106_config
import traceback
from sh1106_class import SH1106

import RPi.GPIO as GPIO

import time
import subprocess

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

#GPIO define
RST_PIN        = 25
CS_PIN         = 8
DC_PIN         = 24

KEY_UP_PIN     = 6 
KEY_DOWN_PIN   = 19
KEY_LEFT_PIN   = 5
KEY_RIGHT_PIN  = 26
KEY_PRESS_PIN  = 13

KEY1_PIN       = 21
KEY2_PIN       = 20
KEY3_PIN       = 16


# 240x240 display with hardware SPI:
disp = SH1106()
disp.init(callback=None)

# Clear display.
disp.clear()
# time.sleep(1)

#init GPIO
# for P4:
# sudo vi /boot/config.txt
# gpio=6,19,5,26,13,21,20,16=pu
GPIO.setmode(GPIO.BCM) 
GPIO.setup(KEY_UP_PIN,      GPIO.IN, pull_up_down=GPIO.PUD_UP)    # Input with pull-up
GPIO.setup(KEY_DOWN_PIN,    GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
GPIO.setup(KEY_LEFT_PIN,    GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Input with pull-up
GPIO.setup(KEY_RIGHT_PIN,   GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(KEY_PRESS_PIN,   GPIO.IN, pull_up_down=GPIO.PUD_UP) # Input with pull-up
GPIO.setup(KEY1_PIN,        GPIO.IN, pull_up_down=GPIO.PUD_UP)      # Input with pull-up
GPIO.setup(KEY2_PIN,        GPIO.IN, pull_up_down=GPIO.PUD_UP)      # Input with pull-up
GPIO.setup(KEY3_PIN,        GPIO.IN, pull_up_down=GPIO.PUD_UP)      # Input with pull-up

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
image = Image.new('1', (disp.width, disp.height), "WHITE")

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# try:
while 1:
    # with canvas(device) as draw:
    if GPIO.input(KEY_UP_PIN): # button is released
        draw.polygon([(20, 20), (30, 2), (40, 20)], outline=255, fill=0)  #Up
    else: # button is pressed:
        draw.polygon([(20, 20), (30, 2), (40, 20)], outline=255, fill=1)  #Up filled
        print("Up")
        
    if GPIO.input(KEY_LEFT_PIN): # button is released
        draw.polygon([(0, 30), (18, 21), (18, 41)], outline=255, fill=0)  #left
    else: # button is pressed:
        draw.polygon([(0, 30), (18, 21), (18, 41)], outline=255, fill=1)  #left filled
        print("left")
        
    if GPIO.input(KEY_RIGHT_PIN): # button is released
        draw.polygon([(60, 30), (42, 21), (42, 41)], outline=255, fill=0) #right
    else: # button is pressed:
        draw.polygon([(60, 30), (42, 21), (42, 41)], outline=255, fill=1) #right filled
        print("right")
        
    if GPIO.input(KEY_DOWN_PIN): # button is released
        draw.polygon([(30, 60), (40, 42), (20, 42)], outline=255, fill=0) #down
    else: # button is pressed:
        draw.polygon([(30, 60), (40, 42), (20, 42)], outline=255, fill=1) #down filled
        print("down")

    if GPIO.input(KEY_PRESS_PIN): # button is released
        draw.rectangle((20, 22,40,40), outline=255, fill=0) #center 
    else: # button is pressed:
        draw.rectangle((20, 22,40,40), outline=255, fill=1) #center filled
        print("center")
        
    if GPIO.input(KEY1_PIN): # button is released
        draw.ellipse((70,0,90,20), outline=255, fill=0) #A button
    else: # button is pressed:
        draw.ellipse((70,0,90,20), outline=255, fill=1) #A button filled
        print("KEY1")
        
    if GPIO.input(KEY2_PIN): # button is released
        draw.ellipse((100,20,120,40), outline=255, fill=0) #B button]
    else: # button is pressed:
        draw.ellipse((100,20,120,40), outline=255, fill=1) #B button filled
        print("KEY2")
        
    if GPIO.input(KEY3_PIN): # button is released
        draw.ellipse((70,40,90,60), outline=255, fill=0) #A button
    else: # button is pressed:
        draw.ellipse((70,40,90,60), outline=255, fill=1) #A button filled
        print("KEY3")
        
    disp.ShowImage(disp.getbuffer(image))
    
# except:
	# print("except")
# GPIO.cleanup()
