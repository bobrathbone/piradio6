#!/usr/bin/env python3
# Raspberry Pi Weather Program Configuration Class
# $Id: wxconfig_class.py,v 1.5 2023/10/04 09:44:44 bob Exp $
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
            
        except configparser.NoSectionError:
            msg = configparser.NoSectionError(section),'in',ConfigFile
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
    print ("")

# End of __main__

# set tabstop=4 shiftwidth=4 expandtab
# retab
