#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# $Id: graphic_display.py,v 1.16 2017/12/12 14:05:28 bob Exp $
# Raspberry Pi display routines
# Graphic screen routines used by touch graphic screen
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
import pdb
from config_class import Configuration

# No interrupt routine if none supplied
def no_interrupt():
	return False

# Lcd Class 
class GraphicDisplay:
	columns = 100
	rows = 10
	size = [600,400]
	font = None
	current_row = 1
	current_column = 1
	delay = 15
	config = Configuration()

	# Display window modes
	MAIN = 0
	RSS = 1
	INFO = 2
	LAST = 2
	mode = MAIN

	# Search modes
	SEARCH_LIST = 0
	SEARCH_PLAYLIST = 1
	SEARCH_ARTISTS = 2
	search_mode = SEARCH_LIST

	# Scroll line values
	textIndex = [0,0,0,0]
	holdCountBegin = [delay,delay,delay,delay,delay]
	holdCountEnd = [delay,delay,delay,delay,delay]
	lineText = ['','','','','']

        def __init__(self,font):
		self.font = font
		return

	# Get display columns 
	def getWidth(self):
		return self.columns

	# Get display rows 
	def getRows(self):
		return self.rows

	# Get display lines (compatability for message class) 
	def getLines(self):
		return self.rows

	# Get display Columns 
	def getColumns(self):
		return self.columns

	# Get row x position
	def getRowPos(self,row):
		self.current_row = row
		h = self.averageFontSize[1]
		pos = int(row * h * 1.5)
		return pos

	# Get next row position
	def getNextRow(self):
		self.current_row += 1
		return self.getRowPos(self.current_row)

	# Get row x position
	def getColumnPos(self,column):
		w = self.averageFontSize[0]
		pos =  int(column * w / 1.1)
		return pos

	# Set the display size, rows and columns
	def setSize(self,size):
		self.size = size
		self.averageFontSize = self.font.size("W")
		w = self.averageFontSize[0]
		h = self.averageFontSize[1]
		self.columns = int(1.1 * self.size[0]/w)
		self.rows = int(self.size[1]/(h*1.5))
		return size 

	# Scroll text routine
	def scroll(self,text,line,max_columns):
		idx = line-1
		index = self.textIndex[idx]

		# Has the line text changed then reset
		if text != self.lineText[idx]:	
			index = 0
			self.lineText[idx] = text

		leng = len(text)

		newText = text[index:(max_columns + index)]

		# Increment index and check
		index += 1

		# this delays scrolling at beginning of sroll
		if self.holdCountBegin[idx] > 0:
			self.holdCountBegin[idx] -= 1
			index = 0

		# this delays scrolling at end of scroll
		if (index + len(newText)) > leng:
			if self.holdCountEnd[idx] < 1:
				self.holdCountEnd[idx] = self.delay
				self.holdCountBegin[idx] = self.delay
				self.textIndex[idx] = 0
			
			self.holdCountEnd[idx] -= 1
		else:
			self.textIndex[idx] = index

		return newText
		
	# Cycle through display modes
	def cycleMode(self):
		self.mode += 1
		if self.mode > self.LAST:
			self.mode = self.MAIN
		return self.mode

	# Set display mode (Source change)
	def setMode(self,mode):
		self.mode = mode
		if self.mode > self.LAST:
			self.mode = self.MAIN
		return self.mode

	# Get display mode
	def getMode(self):
		return self.mode

	# Get search mode
	def getSearchMode(self):
		return self.search_mode

	# Get search mode
	def setSearchMode(self,mode):
		self.search_mode = mode

# End of Graphic Screen class

### Test scroll routine ###
if __name__ == "__main__":
	display = GraphicDisplay(None)
	text = "ABCDEFGHIJKLMNOPQRSTUVWXYX 01234567890"
	try:
		while True:
			print display.scroll(text,1,20)
			time.sleep(0.5)

	except KeyboardInterrupt:
		print "\nExit"
		sys.exit(0)
# End of test routine
