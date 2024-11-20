#!/usr/bin/env python3
# Raspberry Pi Weather Program Configuration Class
# $Id: wxconfig_class.py,v 1.9 2002/01/21 07:04:01 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class reads the /etc/weather.conf file for configuration parameters
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.

import os
import sys
import configparser
import pdb


# System files
ConfigFile = "/etc/weather.conf"

config = configparser.ConfigParser(interpolation=None)

class Configuration:
    _city = "London"
    _countrycode = "GB"
    _language = "EN"

    # Display types
    NO_DISPLAY = 0      # No screen attached
    LCD = 1         # Directly connected LCD
    LCD_I2C_PCF8574 = 2 # LCD PCF8574 I2C backpack
    LCD_I2C_ADAFRUIT = 3    # Adafruit I2C LCD backpack
    LCD_ADAFRUIT_RGB = 4    # Adafruit RGB plate
    GRAPHICAL_DISPLAY = 5   # Graphical or touchscreen  display
    OLED_128x64 = 6     # OLED 128 by 64 pixels
    PIFACE_CAD = 7      # Piface CAD
    ST7789TFT = 8       # Pirate audio TFT with ST7789 controller
    SSD1306 = 9         # Sitronix SSD1306 controller for the 128x64 tft
    SH1106_SPI = 10     # SH1106_SPI controller for Waveshare 1.3" 128x64 tft
    LUMA = 11           # Luma driver for  most OLEDs
    LCD_I2C_JHD1313 = 12        # Grove 2x16 I2C LCD RGB
    LCD_I2C_JHD1313_SGM31323 = 13   # Grove 2x16 I2C RGB LCD & SGM31323 controllor
                                    # for colour backlight

    display_type = LCD
    DisplayTypes = [ 'NO_DISPLAY','LCD', 'LCD_I2C_PCF8574',
             'LCD_I2C_ADAFRUIT', 'LCD_ADAFRUIT_RGB',
             'GRAPHICAL_DISPLAY', 'OLED_128x64',
             'PIFACE_CAD','ST7789TFT','SSD1306','SH1106_SPI','LUMA',
             'LCD_I2C_JHD1313','LCD_I2C_JHD1313_SGM31323' ]

    # Open weathermap Key (Contact OpenWeatherMap.org directly if you need a new key)
    _api_key="080535da15e1e2a21f933846b0ba824a"

    # Temperature units metric(C) or imperial(F)
    # Units standard, metric and imperial units
    _units = "metric"

    # Atmospheric pressure units millibars(M) or inches mercury(I)
    _pressure_units = "M"

    # Set date format, US format =  %H:%M %m/%d/%Y
    _date_format = "%H:%M %d/%m/%Y"

    # Exit command either "" or the command to execute
    _exit_command = ""

    # UDP server for IR remote commands
    _udp_host='localhost'
    _udp_port=5100

    # List of loaded options for display
    configOptions = {}

    # i2c_address
    _i2c_address = 0x00

    _display_width = 0      # Line width of display width 0 = use program default
    _display_lines = 2      # Number of display lines

    # Initialisation routine
    def __init__(self):
        self.getConfig()

    # Get configuration options from /etc/radiod.conf
    def getConfig(self):
        section = 'WEATHER'

        # Get options from /etc/radiod.conf
        # Parameter for each option is passed to the @property setter for that option
        config.read(ConfigFile)
        try:
            options =  config.options(section)
            for option in options:
                option = option.lower()
                parameter = config.get(section,option)
                parameter = parameter.lstrip('"')
                parameter = parameter.rstrip('"')
                parameter = parameter.lstrip("'")
                parameter = parameter.rstrip("'")

                self.configOptions[option] = parameter

                if option == 'city':
                    self.city = parameter

                elif option == 'countrycode':
                    self.countrycode = parameter

                elif option == 'language':
                    self.language = parameter

                elif option == 'api_key':
                    self.api_key = parameter

                elif option == 'units':
                    self.units = parameter

                elif option == 'pressure_units':
                    self.pressure_units = parameter

                elif option == 'date_format':
                    self.date_format = parameter

                elif option == 'exit_command':
                    self.exit_command = parameter

                elif option == 'udp_host':
                    self.udp_host = parameter

                elif option == 'udp_port':
                    self.udp_port = parameter

                else:
                    msg = "Invalid option " + option + ' in section ' \
                        + section + ' in ' + ConfigFile
                    print(msg)

            section = 'DISPLAY'
            options =  config.options(section)
            for option in options:
                option = option.lower()
                parameter = config.get(section,option)
                parameter = parameter.lstrip('"')
                parameter = parameter.rstrip('"')
                parameter = parameter.lstrip("'")
                parameter = parameter.rstrip("'")

                #self.configOptions[option] = parameter

                if option == 'i2c_address':
                    try:
                        self._i2c_address = int(parameter,16)
                    except Exception as e:
                        self.invalidParameter(ConfigFile,option,parameter)

                elif 'display_width' in option:
                    try:
                        self.display_width = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile,option,parameter)

                elif 'display_lines' in option:
                    try:
                        self.display_lines = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile,option,parameter)

                elif 'font_size' in option:
                    try:
                        self.font_size = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile,option,parameter)

                elif 'font_name' in option:
                    self.font_name = parameter

                elif 'display_type' in option:
                    self.display_type = self.LCD    # Default

                    if parameter == 'LCD':
                        self.display_type = self.LCD

                    elif parameter == 'LCD_I2C_PCF8574':
                        self.display_type = self.LCD_I2C_PCF8574

                    elif parameter == 'LCD_I2C_ADAFRUIT':
                        self.display_type = self.LCD_I2C_ADAFRUIT

                    elif parameter == 'LCD_ADAFRUIT_RGB':
                        self.display_type = self.LCD_ADAFRUIT_RGB

                    elif parameter == 'NO_DISPLAY':
                        self.display_type = self.NO_DISPLAY

                    elif parameter == 'GRAPHICAL':
                        self.display_type = self.GRAPHICAL_DISPLAY

                    elif parameter == 'OLED_128x64':
                        self.display_type = self.OLED_128x64

                    elif parameter == 'PIFACE_CAD':
                        self.display_type = self.PIFACE_CAD

                    elif parameter == 'ST7789TFT':
                        self.display_type = self.ST7789TFT

                    elif parameter == 'SSD1306':
                        self.display_type = self.SSD1306

                    elif parameter == 'SH1106_SPI':
                        self.display_type = self.SH1106_SPI

                    elif parameter == 'LCD_I2C_JHD1313':
                        self.display_type = self.LCD_I2C_JHD1313

                    elif parameter == 'LCD_I2C_JHD1313_SGM31323':
                        self.display_type = self.LCD_I2C_JHD1313_SGM31323

                    elif 'LUMA' in parameter:
                        param = parameter.upper()
                        self.display_type = self.LUMA
                        self.device_driver = 'SH1106'  # Default
                        devices = param.split('.')
                        if len(devices) > 0:
                            self.device_driver = devices[1]

                else:
                    msg = "Invalid option " + option + ' in section ' \
                        + section + ' in ' + ConfigFile
                    print(msg)

        except configparser.NoSectionError:
            msg = configparser.NoSectionError(section),'in',ConfigFile
            print(msg)

    # Invalid parameters message
    def invalidParameter(self, ConfigFile, option, parameter):
        msg = "Invalid parameter " + parameter + ' in option ' \
            + option + ' in ' + ConfigFile
        print(msg)

    @property
    def city(self):
        return self._city

    @city.setter
    def city(self, parameter):
        self._city = parameter
        
    @property
    def countrycode(self):
        return self._countrycode

    @countrycode.setter
    def countrycode(self, parameter):
        self._countrycode = parameter
        
    @property
    def language(self):
        return self._language

    @language.setter
    def language(self, parameter):
        self._language = parameter
        
    @property
    def api_key(self):
        return self._api_key

    @api_key.setter
    def api_key(self, parameter):
        self._api_key = parameter
        
    @property
    def units(self):
        return self._units

    @units.setter
    def units(self, parameter):
        self._units = parameter
        

    @property
    def pressure_units(self):
        return self._pressure_units

    @pressure_units.setter
    def pressure_units(self, parameter):
        self._pressure_units = parameter

    @property
    def date_format(self):
        return self._date_format

    @date_format.setter
    def date_format(self, parameter):
        self._date_format = parameter

    @property
    def exit_command(self):
        return self._exit_command

    @exit_command.setter
    def exit_command(self, parameter):
        self._exit_command = parameter

    @property
    def udp_host(self):
        return self._udp_host

    @udp_host.setter
    def udp_host(self, parameter):
        self._udp_host = parameter

    @property
    def udp_port(self):
        return int(self._udp_port)

    @udp_port.setter
    def udp_port(self, parameter):
        self._udp_port = int(parameter)

    # Get Display name
    def getDisplayName(self):
        name = self.DisplayTypes[self.display_type]
        if name == 'LUMA':
            name = name + '.' + self.device_driver
        return name

    # Get Display type
    def getDisplayType(self):
        return self.display_type

    # Get LUMA device name eg SH1106 SSD1306
    @property
    def device_driver(self):
        return self._device_driver

    @device_driver.setter
    def device_driver(self, value):
        self._device_driver = value

    # Get display I2C address
    @property
    def i2c_address(self):
        return self._i2c_address

    @i2c_address.setter
    def i2c_address(self, value):
        if value  > 0x0:
            self._i2c_address = value

    # Get display width
    @property
    def display_width(self):
        return self._display_width

    @display_width.setter
    def display_width(self, value):
        self._display_width = value

    # Get Display lines
    @property
    def display_lines(self):
        return self._display_lines

    @display_lines.setter
    def display_lines(self, value):
        self._display_lines = value

    # Get font size
    @property
    def font_size(self):
        return self._font_size

    @font_size.setter
    def font_size(self, value):
        self._font_size = int(value)

    # Get font name and size
    @property
    def font_name(self):
        return self._font_name

    @font_name.setter
    def font_name(self, value):
        self._font_name = value

