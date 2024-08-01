#!/usr/bin/env python3
# $Id: ssd1306_class.py,v 1.27 2024/03/03 18:43:14 bob Exp $
# This class drives the Sitronix SSD1306 controller for the 128x64 pixel TFT
# It requirs the I2C dtoverlay to be loaded. The I2C address is normally 0x37
#
# $Id: ssd1306_class.py,v 1.27 2024/03/03 18:43:14 bob Exp $
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#          The authors shall not be liable for any loss or damage however caused.
#
# Acknowledgement: Adapted from Pimoroni example code originally adapted from
# code from Tony DiCola & James Divito Adafruit Industries
#
# Pre-requisites: This driver requires the Adafruit SSD1306 python3 packages to be loaded.
# 
# sudo apt-get install git
# git clone https://github.com/adafruit/Adafruit_Python_SSD1306.git
# cd Adafruit_Python_SSD1306
# sudo python3 setup.py install
# OR RUN
# sudo apt -y install libffi-dev
# sudo apt -y install build-essential libi2c-dev i2c-tools python3-dev
# pip3 install Adafruit-SSD1306

import sys,time
import signal
from PIL import Image, ImageDraw, ImageFont
import Adafruit_SSD1306 
import pdb

# Raspberry Pi pin configuration:
RST = None     # on the PiOLED this pin isnt used

# 128x64 display with hardware I2C:
oled = Adafruit_SSD1306.SSD1306_128_64(rst=RST)

width = oled.width
height = oled.height
size = (width,height)

# Line addresses
#        1 2  3  4  
Lines = [0,16,32,48]


# Global definitions
image = None    # PIL image
draw = None     #  Imge draw object
display = None  # Our "canvas"

## SSD1306 TFT display class
class SSD1306:
    # See fc-list command for available fonts
    font = ImageFont.truetype("DejaVuSansMono.ttf", 13)

    # Define display characteristics
    nlines = 4
    nchars = 16

    scroll_speed = 0.002

    def __init__(self):
        return

    # Initialisation routes
    def init(self,callback,code_page=0):
        global image,draw,display
        self.callback = callback
        image = Image.new('1', (size))
        draw = ImageDraw.Draw(image) # This is our canvas 
        display = self  # This is our canvas
        oled.begin()

        # Primitives called by upper layer functions

    # Update the display canvas with all of drawn images
    # Must be called to display the objects previously drawn
    def update(self):
        oled.display()

    # All draw routines must be followed by the display routine
    def drawRectangle(self,location,outline=1,fill=0):
        image = Image.new('1', (size))
        draw = ImageDraw.Draw(image)
        draw.rectangle((location),outline,fill)

    # Draw image at location at x,y
    def drawImage(self,image,x,y):
        try:
            img = Image.open(image).convert('1')
            img = img.resize((width, height))
            oled.image(img)
        except Exception as e:
            print("drawImage",str(e))

    # Dummy set width
    def setWidth(self,width):
        return width

    # This device does not have color capability
    def hasColor(self):
        return False

    # Draw the Splash screen
    def drawSplash(self,image,delay):
        self.drawImage(image,0,0)
        display.update()
        time.sleep(delay)

    # Clear screen
    def clear(self):
        image = Image.new('1', size)
        draw = ImageDraw.Draw(image)
        draw.rectangle((0,0,size), outline=0, fill=0)
        oled.image(image)
        display.update()

    # Set the size of font
    def setFontSize(self,font_size):
        self.font = ImageFont.truetype("DejaVuSansMono.ttf", font_size)
        return self.font

    def out(self,line,text,interrupt):
        if line <= self.nlines:
            if len(text) > self.nchars:
                self._scroll(line,text,interrupt)
            else:
                self._out(line,text)

    def clearLine(self,line):
        if line <= self.nlines:
            x = 0
            y = Lines[line-1]
            draw.rectangle((0,y,width,16 * line), outline=0, fill=0)
            oled.image(image)

    def _out(self,line,text):
        x = 0
        y = Lines[line-1]
        draw.rectangle((0,y,width,16 * line), outline=0, fill=0)
        draw.text((x,y),text[:self.nchars],font=self.font,fill=255)
        oled.image(image)

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
        
                fsize = self.font.getsize(text[i:])
                if fsize[0] <  width:
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

    # Display volume slider on line 4
    def volume(self,vol):
        line = 4 
        x = 0
        # Clear any previous text
        y = Lines[line-1]
        draw.rectangle((0,y,width,16 * line), outline=0, fill=0)
        y = Lines[line-1] + 4
        x1 = width - 1
        y1 = 16*line - 4
        draw.rectangle((x,y,x1,y1), outline=1, fill=0)
        x1 = int(width * vol/100)
        # Draw the volume level
        draw.rectangle((x,y,x1,y1), outline=1, fill=1)

    # Get number of lines for this OLED
    def getLines(self):
        return self.nlines

    # Get character width for this OLED
    def getChars(self):
        return self.nchars

if __name__ == '__main__':
    import os
    import pwd
    from log_class import Log
    from time import strftime

    dateformat = "%H:%M %d/%m/%Y"
    log = None
    UP=1
    log = Log()
    if len(log.getName()) < 1:
        log.init("radio")
    eventStr = "No event"
    volume = 0

    # Signal SIGTERM handler
    def signalHandler(signal,frame):
        display.clear()
        sys.exit(0)

    # Interrupt routine
    def interrupt():
        return False
        
    # Main code
    signal.signal(signal.SIGTERM,signalHandler)
    signal.signal(signal.SIGHUP,signalHandler)
    pid =  str(os.getpid())
    print( "TFT test PID %s" % pid)
    print("Screen %s x %s" % (width,height))

    display = SSD1306()
    display.init(None)
    display.clear()

    # Display splash
    dir = os.path.dirname(__file__)
    display.drawSplash(dir + "/images/raspberrypi.png",2)
    #display.update()

    image = Image.new('1', (width, height))
    draw = ImageDraw.Draw(image) # This is our canvas 

    display.clear()
    while True:
        try:

            display.volume(volume)

            sDate = strftime(dateformat)
            display.out(1,sDate,interrupt)
            
            text = "PID %s Vol %s" % (pid, volume)
            display.out(3,text,interrupt)

            text = "abcdefghijklmnopqrstuvwxyz 0123456789"
            display.out(2,text,interrupt)

            display.update()
            time.sleep(0.3)

            volume += 10
            if volume > 100:
                volume = 0

        except KeyboardInterrupt:
            #pdb.set_trace()
            display.clear()
            text = "    Goodbye     "
            display.clearLine(1)
            display.out(2,text,None)
            display.clearLine(3)
            display.clearLine(4)
            display.update()
            sys.exit(0)

# End of test routine

# :set tabstop=4 shiftwidth=4 expandtab
# :retab

