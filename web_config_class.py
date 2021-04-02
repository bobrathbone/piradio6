#!/usr/bin/env python3
#
# Raspberry Pi Internet Web Configuration Class
# $Id: web_config_class.py,v 1.4 2021/03/23 20:12:00 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class reads the /etc/radiod.conf file for configuration parameters
# but without any logging. It is used in the CGI scripts /var/lib/cgi-bin only.
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.
#

import os
import sys
import configparser
from log_class import Log

# System files
ConfigFile = "/etc/radiod.conf"
config = configparser.ConfigParser()

class Configuration:

    # Remote control parameters 
    remote_led = 0  # Remote Control activity LED 0 = No LED    
    remote_control_host = 'localhost'   # Remote control to radio communication port
    remote_control_port = 5100      # Remote control to radio communication port

    # Shoutcast ID
    shoutcast_key = "anCLSEDQODrElkxl"

    # Initialisation routine
    def __init__(self):
        if not os.path.isfile(ConfigFile) or os.path.getsize(ConfigFile) == 0:
            print("Missing configuration file " + ConfigFile)
        else:
            self.getConfig()

        return

    # Get configuration options from /etc/radiod.conf
    def getConfig(self):
        section = 'RADIOD'

        # Get options
        config.read(ConfigFile)
        try:
            options =  config.options(section)
            for option in options:
                option = option.lower()
                try:
                    parameter = config.get(section,option)
                except:
                    pass

                if option == 'remote_control_host':
                    self.remote_control_host = parameter

                elif option == 'remote_control_port':
                    try:
                        self.remote_control_port = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile,option,parameter)

                if option == 'shoutcast_key':
                    self.shoutcast_key = parameter

        except configparser.NoSectionError:
            pass

        return


    # Invalid parametrs message
    def invalidParameter(self, ConfigFile, option, parameter):
        print("Invalid parameter " + parameter + ' in option ' \
            + option + ' in ' + ConfigFile)
        log.message(msg,log.ERROR)
    

    # Get the remote Host, default localhost
    def getRemoteUdpHost(self):
        return self.remote_control_host

    # Get the remote Port, default 5100
    def getRemoteUdpPort(self):
        return self.remote_control_port

    # Shoutcast key
    def getShoutcastKey(self):
        return self.shoutcast_key

# End Web Configuration of class

# Test Web Configuration class
if __name__ == '__main__':

    config = Configuration()
    print("UDP listen host:", config.getRemoteUdpHost())
    print("UDP listen port:", config.getRemoteUdpPort())
    print("Shoutcast key:", config.getShoutcastKey())

# End of __main__

# :set tabstop=4 shiftwidth=4 expandtab
# :retab
