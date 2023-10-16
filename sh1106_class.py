#!/usr/bin/env python3
# This class drives the Waveshare SH1106 controller using the SPI interface
# as used by the Waveshare 1.3" 128 X 64 OLED RPi hat with 3 buttons and a 5-button joystick 
# It requires the SPI dtoverlay to be loaded. 
#
# $Id: sh1106_class.py,v 1.14 2023/10/04 16:02:01 bob Exp $
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# Modified from original Waveshare SH1106 driver code
# See: https://files.waveshare.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#          The authors shall not be liable for any loss or damage however caused.
#
# It requires the following commands to install the prerequisites
# sudo apt-get install python3-pip
# sudo pip3 install RPi.GPIO
# sudo apt-get install python3-smbus
# sudo pip3 install spidev

import sh1106_config
import RPi.GPIO as GPIO
import time
import pdb
import numpy as np
from PIL import Image,ImageDraw,ImageFont

Device_SPI = sh1106_config.Device_SPI
Device_I2C = sh1106_config.Device_I2C

LCD_WIDTH   = 128 #LCD width
LCD_HEIGHT  = 64  #LCD height

class SH1106:

    # Define display characteristics
    nlines = 4
    nchars = 16

    scroll_speed = 0.04

    # Line addresses
    #        1 2  3  4
    Lines = [0,16,32,48]

    # See fc-list command for available fonts
    font = ImageFont.truetype("DejaVuSansMono.ttf", 13)

    def __init__(self):
        self.width = LCD_WIDTH
        self.height = LCD_HEIGHT
        #Initialize DC RST pin
        self._dc = sh1106_config.DC_PIN
        self._rst = sh1106_config.RST_PIN
        self._bl = sh1106_config.BL_PIN
        self.Device = sh1106_config.Device

    """    Write register address and data     """
    def command(self, cmd):
        if(self.Device == Device_SPI):
            GPIO.output(self._dc, GPIO.LOW)
            sh1106_config.spi_writebyte([cmd])
        else:
            sh1106_config.i2c_writebyte(0x00, cmd)

    # def data(self, val):
        # GPIO.output(self._dc, GPIO.HIGH)
        # sh1106_config.spi_writebyte([val])

    def init(self,callback):
        if (sh1106_config.module_init() != 0):
            return -1
        """Initialize display"""    
        self.reset()
        self.command(0xAE);#--turn off oled panel
        self.command(0x02);#---set low column address
        self.command(0x10);#---set high column address
        self.command(0x40);#--set start line address  Set Mapping RAM Display Start Line (0x00~0x3F)
        self.command(0x81);#--set contrast control register
        self.command(0xA0);#--Set SEG/Column Mapping     
        self.command(0xC0);#Set COM/Row Scan Direction   
        self.command(0xA6);#--set normal display
        self.command(0xA8);#--set multiplex ratio(1 to 64)
        self.command(0x3F);#--1/64 duty
        self.command(0xD3);#-set display offset    Shift Mapping RAM Counter (0x00~0x3F)
        self.command(0x00);#-not offset
        self.command(0xd5);#--set display clock divide ratio/oscillator frequency
        self.command(0x80);#--set divide ratio, Set Clock as 100 Frames/Sec
        self.command(0xD9);#--set pre-charge period
        self.command(0xF1);#Set Pre-Charge as 15 Clocks & Discharge as 1 Clock
        self.command(0xDA);#--set com pins hardware configuration
        self.command(0x12);
        self.command(0xDB);#--set vcomh
        self.command(0x40);#Set VCOM Deselect Level
        self.command(0x20);#-Set Page Addressing Mode (0x00/0x01/0x02)
        self.command(0x02);#
        self.command(0xA4);# Disable Entire Display On (0xa4/0xa5)
        self.command(0xA6);# Disable Inverse Display On (0xa6/a7) 
        time.sleep(0.1)
        self.command(0xAF);#--turn on oled panel

        # Create a canvas
        self.canvas = Image.new('1', (self.width, self.height), "WHITE")
        self.draw = ImageDraw.Draw(self.canvas)
        
   
    def reset(self):
        """Reset the display"""
        GPIO.output(self._rst,GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(self._rst,GPIO.LOW)
        time.sleep(0.1)
        GPIO.output(self._rst,GPIO.HIGH)
        time.sleep(0.1)
    
    def getbuffer(self, image):
        # print "bufsiz = ",(self.width/8) * self.height
        buf = [0xFF] * ((self.width//8) * self.height)
        image_monocolor = image.convert('1')
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()
        # print "imwidth = %d, imheight = %d",imwidth,imheight
        if(imwidth == self.width and imheight == self.height):
            # print ("Vertical")
            for y in range(imheight):
                for x in range(imwidth):
                    # Set the bits for the column of pixels at the current position.
                    if pixels[x, y] == 0:
                        buf[x + (y // 8) * self.width] &= ~(1 << (y % 8))
                        # print x,y,x + (y * self.width)/8,buf[(x + y * self.width) / 8]
                        
        elif(imwidth == self.height and imheight == self.width):
            # print ("Vertical")
            for y in range(imheight):
                for x in range(imwidth):
                    newx = y
                    newy = self.height - x - 1
                    if pixels[x, y] == 0:
                        buf[(newx + (newy // 8 )*self.width) ] &= ~(1 << (y % 8))
        return buf
    
    def drawImage(self,filename,x,y):
        image1 = Image.new('1', (self.width, self.height), "WHITE")
        img = Image.open(filename)
        image1.paste(img, (x,y))
        draw = ImageDraw.Draw(image1)
        self.ShowImage(self.getbuffer(image1))

    # Draw the Splash screen
    def drawSplash(self,filename,delay):
        x = int(self.width/4)
        y = int(0)
        self.drawImage(filename,x,y)
        time.sleep(delay)
    
    # Show the requested image from buffer
    def ShowImage(self, pBuf):
        for page in range(0,8):
            # set page address #
            self.command(0xB0 + page);
            # set low column address #
            self.command(0x02); 
            # set high column address #
            self.command(0x10); 
            # write data #
            # time.sleep(0.01)
            if(self.Device == Device_SPI):
                GPIO.output(self._dc, GPIO.HIGH);
            for i in range(0,self.width):#for(int i=0;i<self.width; i++)
                if(self.Device == Device_SPI):
                    sh1106_config.spi_writebyte([~pBuf[i+self.width*page]]); 
                else :
                    sh1106_config.i2c_writebyte(0x40, ~pBuf[i+self.width*page])
                    
    # Clear screen
    def clear(self):
        """Clear contents of image buffer"""
        _buffer = [0xff]*(self.width * self.height//8)
        self.ShowImage(_buffer) 
            #print "%d",_buffer[i:i+4096]
        extents = (1,1,self.width,self.height)
        self.drawRectangle(extents,outline=1,fill=1)

    # Display text on a given line
    def out(self,line,text,interrupt=None):
        if line < 1 :
            line = 1
        if line <= self.nlines:
            if len(text) > self.nchars:
                self._scroll(line,text,interrupt)
            else:
                self._out(line,text)

    def _out(self,line,text):
        x = 1
        y = self.Lines[line-1]
        x1 = self.width 
        y1 = 16 * line
        draw = ImageDraw.Draw(self.canvas)
        draw.rectangle((x,y,x1,y1), outline=1, fill=1)
        draw.text((x,y), text, font=self.font, fill = 0)

    # Set the size of font
    def setFontSize(self,font_size):
        self.font = ImageFont.truetype("DejaVuSansMono.ttf", font_size)
        return self.font

    # Scroll line - interrupt() breaks out routine if True
    def _scroll(self,line,text,interrupt):
        ilen = len(text)
        skip = False

        # Display only for the width  of the LCD
        self._out(line,text)
        self.update()
       # Small delay before scrolling
        if not skip:
            for i in range(0, 5):
                time.sleep(0.1)
                if interrupt():
                    skip = True
                    break

        # Now scroll the message
        if not skip:
            for i in range(0, ilen):
                self._out(line,text[i:])
                self.update()

                #fsize = self.font.getsize(text[i:])
                fsize = int(self.font.getlength(text[i:]))
                if fsize <  self.width:
                    break

                if interrupt():
                    skip = True
                    break
                else:
                    time.sleep(self.scroll_speed)

        # Small delay before exiting
        if not skip:
            for i in range(0, 5):
                time.sleep(0.1)
                if interrupt():
                        break
        return


    # Update the canvas
    def update(self):
        self.ShowImage(self.getbuffer(self.canvas))

    # Draw a rectangle
    def drawRectangle(self,extents,outline=1,fill=0):
        self.draw = ImageDraw.Draw(self.canvas)
        self.draw.rectangle((extents), outline, fill)

    # Display volume slider on line 4
    def volume(self,vol):
        line = 4
        x = 1
        # Clear any previous text
        y = self.Lines[line-1]
        self.drawRectangle((0,y,self.width,16 * line), outline=1, fill=1)
        y = self.Lines[line-1] + 4
        x1 = self.width - 1
        y1 = 16*line - 4
        self.drawRectangle((x,y,x1,y1), outline=1, fill=0)
        x1 = int(self.width * vol/100)
        if x1 < x:
            x1 = 3 
        # Draw the volume level
        y -= 1
        y1 += 1
        self.drawRectangle((x,y,x1,y1), outline=0, fill=1)

   # This device does not have color capability (monochrome)
    def hasColor(self):
        return False

    # Return number of display lines
    def getLines(self):
        return self.nlines

    # Get character width (not pixels)
    def getWidth(self):
        return self.nchars

    # Set character width 8 to 32 
    def setWidth(self,width):
        self.nchars = width
        return self.nchars

    # Inverse display
    def invert_display(self,inverse):
        if inverse: 
            self.command(0xa7)  
        else:
            self.command(0xa6)  

    # Flip OLED display vertically (not used)
    def flip_display_vertically(self,flip):
        # flip is True or False
        if flip:
            self.command(0xc8)  #0xc0


    # Set Scroll line speed - Best values are 0.2 and 0.3
    # Limit to between 0.08 and 0.6
    def setScrollSpeed(self,speed):
        if speed < 0.08:
                speed = 0.08
        elif speed > 0.6:
                speed = 0.6
        self.scroll_speed = speed
        return self.scroll_speed

# End of SH1106 class

# Test routine
if __name__ == '__main__':
    import os 
    import sys 
    from sh1106_class import SH1106
    from time import strftime

    dateformat = "%H:%M %d/%m/%Y"
    
    # Interrupt routine
    def interrupt():
        return False

    display = SH1106()
    display.init(interrupt)
    display.setScrollSpeed(0.2)
    display.clear()

    # Uncomment to invert display
    #display.flip_display_vertically(True)
    #display.invert_display(True)

    # Display display details
    print("SH1106 SPI display %sx%s pixels" % (display.height, display.width))
    print("Lines: %s, Characters: %s" % (display.nlines,display.nchars))

    # Draw raspberry pi logo
    display.drawSplash('bitmaps/raspberry-pi-logo.bmp',2)
    time.sleep(2)

    # Draw image at position x and y
    #display.drawImage('images/pic.jpg',0,0)
    #time.sleep(3)
    display.setFontSize(12)

    line = 1
    display.clear()
    volume  = 0

    #sys.exit(0) # Debug

    while True:
        try:
            display.volume(volume)
            sDate = strftime(dateformat)
            display.out(1,sDate,interrupt)
            line += 1
            display.out(line,"Volume level " + str(volume),interrupt)
            line += 1
            display.out(line,"abcdefghijklmopqrstuvwxyz 1234567890",interrupt)
            #extents = (0,52,127,60)
            #display.drawRectangle(extents)
            display.update()
            time.sleep(1)
            volume += 5
            if volume > 100:
                volume = 0
            line = 1

        except KeyboardInterrupt:
            print("\nExiting!")
            display.invert_display(False)
            display.clear()
            display.out(1,"Program exited!")
            display.out(2,"")
            display.out(3,"")
            display.out(4,"")
            display.update()
            exit(0)

    # End of test routine

# :set tabstop=4 shiftwidth=4 expandtab
# :retab
