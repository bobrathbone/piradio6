#!/usr/bin/env python3
# This class drives the Sitronix ST7789 controller and 240x240 pixel TFT
#
# $Id: st7789tft_class.py,v 1.21 2002/01/01 13:37:48 bob Exp $
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#          The authors shall not be liable for any loss or damage however caused.
#
# Acknowledgement: Adapted from Pimoroni example code originally adapted from
# code from Tony DiCola Adafruit Industries
#
# Switch settings for radio software
# menu_switch=0
# mute_switch=0
# up_switch=16      Channel up
# down_switch=5     Channel down
# left_switch=6     Volume down
# right_switch=20   Volume up

"""
Key mapping
===========
Volume:  [A] DOWN --- [X] UP
Channel: [B] DOWN --- [Y] UP
"""

import sys,time
import signal
from PIL import Image, ImageDraw, ImageFont
import st7789 as ST7789
import pdb

# Commands to invert display (Not working on Pirate Audio)
ST7789_INVOFF = 0x20
ST7789_INVON = 0x21

tft = ST7789.ST7789(
    port=0,
    rotation=90,
    cs=ST7789.BG_SPI_CS_FRONT,  # BG_SPI_CSB_BACK or BG_SPI_CS_FRONT
    dc=9,
    backlight=13,               
    spi_speed_hz=80 * 1000 * 1000
)

# See fc-list command for available fonts

bgcolor = (0, 0, 150)

# Line addresses
#        1 2  3  4   5   6  
Lines = [0,40,90,130,165,195]
default_fontSize = 25
L2_fontSize = 35

## ST7789 TFT display class
class ST7789:
    scroll_speed = 0.001
    #        1  2  3  4  5  6
    TextLines = ['','','','','','']

    # Define display characteristics
    nlines = 7
    nchars = 16 # Character width can vary
    height = 0 
    width = 0

    # Line 2 is different from the others and uses a larger font
    default_font = ImageFont.truetype("DejaVuSansMono.ttf", default_fontSize)
    L2_font = ImageFont.truetype("DejaVuSansMono.ttf",L2_fontSize)
    L2_large_font = ImageFont.truetype("DejaVuSansMono.ttf",L2_fontSize)

    def __init__(self):
        return

    # Initialisation routes
    def init(self,callback,flip=False):
        global tft,canvas,draw
        self.callback = callback
        tft.begin()

        # Flip display if required (Not working on Pimoroni Pirate Audio)
        if flip:
            tft.command(ST7789_INVON)  # Invert display
        else:
            tft.command(ST7789_INVON)  # Don't invert display

        # Define a canvas to draw on
        self.width = tft.width
        self.height = tft.height
        size = (self.width,self.height)
        canvas = Image.new("RGB", (size), bgcolor)
        draw = ImageDraw.Draw(canvas)

    # Update the display canvas with all of drawn images
    # Must be called to display the objects previously drawn
    def update(self):
        tft.display(canvas)

    # All draw routines must be followed by the update routine
    def drawRectangle(self,location,color):
                draw.rectangle((location),(color))

    # Draw image at location at x,y
    def drawImage(self,image,x,y):
        try:
            img = Image.open(image)
            img = img.resize((tft.width,tft.height))
            tft.display(img)
        except Exception as e:
            print("drawImage",str(e))

    # Dummy set width
    def setWidth(self,width):
        return self.width

    # This device does not have color backgrounds
    def hasColor(self):
        return False

    # Draw text location at x,y (in Pixels)
    def drawText(self,text,x,y,font):
        draw.text((x,y), text, font=font)

    # Draw the Splash screen
    def drawSplash(self,image,delay):
        self.drawImage(image,0,0)
        time.sleep(delay)

    # Clear screen
    def clear(self):
        self.drawRectangle((0, 0, 240, 240), bgcolor)
        tft.display(canvas)

    # Set the size of font
    def setFontSize(self,font_size):
        global font
        font = ImageFont.truetype("DejaVuSansMono.ttf", font_size)

    # Radio interface calls from radiod
    def out(self,line,text,interrupt):
        if line > 6:
            line = 6    

        if line == 2:
            font = self.L2_font
        else:
            font = self.default_font

        if text != self.TextLines[line-1]: 
            if line == 2:
                newSize = L2_fontSize
                font = ImageFont.truetype("DejaVuSansMono.ttf", L2_fontSize)
                size = font.getlength(text)
                fwidth = size
                reduce = 1
                while size > self.width:
                    newSize -= reduce
                    if newSize < 25:
                        break
                    font = ImageFont.truetype("DejaVuSansMono.ttf", 
                        newSize)
                    size = font.getlength(text)
                self.L2_font = font

        size = font.getlength(text)
        if size > self.width:
                self._scroll(line,text,font,interrupt)
        else:
                self._out(line,text,font)

        self.TextLines[line-1] = text
        return

    # Write text to line using line number
    def _out(self,line,text,font):  
        if line > 0 and line <= 6:
            self._clearLine(line,font)
            linepos = Lines[line-1]
            self.drawText(text,0,linepos,font)

    # Scroll line - interrupt() breaks out routine if True
    def _scroll(self,line,text,font,interrupt):
        ilen = len(text)
        skip = False

        # Display only for the width  of the LCD
        self._out(line,text,font)
        self.update()

        # Small delay before scrolling
        for i in range(0, 20):
            time.sleep(self.scroll_speed)
            if interrupt():
                return

        # Now scroll the message
        for i in range(0, ilen):
            self._out(line,text[i:],font)
            self.update()
    
            fsize = font.getlength(text[i:])
            if fsize <  self.width:
                break

            if interrupt():
                return
            else:
                time.sleep(self.scroll_speed)

        # Small delay before exiting
        for i in range(0, 10):
            time.sleep(self.scroll_speed)
            if interrupt():
                return        
        return

    # Clear line using background colour
    def _clearLine(self,line,font):
        linepos = Lines[line-1]

        if line == 2:
            size = self.L2_large_font.size
        else:
            size = font.getlength("ABC")
        height = tft.height/6 - 6
        x1 = 0
        y1 = linepos
        x2 = self.width
        y2 = linepos + height + height/5
        self.drawRectangle((x1,y1,x2,y2), bgcolor)
        return

    # Display volume bar on line 6
    def volume(self,vol):
        border = 2
        border2 = 3
        vwidth = self.width - border * 2
        vheight = 25
        
        x1 = border
        y1 = self.height-border-vheight
        x2 = self.width 
        y2 = x2
        draw.rectangle((x1, y1, x2, y2), (255, 255, 255))
        x1 += border2
        y1 += border2
        x2 -= border2
        y2 = x2
        draw.rectangle((x1, y1, x2, y2), (0, 0, 0))

        # Draw the volume level
        range = (self.width - (border + border2) * 2) * vol/100
        x2 = x1 + range
        draw.rectangle((x1, y1, x2, y2), (100, 0, 255))
        self.update()

    # Get number of lines for this OLED
    def getLines(self):
        return self.nlines

    # Get character width for this OLED
    def getChars(self):
        return self.nchars

