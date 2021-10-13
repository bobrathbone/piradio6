#!/usr/bin/env python3
#
# LCD test program for the lcd_i2c_class.py class
# $Id: lcd_i2c_adafruit.py,v 1.6 2021/09/30 08:03:28 bob Exp $
#
# I2C Adafruit I2C backback driver
# Adapted from RpiLcdBackpack from Paul Knox-Kennedy
# at Adafruit Industries
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
# The authors shall not be liable for any loss or damage however caused.
#
# This version use3s smbus2 from Karl-Petter Lindegaard (MIT)

import time
import pwd,os,sys
from smbus2 import SMBus

from subprocess import * 
from time import sleep, strftime
from datetime import datetime
from config_class import Configuration

config = Configuration()

# No interrupt routine if none supplied
def no_interrupt():
    return False

# I2C LCD class
class Lcd_i2c_Adafruit:
    # commands
    __CLEARDISPLAY=0x01
    __RETURNHOME=0x02
    __ENTRYMODESET=0x04
    __DISPLAYCONTROL=0x08
    __CURSORSHIFT=0x10
    __FUNCTIONSET=0x20
    __SETCGRAMADDR=0x40
    __SETDDRAMADDR=0x80

    # flags for display entry mode
    __ENTRYRIGHT=0x00
    __ENTRYLEFT=0x02
    __ENTRYSHIFTINCREMENT=0x01
    __ENTRYSHIFTDECREMENT=0x00

    # flags for display on/off control
    __DISPLAYON=0x04
    __DISPLAYOFF=0x00
    __CURSORON=0x02
    __CURSOROFF=0x00
    __BLINKON=0x01
    __BLINKOFF=0x00

    # flags for display/cursor shift
    __DISPLAYMOVE=0x08
    __CURSORMOVE=0x00
    __MOVERIGHT=0x04
    __MOVELEFT=0x00

    # flags for function set
    __8BITMODE=0x10
    __4BITMODE=0x00
    __2LINE=0x08
    __1LINE=0x00
    __5x10DOTS=0x04
    __5x8DOTS=0x00

    _rs=0x02
    _e=0x4
    _dataMask=0x78
    _dataShift=3
    _light=0x80


    # I2C Address
    i2c_address = 0x20

    code_page = 0x0 # Font code page 0x0, 0x1 or 0x2

    # Define LCD device constants
    LCD_WIDTH = 16    # Default characters per line
    LCD_CHR = True
    LCD_CMD = False

    LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
    LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
    LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
    LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line

    # Some LCDs use different addresses (16 x 4 line LCDs)
    LCD_LINE_3a = 0x90 # LCD RAM address for the 3rd line (16 char display)
    LCD_LINE_4a = 0xD0 # LCD RAM address for the 4th line (16 char display)

    lcd_line3 = LCD_LINE_3
    lcd_line4 = LCD_LINE_4

    width = LCD_WIDTH
    scroll_speed = 0.2       # Default scroll speed

    # Write nibble to LCD position 
    def writeFourBits(self,value):
        self.__data &= ~self._dataMask
        self.__data |= value << self._dataShift
        self.__data &= ~self._e 
        self.__bus.write_byte_data(0x20,0x09,self.__data)
        time.sleep(0.000001)
        self.__data |= self._e 
        self.__bus.write_byte_data(0x20,0x09,self.__data)
        time.sleep(0.000001)
        self.__data &= ~self._e 
        self.__bus.write_byte_data(0x20,0x09,self.__data)
        time.sleep(0.000101)

    def writeCommand(self,value):
        self.__data &= ~self._rs
        self.writeFourBits(value>>4)
        self.writeFourBits(value&0xf)

    def writeData(self,value):
        self.__data |= self._rs
        self.writeFourBits(value>>4)
        self.writeFourBits(value&0xf)

    # Initialise
    def __init__(self,code_page=0x0):
        self.code_page = code_page
        self.scroll_speed = config.scroll_speed
        self.setScrollSpeed(self.scroll_speed)
        return

    # Initialisation routine
    def init(self, busnum=1, address=0x20):
        self.i2c_address = address  
        
        self.__bus=SMBus(busnum)
        self.__bus.write_byte_data(0x20,0x00,0x00)
        self.__displayfunction = self.__4BITMODE | self.__2LINE | self.__5x8DOTS
        #self.__displaycontrol = self.__DISPLAYCONTROL | self.__DISPLAYON | self.__CURSORON | self.__BLINKON
        self.__displaycontrol = self.__DISPLAYCONTROL | self.__DISPLAYON 
        self.__data = 0
        self.writeFourBits(0x03)
        time.sleep(0.005)
        self.writeFourBits(0x03)
        time.sleep(0.00015)
        self.writeFourBits(0x03)
        self.writeFourBits(0x02)
        self.writeCommand(self.__FUNCTIONSET | self.__displayfunction)

        self.writeCommand(self.__displaycontrol)
        self.writeCommand(0x6)

        # Set code page (Do last of all)
        self.writeCommand(self.__FUNCTIONSET | self.__DISPLAYCONTROL | self.code_page)
        
        # Clear the display, switch blink off and backlight on
        self.clear()
        self.blink(False)
        self.backlight(True)
        return

    # Display Line on LCD
    def out(self,line_number=1,text="",interrupt=no_interrupt):
        if line_number == 1:
            line_address = self.LCD_LINE_1
        elif line_number == 2:
            line_address = self.LCD_LINE_2
        elif line_number == 3:
            line_address = self.lcd_line3
        elif line_number == 4:
            line_address = self.lcd_line4
        #self._byte_out(line_address, LCD_CMD)

        if len(text) > self.width:
            self._scroll(text,line_address,interrupt)
        else:
            self._writeLine(line_address,text)
        return

    # Write a single line to the LCD
    def _writeLine(self,line,text):
        self.writeCommand(line)
        if len(text) < self.width:
            text = text.ljust(self.width, ' ')
        self.message(text[:self.width])
        return


    # Scroll line - interrupt() breaks out routine if True
    def _scroll(self,mytext,line,interrupt):
        ilen = len(mytext)
        skip = False

        self._writeLine(line,mytext[0:self.width + 1])

        if (ilen <= self.width):
            skip = True

        if not skip:
            for i in range(0, 5):
                time.sleep(0.2)
                if interrupt():
                    skip = True
                    break

        if not skip:
            for i in range(0, ilen - self.width + 1 ):
                self._writeLine(line,mytext[i:i+self.width])
                if interrupt():
                    skip = True
                    break
                time.sleep(self.scroll_speed)

        if not skip:
            for i in range(0, 5):
                time.sleep(0.2)
                if interrupt():
                    break
        return



    # Switch back light on and off
    def backlight(self,on):
        if on:
            self.__data |= 0x80
        else:
            self.__data &= 0x7f
        self.__bus.write_byte_data(0x20,0x09,self.__data)


    # Clear display
    def clear(self):
        self.writeCommand(self.__CLEARDISPLAY)
        time.sleep(0.002)


    # Blink cursor
    def blink(self, on):
        if on:
            self.__displaycontrol |= self.__BLINKON
        else:
            self.__displaycontrol &= ~self.__BLINKON
        self.writeCommand(self.__displaycontrol)

    def noCursor(self):
        self.writeCommand(self.__displaycontrol)

    def cursor(self, on):
        if on:
            self.__displaycontrol |= self.__CURSORON
        else:
            self.__displaycontrol &= ~self.__CURSORON
        self.writeCommand(self.__displaycontrol)

    def message(self, text):
        for char in text:
            if char == '\n':
                self.writeCommand(0xC0)
            else:
                self.writeData(ord(char))

    # Get LCD width 0 = use default for program
    def getWidth(self):
        return config.display_width

    # Set the display width
    def setWidth(self,width):
        self.width = width
        # Adjust line offsets if 16 char display
        if width is 16:
            self.lcd_line3 = self.LCD_LINE_3a
            self.lcd_line4 = self.LCD_LINE_4a

    # Set Scroll line speed - Best values are 0.2 and 0.3
    # Limit to between 0.08 and 0.6
    def setScrollSpeed(self,speed):
        if speed < 0.08:
                speed = 0.08
        elif speed > 0.6:
                speed = 0.6
        self.scroll_speed = speed
        return self.scroll_speed

    # Does this screen support color
    def hasColor(self):
        return False

# End of lcd_i2c_class

# No interrupt routine used as default
def no_interrupt():
    return False

# Class test routine
if __name__ == "__main__":

    i2c_addres = 0x27

    try:
        print("Test I2C Adafruit backpack class")
        lcd = Lcd_i2c_Adafruit()
        lcd.init(address=0x27)
        lcd.out(1,"bobrathbone.com")
        lcd.out(2,"Line 2 123456789")
        lcd.out(3,"Line 3 123456789")
        lcd.out(4,"Line 4 123456789")
        time.sleep(4)
        lcd.out(4,"Scroll 4 ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789", no_interrupt)
        sys.exit(0)

    except KeyboardInterrupt:
        print("\nExit")
        sys.exit(0)

# End of test routine
# :set tabstop=4 shiftwidth=4 expandtab
# :retab

