#!/usr/bin/env python
#
# $Id: status_led_class.py,v 1.2 2017/10/23 06:22:32 bob Exp $
# Raspberry Retro Pi Internet Radio
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#

import RPi.GPIO as GPIO
import time


# Status LED class
class StatusLed:
	# Status settings
	CLEAR = 0
	NORMAL = 1
	BUSY   = 2
	SELECT = 3 
	ERROR  = 4 
	red_led = None
	blue_led = None
	green_led = None
	status = -1

	def __init__(self, red_led=23, green_led=27, blue_led=22 ):
		self.red_led = red_led
		self.green_led = green_led
		self.blue_led = blue_led

		# Set up status LEDS
                GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)
		if self.red_led > 0:
			GPIO.setup(self.red_led, GPIO.OUT)
		if self.blue_led > 0:
			GPIO.setup(self.blue_led, GPIO.OUT)
		if self.green_led > 0:
			GPIO.setup(self.green_led, GPIO.OUT)
                return

	# Set the status to normal, busy, error or clear
	def set(self,status):
		if status is not self.status:
			# Reset LEDs
			if self.red_led > 0:
				GPIO.output(self.red_led, False)
			if self.blue_led > 0:
				GPIO.output(self.blue_led, False)
			if self.green_led > 0:
				GPIO.output(self.green_led, False)

			# Switch RGB Led on/off
			if status is self.NORMAL and self.green_led > 0:
				GPIO.output(self.green_led, True)
			elif status is self.BUSY and self.blue_led > 0:
				GPIO.output(self.blue_led, True)
			elif status is self.ERROR and self.red_led > 0:
				GPIO.output(self.red_led, True)
			elif status is self.SELECT and self.green_led > 0:
				GPIO.output(self.green_led, True)
				if self.red_led > 0:
					GPIO.output(self.red_led, True)
			self.status = status
		return self.status

	# Get status 
	def get(self):
		return self.status

if __name__ == "__main__":
	statusLed = StatusLed()
	statusLed.set(StatusLed.NORMAL)
	time.sleep(3)
	statusLed.set(StatusLed.BUSY)
	time.sleep(3)
	statusLed.set(StatusLed.ERROR)
	time.sleep(3)
	statusLed.set(StatusLed.CLEAR)

# End of class
