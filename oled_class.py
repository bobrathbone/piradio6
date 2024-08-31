#!/usr/bin/env python3
# This class drives the Solomon Systech SSD1306 128 by 64 pixel OLED
#
# $Id: oled_class.py,v 1.9 2024/08/16 16:08:08 bob Exp $
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#      The authors shall not be liable for any loss or damage however caused.
#
# Adapted from hello world program from Olimex Limited, www.olimex.com
# See https://github.com/SelfDestroyer/pyMOD-OLED.git
# 

from oled import OLED
from oled import Font
from oled import Graphics
from PIL import Image
import pdb,sys,time
from config_class import Configuration

config = Configuration()

# Line addresses
#        1 2  3  4  5  
Lines = [0,16,32,48,56]

# No interrupt routine if none supplied
def no_interrupt():
    return False

class   Oled:
    dis = None
    f = None # Font
    scale = 1
    width = 20
    lines = 4
    scroll_line = 0
    scroll_speed = 0.1

    def __init__(self,revision=1):
        # Connect to the display on /dev/i2c-1
        self.dis = OLED(revision)
        Graphics.clearLine = self._clearLine
        Font.print_string = _print_string

        # Start communication
        self.dis.begin()

        # Start basic initialization
        self.dis.initialize()

        # Do additional configuration
        self.dis.set_memory_addressing_mode(0)
        self.dis.set_column_address(0, 127)
        # Eight pages
        self.dis.set_page_address(0, 7)
        self.dis.set_scan_direction(0)
        self.dis.set_inverse_display(False) # Black on white
        self.clear()
        self.scroll_speed = config.scroll_speed
        self.setScrollSpeed(self.scroll_speed)
        self.stop_scroll()  # Stop native scrolling

        # Set font scale to 1
        self.f = Font(1)
        return

    # Clear display
    def clear(self):
        self.dis.clear(update=False)

    # Top display routine
    def out(self,line,text,interrupt):
        if len(text) > self.width:
            self._scroll(line,text,interrupt)
        else:
            self._out(line,text)
        return

    # Scroll line - interrupt() breaks out routine if True
    def _scroll(self,line,text,interrupt):
        ilen = len(text)
        skip = False

        # Display only for the width  of the LCD
        self._out(line,text[0:self.width + 1], no_interrupt)
        self.dis.update()

        # Small delay before scrolling
        if not skip:
            for i in range(0, 10):
                time.sleep(0.1)
                if interrupt():
                    skip = True
                    break

        # Now scroll the message
        if not skip:
            for i in range(0, ilen - self.width + 1 ):
                self._out(line,text[i:i+self.width], interrupt)
                self.dis.update()
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

    # Text out
    def _out(self,line_number,text="",interrupt=no_interrupt):
        self.clearLine(line_number)
        nChars = 20 # Default
        if self.scale == 2: 
            nChars = 10 
        line = Lines[line_number-1]

        if self.scroll_line == line_number:
            text = ' ' + text
            nChars = len(text)
        try:
            self.f.print_string(0, line, text[:nChars])
        except Exception as e:
            print(e)
            print("Bad string",text)

    # Update Oled screen
    def update(self):
        self.dis.update()

    def scroll(self,line):
        # Make horizontal scroll
        page = line * 2 - 2
        self.scroll_line = line
        self._scroll(page)

    # Smooth scroll page (Only one at a time)
    def _smooth_scroll(self,page,speed=6):
        self.dis.deactivate_scroll()
        self.dis.vertical_and_horizontal_scroll_setup(self.dis.LEFT_SCROLL,page,page,speed,0)
        #self.dis.horizontal_scroll_setup(self.dis.LEFT_SCROLL, page, page, speed)
        self.dis.activate_scroll()

    # Deactivate smooth scroll
    def stop_scroll(self):
        self.dis.deactivate_scroll()

    def setFontScale(self,scale):
        self.scale = int(scale)
        self.f = Font(self.scale)

    # Draw rectangle
    def drawRectangle(self,x0, y0, x1, y1,fill):
        self._draw_line(x0, y0, x1, y0)  # Top line
        self._draw_line(x0, y1, x1, y1)  # Bottom line
        self._draw_line(x0, y0, x0, y1)  # Left line
        self._draw_line(x1, y0, x1, y1)  # Right line

        if fill:
            for i in range(1, y1-y0):
                self._draw_line(x0, y0+i, x1, y0+i)

    # Draw volume slider (1, 100)
    def drawHorizontalSlider(self,size,lineNumber):
        pos =  ((lineNumber - 1) * 8) + 1
        if size > 100:
            size = 100
        elif size < 0:
            size = 0
        width = int(127*size/100)
        self.clearPage(int(pos/8))
        for x in range(1,6):
            self._clearLine(0, pos+x, 127, pos+x)
            Graphics.draw_line(0, pos+x, width, pos+x)
        self.drawRectangle(0,pos+1,127,pos+6,False)
        self.dis.update()

    # Draw volume slider
    def volume(self,volume): 
        if volume > 100:
            volume = 100
        elif volume < 0:
            volume = 0
        self.drawHorizontalSlider(volume,8)

    # Width and line parameters
    def getWidth(self):
        return self.width

    def getLines(self):
        return self.lines

    def setWidth(self,notused):
        return self.width

    def setLines(self,notused):
        return self.lines

    # Has color 
    def hasColor(self):
        return False

    # Clear line (Line 1 is double size font)
    def clearLine(self,line):
        page = (line-1) * 2
        if page >= 8:   # Last line on page 7
            page = 7
        self.clearPage(page)
        if  line == 1:
            self.clearPage(page + 1)

    # This routine clears a page (0-7)
    def clearPage(self, page):
        x0 = 0
        y0 = page * 8 
        x1 = 127
        y1 = y0
        
        for x in range(0,8):
            Graphics.clearLine(x0, y0+x, x1, y1)
        return

    # Clear line Graphics class override
    def _clearLine(self,x0, y0, x1, y1):
        dx = x1 - x0
        dy = y1 - y0
        D = 2*dy - dx
        Graphics.draw_pixel(x0, y0, on=False)
        y = y0

        for x in range(x0+1, x1+1):
            if D > 0:
                y += 1
                Graphics.draw_pixel(x, y, on=False)
                D += (2*dy - 2*dx)
            else:
                Graphics.draw_pixel(x, y, on=False)
                D += 2*dy
        return

    # Set Scroll line speed - Best values are 0.2 and 0.3
    # Limit to between 0.08 and 0.6
    def setScrollSpeed(self,speed):
        if speed < 0.08:
                speed = 0.08
        elif speed > 0.6:
                speed = 0.6
        self.scroll_speed = speed
        return self.scroll_speed

    # Flip OLED display vertically
    def flip_display_vertically(self,flip):
        # flip is True or False
        if flip:
            self.dis.set_scan_direction(1)
            self.dis.set_segment_remap(remap=True)
        else:
            self.dis.set_scan_direction(0)
            self.dis.set_segment_remap(remap=False)
        return

    # Draw line
    def drawLine(self,x0, y0, x1, y1):
        self._draw_line(x0, y0, x1, y1)

    """
    Alternative line routine using Bresenham's line algorithm.
    The Olimex draw_line routine is not working for vertical lines.
    See https://rosettacode.org/wiki/Bitmap/Bresenham%27s_line_algorithm#Python
    """
    def _draw_line(self, x0, y0, x1, y1):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        sx = -1 if x0 > x1 else 1
        sy = -1 if y0 > y1 else 1
        if dx > dy:
            err = dx / 2.0
            while x != x1:
                #self.set(x, y)
                Graphics.draw_pixel(x, y, True)
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2.0
            while y != y1:
                #self.set(x, y)
                Graphics.draw_pixel(x, y, True)
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy
        #self.set(x, y)
        Graphics.draw_pixel(x, y, True)


    # Draw image location at x,y
    def drawImage(self,bitmap,x,y):
        img = Image.open(bitmap)

        w = img.size[0]
        h = img.size[1]
        try:
            for i in range(0, w):
                for j in range(0, h):
                    xy = (i, j)
                    if img.getpixel(xy):
                        Graphics.draw_pixel(i+x, j+y, False)
                    else:
                        Graphics.draw_pixel(i+x, j+y, True)
        except: pass

    def drawSplash(self,bitmap,delay):
        self.drawImage(bitmap,35,0)
        self.dis.update()
        time.sleep(delay)
        self.clear()
        return

