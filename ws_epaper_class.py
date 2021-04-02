#!/usr/bin/env python
#
#!/usr/bin/env python
# This class drives the Solomon Systech SSD1306 128 by 64 pixel OLED
#
# $Id: ws_epaper_class.py,v 1.1 2020/10/10 15:00:48 bob Exp $
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#          The authors shall not be liable for any loss or damage however caused.
#
# Waveshare 2.13inch e-paper display class for Internet radio
# 
#

from waveshare import epd2in13
import sys,time
import Image
import ImageDraw
import ImageFont
import pdb

fontType = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
fontSize = 24


# No interrupt routine if none supplied
def no_interrupt():
        return False

class   Epd:
	# Oversize message handling
	TRUNCATE=0
	SCROLL=1
	WRAP=2

	oversize = WRAP

	height = 0
	width = 0
	line_fill = 255
	char_fill = 0
	tLines = 4
	tWidth = 18
	volumeLevel = 0

	# Scroll buffer
	LineBuffer= []
	BufferIndex = []

	def __init__(self):
		self.epd = epd2in13.EPD()
		self.epd.init(self.epd.lut_full_update)
		self.height = epd2in13.EPD_HEIGHT
		self.width = epd2in13.EPD_WIDTH
		self.epd.display_frame()

		# Set up partial update mode
		self.epd.delay_ms(100)
		self.epd.init(self.epd.lut_partial_update)

		# Create line frame
		self.frame = Image.new('1', (250, 28), 255)  # 255: clear the frame
		self.draw = ImageDraw.Draw(self.frame)

		# Create font
		self.font = ImageFont.truetype(fontType,fontSize)

		# Create scroll line buffers
		for i in range(0,self.tLines):
			self.LineBuffer.append('')
			self.BufferIndex.append(0)
			 
		self.oversize = self.TRUNCATE

	# Clear the screen
	def clear(self):
		# 255: clear the frame
		image = Image.new('1', (self.width, self.height), 255)
		draw = ImageDraw.Draw(image)
		self.epd.clear_frame_memory(0xFF)
		# Clear both memory areas of the e-paper display
		self.epd.set_frame_memory(image, 0, 0)
		self.epd.display_frame()
		self.epd.set_frame_memory(image, 0, 0)
		self.epd.display_frame()

	# Top display routine
	def out(self,line_number,text,interrupt):
		if len(text) > self.tWidth:
			
			if self.oversize == self.SCROLL:			
				self._scroll(line_number,text)

			elif self.oversize == self.WRAP:
				self._wrap(line_number,text)
				self.BufferIndex[line_number-1] += 1 #DEBUG

			else:
				self._out(line_number,text[:self.tWidth])
		else:
			self._out(line_number,text)
		return

	# Text out
	def _out(self,line_number,text="",interrupt=no_interrupt):
		self.LineBuffer[line_number-1] = text
		return

	def _wrap(self,line_number,text="",interrupt=no_interrupt):
		self.LineBuffer[line_number-1] = text[:self.tWidth]
		self.LineBuffer[line_number] = text[self.tWidth:]
		return

	# Set oversize text behaviour
	def setWrap(self,mode):
		if mode >= self.TRUNCATE and mode <= self.WRAP:
			self.oversize = mode

	# Update the display
	def update(self):
		# Write text to lines
		for i in range(0,self.tLines):
			text = self.LineBuffer[i]
			print i+1,text
			if len(text) > 0 or self.BufferIndex[i] > 0:
				line_number = i+1
				image_width, image_height  = self.frame.size
				self.draw.rectangle((0, 0, image_width, image_height), 
							fill = self.line_fill)
				self.draw.text((0, 0), text, font = self.font, 
							fill = self.char_fill)
				
				xPos = 0
				yPos = (line_number - 1) * image_height

				xPos = self.height - image_width - xPos
				self.epd.set_frame_memory(self.frame.transpose(Image.ROTATE_90), 
							yPos, xPos)
		# Draw volume slider
		self.drawSlider(5,self.volumeLevel)
		# Update screen
		self.epd.display_frame()

	# Scroll text
	def _scroll(self,line_number,text="",interrupt=no_interrupt):
		sText = text[self.BufferIndex[line_number-1]:]
		self._out(line_number,sText)
		fSize = self.font.getsize(sText)
		if fSize[0] > self.height:
			self.BufferIndex[line_number-1] += 1
		else:
			self.BufferIndex[line_number-1] = 0
			
		return

	# Reverse screen colour
	def reverse(self,truefalse):
		if truefalse:
			self.line_fill = 0
			self.char_fill = 255
		else:
			self.line_fill = 255
			self.char_fill = 0

	# Has color
	def hasColor(self):
		return False

	# Flip ePaper display vertically TO BE DONE
	def flip_display_vertically(self,flip):
		return

	# Send display to sleep
	def sleep(self):
		self.epd.sleep()

	# Get terminal width in characters
        def getWidth(self):
                return self.tWidth

	# Get number of terminal lines
        def getLines(self):
                return self.tLines

	# set width unused
	def setWidth(self,notused):
                return self.tWidth

	# Draw splash
	def drawSplash(self,bitmap,delay):
		self.clear()
		image = Image.open(bitmap)
		image = image.rotate(90)
		size = (96,96)
		image = image.resize(size=size,resample=0)
		xPos = (self.width-size[0])/2
		yPos = (self.height-size[1])/2
		self.epd.set_frame_memory(image, xPos, yPos)
		self.epd.display_frame()
		self.epd.set_frame_memory(image, xPos, yPos)
		self.epd.display_frame()
		#self.epd.set_frame_memory(self.epd.display_frame.transpose(Image.ROTATE_90),0,0) 
		self.epd.display_frame()
		time.sleep(delay)
		self.clear()
		return

	# Set volume slider
        def volume(self,volume):
                if volume > 100:
                        volume = 100
                elif volume < 0:
                        volume = 0
		self.volumeLevel = volume
		return

	# Draw the volume slider
	def drawSlider(self,line_number,volume):
		border = 3
		image_width, image_height  = self.frame.size
		self.draw.rectangle((0, 0, image_width, image_height), fill = 0)
		self.draw.rectangle((border, border, volume*image_width/100, image_height - border), fill = 1)
		xPos = 0
		yPos = (line_number - 1) * image_height

		xPos = self.height - image_width - xPos
		self.epd.set_frame_memory(self.frame.transpose(Image.ROTATE_90), 
					yPos, xPos)
		return

# End of Epd class

# Class test routine
if __name__ == "__main__":
        import time,datetime
	epd = Epd()
	epd.setWrap(epd.WRAP)

	epd.clear()
	epd.reverse(False)
	epd.drawSplash('bitmaps/raspberry-pi-logo.bmp',2)
	volume = 90
	try:
		while True:
			text =  time.strftime('%d/%m/%Y %H:%M')
			epd.out(1,text,no_interrupt)
			epd.out(2,"Bob Rathbone",no_interrupt)
			epd.out(3,"ABCDEFGHIJKLMNOPQRSTUVWXYZ",no_interrupt)
			#pdb.set_trace()
			#epd.out(4,"0123456789",no_interrupt)
			epd.volume(volume)
			epd.update()
			volume -= 5
			if volume < 0:
				volume = 90
			

	except KeyboardInterrupt:
		print "\nExit"
		epd.sleep()
		sys.exit(0)

# End of test functions
