#!/usr/bin/env python3
# -*- coding: latin-1 -*-
#
# $Id: display_class.py,v 1.87 2025/01/15 12:27:36 bob Exp $
# Raspberry Pi display routines
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.
#

import pdb
import os,sys
import time,pwd
from config_class import Configuration
from log_class import Log

config = Configuration()
log = Log()

screen = None

SCREEN_LINES = 2    # Default screen lines
SCREEN_WIDTH = 16   # Default screen width

# No interrupt if not supplied
def no_interrupt():
    return False

# Display Class 
class Display:
    translate = None    # Translate class

    lines = SCREEN_LINES    # Default lines
    width = SCREEN_WIDTH    # Default width
    saved_volume = 0
    saved_font_size = 1
    saved_time = ''         # Prevent unecessary diplay of time

    delay = 0  # Delay (volume) display for n cycles (2 line displays or volume display)

    # The Adafruit RGB plate has buttons otherwis False
    has_buttons = False
    has_screen = True

    # The OLED_128x64, ST7789TFT and SSD1306 OLEDS all display volume as
    # a bar on the bottom line of the screen. True for OLEDs, False for LCDs 
    _isOLED = False
    _mute_line = 4  # Line to display mute message
    _refresh_volume_bar = False  # If previously muted force display of OLED volume slider
    _no_scrolling = False   # Suppress scrolling during volume display update

    i2c_bus = 1 # All later RPIs use bus 1 (old RPIs use bus 0)

    lineBuffer = []     # Line buffer 
    ImageColor = None

    def __init__(self,translate):
        self.translate = translate

    # Initialise 
    def init(self,callback=None,display2_type=0,display2_i2c=0,device_name=""):
        self.callback = callback
        log.init('radio')
        self.setupDisplay(display2_type,display2_i2c,device_name)
    
    # Set up configured screen class
    # If display2_type or display2_i2c are set they override the settings
    # in /etc/radiod.conf to support a two screen system
    def setupDisplay(self,display2_type,display2_i2c,device_name):
        global screen,config
        device_driver = ''

        if display2_type > 0:
            dtype = display2_type
        else:
            dtype = config.getDisplayType()
        i2c_address = 0x0

        if display2_i2c > 0:
            configured_i2c = display2_i2c
        else:
            configured_i2c = config.i2c_address

        self.i2c_bus = config.i2c_bus
        scroll_speed = config.scroll_speed
        self.width = config.display_width

        # Set up font code page. If 0 use codepage in font file
                # If > 1 override with the codepage parameter in configuration file
        code_page = config.codepage # 0, 1 or 2
        log.message("Translation code page in radiod.conf = " + str(code_page),log.INFO)

        if code_page > 0:
                self.code_page = code_page - 1
        else:
                self.code_page = self.translate.getPrimaryCodePage()

        if dtype == config.NO_DISPLAY:
            from no_display import No_Display
            screen = No_Display()
            self.has_screen = False

        elif dtype == config.LCD_I2C_PCF8574:
            from lcd_i2c_pcf8574 import Lcd_i2c_pcf8574
            screen = Lcd_i2c_pcf8574()

            if configured_i2c != 0:
                i2c_address = configured_i2c
            else:
                i2c_address = 0x27

            screen.init(address = i2c_address,busnum=self.i2c_bus,
                    code_page=self.code_page)
            screen.setScrollSpeed(scroll_speed)
            screen.setWidth(self.width)
            i2c_interface = True

        elif dtype == config.LCD_I2C_JHD1313:
            from PIL import ImageColor
            self.ImageColor = ImageColor
            from lcd_i2c_jhd1313 import Lcd_i2c_jhd1313
            screen = Lcd_i2c_jhd1313()

            if configured_i2c != 0:
                i2c_address = configured_i2c
            else:
                i2c_address = 0x3e

            screen.init(address = i2c_address,code_page=self.code_page)
            screen.setScrollSpeed(scroll_speed)
            i2c_interface = True

        elif dtype == config.LCD_I2C_JHD1313_SGM31323:
            from PIL import ImageColor
            self.ImageColor = ImageColor
            from lcd_i2c_jhd1313_sgm31323 import Lcd_i2c_jhd1313_sgm31323
            screen = Lcd_i2c_jhd1313_sgm31323()

            if configured_i2c != 0:
                i2c_address = configured_i2c
            else:
                i2c_address = 0x3e

            screen.init(i2c_address=i2c_address,code_page=self.code_page,
                        i2c_rgb_address=config.i2c_rgb_address)
            screen.setScrollSpeed(scroll_speed)
            i2c_interface = True

        elif dtype == config.LCD_I2C_ADAFRUIT:
            from lcd_i2c_adafruit import Lcd_i2c_Adafruit
            screen = Lcd_i2c_Adafruit(code_page = self.code_page)

            if configured_i2c != 0:
                i2c_address = configured_i2c
            else:
                i2c_address = 0x20

            screen.init(address = i2c_address, busnum=self.i2c_bus)
            screen.setScrollSpeed(scroll_speed)
            i2c_interface = True

        elif dtype == config.LCD_ADAFRUIT_RGB:
            from lcd_adafruit_class import Adafruit_lcd
            screen = Adafruit_lcd()

            if configured_i2c != 0:
                i2c_address = configured_i2c
            else:
                i2c_address = 0x20

            screen.init(address = i2c_address, busnum = self.i2c_bus,
                    callback = self.callback, code_page=self.code_page)

            # This device has its own buttons on the I2C intertface
            self.has_buttons = True
            i2c_interface = True

        elif dtype == config.OLED_128x64:
            from oled_class import Oled
            screen = Oled()
            self.width = 20
            self.lines = 5
            # Set vertical display
            screen.flip_display_vertically(config.flip_display_vertically)
            self._isOLED = True
            self._mute_line = 4

        elif dtype == config.PIFACE_CAD:
            from lcd_piface_class import Lcd_Piface_Cad
            screen = Lcd_Piface_Cad()
            screen.init(callback=self.callback,code_page = code_page)
            # This device has its own buttons on the SPI intertface
            self.has_buttons = True

        elif dtype == config.ST7789TFT:
            from st7789tft_class import ST7789
            screen = ST7789()
            screen.init(callback=self.callback,flip=config.flip_display_vertically)
            self.has_buttons = False # Use standard button ineterface
            self._isOLED = True
            self._mute_line = 5

        elif dtype == config.SSD1306:
            from ssd1306_class import SSD1306
            screen = SSD1306()
            screen.init(callback=self.callback,code_page = code_page)
            self.has_buttons = False # Use standard button interface
            self._isOLED = True
            self._mute_line = 4

        elif dtype == config.SH1106_SPI:
            from sh1106_class import SH1106
            screen = SH1106()
            screen.init(callback=self.callback)
            self.has_buttons = False # Use standard button interface
            self._isOLED = True
            self._mute_line = 4
            screen.setScrollSpeed(scroll_speed)

        elif dtype == config.LUMA:
            from luma_class import LUMA
            screen = LUMA()
            if len(device_name) > 0:
                device_driver = device_name
            else:
                device_driver = config.device_driver
            rotation = 0
            if config.flip_display_vertically:
                rotation = 2
            screen.init(callback=self.callback,code_page=code_page, 
                        device_driver=device_driver,rotation=rotation,
                        font_size=config.font_size,font_name=config.font_name)
            screen.setScrollSpeed(scroll_speed)
            self.has_buttons = False # Use standard button interface
            self._isOLED = True
            self._mute_line = 4

        elif dtype == config.WS_SPI_SSD1309:
            from ws_spi_ssd1309_class import WS_spi_ssd1309
            screen = WS_spi_ssd1309()
            if len(device_name) > 0:
                device_driver = device_name
            else:
                device_driver = config.device_driver
            flip = config.flip_display_vertically
            screen.init(callback=self.callback,flip=flip,device_driver=device_driver)
            self._isOLED = True
            screen.setScrollSpeed(scroll_speed)
            self._mute_line = 5
            screen.drawFrame()  # Specific to this display

        else:
            # Default LCD
            from lcd_class import Lcd
            screen = Lcd()
            screen.init(code_page = self.code_page)
            screen.setScrollSpeed(scroll_speed)
            self._mute_line = config.display_lines

        # Log code files used and codepage
        log.message("Display code page " + str(hex(self.code_page)), log.INFO)

        font_files = self.translate.getFontFiles()
        for i in range (0,len(font_files)):
            log.message("Loaded " + str(font_files[i]), log.INFO)

        # Set up number of lines (if 0 use default from screen driver)
        self.lines = config.display_lines 
        if self.lines <= 0:
            if self._isOLED:
                self.lines = screen.getLines()
            else:
                # If an LCD display_lines = 0 is invalid
                self.lines = 2

        # Set up screen width (if 0 use default from screen driver)
        self.width = config.display_width  
        if self.width <= 0:
            # This may be in characters or pixels
            self.width = screen.getWidth()
            if self._isOLED:
                self.width = self.width // 5   # Estimate only

        sName  = self.getDisplayName()
        d =  ''
        if len(device_driver) > 0:
            d = '.' + device_driver
        msg = 'Screen ' + sName + d  + ' Lines=' + str(self.lines) \
             + ' Character width=' + str(self.width) 

        print(msg)
        log.message(msg, log.INFO)
        
        if i2c_address > 0 and i2c_interface:
            msg = msg + ' Address=' + hex(i2c_address)

        log.message(msg, log.INFO)

        if dtype == config.WS_SPI_SSD1309:
            screen.drawSplash(delay=3)
        else:
            self.splash()

        # Set up number of lines and display buffer
        for i in range(0, self.lines):
            self.lineBuffer.insert(i,'')    
        return

    # Get display type
    def getDisplayType(self):
        return config.getDisplayType()

    # Get display name
    def getDisplayName(self):
        return config.getDisplayName()

    # Get LCD width
    def getWidth(self):
        return self.width

    # Set the display width
    def setWidth(self,width):
        if not self._isOLED:
            self.width = width
        return self.width

    # Get LCD number of lines
    def getLines(self):
        return self.lines

    # Switch off scrolling when adjusting the volume
    # OnOff is True or False
    def noScrolling(self,OnOff):
        self._no_scrolling = OnOff

    # Set font size
    def setFontSize(self,size):
        displayType = config.getDisplayType()
        if displayType == config.OLED_128x64:
            screen.setFontSize(size)

    # Set font scale
    def setFontScale(self,scale):
        displayType = config.getDisplayType()
        if displayType == config.OLED_128x64:
            screen.setFontScale(scale)

    # Set font name
    def setFontName(self,name):
        displayType = config.getDisplayType()
        if displayType == config.OLED_128x64 and size != self.saved_font_size:
            screen.setFontName(name)
            self.saved_font_name = name
        else:
            screen.setFontName(name)

    # Display a flash image for delay seconds
    def drawSplash(self,image,delay):
        screen.drawSplash(image,delay)

    # Send string to display if it has not already been displayed
    def out(self,line,message,interrupt=no_interrupt,rssfeed=False):
        global screen
        index = line-1
        leng = len(message)

        # scrolling=yes/no in /etc/radiod.conf permanently switches scrolling on/off
        # _no_scrolling is temporary to improve performance during volume change operation

        if self._no_scrolling or not config.scrolling:
            if self.isOLED():
                leng = self.getChars()
            else:
                if not rssfeed:
                    leng = self.width
            message = message[0:leng]

        if leng < 1:
            message = " "
            leng = 1
        
        # Check if screen has enough lines display message
        if line <= self.lines:
            # Always display messages that need to be scrolled
            if leng > self.width:
                screen.out(line,message,interrupt)

            # Only display if this is a different message on this line
            elif message !=  self.lineBuffer[index]:
                screen.out(line,message,interrupt)
                self.update()

            # Store the message in the line buffer for comparison
            # with the next message
            self.lineBuffer[index] = message    
        return

    # Clear the line buffer to force redisplay of the line specified
    def clearLineBuffer(self,line):
        index = line - 1
        if index >= 0 and index <= self.lines:     
            self.lineBuffer[index] = ''    

    # Update screen buffer (Only for OLEDs)
    def update(self):
        if self.isOLED(): 
            screen.update()

    # With OLEDs the amount of characters on a line varies
    # This routine should not be called unless the screen is an OLED
    def getChars(self):
        if self.isOLED():
            leng = screen.getChars()
        else:
            leng = self.width
        return leng

    # Clear display and line buffer
    def clear(self):
        screen.clear()
        self.lineBuffer = []        # Line buffer 
        for i in range(0, self.lines):
            self.lineBuffer.insert(i,'')    
        self.saved_volume = 0
        return

    # Set get delay cycles ( Used for temporary message displays)
    def setDelay(self,cycles):
        self.delay = cycles
        return self.delay

    # Used to display changed volume on 2 line displays
    def getDelay(self):
        return self.delay

    # Count down volume display delay on 2 line displays
    def decrementDelay(self):
        self.delay -= 1
        if self.delay < 0:
            self.delay = 0
        return self.delay

    # Check to see if the display has buttons
    def hasButtons(self):
        return self.has_buttons

    # Check to see Adafruit RGB buttons pressed 
    def checkButton(self):
        screen.checkButtons()   # Generates event if button pressed
        return

    # Is this a null screen
    def hasScreen(self):
        return self.has_screen

    # Is this a colour screen
    def hasColor(self):
        return screen.hasColor()

    def getMuteLine(self):
        return self._mute_line

    # LCD Backlight
    def backlight(self, label):
        if self.hasColor():
            dtype = config.getDisplayType()
            try:
                if dtype == config.LCD_ADAFRUIT_RGB:
                    # For Adafruit screen with RGB colour
                    color = self.getBackColor(label)
                    screen.backlight(color)
                elif dtype == config.LCD_I2C_JHD1313 or dtype == config.LCD_I2C_JHD1313_SGM31323:
                    # For Grove JHD1313 RGB display
                    rgbcolor = config.getRgbColor(label)
                    rgb = self.ImageColor.getrgb(rgbcolor)
                    screen.backlight(rgb)
            except Exception as e:  
                log.message("Error display.backlight " + str(e),log.ERROR)
        return
    
    # Get background colour by name label. Returns an integer
    def getBackColor(self, label):
        return config.getBackColor(label)
        
    # Get background colour by name index. Returns a color name
    def getBackColorName(self, index):
        return config.getBackColorName(index)

    # Oled volume bar. Not used by LCDs
    def volume(self,volume):
        if self.saved_volume != volume or self._refresh_volume_bar:
            self.saved_volume = volume
            dType = config.getDisplayType()
            screen.volume(volume)
            self.update()
            self._refresh_volume_bar = False

    # Is this an OLED display (Volume bar on the bottom line)
    def isOLED(self):
        return self._isOLED

    # Display splash logo
    def splash(self):
        delay = 3
        if self.isOLED():
            dir = os.path.dirname(__file__)
            bitmap = dir + '/' + config.splash_screen
            try:
                if os.path.exists(bitmap):
                    screen.drawSplash(bitmap,delay)
                else:
                    print(bitmap,"does not exist")
            except Exception as e:
                print("Splash:",e)

    # Force volume bar to be displayed during unmute
    # and control changes. For OLEDs only
    def refreshVolumeBar(self):
        if self._isOLED:
            self._refresh_volume_bar = True
            #if self.getLines() == 4:
            if self.getLines() == self._mute_line:
                #self.out(4, "", no_interrupt)
                self.out(self._mute_line, "", no_interrupt)
    
# End of Display class


### Test routine ###
if __name__ == "__main__":
    from translate_class import Translate
    translate = Translate()

    try:
        print("Test display_class.py")
        display = Display(translate)
        display.init()
        display_type = display.getDisplayType()
        display_name = display.getDisplayName()
        print("Display type",display_type,display_name)
        color = display.getBackColor('bg_color')
        print("bg_color",color,display.getBackColorName(display.getBackColor('bg_color')))
        display.backlight('search_color')
        display.splash()
        time.sleep(2)
        display.out(1,"bobrathbone.com")
        display.out(2,"Line 2 123456789")
        display.out(3,"Line 3 123456789")
        display.out(4,"Line 4 123456789")
        time.sleep(2)
        display.out(4,"Scroll 4 ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789", no_interrupt)
        time.sleep(1)
        display.out(4,"End of test")
        sys.exit(0)

    except KeyboardInterrupt:
        print("\nExit")
        sys.exit(0)
# End of test routine

# set tabstop=4 shiftwidth=4 expandtab
# retab

