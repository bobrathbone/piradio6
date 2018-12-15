#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# $Id: lcd_piface_class.py,v 1.13 2018/12/04 07:59:51 bob Exp $
# Raspberry Pi Internet Radio
# using a Piface backlit LCD plate
#
# Author : Patrick Zacharias/Bob Rathbone
# Site   : N/A
#
# From original LCD routines : piface.co.uk
# Site   : http://piface.github.io/pifacecad
#
# Based on Bob Rathbone's LCD class
# Bob Rathbone's site	: http://bobrathbone.com
#
# To use this program you need pifacecommon and pifacecad installed
# for their respective Python versions
#
# At the moment this program can only be executed with Python2.7
#
# This program uses  Music Player Daemon 'mpd'and it's client 'mpc'
# See http://mpd.wikia.com/wiki/Music_Player_Daemon_Wiki
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#	     The authors shall not be liable for any loss or damage however caused.
#

import os,sys
import time
from translate_class import Translate
from __init__ import *

import subprocess
import pifacecommon
import pifacecad
from pifacecad.lcd import LCD_WIDTH

PLAY_SYMBOL = pifacecad.LCDBitmap(
    [0x10, 0x18, 0x1c, 0x1e, 0x1c, 0x18, 0x10, 0x0])
PAUSE_SYMBOL = pifacecad.LCDBitmap(
    [0x0, 0x1b, 0x1b, 0x1b, 0x1b, 0x1b, 0x0, 0x0])
INFO_SYMBOL = pifacecad.LCDBitmap(
    [0x6, 0x6, 0x0, 0x1e, 0xe, 0xe, 0xe, 0x1f])
MUSIC_SYMBOL = pifacecad.LCDBitmap(
    [0x2, 0x3, 0x2, 0x2, 0xe, 0x1e, 0xc, 0x0])

PLAY_SYMBOL_INDEX = 0
PAUSE_SYMBOL_INDEX = 1
INFO_SYMBOL_INDEX = 2
MUSIC_SYMBOL_INDEX = 3
#Symbols were taken from the pifacecad examples and aren't in use yet

# The wiring for the LCD is as follows:
# 1 : GND
# 2 : 5V
# 3 : Contrast (0-5V)*
# 4 : RS (Register Select)
# 5 : R/W (Read Write)       - GROUND THIS PIN
# 6 : Enable or Strobe
# 7 : Data Bit 0	     - NOT USED
# 8 : Data Bit 1	     - NOT USED
# 9 : Data Bit 2	     - NOT USED
# 10: Data Bit 3	     - NOT USED
# 11: Data Bit 4
# 12: Data Bit 5
# 13: Data Bit 6
# 14: Data Bit 7
# 15: LCD Backlight +5V**
# 16: LCD Backlight GND


# Define LCD device constants
LCD_WIDTH = 16    # Default characters per line
LCD_CHR = True
LCD_CMD = False

# Timing constants
E_PULSE = 0.00005
E_DELAY = 0.00005


translate = Translate()

