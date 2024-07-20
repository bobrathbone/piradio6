#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Weather station class
# $Id: weather_class.py,v 1.16 2024/06/21 12:47:04 bob Exp $
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
# Configuration for this program is in /etc/weather.conf
#
# Install the pre-requisite packages
# sudo pip3 install request
# sudo pip3 install geocoder
# sudo pip3 install beautifulsoup4
# sudo apt-get install python3-lxml


import pdb
import os
import sys
import time
from wxconfig_class import Configuration

try:
    import requests
except ImportError:
    exit("This script requires the requests module\nInstall with: sudo pip3 install requests")

try:
    import geocoder
except ImportError:
    exit("This script requires the geocoder module\nInstall with: sudo pip3 install geocoder")

try:
    from bs4 import BeautifulSoup
except ImportError:
    exit("This script requires the bs4 module\nInstall with: sudo pip3 install beautifulsoup4")

abs_zero = float(273.15)
hpa2inches = 0.029529983071445

config = Configuration()

# Weather Class
class Weather:

    # Pressure units I=Imperial(Inches) M=Metric(Millibars)
    pressure_units = 'I'

    location = "%s,%s" % (config.city,config.countrycode)

    # Open weathermap and API Key (Contact openweathermap.org)


    def __init__(self):
        self.coords = self.get_coords(self.location) 
        self.latitude = self.convertCoordinate(self.coords[0],'lat')
        self.longitude = self.convertCoordinate(self.coords[1],'long')

        self.url = "https://api.openweathermap.org/data/2.5/weather?q=" + self.location\
              + "&mode=xml" + "&units=" + config.units + "&pressure_units=" + config.pressure_units\
              + "&lang=" + config.language + "&APPID=" + config.api_key

        print(self.url)

    # Get current weather, See https://openweathermap.org/current 
    def get(self):
        weather = {}

        res = requests.get(self.url)
        if res.status_code == 200:

            soup = BeautifulSoup(res.content, "xml")
            curr = soup.find_all("current")

            weather["location"] = self.location

            #weather["coords"] = self.coords
            weather["latitude"] = self.latitude
            weather["longitude"] = self.longitude

            # Temperature, decimal precision 2
            x = curr[0].find("temperature")

            temperature = float(x.attrs['value'])
            temperature = round(temperature, 1)
            weather["temperature"] = temperature
            
            x = curr[0].find("humidity")
            weather["humidity"] = (x.attrs['value'] + '%')

            weather["units"] = config.units 

            x = curr[0].find("pressure")
            pressure = float((x.attrs['value']))

            temp_units = 'C'
            if config.units == "imperial" or config.pressure_units == 'I':
                temp_units = 'F'
                pressure_units = '"'
                pressure = self.convert2inches(pressure)
            else:
                pressure_units = "mb"

            weather["pressure"] = pressure
            weather["temp_units"] = temp_units 
            weather["pressure_units"] = pressure_units 

            x = curr[0].find("weather")
            weather["summary"] = (x.attrs['value'])

            x = curr[0].find("clouds")
            weather["clouds"] = (x.attrs['value'])

            #x = curr[0].find("wind")
            #weather["wind"] = (x.attrs['speed'])
                
            return weather
        elif res.status_code == 401:
            msg = "Invalid API key. See https://openweathermap.org/faq#error401 for more info."
            return msg
        else:
            msg = "Status code %s" % res.status_code
            return msg 

    # Convert a city name and country code to latitude and longitude
    def get_coords(self,location):
        coords = None
        try:
            g = geocoder.arcgis(location)
            coords = g.latlng
            status = g.status
        except:
            print("geocode error %s", status)

        if coords == None:
            msg = "Trying to get coordinates for " +  config.city +  " (" + config.countrycode + ")"
            print (msg)
            time.sleep(3)  # Wait before letting the weather.service retry
            sys.exit(1)

        return coords


    # Convert to degrees,minutes and seconds
    def convertCoordinate(self,coordinate,latlong):
        ns = 'N'
        ew = 'E'
        if coordinate < 0:
            ns='S'
            ew='W'
            coordinate = abs(coordinate)
        if latlong == 'long':
            sLatLong = ew
        else:
            sLatLong = ns
        degrees = int(coordinate)
        minutes = int((coordinate - degrees) * 60)
        seconds = int((coordinate - degrees - float(float(minutes)/float(60))) * 3600)
        loc = str("%03d° %02d\" %02d\'%s" % (degrees,minutes,seconds,sLatLong))
        return loc

    # Convert millibars to inches
    def convert2inches(self,hPA):
        inches = hPA * hpa2inches
        inches = round(inches,2)
        return inches

# End of Weather class

if __name__ == "__main__":
    weather = Weather()

    while True:
        try:
            print("Test Weather class")
            result = weather.get()
            print(result)
            time.sleep(180)

        except KeyboardInterrupt:
            print("\nExit")
            sys.exit(0)

# End of test routine

# set tabstop=4 shiftwidth=4 expandtab
# retab
