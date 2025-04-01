#!/usr/bin/env python3
# -*- coding: latin-1 -*-
#
# $Id: lcd_class_gpiozero.py,v 1.3 2025/02/15 10:53:23 bob Exp $
# Raspberry Pi display routines
# using an HD44780 or MC0100 LCD or OLED character display
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# From original LCD routines : Matt Hawkins
# Site   : http://www.raspberrypi-spy.co.uk
# Timing improvements from Robert Coward/Paul Carpenter
# Site   : http://www.raspberrypi-spy.co.uk
#     http://www.pcserviceslectronics.co.uk
#
# Amended 15 February 2025 by Bob Rathbone to use gpiozero calls 
# instead of legacy RPi.GPIO calls
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.
#

import os,sys,pdb
import time,pwd
from gpiozero import OutputDevice
from config_class import Configuration

# The wiring for the LCD is as follows:
# 1 : GND
# 2 : 5V
# 3 : Contrast (0-5V)*
# 4 : RS (Register Select)
# 5 : R/W (Read Write)       - GROUND THIS PIN
# 6 : Enable or Strobe
# 7 : Data Bit 0         - NOT USED
# 8 : Data Bit 1         - NOT USED
# 9 : Data Bit 2         - NOT USED
# 10: Data Bit 3         - NOT USED
# 11: Data Bit 4
# 12: Data Bit 5
# 13: Data Bit 6
# 14: Data Bit 7
# 15: LCD Backlight +5V**
# 16: LCD Backlight GND

# Define LCD device constants
LCD_WIDTH = 20    # Default characters per line
LCD_CHR = True
LCD_CMD = False

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line
LCD_LINE_3 = 0x94 # LCD RAM address for the 3rd line
LCD_LINE_4 = 0xD4 # LCD RAM address for the 4th line
# Some LCDs use different addresses (16 x 4 line LCDs)
LCD_LINE_3a = 0x90 # LCD RAM address for the 3rd line (16x4 char display)
LCD_LINE_4a = 0xD0 # LCD RAM address for the 4th line (16x4 char display)

# Timing constants
E_PULSE = 0.0005    # Pulse width of enable (Was 0.0005)
E_DELAY = 0.0005    # Delay between writes
E_POSTCLEAR = 0.3   # Delay after clearing display

# Define GPIO to LCD mapping
gpios = {
        'lcd_select':0,
        'lcd_enable':0,
        'lcd_data4':0,
        'lcd_data5':0,
        'lcd_data6':0,
        'lcd_data7':0
}

LCD_D4_21 = 21    # Rev 1 Board
LCD_D4_27 = 27    # Rev 2 Board

config = Configuration()

# No interrupt routine if none supplied
def no_interrupt():
    return False