if __name__ == '__main__':
    import os
    from log_class import Log
    from time import strftime
    from button_class import Button

    display = None
    mesg = "Press a button!"
    event = False
    incVolume = True

    dateformat = "%H:%M %d/%m/%Y"
    log = Log()
    log.init("radio")
    UP=1
    volume = 50

    # Signal SIGTERM handler
    def signalHandler(signal,frame):
        execCommand("sudo systemctl stop mpd.socket")
        display.clear()
        sys.exit(0)

    # Interrupt routine
    def interrupt():
        global event
        event1 = event
        event = False
        return event1
        
    # Execute system command
    def execCommand(cmd):
            p = os.popen(cmd)
            return  p.readline().rstrip('\n')

    def buttonEvent(gpio):
        global volume,incVolume,mesg,event
        button = ''
        if gpio == 5:
            button = "A Channel down"
            incVolume = False
        elif gpio == 6:
            button = "B Volume down"
            volume = volume - 10
            incVolume = False
        elif gpio == 16:
            button = "X Channel up"
        elif gpio == 24:
            button = "Y Volume up"
            volume = volume + 10
        else:
            button = "?"
        event = True
        mesg = button + ' ' + str(gpio)

        if volume > 100:
            volume = 100
        elif volume < 0:
            volume = 0
        print("Button event",gpio,"Button",button,volume)

    # Define the buttons
    def setupButtons():
        Button(5, buttonEvent, log, pull_up_down=UP)
        Button(6, buttonEvent, log, pull_up_down=UP)
        Button(16, buttonEvent, log, pull_up_down=UP)
        Button(24, buttonEvent, log, pull_up_down=UP)
    
    # Main code
    signal.signal(signal.SIGTERM,signalHandler)
    signal.signal(signal.SIGHUP,signalHandler)

    setupButtons()
    display = ST7789()

    # Set flip=True to flip display vertically
    display.init(callback=None,flip=True)
    dir = os.path.dirname(__file__)
    display.drawSplash(dir + "/images/raspberrypi.png",2)
    display.update
    display.drawSplash(dir + "/images/spotify.png",2)


    display.clear()
    while True:
        try:

            # Increment volume bar until volume up/down pressed 
            if incVolume:
                volume += 10
                if volume > 100:
                    volume = 0

            display.volume(volume)

            sDate = strftime(dateformat)
            display.out(1,sDate,interrupt)
            
            text = "TFT display test"
            display.out(3,text,interrupt)

            text = "   PID " + str(os.getpid())
            display.out(4,text,interrupt)

            text = mesg
            display.setFontSize(20)
            display.out(5,text,interrupt)

            text = "abcdefghijklmnopqrstuvwxyz 0123456789"
            display.out(2,text,interrupt)

            display.update()
            time.sleep(0.3)

        except KeyboardInterrupt:
            display.clear()
            text = "  Goodbye"
            display.setFontSize(35)
            display.out(5,text,None)
            display.update()
            sys.exit(0)

# End of test routine

# :set tabstop=4 shiftwidth=4 expandtab
# :retab

