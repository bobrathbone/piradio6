#!/usr/bin/env python3
# $Id: luma_class.py,v 1.37 2002/01/21 06:45:41 bob Exp $
# This class drives the SH1106 controller for the 128x64 pixel TFT
# It requirs the I2C dtoverlay to be loaded. The I2C address is normally 0x37
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#          The authors shall not be liable for any loss or damage however caused.
#
# Pre-requisites: This driver requires the Adafruit SSD1306 python3 packages to be loaded.
# https://luma-oled.readthedocs.io/en/latest/
# Enable I2C
# 
# Install dependencies
# sudo -H pip3 install --upgrade luma.oled
# sudo apt-get install python3 python3-pip python3-pil libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev libopenjp2-7 libtiff5 -y
# sudo -H pip3 install luma.oled
# sudo apt-get install python3-pil
# 

import sys,time
import signal
import pdb

from luma.core.interface.serial import i2c, spi, pcf8574
from luma.core.interface.parallel import bitbang_6800
from luma.core.render import canvas
from luma.oled.device import ssd1306, ssd1309, ssd1325, ssd1331, sh1106, ws0010

from PIL import ImageFont, Image, ImageDraw

# Raspberry Pi pin configuration:
RST = None     # on the PiOLED this pin isnt used

# rev.1 users set port=0
# substitute spi(device=0, port=0) below if using that interface
# substitute bitbang_6800(RS=7, E=8, PINS=[25,24,23,27]) below if using that interface
serial = i2c(port=1, address=0x3C)

# 128x64 display with hardware I2C:
oled = sh1106(serial)


# Test text do determine number of characters to fit the screen
sText = "The quick brown fox jumped over the lazy dog"

# Global definitions
image = None    # PIL image
display = None  # Our "canvas"

## LUMA TFT display class
class LUMA:
    # See fc-list command for available fonts
    font_name = "DejaVuSansMono.ttf"
    font_size = 13
    font = ImageFont.truetype(font_name, font_size)

    # Define display characteristics
    nlines = 4
    nchars = 20
    line_height = 16
    bartop = 4  # Volume bar top size correction
    barbot = 4  # Volume bar bottom size correction
    scroll_speed = 0.005
    iVolume = 0
    rotation = 0

    # Line addresses
    #        1 2  3  4  
    Lines = [0,16,32,48]
    TextLines = ["","","",""]

    def __init__(self):
        return

    # Initialisation routes
    def init(self,callback=None,code_page=0,device_driver='SH1106',
             font_size=13,font_name="DejaVuSansMono.ttf",rotation=0):
        #global image,draw,display,oled
        global image,display,oled
        self.callback = callback
        self.rotation = rotation
        self.font_size = font_size
        self.font_name = font_name.replace('"','')
        self.font = ImageFont.truetype(self.font_name, self.font_size)
        oled = self.configureDevice(device_driver,self.rotation)

        # Work out number of characters will fit on the screen
        i = len(sText)
        while self.font.getlength(sText[:i]) > float(oled.width):
            i = i-1
        self.nchars = i

    # Configure the LUMA oled device and screen orientation
    # ssd1306, ssd1309, ssd1325, ssd1331, sh1106, ws0010
    def configureDevice(self,device_driver,rotation):
        self.device_driver = device_driver.upper()
        if self.device_driver == 'SSD1306':
            oled = ssd1306(serial,rotate=rotation)
        elif self.device_driver == 'SSD1309':
            oled = ssd1309(serial,rotate=rotation)
        elif self.device_driver == 'SSD1331':
            oled = ssd1331(serial,rotate=rotation)
        elif self.device_driver == 'WS0010':
            oled = ws0010(serial,rotate=rotation)
        elif self.device_driver == 'SH1106_128X32':
            # Although this is a 128x32 bit display    
            # Luma maps it to 128x64 bits
            oled = sh1106(serial,rotate=rotation)
            self.bartop = 2
            self.barbot = 0
        else:
            oled = sh1106(serial,rotate=rotation)
        return oled
        
    # Draw image at location at x,y
    def drawImage(self,image,x,y):
        try:
            background = Image.new("RGBA", oled.size, "white")
            img = Image.open(image).convert('1')
            #img = img.resize((oled.width, oled.height))
            size = oled.height
            img = img.resize((size, size))
            background.paste(img, (x,0))
            oled.display(background.convert(oled.mode))
        except Exception as e:
            print("drawImage:",str(e))

    # Dummy set width
    def setWidth(self,width):
        return width

    # This device does not have color capability
    def hasColor(self):
        return False

    # Draw the Splash screen
    def drawSplash(self,image,delay):
        if oled.width > oled.height:
            x = int((oled.width -  oled.height) / 2)
        self.drawImage(image,x,0)
        time.sleep(delay)

    # Clear screen
    def clear(self):
        oled.clear()
        for i in range(self.nlines):
            self.TextLines[i] = "" 

    # Set the size of font
    def setFontSize(self,font_size):
        self.font = ImageFont.truetype(self.font_name, font_size)
        return self.font

    # Set the font name
    def setFontName(self,font_name):
        self.font = ImageFont.truetype(self.font_name, self.font_size)
        return self.font

    def out(self,line,text,interrupt):
        if line <= self.nlines:
            if len(text) > self.nchars:
                self._scroll(line,text,interrupt)
            else:
                self._out(line,text)

    # Clear single line buffer
    def clearLine(self,line):
        if line <= self.nlines:
            self.TextLines[line-1] = ""

    # The _out routine stores the texi TextLines for update to display
    def _out(self,line,text):
        self.TextLines[line-1] = text[:self.nchars + 1]

    # The update routine displays the buffered lines and volume
    def update(self):
        x = 0
        with canvas(oled) as draw:
            for i in range(self.nlines):
                y = self.Lines[i]
                text = self.TextLines[i]
                draw.text((x,y),text,font=self.font,fill=255)
            
            # Display volume bar or mute message
            # Any text in line buffer 4 overrides display of the volume bar
            if self.nlines > 3 and len(self.TextLines[3]) > 1:
                y = self.Lines[3]
                text = self.TextLines[3]
                draw.text((x,y),text[:self.nchars],font=self.font,fill=255)
            else: 
                self._volume(draw,self.iVolume)

    # Scroll line - interrupt() breaks out routine if True
    def _scroll(self,line,text,interrupt):
        ilen = len(text)
        skip = False

        # Display only for the width  of the LCD
        self._out(line,text)
        self.update()

        # Small delay before scrolling
        if not skip:
            for i in range(0, 16):
                time.sleep(self.scroll_speed)
                if interrupt():
                    skip = True
                    break

        # Now scroll the message
        if not skip:
            for i in range(0, ilen):
                self._out(line,text[i:])
                self.update()
        
                fsize = self.font.getlength(text[i:])
                if fsize <=  float(oled.width):
                    break

                if interrupt():
                    skip = True
                    break
                else:
                    time.sleep(self.scroll_speed)

        # Small delay before exiting
        if not skip:
            for i in range(0, 16):
                time.sleep(self.scroll_speed)
                if interrupt():
                        break
        return

    def volume(self,vol):
        self.iVolume = vol

    # Display volume slider on line 4
    def _volume(self,draw,vol):
        line = len(self.Lines)
        x = 0
        # Clear any previous text
        y = self.Lines[line-1]
        draw.rectangle((0,y,oled.width,self.line_height * line), outline=0, fill=0)
        y = self.Lines[line-1] + self.bartop
        x1 = oled.width - 1
        y1 = self.line_height*line - self.barbot  
        draw.rectangle((x,y,x1,y1), outline=1, fill=0)
        x1 = int(oled.width * vol/100)
        # Draw the volume level
        draw.rectangle((x,y,x1,y1), outline=1, fill=1)

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

    # Get Luma device
    def getDeviceDriver(self):
        return self.device_driver

