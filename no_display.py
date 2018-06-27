#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# $Id: no_display.py,v 1.3 2018/04/22 13:13:31 bob Exp $
# Raspberry Pi display routines
# Null screen routines used by retro radio 
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.
#

import os,sys
import time,pwd
import RPi.GPIO as GPIO
from translate_class import Translate
from config_class import Configuration


# No interrupt routine if none supplied
def no_interrupt():
	return False

# Lcd Class 
class No_Display:

        def __init__(self):
		return

	# Initialise for either revision 1 or 2 boards
	def init(self,revision=2):
		return

	# Set the display width
	def setWidth(self,width):
		return 

	# Get LCD width 
	def getWidth(self):
		return 0

	# Display Line on LCD
	def out(self,line_number=1,text="",interrupt=no_interrupt):
		return

        # Set Scroll line speed - Best values are 0.2 and 0.3
        # Limit to between 0.05 and 1.0
        def setScrollSpeed(self,speed):
                return

	# Clear display
	def clear(self):
                return

	# Return colour False
	def hasColor(self):
                return False

# End of No Screen class
