#!/usr/bin/env python
#
# Raspberry Pi Internet Radio Menu Class
# $Id: menu_class.py,v 1.12 2018/05/30 08:21:14 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class uses  Music Player Daemon 'mpd' and the python-mpd library
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#	     The authors shall not be liable for any loss or damage however caused.
#
import sys

from config_class import Configuration
from language_class import Language

config = Configuration()
language = Language()

class Menu:

	# Menu mode
	MENU_TIME = 0
	MENU_SEARCH  = 1
	MENU_SOURCE  = 2
	MENU_OPTIONS  = 3
	MENU_RSS  = 4
	MENU_INFO  = 5
	MENU_LAST = MENU_INFO     # Last one a user can select
	MENU_SLEEP = 6	  # Sleep after timer or waiting for alarm
	MENU_SHUTDOWN = -1

	sMode = ["MENU_TIME", "MENU_SEARCH", "MENU_SOURCE",
		 "MENU_OPTIONS", "MENU_RSS", "MENU_INFO", "MENU_SLEEP"]

	menu_mode = MENU_TIME

	# Menu options in MENU_OPTIONS mode
	OPTION_RANDOM = 0
	OPTION_CONSUME = 1
	OPTION_REPEAT = 2
	OPTION_SINGLE = 3
	OPTION_RELOADLIB = 4
	OPTION_STREAMING = 5
	OPTION_ALARM = 6
	# All above are true or False, all below are values
	OPTION_ALARMSETHOURS = 7
	OPTION_ALARMSETMINS = 8
	OPTION_TIMER = 9
	OPTION_SELECTCOLOR = 10
	OPTION_WIFI = 11
	OPTION_ADA_LAST = OPTION_SELECTCOLOR

	OptionNames = [ 'Random', 'Consume', 'Repeat', 'Single', 'Reload media', \
			 'Streaming', 'Alarm', 'Hours', 'Minutes', 'Timer', 'Setup WIFI', 'Colour' ] 

	option = OPTION_RANDOM
	option_last = OPTION_TIMER
	option_changed = False

	# Other definitions
	UP = 0
	DOWN = 1

	# Initialisation routine
	def __init__(self):
		return

	# Get the menu mode
	def mode(self):
		return self.menu_mode

	# Cycle the menu mode
	def cycle(self):
		self.menu_mode += 1
		if self.menu_mode > self.MENU_LAST:
			self.menu_mode = self.MENU_TIME
		return self.menu_mode

	# Mode string for debugging
	def getName(self):
		return self.sMode[self.menu_mode]

	# Set menu mode
	def set(self,menu_mode):
		self.menu_mode = menu_mode
		return self.menu_mode

        # Get current option 
        def getOption(self):
                return self.option

	# Get the option name
        def getOptionName(self, option):
                return self.OptionNames[option]

	# Get the option name
        def getNextOption(self, direction):
		if direction == self.UP:
			self.option += 1
		else:
			self.option -= 1

		if self.option < 0:
			self.option = self.option_last 
		elif self.option > self.option_last:
			self.option = 0

                return self.option

        # Option changed
        def optionChanged(self):
                return self.option_changed

	# Set option changed
        def optionChangedTrue(self):
                self.option_changed = True
                return

        def optionChangedFalse(self):
                self.option_changed = False
                return

# End of menu class

### Test routine ###
if __name__ == "__main__":
	print "Test menu_class.py"
	menu = Menu()
	print "Mode", menu.mode()
	menu.cycle()
	print "Mode", menu.mode()
	sys.exit(0)
	
