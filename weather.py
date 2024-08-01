#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Weather station class
# $Id: weather.py,v 1.22 2023/09/26 07:07:06 bob Exp $
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

from time import strftime
from display_class import Display
from translate_class import Translate
from weather_class import Weather
from wxconfig import *
from udp_server_class import UDPServer
from udp_server_class import RequestHandler


weather = Weather()
translate = Translate()
display = Display(translate)

lines = display.getLines()
wx = None

server = None

# Return date and time
def getDateTime():
    todaysdate = strftime(DATE_FORMAT)
    return todaysdate

# Display weather
def displayWeather(getnew):
    global wx

    if getnew:
        wx = weather.get()
        print(wx)
        print('\n')
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
    sys.exit(0)

# Execute a system command
def execCommand(cmd):
    p = os.popen(cmd)
    return  p.readline().rstrip('\n')

# Exit program
def exitProgram():
    display.clear()
    display.out(1,"Program finished")
    cmd = EXIT_COMMAND 
    if len(cmd) > 3:
        print(cmd)
        execCommand(cmd)
    sys.exit(0)

# Call back routine for the IR remote and Web Interface
def remoteCallback():
    global server
    key = server.getData()
    msg = "Remote control sent %s" % key
    print(msg)
    if key == 'KEY_EXIT':
        print("Setting SHUTDOWN event")
        event.set(event.SHUTDOWN)

# Start the UDP server to listen to IR commands
def startUdpServer():
    global server
    # Start the IR remote control listener
    started = False
    try:
        server = UDPServer((UDP_HOST,UDP_PORT),RequestHandler)
        msg = "UDP Server listening on " + UDP_HOST + " port " + str(UDP_PORT)
        print(msg)
        server.listen(server,remoteCallback)
        started = True
    except Exception as e:
        print(str(e))
        print("UDP server could not bind to " + UDP_HOST
                + " port " + str(UDP_PORT))
        return started

# Main weather display routine
from config_class import Configuration
from event_class import Event

config = Configuration()
event = Event(config)

signal.signal(signal.SIGTERM,signalHandler)
signal.signal(signal.SIGHUP,signalHandler)
display.init()
count = 0
getnew = True
startUdpServer()

while True:
    if event.detected():
        type = event.getType()
        name = event.eventNames[int(type)]
        print("Event %d %s" % (type,name))
        if name == "MENU_BUTTON_DOWN" or name == "MUTE_BUTTON_DOWN" or name == "SHUTDOWN":
            exitProgram()
        else:
            event.clear()
    try:
        if display.lines > 2:
            display.out(1,getDateTime())
        displayWeather(getnew)
        if count < 1:   
            count = 300
            getnew = True 
        else:
            count -= 1
            time.sleep(1)
            getnew = False 

    except KeyboardInterrupt:
        display.clear()
        exitProgram()

# End of script 

# set tabstop=4 shiftwidth=4 expandtab
# retab