# End of configuration class

# Test configuration routine
if __name__ == '__main__':

    config = Configuration()

    print ("Weather configuration file:", ConfigFile)
    print ("Labels in brackets (...) are the parameters found in",ConfigFile)
    print ("\n[WEATHER] section")
    print ("---------------")
    print ("City (city):", config.city)
    print ("Country code (countrycode):", config.countrycode)
    print ("API key (api_key):", config.api_key)
    print ("Language (language):", config.language)
    print ("Display units (units):", config.units)
    print ("Pressure units (pressure_units):", config.pressure_units)
    print ("Date format (date_format):", config.date_format)
    print ("Exit command (exit_command):", config.exit_command)
    print ("UDP host (udp_host):", config.udp_host)
    print ("UDP port (udp_port):", config.udp_port)
    print ("\n[DISPLAY] section")
    print ("-------------------")
    print ("Display type (display_type):", config.getDisplayType(), config.getDisplayName())
    print ("Display lines (display_lines):", config.display_lines)
    print ("Display width (display_width):", config.display_width)
    print ("TFT display font name (font_name):", config.font_name)
    print ("TFT display font size (font_size):", config.font_size)
    print ("I2C address (i2c_address):", hex(config.i2c_address))
    print ("")

# End of __main__

# set tabstop=4 shiftwidth=4 expandtab
# retab