# Lcd Class 
class Lcd_Piface_Cad:
	width = LCD_WIDTH
	RawMode = False

	# Port expander input pin definitions
	LEFT_BUTTON = 0
	DOWN_BUTTON = 1
	UP_BUTTON   = 2
	RIGHT_BUTTON= 3
	MENU_BUTTON = 4

	def __init__(self):
		return

	# Initialise for either revision 1 or 2 boards
	def init(self,callback=None):
	# LED outputs
		self.cad = pifacecad.PiFaceCAD()
		# set up cad
		self.event = callback	
		self.cad.lcd.blink_off()
		self.cad.lcd.cursor_off()
		self.cad.lcd.backlight_on()

		self.cad.lcd.store_custom_bitmap(PLAY_SYMBOL_INDEX, PLAY_SYMBOL)
		self.cad.lcd.store_custom_bitmap(PAUSE_SYMBOL_INDEX, PAUSE_SYMBOL)
		self.cad.lcd.store_custom_bitmap(INFO_SYMBOL_INDEX, INFO_SYMBOL)
		return


	# Set the display width
	def setWidth(self,width):
		self.width = width
		return

	# Display Line 
	def out(self,line,text,interrupt=None):
		if len(text) > self.width:
			self._scroll(line,text,interrupt)
		else:
			self._string(line,text)
		return

	# Send string to display
	def _string(self,line,message):
		self.cad.lcd.set_cursor(0, int(line)-1)
		s = message.ljust(self.width," ")
		if not self.RawMode:
			s = translate.toLCD(s)
		self.cad.lcd.write(s)
		return


	# Scroll line - interrupt() breaks out routine if True
	def _scroll(self,line,mytext,interrupt):
		ilen = len(mytext)
		skip = False

		self._string(line,mytext[0:self.width + 1])
	
		if (ilen <= self.width):
			skip = True

		if not skip:
			# Delay before scrolling
			for i in range(0, 5):
				time.sleep(0.2)
				if interrupt():
					skip = True
					break

		if not skip:
			# Scroll the line
			for i in range(0, ilen - self.width + 1 ):
				self._string(line,mytext[i:i+self.width])
				if interrupt():
					skip = True
					break

		if not skip:
			# Delay after scrolling
			for i in range(0, 5):
				time.sleep(0.2)
				if interrupt():
					break
		return

	# Check which button was pressed
	def checkButtons(self):
		if self.buttonPressed(self.MENU_BUTTON):
			self.event.set(self.event.MENU_BUTTON_DOWN)
			# 2 seconds button down shuts down the radio
			count = 10
			while self.buttonPressed(self.MENU):
				time.sleep(0.2)
				count -= 1
				if count < 0:
					self.event.set(self.event.SHUTDOWN)
					break

		elif self.buttonPressed(self.UP_BUTTON):
			self.event.set(self.event.UP_SWITCH)

		elif self.buttonPressed(self.DOWN_BUTTON):
			self.event.set(self.event.DOWN_SWITCH)

		elif self.buttonPressed(self.LEFT_BUTTON):
			self.event.set(self.event.LEFT_SWITCH)
			count = 10
			while self.buttonPressed(self.RIGHT_BUTTON):
				time.sleep(0.2)
				count -= 1
				if count < 0:
					self.event.set(self.event.MUTE_BUTTON_DOWN)
					time.sleep(0.5)
					break

		elif self.buttonPressed(self.RIGHT_BUTTON):
			self.event.set(self.event.RIGHT_SWITCH)
			count = 10
			while self.buttonPressed(self.LEFT_BUTTON):
				time.sleep(0.2)
				count -= 1
				if count < 0:
					self.event.set(self.event.MUTE_BUTTON_DOWN)
					time.sleep(0.5)
					break

		return

	# Dummy routine
	def setScrollSpeed(self,speed):
		return

	# Set raw mode on (No translation)
	def setRawMode(self,value):
		self.RawMode = value
		return
	
	# Read state of single button
	def buttonPressed(self, b):
		button =  self.cad.switches[b].value
		return button

	# Clear the display
	def clear(self):
		self.cad.lcd.clear()
	
	# Sets cursor home
	def home(self):
		self.cad.lcd.home()
		return

	# Get LCD width
	def getWidth(self):
		return self.width

	# Does this screen support color
	def hasColor(self):
		return False

# End of Lcd class
# Class test routine
if __name__ == "__main__":
	import pwd

	if pwd.getpwuid(os.geteuid()).pw_uid > 0:
		print ("This program must be run with sudo or root permissions!")
		sys.exit(1)

	try:
		print ("Test lcd_class.py")
		lcd = Lcd_Piface_Cad()
		lcd.init()
		lcd.setWidth(16)
		lcd.out(1,"bobrathbone.com")
		lcd.out(2,"Press any button")
		#time.sleep(4)
		#lcd.out(4,"Scroll 4 ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789", no_interrupt)
		#lcd.out(4,"End of test")

		while True:
			msg = ""
			if lcd.buttonPressed(lcd.MENU_BUTTON):
				msg = "MENU button pressed"
			elif lcd.buttonPressed(lcd.UP_BUTTON):
				msg = "UP button pressed"
			elif lcd.buttonPressed(lcd.DOWN_BUTTON):
				msg = "DOWN button pressed"
			elif lcd.buttonPressed(lcd.LEFT_BUTTON):
				msg = "LEFT button pressed"
			elif lcd.buttonPressed(lcd.RIGHT_BUTTON):
				msg = "RIGHT button pressed"

			if len(msg) > 0: 
				print (msg)
				lcd.out(2,msg)

			time.sleep(0.1)

	except KeyboardInterrupt:
		print ("\nExit")
		sys.exit(0)
# End of test routine
