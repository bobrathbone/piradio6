#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# $Id: ws_spi_ssd1309_class.py,v 1.17 2024/11/25 10:17:30 bob Exp $
# This class drives the waveshare SSD1309 OLED with SPI interface
# It requires the SPI dtoverlay to be loaded. 
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#          The authors shall not be liable for any loss or damage however caused.

import sys
import os
import pdb
import socket

dir = os.getcwd()
libdir = os.path.join(dir,'waveshare_OLED/lib')
picdir = os.path.join(dir,'waveshare_OLED/pic')
fontdir = os.path.join(dir,'waveshare_OLED/fonts')

if os.path.exists(libdir):
    sys.path.append(libdir)

import time
import traceback
from waveshare_OLED.lib import OLED_2in42
from waveshare_OLED.lib import OLED_1in5_b
from PIL import Image,ImageDraw,ImageFont,ImageOps

# Test text do determine number of characters to fit the screen
sText = "The quick brown fox jumped over the lazy dog"

class WS_spi_ssd1309:

    # See fc-list command for available fonts
    #font_name = "DejaVuSansMono.ttf"
    #font_name = "Font.ttc"
    #font_size = 13
    #font = ImageFont.truetype(font_name, font_size)

    # Define display characteristics
    nlines = 5
    nchars = 20
    scroll_speed = 0.05
    iVolume = 0
    rotation = 0

    # Line addresses
    #        1 2  3  4  5
    Lines = [0,14,26,38,48]
    TextLines = ["","","","",""]

    width = 128
    height = 64
    line_height = int(height/nlines)

    def __init__(self):
        self.image1 = Image.new('1', (self.width, self.height), "WHITE")
        return

    # Initialise routine with driver specified in configuration file
    def init(self,callback=None, flip=False, device_driver="2in42"):
        device_driver=device_driver.lower()
        if device_driver == "1in5":
            self.disp = OLED_1in5_b.OLED_1in5_b(spi_freq = 1000000)
        else:
            self.disp = OLED_2in42.OLED_2in42(spi_freq = 1000000)

        self.flip_img = flip
        self.disp.Init()
            
        self.font = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 10)
        self.font2 = ImageFont.truetype(os.path.join(fontdir, 'Font.ttc'), 12)

        # Work out number of characters will fit on the screen (aproximate)
        i = len(sText)
        while self.font.getlength(sText[:i]) > float(self.width):
            i = i-1
        self.nchars = i
        return

    # Clear the OLED display 
    def clear(self):
        self.disp.clear()

    def getHeight(self):
        return self.height

    def getWidth(self):
        return self.width

    def drawImage(self,image):
        self.Himage2 = Image.new('1', (self.width, self.height), 255)  # 255: clear the frame
        bmp = Image.open(os.path.join(picdir, image))
        self.Himage2.paste(bmp, (0,0))
        if self.flip_img:
            img = self.Himage2.rotate(180)
        else:
            img = self.Himage2
        self.disp.ShowImage(self.disp.getbuffer(img)) 

    def drawLine(self,pos,fill=0,width=0):
        img1 = ImageDraw.Draw(self.image1)
        img1.line(pos, fill, width) 
    
    def drawSplash(self,image=None,delay=3):
        img1 = Image.open(os.path.join(picdir, 'raspberry-pi-logo.bmp'))
        img2 = Image.open(os.path.join(picdir, 'waveshare.bmp'))
        img = Image.new('1', (self.width, self.height), "WHITE")
        img.paste(img1,(0,0))
        img.paste(img2,(int(self.width/2),1))
        img.save(os.path.join(picdir,'splash.bmp'))
        self.drawImage('splash.bmp')
        time.sleep(delay)
    
    # Draw a frame around outside
    def drawFrame(self):
        self.drawLine([(0,0),(127,0)], fill=0, width=0)
        self.drawLine([(0,0),(0,63)], fill = 0)
        self.drawLine([(0,63),(127,63)], fill = 0)
        self.drawLine([(127,0),(127,63)], fill = 0)

    # Update display buffer 
    def update(self):
        if self.flip_img:
            img = self.image1.rotate(180)
        else:
            img = self.image1
        self.disp.ShowImage(self.disp.getbuffer(img))

    # This device does not have color capability
    def hasColor(self):
        return False

    # Set the size of font (ignore)
    def setFontSize(self,font_size):
        return

    # Set the font name (ignore)
    def setFontName(self,font_name):
        return

    # Clear single line buffer
    def clearLine(self,line):
        if line <= self.nlines:
            self.TextLines[line-1] = ""

    def drawText(self,pos,text,font,fill=0,centre=False):
        x = pos[0]
        y = pos[1] 
        x1 = self.width - 2
        y1 = y + self.line_height
        self.drawRectangle((x-2,y,x1,y1), 1, 1)
        draw = ImageDraw.Draw(self.image1) 
        if centre:
            x = (self.width - self.font2.getlength(text)) / 2
            pos = (x,y)
        draw.text(pos, text, font=font, fill=fill)

    # Main text output routine
    def out(self,line,text,interrupt):
        if line <= self.nlines:
            i = len(text)
            while self.font.getlength(text[:i]) > float(self.width):
                i = i-1
                self.nchars = i
                self._scroll(line,text,interrupt)
            else:
                self._out(line,text)

    # The _out routine stores the text TextLines for updating display
    def _out(self,line,text,allow_centre=True):
        self.TextLines[line-1] = text[:self.nchars + 1]
        font = self.font
        x = 4
        y = self.Lines[line-1] + 2
        centre = False
        if allow_centre:
            if line == 1 or line == 5:   
                centre = True
                if line == 1:
                    font = self.font2
        self.drawText((x,y),text,font=font,fill=0,centre=centre)
 
    # Scroll line - interrupt() breaks out routine if True
    def _scroll(self,line,text,interrupt):
        ilen = len(text)
        skip = False

        # Display only for the width  of the LCD
        self._out(line,text[:self.nchars],allow_centre=False)
        self.update()

        # Small delay before scrolling
        if not skip:
            for i in range(0, 30):
                time.sleep(0.05)
                if interrupt():
                    skip = True
                    break

        # Now scroll the message
        fWidth = float(self.width)-3 # Screen width in pixels
        if not skip:
            for i in range(0, ilen):

                x = len(text[i:])
                self._out(line,text[i:],allow_centre=False)
                self.update()

                fSize = self.font.getlength(text[i:]) 
                if int(fSize) <=  int(fWidth):
                    break

                if interrupt():
                    skip = True
                    break
                else:
                    time.sleep(self.scroll_speed)

        # Small delay before exiting
        if not skip:
            for i in range(0, 30):
                #time.sleep(self.scroll_speed)
                time.sleep(0.05)
                if interrupt():
                        break
        return

    def drawRectangle(self,pos,fill,outline):
        img1 = ImageDraw.Draw(self.image1)
        img1.rectangle(pos,outline=outline,fill=fill)

    # Display volume slider on line 5
    def volume(self,vol):
        line = len(self.Lines)  # Get last line
        x = 0
        margin = 5
        # Clear any previous text
        x = margin
        y = self.Lines[line-1] + margin 
        x1 = self.width - margin

        # Draw slider ribbon
        y1 = self.line_height * line  - 2
        self.drawRectangle((x-2,y,x1,y1), 1, 1)
        self.drawRectangle((x,y,x1,y1), 1, 0)

        # Draw the volume level bar
        x1 = int((self.width-2*margin) * vol/100) + margin
        self.drawRectangle((x,y,x1,y1), outline=0, fill=0)

    # Get number of lines for this OLED
    def getLines(self):
        return self.nlines

    # Get character width for this OLED
    def getChars(self):
        return self.nchars

    # Set the scroll speed. 0 = use default
    def setScrollSpeed(self,scroll_speed):
        if scroll_speed > 0:
            self.scroll_speed = scroll_speed

    # Dummy set width
    def setWidth(self,width):
        return width


