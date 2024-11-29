#!/usr/bin/env python3
#
# $Id: lcd_i2c_jhd1313_sgm31323.py,v 1.8 2024/11/25 10:17:29 bob Exp $
#
# Driver class for the Grove JHD1313 I2C LCD RGB display, version 5
# This introduced the SGM31323 backlight driver and altered the I2C addresses
#
# Adapted from Grove Industries LCD RGB code
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
# Originally adapted from code at http://www.dexterindustries.com/GrovePi
#
# Converted from lcd_i2c_jhd1313 by Dave Jesse (UK) to support Grove V5 LCD
# using the SGM31323 controller chip for RGB backlight control 
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
# The authors shall not be liable for any loss or damage however caused.
#
# Original Dexter Industries Licences
# Released under the MIT license (http://choosealicense.com/licenses/mit/).
# For more information see https://github.com/DexterInd/GrovePi/blob/master/LICENSE
#

import smbus
import time,sys
import pdb
import RPi.GPIO as GPIO                       
from config_class import Configuration

rev = GPIO.RPI_REVISION
if rev == 2 or rev == 3:
    bus = smbus.SMBus(1)
else:
    bus = smbus.SMBus(0)

# No interrupt routine if none supplied
def no_interrupt():
    return False

# Grove display V5.0 has JHD1313 controller for the LCD
# and SGM31323 controller for the RGB backlight (change from V4.0)
DISPLAY_RGB_ADDR = 0x30
DISPLAY_TEXT_ADDR = 0x3e

# Device commands. See JHD1313 FP/RGB-1 1.4 specification 
LCD_CLEAR = 0x01
LCD_CURSOR_RESET = 0x02
LCD_NO_CURSOR = 0x04
LCD_DISPLAY_ON = 0x08
LCD_TWO_LINE_MODE = 0x28

config = Configuration()

