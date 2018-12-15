#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# $Id: display_class.py,v 1.36 2018/11/14 13:15:39 bob Exp $
# Raspberry Pi display routines
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#	     The authors shall not be liable for any loss or damage however caused.
#

import pdb
import os,sys
import time,pwd
from translate_class import Translate
from config_class import Configuration
from log_class import Log

translate = Translate()
config = Configuration()
log = Log()

screen = None

SCREEN_LINES = 2	# Default screen lines
SCREEN_WIDTH = 16	# Default screen width

# No interrupt if not supplied
def no_interrupt():
	return False

# Display Class 
class Display:

	lines = SCREEN_LINES	# Default lines
	width = SCREEN_WIDTH	# Default width
	saved_volume = 0
	saved_font_size = 1

	delay = 0  # Delay (volume) display for n cycles (2 line displays)

	# The Adafruit RGB plate has buttons otherwis False
	has_buttons = False
	has_screen = True

	i2c_bus = 1	# All later RPIs use bus 1 (old RPIs use bus 0)

	lineBuffer = []		# Line buffer 

	def __init__(self):
		return

	# Initialise 
	def init(self, callback=None):
		self.callback = callback
		log.init('radio')
		self.setupDisplay()
		return
	
	# Set up configured screen class
	def setupDisplay(self):
		global screen
		dtype = config.getDisplayType()
		i2c_address = 0x0
		configured_i2c = config.getI2Caddress()
		log.message("I2C address " + hex(configured_i2c), log.DEBUG)
		self.i2c_bus = config.getI2Cbus()

		if dtype == config.NO_DISPLAY:
			from no_display import No_Display
			screen = No_Display()
			self.has_screen = False

		elif dtype == config.LCD_I2C_PCF8574:
			from lcd_i2c_pcf8574 import Lcd_i2c_pcf8574
			screen = Lcd_i2c_pcf8574()

			if configured_i2c != 0:
				i2c_address = configured_i2c
			else:
				i2c_address = 0x27

			screen.init(address = i2c_address, busnum=self.i2c_bus)

		elif dtype == config.LCD_I2C_ADAFRUIT:
			from lcd_i2c_adafruit import Lcd_i2c_Adafruit
			screen = Lcd_i2c_Adafruit()

			if configured_i2c != 0:
				i2c_address = configured_i2c
			else:
				i2c_address = 0x20

			screen.init(address = i2c_address, busnum=self.i2c_bus)

		elif dtype == config.LCD_ADAFRUIT_RGB:
			from lcd_adafruit_class import Adafruit_lcd
			screen = Adafruit_lcd()

			if configured_i2c != 0:
				i2c_address = configured_i2c
			else:
				i2c_address = 0x20

			screen.init(address = i2c_address, busnum = self.i2c_bus, \
				    callback = self.callback)

			# This device has its own buttons on the I2C intertface
			self.has_buttons = True

		elif dtype == config.OLED_128x64:
			from oled_class import Oled
			screen = Oled()
			self.width = 20
			self.lines = 5
			# Set vertical display
			screen.flip_display_vertically(config.flipVertical())

		elif dtype == config.PIFACE_CAD:
			from lcd_piface_class import Lcd_Piface_Cad
			screen = Lcd_Piface_Cad()

			screen.init(callback = self.callback)

			# This device has its own buttons on the SPI intertface
			self.has_buttons = True

		else:
			from lcd_class import Lcd
			screen = Lcd()
			screen.init()

		# Set up screen width (if 0 use default)
		self.width = config.getWidth()	
		self.lines = self.getLines()

		if self.width != 0:
			screen.setWidth(config.getWidth())
		else:
			screen.setWidth(SCREEN_WIDTH)

		sName  = self.getDisplayName()
		msg = 'Screen ' + sName + ' Lines=' + str(self.lines) \
			 + ' Width=' + str(self.width) 
		
		if i2c_address > 0:
			msg = msg + ' Address=' + hex(i2c_address)

		log.message(msg, log.DEBUG)

		self.splash()

		# Set up number of lines and display buffer
		for i in range(0, self.lines):
			self.lineBuffer.insert(i,'')	
		return

	# Get display type
	def getDisplayType(self):
		return config.getDisplayType()

	# Get display name
	def getDisplayName(self):
		return config.getDisplayName()

	# Get LCD width
	def getWidth(self):
		self.width = config.getWidth()
		return self.width

	# Set the display width
	def setWidth(self,width):
		self.width = width
		return width

	# Get LCD number of lines
	def getLines(self):
		self.lines = config.getLines()
		if self.lines < 1:
			self.lines = 2
		return self.lines

	# Set font
	def setFont(self,size):
		displayType = config.getDisplayType()
		if displayType == config.OLED_128x64 and size != self.saved_font_size:
			screen.setFont(size)
			self.saved_font_size = size

	# Send string to display if it has not already been displayed
	def out(self,line,message,interrupt=no_interrupt):
		global screen
		leng = len(message)
		index = line-1
		displayType = config.getDisplayType()
		#pdb.set_trace()

		if leng < 1:
			message = " "
			leng = 1
		
		# Check if screen has enough lines display message
		if line <= self.lines:
			# Always display messages that need to be scrolled
			if leng > self.width:
				screen.out(line,message,interrupt)
				self.update(screen,displayType)

			# Only display if this is a different message on this line
			elif message !=  self.lineBuffer[index]:
				message = translate.toLCD(message)
				screen.out(line,message,interrupt)
				self.update(screen,displayType)

			# Store the message in the line buffer for comparison
			# with the next message
			self.lineBuffer[index] = message	
		return

	# Update screen (Only OLED)
	def update(self,screen,displayType):
		if displayType == config.OLED_128x64:
			screen.update()
		return

	# Clear display and line buffer
	def clear(self):
		if config.getDisplayType() == config.OLED_128x64:
			screen.clear()
			self.lineBuffer = []		# Line buffer 
			for i in range(0, self.lines):
				self.lineBuffer.insert(i,'')	
			self.saved_volume = 0
		return

	# Set get delay cycles ( Used for temporary message displays)
	def setDelay(self,cycles):
		self.delay = cycles
		return

	# Used to display changed volume on 2 line displays
	def getDelay(self):
		self.delay -= 1
		if self.delay < 0:
			self.delay = 0
		return self.delay

	# Check to see if the display has buttons
	def hasButtons(self):
		return self.has_buttons

	# Check to see Adafruit RGB buttons pressed 
	def checkButton(self):
		screen.checkButtons()	# Generates event if button pressed
		return

	# Is this a null screen
	def hasScreen(self):
		return self.has_screen

	# Is this a colour screen
	def hasColor(self):
		return screen.hasColor()

	# For Adafruit screen with RGB colour
   	def backlight(self, label):
		if self.hasColor():
			screen.backlight(self.getBackColor(label))
		return
	
	# Get background colour by name label. Returns an integer
	def getBackColor(self, label):
		return config.getBackColor(label)
		
	# Get background colour by name index. Returns a color name
	def getBackColorName(self, index):
		return config.getBackColorName(index)

	# Oled volume bar
	def volume(self,volume):
		if self.saved_volume != volume:
			screen.volume(volume)
			self.saved_volume = volume

	# Display splash logo
	def splash(self):
		delay = 3
		dtype = config.getDisplayType()
		if dtype == config.OLED_128x64:
			dir = os.path.dirname(__file__)
			bitmap = dir + '/' + config.getSplash()
			try:
				if os.path.exists(bitmap):
					screen.drawSplash(bitmap,delay)
				else:
					print bitmap,"does not exist"
			except Exception as e:
				print "Splash:",e
			
# End of Display class


### Test routine ###
if __name__ == "__main__":

	if pwd.getpwuid(os.geteuid()).pw_uid > 0:
		print "This program must be run with sudo or root permissions!"
		sys.exit(1)

	try:
		print "Test display_class.py"
		display = Display()
		display.init()
		display_type = display.getDisplayType()
		display_name = display.getDisplayName()
		print "Display type",display_type,display_name
		#pdb.set_trace()
		color = display.getBackColor('bg_color')
		print "bg_color",color,display.getBackColorName(display.getBackColor('bg_color'))
		display.backlight('search_color')
		#display.splash()
		display.out(1,"bobrathbone.com")
		display.out(2,"Line 2 123456789")
		display.out(3,"Line 3 123456789")
		display.out(4,"Line 4 123456789")
		time.sleep(2)
		display.out(4,"Scroll 4 ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789", no_interrupt)
		time.sleep(1)
		display.out(4,"End of test")
		sys.exit(0)

	except KeyboardInterrupt:
		print "\nExit"
		sys.exit(0)
# End of test routine