# End of WS_spi_oled class:
    
if __name__ == '__main__':
    from time import strftime

    dateformat = "%H:%M:%S %d/%m/%Y"

    # Interrupt routine
    def interrupt():
        return False

    try:
        #pdb.set_trace()

        print("\rWaveshare 2.42-inch OLED ")
        # Initialize library.
        disp = WS_spi_ssd1309() 
        driver = "2in42"    # or "1in5_B"
        # Flip the display vertically
        flip = True
        disp.init(callback=None, flip=flip, device_driver=driver)  

        # Clear display.
        disp.clear()
        disp.drawSplash(3)
        disp.update()

        disp.drawFrame()
        disp.setFontSize(10)

        volume = 0
        while True:
            sDate = strftime(dateformat)
            disp.out(1,"",interrupt)
            disp.volume(volume)
            disp.out(1,sDate,interrupt)
            text = "Bob Rathbone IT"
            disp.out(2,text,interrupt)
            text = "bob@bobrathbone.com"
            disp.out(3,text,interrupt)
            hostname = socket.gethostname()
            ipaddr = socket.gethostbyname(hostname)
            text = "IP %s" % ipaddr.split()[0] 
            disp.out(5,text,interrupt)
            text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789"
            disp.out(4,text,interrupt)

            # Flip the display and display buffer
            disp.update()

            volume += 10
            if volume > 100:
                volume = 0


    except IOError as e:
            print(str(e))
            
    except KeyboardInterrupt:    
        print("Ctrl + c:")
        disp.clear()
        exit()

# End of test routine

# :set tabstop=4 shiftwidth=4 expandtab
# :retab
