#!/usr/bin/env python3
#
# $Id: log_class.py,v 1.5 2023/07/06 08:44:19 bob Exp $
# Raspberry Pi Internet Radio Logging class
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.
#
# Log levels are :
#   CRITICAL 50 
#   ERROR 40 
#   WARNING 30 
#   INFO 20 
#   DEBUG 10 
#   NOTSET 0 
#
#  See https://docs.python.org/2/library/logging.html
#

import os,sys
import logging
import logging.handlers as handlers
import configparser
config = configparser.ConfigParser()

ConfigFile = "/etc/radiod.conf"

class Log:

    CRITICAL = logging.CRITICAL
    ERROR = logging.ERROR
    WARNING = logging.WARNING
    INFO = logging.INFO
    DEBUG = logging.DEBUG
    NONE = 0

    module = ''     # Module name for log entries
    loglevel = logging.INFO
    sMessage = ''   # Duplicate message prevention

    def __init__(self):
        return 

    # Initialise log and set module name (usually "radio")
    def init(self,module):
        self.module = module
        self.loglevel = self.getConfig()
        return 

    # Get module name (usually "radio") to check if initialised
    def getName(self):
        return self.module

    def message(self,message,level):
        # Set up logging, level 
        if level != self.NONE and message != self.sMessage:
            try:
                logger = logging.getLogger('gipiod')
                hdlr = logging.FileHandler('/var/log/radiod/' + self.module + '.log')
                formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
                hdlr.setFormatter(formatter)
                logger.addHandler(hdlr)
                logger.setLevel(self.loglevel)

                # write to log
                if level == self.CRITICAL:
                    logger.critical(message)
                elif level == self.ERROR:
                    logger.error(message)
                elif level == self.WARNING:
                    logger.warning(message)
                elif level == self.INFO:
                    logger.info(message)
                elif level == self.DEBUG:
                    logger.debug(message)

                logger.removeHandler(hdlr)
                hdlr.close()
                self.sMessage = message

            except Exception as e:
                print (str(e))
        return

    # Truncate the log file
    def truncate(self):
        logging.FileHandler('/var/log/radiod/' + self.module + '.log','w')
        return

    # Temporary set log level
    def setLevel(self,level):
        self.loglevel = level
        return

    # Get the log level from the configuration file
    def getLevel(self):
        return self.loglevel

    # Get configuration loglevel option
    def getConfig(self):
        section = 'RADIOD'
        option = 'loglevel'
        strLogLevel = 'INFO'

        # Get loglevel option
        config.read(ConfigFile)
        try:
            strLogLevel = config.get(section,option)

        except configparser.NoSectionError:
            msg = configparser.NoSectionError(section),'in',ConfigFile
            self.message(msg,self.ERROR)

        if strLogLevel == "CRITICAL":
            loglevel = self.CRITICAL
        elif strLogLevel == "ERROR":
            loglevel = self.ERROR
        elif strLogLevel == "WARNING":
            loglevel = self.WARNING
        elif strLogLevel == "INFO":
            loglevel = self.INFO
        elif strLogLevel == "DEBUG":
            loglevel = self.DEBUG
        elif strLogLevel == "NONE":
            loglevel = self.NONE
        else:
            loglevel = self.INFO
        return loglevel

# End of log class

# set tabstop=4 shiftwidth=4 expandtab
# retab
