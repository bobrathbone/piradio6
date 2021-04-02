#!/usr/bin/env python3
# Raspberry Pi Internet Radio Configuration Class
# $Id: config_class.py,v 1.11 2021/03/12 13:08:33 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class reads the /etc/radiod.conf file for configuration parameters
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.
#

import os
import sys
import configparser
from log_class import Log
from constants import *
import pdb

# System files
ConfigFile = "/etc/radiod.conf"
Airplay = "/usr/local/bin/shairport-sync"

log = Log()
config = configparser.ConfigParser(interpolation=None)

class Configuration:
    # Input source
    RADIO = 0
    PLAYER = 1
    AIRPLAY = 2

    """
    Station name source. LIST= from stationlist file 
    or STREAM from radio stream
    """
    LIST = 0
    STREAM = 1

    # Display types
    NO_DISPLAY = 0      # No screen attached
    LCD = 1         # Directly connected LCD
    LCD_I2C_PCF8574 = 2 # LCD PCF8574 I2C backpack
    LCD_I2C_ADAFRUIT = 3    # Adafruit I2C LCD backpack
    LCD_ADAFRUIT_RGB = 4    # Adafruit RGB plate
    GRAPHICAL_DISPLAY = 5   # Graphical or touchscreen  display
    OLED_128x64 = 6     # OLED 128 by 64 pixels
    PIFACE_CAD = 7      # Piface CAD 
    ST7789TFT = 8       # Pirate audio TFT with ST7789 controller

    display_type = LCD
    DisplayTypes = [ 'NO_DISPLAY','LCD', 'LCD_I2C_PCF8574', 
             'LCD_I2C_ADAFRUIT', 'LCD_ADAFRUIT_RGB', 
             'GRAPHICAL_DISPLAY', 'OLED_128x64', 
             'PIFACE_CAD','ST7789TFT' ]

    # User interface ROTARY or BUTTONS
    ROTARY_ENCODER = 0
    BUTTONS = 1
    GRAPHICAL=2
    COSMIC_CONTROLLER = 3   # IQAudio cosmic controller
    PIFACE_BUTTONS = 4  # PiFace CAD buttons 
    ADAFRUIT_RGB = 5    # Adafruit RGB I2C 5 button interface
    user_interface = ROTARY_ENCODER

    UserInterfaces = [ 'ROTARY_ENCODER','BUTTONS', 'GRAPHICAL', 
             'COSMIC_CONTROLLER', 'PIFACE_BUTTONS', 'ADAFRUIT_RGB', 
             ] 

    # Rotary class selection
    STANDARD = 0    # Select rotary_class.py
    ALTERNATIVE = 1 # Select rotary_class_alternate.py

    # Configuration parameters
    mpdport = 6600          # MPD port number
    client_timeout = 10     # MPD client timeout in secons 3 to 15 seconds
    dateFormat = "%H:%M %d/%m/%Y"   # Date format
    volume_range = 100      # Volume range 10 to 100
    volume_increment = 1    # Volume increment 1 to 10
    display_playlist_number = False # Two line displays only, display station(n)
    source = RADIO          # Source RADIO or Player
    load_last = False       # Auto load media if no Internet on startup
    rotary_class = STANDARD # Rotary class STANDARD or ALTERNATIVE 
    display_width = 0       # Line width of display width 0 = use program default
    display_lines = 2       # Number of display lines
    scroll_speed = float(0.3)   # Display scroll speed (0.01 to 0.3)
    airplay = False     # Use airplay
    mixerPreset = 0     # Mixer preset volume (0 disable setting as MPD controls it)
    audio_out=""        # Audio device string such as headphones, HDMI or DAC
    audio_config_locked = True    # Don't allow dynamic updating of audio configuration
    display_blocks = False  # Display volume in blocks
    fullscreen = True   # Graphics screen fullscreen yes no 
    startup_playlist = ""   # Startup playlist if defined
    screen_saver = 0    # Screen saver time n minutes, 0 = No screen save
    flip_display_vertically = False # Flip OLED display vertically
    stationNamesSource = LIST # Station names from playlist names or STREAM
    mute_action = 0     # MPD action on mute, 1=pause, 2=stop, 0=volume off only

    # Remote control parameters 
    remote_led = 0  # Remote Control activity LED 0 = No LED    
    remote_control_host = 'localhost'   # Remote control to radio communication port
    remote_listen_host = 'localhost'    # Remote control to radio communication port
    remote_control_port = 5100          # Remote control to radio communication port

    i2c_address = 0x00  # Use defaults or use setting in radiod.conf 
    i2c_bus = 1     # The I2C bus is normally 1
    speech = False          # Speech on for visually impaired or blind persons
    isVerbose = False       # Extra speech verbosity
    speak_info = False      # If speach enable also speak info (IP address and hostname)
    speech_volume = 80      # Percentage speech volume 
    logfile_truncate = False    # Truncate logfile otherwise write to end
    comitup_ip = "10.41.0.1"    # Comitup initial IP address.

    # Shoutcast ID
    shoutcast_key = "anCLSEDQODrElkxl"

    # Internet check URL and port number
    internet_check_url="google.com"
    internet_check_port=80
    internet_timeout=10

    # Graphics screen default parameters [SCREEN] section
    fullscreen = True   # Display graphics fulll screen
    window_title = "Bob Rathbone Internet Radio %V - %H"    # Window title
    window_color = 'blue'   # Graphics screen background colour
    labels_color = 'white'  # Graphics screen labels colour
    display_window_color = 'navy'       # Display window background colour
    display_window_labels_color = 'white'   # Display window labels colour
    display_mouse = False   # Hide mouse
    switch_programs = False # Allow switch between gradio and vgradio
    slider_color = 'red'    # Search window slider default colour 
    banner_color = 'black'  # Time banner text colour
    wallpaper = ''      # Background wallpaper
    graphicDateFormat="%H:%M:%S %A %e %B %Y"    # Format for graphic screen

    # Specific to the vintage graphic radio
    scale_labels_color = 'white'    # Vintage screen labels colour
    stations_per_page = 50      # maximum stations per page
    display_date = True         # Display time and date
    display_title = True        # Display title play (at bottom of screen)
    splash_screen = 'bitmaps/raspberry-pi-logo.bmp' # Splash screen (OLED)
    screen_size = (800,480)     # Screen size 800x480 (7 inch) or 720x480 (3.5 inch)
    bluetooth_device='00:00:00:00:00:00'    # Bluetooth device ID
    translate_lcd = True        # Translate characters for LCD display
                                # True for latin character LCDs.
                                # False for Russian/Cyrillic character LCDs
    romanize = True     # Romanize language(convert to Latin). e.g. Russian
    codepage = 0        # LCD font page 0,1,2 depending upon make of LCD
    language='English'  # Translation table in /usr/share/radio/fonts eg Russian
    controller='HD44780U'   # LCD/OLED controller type

    shutdown = True     # Shutdown when exiting radio
    
    # Colours for Adafruit LCD
    color = { 'OFF': 0x0, 'RED' : 0x1, 'GREEN' : 0x2, 'YELLOW' : 0x3,
          'BLUE' : 0x4, 'VIOLET' : 0x5, 'TEAL' : 0x6, 'WHITE' : 0x7 }

    colorName = { 0: 'Off', 1 : 'Red', 2 : 'Green', 3 : 'Yellow',
            4 : 'Blue', 5 : 'Violet', 6 : 'Teal', 7 : 'White' }

    colors = { 'bg_color' : 0x0,
           'mute_color' : 0x0,
           'shutdown_color' : 0x0,
           'error_color' : 0x0,
           'search_color' : 0x0,
           'source_color' : 0x0,
           'info_color' : 0x0,
           'menu_color' : 0x0,
           'sleep_color': 0x0 }

    # List of loaded options for display
    configOptions = {}

    #  GPIOs for switches and rotary encoder configuration (40 pin wiring)
    switches = { "menu_switch": 17,
             "mute_switch": 4,
             "left_switch": 14,
             "right_switch": 15,
             "up_switch": 24,
             "down_switch": 23,
           }

    # Pull up/down resistors (For button class only)
    pull_up_down = DOWN # Default

    # Values for the rotary switch on vintage radio (Not rotary encoders)
    # Zero values disable usage 
    menu_switches = {"menu_switch_value_1": 0,  # Normally 24
             "menu_switch_value_2": 0,  # Normally 8
             "menu_switch_value_4": 0,  # Normally 7
            }
    
    # RGB LED definitions for vintage radio
    # Zero values disable usage 
    rgb_leds = { "rgb_green": 0,    # Normally 27
             "rgb_blue": 0, # Normally 22
             "rgb_red": 0,  # Normally 23
           }

    #  GPIOs for LCD connections
    lcdconnects = { 
             "lcd_enable": 8,
             "lcd_select": 7,
             "lcd_data4": 27,
             "lcd_data5": 22,
             "lcd_data6": 23,
             "lcd_data7": 24,
           }

    # Initialisation routine
    def __init__(self):
        log.init('radio')
        if not os.path.isfile(ConfigFile) or os.path.getsize(ConfigFile) == 0:
            log.message("Missing configuration file " + ConfigFile, log.ERROR)
        else:
            self.getConfig()

        return

    # Get configuration options from /etc/radiod.conf
    def getConfig(self):
        section = 'RADIOD'

        # Get options
        config.read(ConfigFile)
        try:
            options =  config.options(section)
            for option in options:
                option = option.lower()
                parameter = config.get(section,option)
                
                self.configOptions[option] = parameter

                if option == 'loglevel':
                    next

                elif option == 'codecs':
                    next

                elif option == 'volume_range':
                    range = 100
                    try:
                        range = int(parameter)
                        if range < 10:
                            range = 10
                        if range > 100:
                            range = 100
                        self.volume_range = range
                        self.volume_increment = int(100/range)
                    except:
                        self.invalidParameter(ConfigFile,option,parameter)

                elif option == 'user_interface':
                    if parameter == 'buttons':
                        self.user_interface =  self.BUTTONS
                    elif parameter == 'rotary_encoder':
                        self.user_interface =  self.ROTARY_ENCODER
                    elif parameter == 'graphical':
                        self.user_interface =  self.GRAPHICAL
                    elif parameter == 'cosmic_controller':
                        self.user_interface =  self.COSMIC_CONTROLLER
                    elif parameter == 'phatbeat':
                        self.user_interface =  self.BUTTONS
                    elif parameter == 'pifacecad':
                        self.user_interface =  self.PIFACE_BUTTONS

                elif option == 'remote_led':
                    try:
                        self.remote_led = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile,option,parameter)

                elif option == 'remote_control_host':
                    self.remote_control_host = parameter

                elif option == 'remote_control_port':
                    try:
                        self.remote_control_port = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile,option,parameter)

                elif option == 'remote_listen_host':
                    self.remote_listen_host = parameter

                elif option == 'mpdport':
                    try:
                        self.mpdport = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile,option,parameter)

                elif option == 'client_timeout':
                    try:
                        self.client_timeout = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile,option,parameter)

                elif option == 'dateformat':
                    self.dateFormat = parameter

                elif option == 'display_playlist_number':
                    self.display_playlist_number = self.convertYesNo(parameter)

                elif option == 'station_names':
                    if parameter == 'stream':
                        self.stationNamesSource =  self.STREAM
                    else:
                        self.stationNamesSource =  self.LIST

                elif option == 'flip_display_vertically':
                    self.flip_display_vertically = self.convertYesNo(parameter)

                elif option == 'splash':
                    self.splash_screen = parameter

                elif option == 'startup':
                    if parameter == 'RADIO': 
                        self.source =  self.RADIO
                    elif parameter == 'MEDIA':
                        self.source =  self.PLAYER
                    elif parameter == 'AIRPLAY':
                        self.source =  self.AIRPLAY
                    elif parameter == 'LAST': 
                        self.load_last = True
                    elif len(parameter) > 0:
                        self.startup_playlist = parameter

                elif option == 'i2c_address':
                    try:
                        value = int(parameter,16)
                        if value  > 0x0:
                            self.i2c_address =  value
                    except Exception as e:
                        print ("i2c_address", e)
                        self.invalidParameter(ConfigFile,option,parameter)

                elif option == 'i2c_bus':
                    try:
                        value = int(parameter)
                        if value  > 0 or parameter <= 1:
                            self.i2c_bus =  value
                        else:
                            self.invalidParameter(ConfigFile,option,parameter)

                    except:
                        self.invalidParameter(ConfigFile,option,parameter)

                elif 'color' in option:
                    try:
                        self.colors[option] = self.color[parameter]
                    except:
                        self.invalidParameter(ConfigFile,option,parameter)

                elif option == 'speech':
                    self.speech = self.convertYesNo(parameter)

                elif option == 'verbose':
                    self.isVerbose = self.convertYesNo(parameter)

                elif option == 'speak_info':
                    self.speak_info = self.convertYesNo(parameter)

                elif option == 'volume_display':
                    if parameter == 'blocks':
                        self.display_blocks = True

                elif option == 'speech_volume':
                    try:
                        self.speech_volume = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile,option,parameter)

                elif option == 'pull_up_down':
                    if parameter == 'up':
                        self.pull_up_down = UP
                    else:
                        self.pull_up_down = DOWN

                elif '_switch' in option and not 'menu_switch_value'in option:
                    try:
                        self.switches[option] = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile,option,parameter)

                elif 'display_width' in option:
                    try:
                        self.display_width = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile,option,parameter)

                elif 'display_lines' in option:
                    try:
                        self.display_lines = int(parameter)
                    except:
                        self.invalidParameter(ConfigFile,option,parameter)

                elif 'scroll_speed' in option:
                    try:
                        self.scroll_speed = float(parameter)
                    except:
                        self.invalidParameter(ConfigFile,option,parameter)

                elif 'codepage' in option:
                    codepage = int(parameter)
                    if codepage >= 0 and codepage <= 4:
                        self.codepage = codepage
                    
                elif 'lcd_' in option:
                    try:
                        lcdconnect = int(parameter)
                        self.lcdconnects[option] = lcdconnect
                    except:
                        self.invalidParameter(ConfigFile,option,parameter)

                elif 'rgb' in option:
                    try:
                        led = int(parameter)
                        self.rgb_leds[option] = led
                    except:
                        msg = "Invalid RGB LED connect parameter " +  option
                        log.message(msg,log.ERROR)

                elif 'menu_switch_value_' in option:
                    try:
                        menuswitch = int(parameter)
                        self.menu_switches[option] = menuswitch
                    except:
                        self.invalidParameter(ConfigFile,option,parameter)

                elif 'display_type' in option:
                    self.display_type = self.LCD    # Default

                    if parameter == 'LCD':
                        self.display_type = self.LCD

                    elif parameter == 'LCD_I2C_PCF8574':
                        self.display_type = self.LCD_I2C_PCF8574

                    elif parameter == 'LCD_I2C_ADAFRUIT':
                        self.display_type = self.LCD_I2C_ADAFRUIT

                    elif parameter == 'LCD_ADAFRUIT_RGB':
                        self.display_type = self.LCD_ADAFRUIT_RGB

                    elif parameter == 'NO_DISPLAY':
                        self.display_type = self.NO_DISPLAY

                    elif parameter == 'GRAPHICAL':
                        self.display_type = self.GRAPHICAL_DISPLAY

                    elif parameter == 'OLED_128x64':
                        self.display_type = self.OLED_128x64

                    elif parameter == 'PIFACE_CAD':
                        self.display_type = self.PIFACE_CAD

                    elif parameter == 'ST7789TFT':
                        self.display_type = self.ST7789TFT

                    else:
                        self.invalidParameter(ConfigFile,option,parameter)

                elif option == 'rotary_class':
                    if parameter == 'standard':
                        self.rotary_class = self.STANDARD
                    else:
                        self.rotary_class = self.ALTERNATIVE

                elif option == 'exit_action':
                    if parameter == 'stop_radio':
                        self.shutdown = False
                    else:
                        self.shutdown = True

                elif option == 'log_creation_mode':
                    if parameter == 'truncate':
                        self.logfile_truncate = True
                    else:
                        self.logfile_truncate = False

                elif option == 'shoutcast_key':
                    self.shoutcast_key = parameter

                elif option == 'internet_check_url':
                    self.internet_check_url = parameter

                elif option == 'internet_check_port':
                    self.internet_check_port = int(parameter)

                elif option == 'internet_timeout':
                    self.internet_timeout = int(parameter)

                elif option == 'bluetooth_device':
                    self.bluetooth_device = parameter

                elif option == 'mute_action':
                    if parameter == 'pause':
                        self.mute_action = PAUSE
                    elif parameter == 'stop':
                        self.mute_action = STOP

                elif option == 'translate_lcd':
                    self.translate_lcd = self.convertOnOff(parameter)

                elif option == 'language':
                    self.language = parameter

                elif option == 'controller':
                    self.controller = parameter
                
                elif option == 'romanize':
                    self.romanize = self.convertOnOff(parameter)

                elif option == 'audio_out':
                    audio_out = parameter.lstrip('"')
                    self.audio_out = audio_out.rstrip('"')

                elif option == 'audio_config_locked':
                    self.audio_config_locked = self.convertYesNo(parameter)

                elif option == 'comitup_ip':
                    self.comitup_ip = parameter

                else:
                    msg = "Invalid option " + option + ' in section ' \
                        + section + ' in ' + ConfigFile
                    log.message(msg,log.ERROR)

        except configparser.NoSectionError:
            msg = configparser.NoSectionError(section),'in',ConfigFile
            log.message(msg,log.ERROR)

        # Read Airplay parameters
        section = 'AIRPLAY'

        # Get options
        config.read(ConfigFile)
        try:
            options =  config.options(section)
            for option in options:
                option = option.lower()
                parameter = config.get(section,option)
                
                self.configOptions[option] = parameter

                if option == 'airplay':
                    if parameter == 'yes' and os.path.isfile(Airplay):
                        self.airplay = True

                # Name has been changed from mixer_volume to mixer_preset in v6.7
                elif option == 'mixer_volume' or option == 'mixer_preset':
                    volume = 100
                    try:
                        volume = int(parameter)
                        if volume < 0:
                            volume = 0
                        if volume > 100:
                            volume = 100
                        self.mixerPreset = volume
                    except:
                        self.invalidParameter(ConfigFile,option,parameter)

                elif option == 'mixer_volume_id':
                    next    # No longer used 

                else:
                    msg = "Invalid option " + option + ' in section ' \
                        + section + ' in ' + ConfigFile
                    log.message(msg,log.ERROR)


        except configparser.NoSectionError:
            msg = configparser.NoSectionError(section),'in',ConfigFile
            log.message(msg,log.WARNING)

        section = 'SCREEN'
        # Get options
        config.read(ConfigFile)
        try:
            options =  config.options(section)
            for option in options:
                option = option.lower()
                parameter = config.get(section,option)
                
                self.configOptions[option] = parameter

                if option == 'screen_size':
                    sW,sH = parameter.split('x')    
                    w = int(sW)
                    h = int(sH)
                    self.screen_size = (w,h)
            
                if option == 'fullscreen':
                    self.fullscreen = self.convertYesNo(parameter)
                
                elif option == 'window_color':
                    self.window_color = parameter
                    
                elif option == 'window_title':
                    self.window_title = parameter
                    
                elif option == 'banner_color':
                    self.banner_color = parameter
                    
                elif option == 'labels_color':
                    self.labels_color = parameter
                    
                elif option == 'scale_labels_color':
                    self.scale_labels_color = parameter
                    
                elif option == 'display_window_color':
                    self.display_window_color = parameter
                    
                elif option == 'display_window_labels_color':
                    self.display_window_labels_color = parameter
                    
                elif option == 'slider_color':
                    self.slider_color = parameter

                elif option == 'stations_per_page':
                    self.stations_per_page = int(parameter)

                elif option == 'screen_saver':
                    self.screen_saver = int(parameter)

                elif option == 'wallpaper':
                    if os.path.exists(parameter):
                        self.wallpaper = parameter

                elif option == 'dateformat':
                    self.graphicDateFormat = parameter

                elif option == 'display_mouse':
                    self.display_mouse = self.convertYesNo(parameter)
                    
                elif option == 'switch_programs':
                    self.switch_programs = self.convertYesNo(parameter)
                    
                elif option == 'display_date':
                    self.display_date = self.convertYesNo(parameter)
                    
                elif option == 'display_title':
                    self.display_title = self.convertYesNo(parameter)

        except configparser.NoSectionError:
            msg = configparser.NoSectionError(section),'in',ConfigFile
            log.message(msg,log.WARNING)
        return


    # Convert yes/no to True/False
    def convertYesNo(self,parameter):
        true_false = False
        if parameter == 'yes':
            true_false = True
        return true_false

    # Convert On/Off to True/False
    def convertOnOff(self,parameter):
        true_false = False
        if parameter == 'on':
            true_false = True
        return true_false

    # Invalid parameters message
    def invalidParameter(self, ConfigFile, option, parameter):
        msg = "Invalid parameter " + parameter + ' in option ' \
            + option + ' in ' + ConfigFile
        log.message(msg,log.ERROR)
    
    # Get routines

    # Get I2C backpack address
    def getI2Caddress(self):
        return self.i2c_address

    # Get I2C bus number
    def getI2Cbus(self):
        return self.i2c_bus

    # Get the volume range
    def getVolumeRange(self):
        return self.volume_range

    # Get the volume increment
    def getVolumeIncrement(self):
        return self.volume_increment

    # Get the volume display
    def displayVolumeBlocks(self):
        return self.display_blocks

    # Get the remote control activity LED number
    def getRemoteLed(self):
        return self.remote_led

    # Get the remote Host default localhost
    def getRemoteUdpHost(self):
        return self.remote_control_host

    # Get the UDP server listener IP Host default localhost
    # or 0.0.0.0 for all interfaces
    def getRemoteListenHost(self):
        return self.remote_listen_host

    # Get the remote Port  default 5100
    def getRemoteUdpPort(self):
        return self.remote_control_port

    # Get the mpdport
    def getMpdPort(self):
        return self.mpdport

    # Get the date format
    def getDateFormat(self):
        return self.dateFormat

    # Get the date format for graphic screen
    def getGraphicDateFormat(self):
        return self.graphicDateFormat

    # Get display playlist number (Two line displays only)
    def getDisplayPlaylistNumber(self):
        return self.display_playlist_number

    # Get the startup source 0=RADIO or 1=MEDIA
    def getSource(self):
        return self.source

    # Get load last playlist option
    def loadLast(self):
        return self.load_last

    # Get the startup source name RADIO MEDIA
    def getSourceName(self):
        source_name = "MEDIA"
        if self.getSource() < 1:
            source_name = "RADIO"
        return source_name

    # Get the remote Port  default 5100
    def getRemoteUdpPort(self):
        return self.remote_control_port

    # Get the mpdport
    def getMpdPort(self):
        return self.mpdport

    # Get MPD Client Timeout 2 to 15 seconds (default 5)
    def getClientTimeout(self):
        timeout = self.client_timeout
        if timeout < 2:
            timeout = 2
        elif timeout > 15:
            timout = 15
        return timeout

    # Get the date format
    def getDateFormat(self):
        return self.dateFormat

    # Get display playlist number (Two line displays only)
    def getDisplayPlaylistNumber(self):
        return self.display_playlist_number

    # Get the startup source 0=RADIO or 1=MEDIA
    def getSource(self):
        return self.source

    # Get the startup source name RADIO MEDIA
    def getSourceName(self):
        source_name = "MEDIA"
        if self.getSource() < 1:
            source_name = "RADIO"
        return source_name

    # Get the background color (Integer)
    def getBackColor(self,sColor):
        color = 0x0
        try: 
            color = self.colors[sColor]
        except:
            log.message("Invalid option " + sColor, log.ERROR)
        return color

    # Get the background colour string name
    def getBackColorName(self,iColor):
        sColor = 'None' 
        try: 
            sColor = self.colorName[iColor]
        except:
            log.message("Invalid option " + int(iColor), log.ERROR)
        return sColor

    # Get speech
    def hasSpeech(self):
        return self.speech  

    # Get verbose
    def verbose(self):
        return self.isVerbose   

    # Get verbose
    def speakInfo(self):
        return self.speak_info  

    # Get speech volume % of normal volume level
    def getSpeechVolumeAdjust(self):
        return self.speech_volume

    # Display parameters
    def display(self):
        for option in sorted(self.configOptions):
            param = self.configOptions[option]
            if option != 'None':
                log.message(option + " = " + param, log.DEBUG)
        return

    # Return the ID of the rotary class to be used STANDARD or ALTERNATIVE
    def getRotaryClass(self):
        return self.rotary_class

    # Returns the switch GPIO configuration by label
    def getSwitchGpio(self,label):
        switch = -1
        try:
            switch = self.switches[label]
        except:
            msg = "Invalid switch label " + label
            log.message(msg, log.ERROR)
        return switch

    # Returns the LCD GPIO configuration by label
    def getLcdGpio(self,label):
        lcdconnect = -1
        try:
            lcdconnect = self.lcdconnects[label]
        except:
            msg = "Invalid LCD connection label " + label
            log.message(msg, log.ERROR)
        return lcdconnect

    # Get the RGB Led configuration by label (Retro radio only)
    def getRgbLed(self,label):
        led = -1
        try:
            led = self.rgb_leds[label]
        except:
            msg = "Invalid RGB configuration label " + label
            log.message(msg, log.ERROR)
        return led

    # Get the RGB Led configuration by label (Retro radio only)
    def getMenuSwitch(self,label):
        menuswitch = -1
        try:
            menuswitch = self.menu_switches[label]
        except:
            msg = "Invalid menu switch configuration label " + label
            log.message(msg, log.ERROR)
        return menuswitch

    # User interface (Buttons or Rotary encoders or uther)
    def getUserInterface(self):
        return self.user_interface

    # User interface (Buttons or Rotary encoders)
    def getUserInterfaceName(self):
        return self.UserInterfaces[self.user_interface]

    # Get Display type
    def getDisplayType(self):
        return self.display_type

    # Get Display name
    def getDisplayName(self):
        return self.DisplayTypes[self.display_type]

    # Get LCD width
    def getWidth(self):
        return self.display_width

    # Get Display lines
    def getLines(self):
        return self.display_lines

    # Get scroll speed
    def getScrollSpeed(self):
        return self.scroll_speed

    # Get airplay option
    def getAirplay(self):
        return self.airplay

    # Get mixer volume preset
    def getMixerPreset(self):
        return self.mixerPreset

    # Get startup playlist
    def getStartupPlaylist(self):
        return self.startup_playlist

    # Shutdown option
    def doShutdown(self):
        return self.shutdown

    # Pull Up/Down resistors (Button interface only)
    def getPullUpDown(self):
        return self.pull_up_down

    # Truncate logfile
    def logTruncate(self):
        return self.logfile_truncate

    # SCREEN section
    def getSize(self):
        return self.screen_size

    # Fullscreen option for graphical screen
    def fullScreen(self):
        return self.fullscreen

    # Get graphics window title
    def getWindowTitle(self):
        return self.window_title

    # Get graphics window colour
    def getWindowColor(self):
        return self.window_color

    # Get time banner text colour
    def getBannerColor(self):
        return self.banner_color

    # Get graphics labels colour
    def getLabelsColor(self):
        return self.labels_color

    # Get graphics labels colour
    def getScaleLabelsColor(self):
        return self.scale_labels_color

    # Get display window colour
    def getDisplayWindowColor(self):
        return self.display_window_color

    # Get display window labels colour
    def getDisplayLabelsColor(self):
        return self.display_window_labels_color

    # Get slider colour
    def getSliderColor(self):
        return self.slider_color

    # Get maximum stations displayed per page (vintage graphic radio)
    def getMaximumStations(self):
        if self.stations_per_page > 50:
            self.stations_per_page = 50
        return self.stations_per_page

    # Get window wallpaper
    def getWallPaper(self):
        return self.wallpaper

    # Mouse hidden 
    def displayMouse(self):
        return self.display_mouse

    # Allow program switch
    def switchPrograms(self):
        return self.switch_programs

    # Display date and time yes/no
    def displayDate(self):
        return self.display_date

    # Display date and time yes/no
    def displayTitle(self):
        return self.display_title

    # Screensaver time
    def screenSaverTime(self):
        return self.screen_saver

    # Shoutcast key
    def getShoutcastKey(self):
        return self.shoutcast_key

    # Bluetooth device
    def getBluetoothDevice(self):
        return self.bluetooth_device

    # Bluetooth device
    def getMuteAction(self):
        return self.mute_action

    # Oled flip display setting
    def flipVertical(self):
        return self.flip_display_vertically

    # Oled flip display setting
    def getSplash(self):
        return self.splash_screen

    # Station names from playlist names or from the stream 
    def getStationNamesSource(self):
        return self.stationNamesSource

    # Get translate LCD characters
    def getTranslate(self):
        return self.translate_lcd

    # Get translate LCD characters
    def getLcdFontPage(self):
        return self.codepage

    # Get Romanize language e.g. Russian/Cyrillic characters
    def getRomanize(self):
        return self.romanize

    def getAudioOut(self):
        return self.audio_out

    # Get language e.g. Russian or English etc
    def getLanguage(self):
        return self.language

    # Get controller type HD44780U or HD44780
    def getController(self):
                return self.controller

    def getComitupIp(self):
                return self.comitup_ip

    def getInternetCheckUrl(self):
        return self.internet_check_url

    def getInternetCheckPort(self):
        return self.internet_check_port

    def getInternetTimeout(self):
        return self.internet_timeout

    def audioConfigLocked(self):
        return self.audio_config_locked

