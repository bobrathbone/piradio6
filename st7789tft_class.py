#!/usr/bin/env python3
# This class drives the Sitronix ST7789 controller and 240x240 pixel TFT
#
# $Id: st7789tft_class.py,v 1.10 2023/07/06 11:11:37 bob Exp $
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

import sys,time
import signal
from PIL import Image, ImageDraw, ImageFont
import ST7789 as ST7789
import pdb

# Create ST7789 LCD display class.
tft = ST7789.ST7789(
    port=0,
    rotation=90,
    cs=ST7789.BG_SPI_CS_FRONT,  # BG_SPI_CSB_BACK or BG_SPI_CS_FRONT
    dc=9,
    backlight=13,               
    spi_speed_hz=80 * 1000 * 1000
)

# Flip display vertically set rotation=270
tft_flip = ST7789.ST7789(
    port=0,
    rotation=270,
    cs=ST7789.BG_SPI_CS_FRONT,  # BG_SPI_CSB_BACK or BG_SPI_CS_FRONT
    dc=9,
    backlight=13,               
    spi_speed_hz=80 * 1000 * 1000
)

# See fc-list command for available fonts

WIDTH = tft.width
HEIGHT = tft.height
size = (WIDTH,HEIGHT)
bgcolor = (0, 0, 150)

# Define a canvas to draw on
canvas = Image.new("RGB", (size), bgcolor)
draw = ImageDraw.Draw(canvas)

# Line addresses
#        1 2  3  4   5   6  
Lines = [0,40,90,130,165,195]
default_fontSize = 25
L2_fontSize = 35

## ST7789 TFT display class
class ST7789:
    scroll_speed = 0.01
    #        1  2  3  4  5  6
    TextLines = ['','','','','','']

    # Define display characteristics
    nlines = 7
    nchars = 16 # Character width can vary

    # Line 2 is different from the others and uses a larger font
    default_font = ImageFont.truetype("DejaVuSansMono.ttf", default_fontSize)
    L2_font = ImageFont.truetype("DejaVuSansMono.ttf",L2_fontSize)
    L2_large_font = ImageFont.truetype("DejaVuSansMono.ttf",L2_fontSize)

    def __init__(self):
        return

    # Initialisation routes
    def init(self,callback,flip=False):
        global tft,tft_flip
        self.callback = callback

        # Flip display if required
        if flip:
            tft = tft_flip   
        tft.begin()

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
            img = img.resize((WIDTH, HEIGHT))

            #img = img.resize(float(80),float(80))
            # img = img.thumbnail(80,80)    # Gives __getitem__ error
            #img.show() # X-Windows  and imagemagick package required
            #img = img.thumbnail((80,80), img.ANTIALIAS) # Gves error
            tft.display(img)
        except Exception as e:
            print("drawImage",str(e))

    # Dummy set width
    def setWidth(self,width):
        return WIDTH

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
                size = font.getsize(text)
                fwidth = size[0]
                reduce = 1
                while size[0] > WIDTH:
                    newSize -= reduce
                    if newSize < 25:
                        break
                    font = ImageFont.truetype("DejaVuSansMono.ttf", 
                        newSize)
                    size = font.getsize(text)
                self.L2_font = font
            self.TextLines[line-1] = text

        size = font.getsize(text)
        if size[0] > WIDTH:
                self._scroll(line,text,font,interrupt)
        else:
                self._out(line,text,font)
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
        if not skip:
            for i in range(0, 10):
                time.sleep(0.1)
                if interrupt():
                    skip = True
                    break

        # Now scroll the message
        if not skip:
            for i in range(0, ilen):
                self._out(line,text[i:],font)
                self.update()
        
                fsize = font.getsize(text[i:])
                if fsize[0] <  WIDTH:
                    break

                if interrupt():
                    skip = True
                    break
                else:
                    time.sleep(self.scroll_speed)

        # Small delay before exiting
        if not skip:
            for i in range(0, 10):
                time.sleep(0.1)
                if interrupt():
                        break
        return

    # Clear line using background colour
    def _clearLine(self,line,font):
        linepos = Lines[line-1]

        if line == 2:
            size = self.L2_large_font.getsize("ABC")
        else:
            size = font.getsize("ABC")

        height =  size[1] 
        x1 = 0
        y1 = linepos
        x2 = WIDTH
        y2 = linepos + height + height/5
        self.drawRectangle((x1,y1,x2,y2), bgcolor)
        return

    def volume(self,vol):
        border = 2
        border2 = 3
        vwidth = WIDTH - border * 2
        vheight = 25
        
        x1 = border
        y1 = HEIGHT-border-vheight
        x2 = WIDTH 
        y2 = x2
        draw.rectangle((x1, y1, x2, y2), (255, 255, 255))
        x1 += border2
        y1 += border2
        x2 -= border2
        y2 = x2
        draw.rectangle((x1, y1, x2, y2), (0, 0, 0))

        # Draw the volume level
        range = (WIDTH - (border + border2) * 2) * vol/100
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

    dateformat = "%H:%M %d/%m/%Y"
    log = None
    if len(log.getName()) < 1:
        log.init("radio")
    UP=1
    log = Log()
    eventStr = "No event"
    volume = 90

    # Signal SIGTERM handler
    def signalHandler(signal,frame):
        execCommand("sudo systemctl stop mpd.socket")
        display.clear()
        sys.exit(0)

    # Interrupt routine
    def interrupt():
        return False
        
    # Execute system command
    def execCommand(cmd):
            p = os.popen(cmd)
            return  p.readline().rstrip('\n')

    def buttonEvent(gpio):
        global eventStr,volume
        volChange = False
        adjust = 0  
        button = ''
        if gpio == 5:
            button = "A"
            execCommand("mpc prev")
        elif gpio == 6:
            button = "B"
            adjust = -5
            volChange = True
        elif gpio == 16:
            button = "X"
            execCommand("mpc next")
        elif gpio == 24:
            button = "Y"
            adjust = 5
            volChange = True
        else:
            button = "?"
        eventStr = "Button " + button + " pressed"
        volume += adjust
        if volume > 100:
            volume = 100
        elif volume < 0:
            volume = 0

        if volChange:
            execCommand("mpc volume " + str(volume))
        
        
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
    display.init(callback=None,flip=False)
    dir = os.path.dirname(__file__)
    display.drawSplash(dir + "/images/raspberrypi.png",2)
    display.update
    display.drawSplash(dir + "/images/spotify.png",2)


    display.clear()
    while True:
        try:
            #display.drawRectangle((0, 0, 240, 240), (0, 30, 0))
            volume += 10
            if volume > 100:
                volume = 0

            display.volume(volume)

            sDate = strftime(dateformat)
            display.out(1,sDate,interrupt)
            
            #display.setFontSize(25)
            text = "abcdefghijklmnopqrstuvwxyz 0123456789"
            display.out(2,text,interrupt)

            text = "TFT display test"
            display.out(3,text,interrupt)

            text = "   PID " + str(os.getpid())
            display.out(4,text,interrupt)

            text = "www.bobrathbone.com"
            display.setFontSize(20)
            display.out(5,text,interrupt)

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