# End of Oled class

# Override Font.print_string
def _print_string(self,x0, y0, text):
    """
    Print string to display.

    :param x0:  Start X position
    :param y0:  Start Y position
    :param string:  String to display
    :return: None
    """
    idx = 0
    x = x0
    y = y0
    
    string = text[idx:20]
    for i in string:
        if x >= OLED.oled_width - (6 * self.scale):
            x = 0
            y += (8 * self.scale)

        if y >= OLED.oled_height:
            return

        self.print_char(x, y, i)
        x += (6 * self.scale)

    # Get character width for this OLED
    def getChars():
        return self.width

# Class test routine
if __name__ == "__main__":
    import time,datetime
    from time import strftime
    #dateformat = "%H:%M %d/%m/%y"
    dateformat = "%H:%M %d%m"
    mesg = "B.Rathbone abcdefghijklmonopqrstuvwxyz 123456789 ABCDE"

    try:
        oled = Oled()
        oled.clear()

        # Change False to True to flip display
        oled.flip_display_vertically(True)

        # Draw splash
        oled.drawSplash("bitmaps/raspberry-pi-logo.bmp",2)

        oled.setFontScale(2)
        sDate = strftime(dateformat)
        oled.out(1,sDate,no_interrupt)
        oled.setFontScale(1)
        oled.out(2,"abcdefghijklmonopqrstuvwxyz",no_interrupt)
        oled.out(3,mesg,no_interrupt)
        oled.out(4,"ABCEFGHIJKLMONOPQRSTUVWXYZz",no_interrupt)
        oled.volume(50)
        oled.update()

    except KeyboardInterrupt:
        print("\nExit")
        sys.exit(0)

def no_interrupt():
    return False

# End of test code
# :set tabstop=4 shiftwidth=4 expandtab
# :retab