# End Configuration of class

# Test Configuration class
if __name__ == '__main__':

    config = Configuration()
    print ("User interface:", config.getUserInterface(), config.getUserInterfaceName())
    print ("Configuration file:", ConfigFile)
    print ("Volume range:", config.getVolumeRange())
    print ("Volume increment:", config.getVolumeIncrement())
    print ("Mpd port:", config.getMpdPort())
    print ("Mpd client timeout:", config.getClientTimeout())
    print ("Remote LED:", config.getRemoteLed())
    print ("Remote LED port:", config.getRemoteUdpPort())
    print ("Date format:", config.getDateFormat())
    print ("Display playlist number:", config.getDisplayPlaylistNumber())
    print ("Source:", config.getSource(), config.getSourceName())
    print ("Load last playlist", config.loadLast())
    print ("Background colour number:", config.getBackColor('bg_color'))
    print ("Background colour:", config.getBackColorName(config.getBackColor('bg_color')))
    print ("Speech:", config.hasSpeech())
    print ("Speech volume adjustment:", str(config.getSpeechVolumeAdjust()) + '%')
    print ("Verbose:", config.verbose())
    print ("Speak info:", config.speakInfo())
    print ("Audio out:",config.getAudioOut())
    print ("Audio Configuration locked:",config.audioConfigLocked())
    print ("Comitup IP:",config.getComitupIp())

    print ("pull_up_down:", config.getPullUpDown())
    for switch in config.switches:
        print (switch, config.getSwitchGpio(switch))
    
    for lcdconnect in sorted(config.lcdconnects):
        print (lcdconnect, config.getLcdGpio(lcdconnect))
    
    for led in config.rgb_leds:
        print (led, config.getRgbLed(led))
    
    for menuswitch in config.menu_switches:
        print (menuswitch, config.getMenuSwitch(menuswitch))
    
    rclass = ['Standard', 'Alternative']
    rotary_class = config.getRotaryClass()
    print ("Rotary class:", rotary_class, rclass[rotary_class])
    print ("Display type:", config.getDisplayType(), config.getDisplayName())
    print ("Display lines:", config.getLines())
    print ("Display width:", config.getWidth())
    print ("LCD font page:", config.getLcdFontPage())
    print ("Full screen:", config.fullScreen())
    print ("Grapic screen size:", config.getSize())
    print ("Scroll speed:", config.getScrollSpeed())
    print ("Airplay:", config.getAirplay())
    print ("Mixer Volume Preset:", config.getMixerPreset())
    print ("Translate LCD characters:", config.getTranslate())
    print ("LCD Controller:", config.getController())
    print ("Language:", config.getLanguage())
    print ("Romanize:", config.getRomanize())

    print ("Bluetooth device:", config.getBluetoothDevice())

    # I2C parameters
    print ("I2C bus", config.getI2Cbus())
    print ("I2C address:", hex(config.getI2Caddress()))
    
    # Shoucast
    print ("Shoutcast key:", config.getShoutcastKey())

    # Internet check
    print ("Internet check URL: ", config.getInternetCheckUrl())
    print ("Internet check port:", config.getInternetCheckPort())
    print ("Internet timeout: ", config.getInternetTimeout())
    
    # OLED
    print ("Flip screen vertical:",config.flipVertical())
    print ("Splash screen:",config.getSplash())
# End of __main__

# set tabstop=4 shiftwidth=4 expandtab
# retab