# Lcd Class 
class Lcd:

    # The gpios dict is only used during the init stage to check that
    # all gpios have been set to a non-zero value otherwise access
    # to the routines is blocked
    gpios['lcd_select'] = 7
    gpios['lcd_enable']  = 8
    gpios['lcd_data4'] = LCD_D4_27
    gpios['lcd_data5'] = 22
    gpios['lcd_data6'] = 23
    gpios['lcd_data7'] = 24

    lcd_line1 = LCD_LINE_1
    lcd_line2 = LCD_LINE_2
    lcd_line3 = LCD_LINE_3
    lcd_line4 = LCD_LINE_4

    active_scroll_line = 0

    width = LCD_WIDTH
    # If display can support umlauts set to True else False
    scroll_speed = 0.35   # Default scroll speed

    def __init__(self):
        return

    # Initialise for either revision 1 or 2 boards
    def init(self,revision=2,code_page=1):
        self.code_page = code_page

        if revision == 1:
            self.lcd_data4 = LCD_D4_21  #REMOVE
            gpios['lcd_data4'] = LCD_D4_21

        # Get LCD configuration connects including self.lcd_data4
        gpios['lcd_select'] = config.getLcdGpio("lcd_select")
        gpios['lcd_enable']  = config.getLcdGpio("lcd_enable")

        if revision != 1:
            gpios['lcd_data4'] = config.getLcdGpio("lcd_data4")

        gpios['lcd_data5'] = config.getLcdGpio("lcd_data5")
        gpios['lcd_data6'] = config.getLcdGpio("lcd_data6")
        gpios['lcd_data7'] = config.getLcdGpio("lcd_data7")

        # Check that every LCD pin has been assigned a non-zero value
        self.lcd_configured = True 
        for key in gpios.keys():
            gpio = gpios[key]
            gpios[key] = gpio
            if gpio < 1:
                # Block 
                self.lcd_configured = False 
                print("GPIO %s invalid value %d, must be non-zero" % (key,gpio))

        if not self.lcd_configured:
            print("Check value(s) in /etc/radiod.conf configuration file")

        # Assign checked values to GPIO outputs
        self.lcd_enable = gpios['lcd_enable']
        self.lcd_select = gpios['lcd_select']
        self.lcd_data4 = gpios['lcd_data4']
        self.lcd_data5 = gpios['lcd_data5']
        self.lcd_data6 = gpios['lcd_data6']
        self.lcd_data7 = gpios['lcd_data7']

        if self.lcd_configured: 
            # Configure GPIO pins as output
            self.enablePin = OutputDevice(self.lcd_enable)
            self.selectPin = OutputDevice(self.lcd_select)
            self.data4Pin = OutputDevice(self.lcd_data4)
            self.data5Pin = OutputDevice(self.lcd_data5)
            self.data6Pin = OutputDevice(self.lcd_data6)
            self.data7Pin = OutputDevice(self.lcd_data7)

            self.lcd_init()

        return

    # Initialise the display

    def lcd_init(self):

        # Set up font table selection 0x0, 0x1 or 0x2
        data_len = 0x28         # 101000 Data length, number of lines, font table
        select_font = self.code_page | data_len        # Add font table selection

        self._byte_out(0x33,LCD_CMD) # 110011 Initialise 
        self._byte_out(0x32,LCD_CMD) # 110010 Initialise
        self._byte_out(0x06,LCD_CMD) # 000110 Cursor move direction
        self._byte_out(0x14,LCD_CMD) # shift cursor position to right

        # Write registers
        self._byte_out(0x08, LCD_CMD) # 001000 reset display
        self._byte_out(0x17,LCD_CMD) # character mode, power on
        self._byte_out(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
    
        # Set up code page selection
        self._byte_out(select_font,LCD_CMD) # 101000 Data length,number of lines,font table
        self.clear()
        return
     
    # Output byte to LCD  mode = Command or Data
    def _byte_out(self,bits, mode):
        # Send byte to data pins
        # bits = data
        # mode = True  for character
        #   False for command

        self.data4Pin.off()
        self.data5Pin.off()
        self.data6Pin.off()
        self.data7Pin.off()

        if mode:
            self.selectPin.on()
        else:
            self.selectPin.off()

        if bits&0x10==0x10:
            self.data4Pin.on()
        if bits&0x20==0x20:
            self.data5Pin.on()
        if bits&0x40==0x40:
            self.data6Pin.on()
        if bits&0x80==0x80:
            self.data7Pin.on()

        # Toggle 'Enable' pin
        time.sleep(E_DELAY)
        self.enablePin.on()
        time.sleep(E_PULSE)
        self.enablePin.off()
        time.sleep(E_DELAY)

        # Low bits
        self.data4Pin.off()
        self.data5Pin.off()
        self.data6Pin.off()
        self.data7Pin.off()

        if bits&0x01==0x01:
           self.data4Pin.on()
        if bits&0x02==0x02:
           self.data5Pin.on()
        if bits&0x04==0x04:
           self.data6Pin.on()
        if bits&0x08==0x08:
           self.data7Pin.on()

        # Toggle 'Enable' pin
        time.sleep(E_DELAY)
        self.enablePin.on()
        time.sleep(E_PULSE)
        self.enablePin.off()
        time.sleep(E_DELAY)
        return

    # Set the display width
    def setWidth(self,width):
        self.width = width
        # Adjust line offsets if 16 char display
        if width == 16:
            self.lcd_line3 = LCD_LINE_3a
            self.lcd_line4 = LCD_LINE_4a
        return

    # Get LCD width 
    def getWidth(self):
        return config.display_width

    # Display Line on LCD
    def out(self,line_number=1,text="",interrupt=no_interrupt):
        if not self.lcd_configured:
            return
        if line_number == 1:
            line_address = self.lcd_line1
        elif line_number == 2:
            line_address = self.lcd_line2
        elif line_number == 3:
            line_address = self.lcd_line3
        elif line_number == 4:
            line_address = self.lcd_line4 

        self._byte_out(line_address, LCD_CMD)

        if len(text) > self.width:
            self._scroll(line_address,text,interrupt)
        else:
            self._string(text,interrupt)
        return

    # Send string to display
    def _string(self,text,interrupt):
        s = text.ljust(self.width," ")
        for i in range(self.width):
            self._byte_out(ord(s[i]),LCD_CHR)

        # Call interrupt routine
        interrupt()
        return


    # Scroll line - interrupt() breaks out routine if True
    def _scroll(self,line,text,interrupt):
        ilen = len(text)
        skip = False

        # Display only for the width  of the LCD
        self._byte_out(line, LCD_CMD)
        self._string(text[0:self.width + 1], no_interrupt)
    
        # Small delay before scrolling
        if not skip:
            for i in range(0, 10):
                time.sleep(0.2)
                if interrupt():
                    skip = True
                    break

        # Now scroll the message
        if not skip:
            for i in range(0, ilen - self.width + 1 ):
                self._byte_out(line, LCD_CMD)
                self._string(text[i:i+self.width], interrupt)
                if interrupt():
                    skip = True
                    break
                else:
                    time.sleep(self.scroll_speed) 

        # Small delay before exiting
        if not skip:
            for i in range(0, 10):
                time.sleep(0.2)
                if interrupt():
                    break
        return

    # Set Scroll line speed - Best values are 0.2 and 0.3
    # Limit to between 0.05 and 0.9. 0=use default
    def setScrollSpeed(self,speed):
        if speed == float(0):
            speed = self.scroll_speed
        if speed < 0.05:
            speed = 0.05
        elif speed > 0.9:
            speed = 0.9
        self.scroll_speed = speed
        return self.scroll_speed

    # Clear display
    def clear(self):
        if self.lcd_configured:
            self._byte_out(0x01,LCD_CMD) # 000001 Clear display
            time.sleep(E_POSTCLEAR)
        return

    # Does this screen support color
    def hasColor(self):
        return False

# End of Lcd class

# No interrupt routine used as default
def no_interrupt():
    return False

# Class test routine
if __name__ == "__main__":
    test_Russian = False
    from translate_class import Translate
    translate = Translate() # Test routine in __main__

    try:
        print("Test lcd_class.py")

        # Code page. 0=Use primary font code page
        # 1 to 3 override primary font codepage. gives 0x0 to 0x2 
        page = 3    # MC0100 Russian

        lcd = Lcd()
        if test_Russian:
            lcd.init(code_page=page)
        else:
            lcd.init()

        # Print pin assignments
        print("lcd_enable",lcd.lcd_enable)
        print("lcd_select",lcd.lcd_select)
        print("lcd_data4",lcd.lcd_data4)
        print("lcd_data5",lcd.lcd_data5)
        print("lcd_data6",lcd.lcd_data6)
        print("lcd_data7",lcd.lcd_data7)

        lcd.clear()

        lcd.out(1,"bobrathbone.com")

        if test_Russian:
            text2 = "Радио Пятница" # Radio Pyatnica
            text2 = "Белоруссией и Украиной"
            text3 = "Россия - самая"
            text3 = "На юге Россия"
            text4 = "большая страна в мире"
            text4 = "Она охватывает часть" 
            text4 = "охватывает часть" 
            text4 = "Перекрёстки"
            print(text2)
            print(text3)
            print(text4)
            translate.setTranslate(True)
            translate.setRomanize(True)
            text2 = translate.all(text2)
            text3 = translate.all(text3)
            text4 = translate.all(text4)
        else:
            text2 = "Line 2 123456789"
            text3 = "Line 3 123456789"
            text4 = "Line 4 123456789"
            #text2 = "äöüßÄÖÜ"  # Test German umlauts

        lcd.out(2,text2)
        lcd.out(3,text3)
        lcd.out(4,text4)
        time.sleep(2)
        lcd.out(4,"Scroll 4 ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789", no_interrupt)
        time.sleep(2)
        lcd.out(4,"End of test")
        sys.exit(0)

    except KeyboardInterrupt:
        print("\nExit")
        # XXXX GPIO.cleanup()
        sys.exit(0)
# End of test routine
# :set tabstop=4 shiftwidth=4 expandtab
# :retab