class Lcd_i2c_jhd1313_sgm31323:

    scroll_speed = 0.1
    lines = 2   # LCD number of lines
    width = 16  # LCD number of characters

    lines = ["",""]  # Text lines 

    # __init__
    def __init__(self):
        return

    # Initialisation routine
    def init(self,i2c_address=DISPLAY_TEXT_ADDR,code_page=0,
            i2c_rgb_address=DISPLAY_RGB_ADDR):
        self.code_page = code_page  # Future use. LCD only has one codepage
        self.i2c_address = i2c_address
        self.i2c_rgb_address = i2c_rgb_address
        #print("i2c_address",hex(self.i2c_address))
        #print("i2c_rgb_address",hex(self.i2c_rgb_address))
        self.backlight((0,128,64))
        self.clear()

    def out(self,line=1,text="",interrupt=no_interrupt):
        if line == 1 or line == 2:
            if len(text) > self.width:
                self._scroll(line,text,interrupt)
            else:
                self._writeLines(line,text)

    # Write 2 lines to the LCD
    def _writeLines(self,line,text):
        if self.lines[line-1] != text:
            self.lines[line-1] = text[:16].ljust(16)
            text_out = self.lines[0] + "\n" + self.lines[1]
            self._out(text_out)

    # Set backlight to (R,G,B) (values from 0..255 for each)
    def backlight(self,color):
        r = color[0]
        g = color[1]
        b = color[2]
        self.setRGB(r,g,b)

    def setRGB(self,r,g,b):
        # I2C control for SGM31323
        # Register 0 set to keep display always ON
        bus.write_byte_data(self.i2c_rgb_address, 0x00, 0x18)
        # Register 4 set to keep each colour always ON
        bus.write_byte_data(self.i2c_rgb_address, 0x04, 0x15)
        bus.write_byte_data(self.i2c_rgb_address, 0x06, r)
        bus.write_byte_data(self.i2c_rgb_address, 0x07, g)
        bus.write_byte_data(self.i2c_rgb_address, 0x08, b)

    # Set display text \n for second line(or auto wrap)
    def _out(self,text,interrupt=None):
        self._textCommand(LCD_CURSOR_RESET) # Reposition cursor to start
        self._textCommand(LCD_DISPLAY_ON | LCD_NO_CURSOR) # display on, no cursor
        self._textCommand(LCD_TWO_LINE_MODE) # 2 lines
        time.sleep(.05)
        count = 0
        row = 0
        for c in text:
            if c == '\n' or count == self.width:
                count = 0
                row += 1
                if row == 2:
                    break
                self._textCommand(0xc0)
                if c == '\n':
                    continue
            count += 1
            bus.write_byte_data(DISPLAY_TEXT_ADDR,0x40,ord(c))
        if interrupt != None:
            interrupt()

    # Scroll line - interrupt() breaks out routine if True
    def _scroll(self,line,text,interrupt):
        ilen = len(text)
        skip = False

        # Display only for the width  of the LCD
        self._writeLines(line,text[:self.width])

        # Small delay before scrolling
        if not skip:
            for i in range(0, 10):
                time.sleep(self.scroll_speed)
                if interrupt():
                    skip = True
                    break

        # Now scroll the message
        if not skip:
            for i in range(0, ilen - self.width + 1 ):
                self._writeLines(line,text[i:i+self.width])
                if interrupt():
                    skip = True
                    break
                else:
                    time.sleep(self.scroll_speed)

        # Small delay before exiting
        if not skip:
            for i in range(0, 10):
                time.sleep(self.scroll_speed)
                if interrupt():
                    break

    # Send command to display (no need for external use)
    # See JHD1313 FP-RGB-1 1.4 10. Instruction set
    def _textCommand(self,cmd):
        bus.write_byte_data(DISPLAY_TEXT_ADDR,0x80,cmd)

    # Clear display
    def clear(self):
        self._textCommand(LCD_CLEAR) # clear display

    # Does this LCD support color backlight
    def hasColor(self):
        return True

    # Get LCD width
    def getWidth(self):
        return config.display_width

    # Set the display width (Do not set as it is fixed)
    def setWidth(self,width):
        return 

    # Set Scroll line speed - Best values are 0.05 and 0.1
    # Limit to between 0.03 and 0.1 
    def setScrollSpeed(self,speed):
        if speed < 0.001:
            speed = 0.001
        elif speed > 0.6:
            speed = 0.6
        self.scroll_speed = speed
        return self.scroll_speed

# End of class

# No interrupt routine used as default
def no_interrupt():
    return False

# Class test routine
if __name__ == "__main__":

    from time import strftime
    dateformat = "%H:%M %d/%m/%Y"

    try:
        print("Test I2C Grove V5.0 JHD1313L with SGM31323 backlight class")
        lcd = Lcd_i2c_jhd1313_sgm31323()
        lcd.init(i2c_address=DISPLAY_TEXT_ADDR)
        lcd.clear()
        lcd.backlight((255,255,255))
        lcd.out(1,"bobrathbone.com")
        lcd.out(2,"Line 2 123456789")
        time.sleep(3)
        lcd.backlight((64,0,0))
        lcd.out(2,"ABCDEFG")
        time.sleep(3)
        for colour, text in [((20,0,0), "Dull Red"),
                             ((255,0,0), "BRIGHT RED"),
                             ((0,20,0),"Dull Green"),
                             ((0,255,0), "BRIGHT GREEN"),
                             ((0,0,20), "Dull Blue"),
                             ((0,0,255),"BRIGHT BLUE"),
                             ]:
            lcd.backlight(colour)
            lcd.out(1, text)
            time.sleep(3)
        
        while True:
            lcd.backlight((0,128,64))
            sDate = strftime(dateformat)
            lcd.out(1,sDate)
            lcd.out(2,"ABCDEFGHIJKLMNOPQRSTUVWXYZ",no_interrupt)
            time.sleep(0.2)
        sys.exit(0)

    except KeyboardInterrupt:
        print("\nExit")
        sys.exit(0)

# End of test routine

# :set tabstop=4 shiftwidth=4 expandtab
# :retab

