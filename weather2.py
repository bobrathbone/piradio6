#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Weather station class
# $Id: weather2.py,v 1.9 2024/08/01 14:13:06 bob Exp $
#
# Author: Bob Rathbone
# Site   : https://www.bobrathbone.com/
# Code extracts from Pimoroni Ltd
# Site   : https://shop.pimoroni.com/
#
# This program interrogates openweathermap weather service for the specified location and displays
# it on the configured display in /etc/radiod.conf
# See https://openweathermap.org for weather information
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#

import sys
import os
import time
import pdb
import signal
import subprocess
import socket
import RPi.GPIO as GPIO

from time import strftime
from display_class import Display
from translate_class import Translate
from weather_class import Weather
from wxconfig_class import Configuration

wxconfig = Configuration()
weather = Weather()
translate = Translate()
display = Display(translate)
ip_addr = ''  # Local IP address

#lines = display.getLines()
lines = 4
wx = None

# Return date and time
def getDateTime():
    todaysdate = strftime(wxconfig.date_format)
    return todaysdate

# Display weather
def displayWeather(getnew):
    global wx

    if getnew:
        try:
            wx = weather.get()
            print(wx)
            print('\n')
        except Exception as e:
            print(str(e))
            pass
    try:
        location = wx['location']
        temperature = wx['temperature']
        units = wx['units']
        temp_units = wx['temp_units']
        humidity = wx['humidity']
        pressure = wx['pressure']
        pressure_units = wx['pressure_units']
        summary = wx['summary']
        clouds = wx['clouds']
        if int(clouds) > 0:
            clouds = clouds + '%'
        else:
            clouds = ''
    except:
        display.out(2,wx)
        sys.exit(1)

    if lines > 2:
        display.out(2,location)
        display.out(3,"%s%s %s%s %s" % (temperature,temp_units,pressure,pressure_units,humidity))
        display.out(4,"%s %s" % (summary.capitalize(),clouds))
    else:
        display.out(1,"%s%s %s%s %s" % (temperature,temp_units,pressure,pressure_units,humidity))
        display.out(2,"%s %s" % (summary.capitalize(),clouds))

# Signal SIGTERM handler
def signalHandler(signal,frame):
    display.clear()
    display.out(1,"End of progrram")
    time.sleep(3)
    sys.exit(0)

# Get IP address
def get_ip():
    global ip_addr
    if len(ip_addr) < 7:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            # Google DNS
            s.connect(('8.8.8.8', 1))
            ip_addr = s.getsockname()[0]
        except Exception:
            IP = ''
        finally:
            s.close()
    return ip_addr

# Wait for the network
def waitForNetwork():
    ipaddr = ""
    waiting4network = True
    count = 30
    while waiting4network:
        ipaddr = get_ip()
        if (count < 0) or (len(ipaddr) > 3):
            waiting4network = False
        else:
            time.sleep(0.5)
    return ipaddr

# Main weather display routine
if __name__ == '__main__':

    # This is the radio configuration in /etc/radiod.conf
    from config_class import Configuration
    config = Configuration()
    from event_class import Event

    signal.signal(signal.SIGTERM,signalHandler)
    signal.signal(signal.SIGHUP,signalHandler)

    # Display on same screen as radio 
    # display.init()     # Initialise

    # Display weather on a second screen

    display2_type = wxconfig.display_type
    luma_name = wxconfig.luma_device
    display2_i2c = wxconfig.i2c_address
    callback = None
    display.init(callback,display2_type,display2_i2c,luma_name)
    
    ip_addr = waitForNetwork()
    
    # Only initialise if there is an IP address
    if len(ip_addr) > 7:
        weather.init()
    else:
        print("No network found - Exiting")
        sys.exit(1)

    count = 0
    getnew = True

    while True:
        try:
            if display.lines > 2:
                display.out(1,getDateTime())
            try:
                displayWeather(getnew)
            except:
                pass
            if count < 1:   
                count = 300
                getnew = True 
            else:
                count -= 1
                time.sleep(1)
                getnew = False 

        except KeyboardInterrupt:
            display.clear()
            exit(0)

# End of script 

# set tabstop=4 shiftwidth=4 expandtab
# retab
