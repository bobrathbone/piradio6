#!/usr/bin/env python
# Raspberry Pi Button Push Button Class
# $Id: button_class.py,v 1.7 2017/10/21 11:34:16 bob Exp $
#
# Author: Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class uses standard rotary encoder with push switch
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#
#

import os,sys,pwd
import time
import RPi.GPIO as GPIO
from log_class import Log

log = Log()

class Button:

	def __init__(self, button,callback):
		self.button = button
		self.callback = callback

		log.init('radio')
		msg = "Button created for GPIO " +  str(self.button)
		log.message(msg, log.DEBUG)
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)

		try:
			# The following lines enable the internal pull-up resistor
			GPIO.setup(self.button, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

			# Add event detection to the GPIO inputs
			GPIO.add_event_detect(self.button, GPIO.RISING, callback=self.button_event,
						bouncetime=200)
		except Exception as e:
			log.message("Button GPIO initialise error " + str(e), log.DEBUG)
			sys.exit(1)
	 
	# Push button event
	def button_event(self,button):
		log.message("Push button event GPIO " + str(button), log.DEBUG)
	    	event_button = self.button
		self.callback(event_button)	# Pass button event to event class
		return

	# Was a button pressed (goes from 0 to 1)
	def pressed(self):
		state = GPIO.input(self.button)
		if state == 1:
			pressed = True
		else:
			pressed = False
		return pressed

# End of Button Class

### Test routine ###

def interrupt(gpio):
        print "Button pressed on GPIO", gpio
        return

if __name__ == "__main__":

	from config_class import Configuration
	config = Configuration()

        if pwd.getpwuid(os.geteuid()).pw_uid > 0:
                print "This program must be run with sudo or root permissions!"
                sys.exit(1)

	print "Test Button Class"
	
	# Get configuration
	left_switch = config.getSwitchGpio("left_switch")
	right_switch = config.getSwitchGpio("right_switch")
	mute_switch = config.getSwitchGpio("mute_switch")
	down_switch = config.getSwitchGpio("down_switch")
	up_switch = config.getSwitchGpio("up_switch")
	menu_switch = config.getSwitchGpio("menu_switch")

	print "Left switch GPIO", left_switch
	print "Right switch GPIO", right_switch
	print "Up switch GPIO", up_switch
	print "Down switch GPIO", down_switch
	print "Mute switch GPIO", mute_switch
	print "Menu switch GPIO", menu_switch

        Button(left_switch, interrupt)
        Button(right_switch, interrupt)
        Button(mute_switch, interrupt)
        Button(down_switch, interrupt)
        Button(up_switch, interrupt)
        Button(menu_switch, interrupt)

        try:
                while True:
                        time.sleep(0.2)

        except KeyboardInterrupt:
                print " Stopped"
                sys.exit(0)

# End of script