if __name__ == '__main__':
    import os
    from log_class import Log
    from time import strftime

    dateformat = "%H:%M %d/%m/%Y"
    log = None
    UP=1
    log = Log()
    eventStr = "No event"
    volume = 0
    speed_test = False

    # Luma device for SSD1306, SSD1309, SSD1325, SSD1331, SH1106, SH1106_128x32, WS0010
    # Change to the device you want to test and the font size 
    device = 'SH1106' 
    #device = 'SSD1309' 
    font_size = 12
    font_name = "DejaVuSansMono.ttf"

    # Flip the display
    NORMAL=0
    FLIP=2

    # Signal SIGTERM handler
    def signalHandler(signal,frame):
        display.clear()
        sys.exit(0)

    # Interrupt routine
    def interrupt():
        return False
        
    # Centre text
    def centreText(text):
        nchars = display.getChars()
        text = text[:nchars]
        textLen = len(text)  
        lmargin = int((nchars - textLen)/2)
        text = "         "[:lmargin] + text
        return text

    # Main code
    signal.signal(signal.SIGTERM,signalHandler)
    signal.signal(signal.SIGHUP,signalHandler)

    pid =  str(os.getpid())
    print( "LUMA TFT test PID %s" % pid)

    display = LUMA()
    # FLIP = Flip display verticaly, NORMAL = Don't flip
    display.init(None,device_driver=device,font_name=font_name,font_size=font_size,rotation=NORMAL)
    font = display.setFontSize(font_size)

    print("OLED = " + display.getDeviceDriver())
    print("Screen: %s x %s" % (oled.width,oled.height))
    print("Lines:" + str(display.getLines()) + " Character Width:" + str(display.getChars()))
    print("Font size: " + str(font_size))
    print("Oled color:",display.hasColor())

    display.clear()

    # Display splash
    dir = os.path.dirname(__file__)
    display.drawSplash(dir + "/images/raspberrypi.png",2)

    display.clear()
    while True:
        try:
            display.volume(volume)

            sDate = strftime(dateformat)
            sDate = "10:30 6/10"
            display.out(1,sDate,interrupt)
            
            text = "abcdefghijklmnopqrstuvwxyz 0123456789"
            if speed_test:
                display.out(2,text[0:display.getChars()],interrupt)
            else:
                display.out(2,text,interrupt)
    
            text = "PID %s Vol %s" % (pid, volume)
            display.out(3,text,interrupt)

            display.update()

            volume += 10
            if volume > 100:
                volume = 0

        except KeyboardInterrupt:
            display.clear()
            text = centreText("Goodbye") 
            display.out(2,text,None)
            display.update()
            time.sleep(3)
            sys.exit(0)

# End of test routine

# :set tabstop=4 shiftwidth=4 expandtab
# :retab

