#!/usr/bin/env python3
#
# Raspberry Pi Internet language Class
# $Id: message_class.py,v 1.1 2020/10/10 15:00:46 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class is responsible for generating messages to be displayed by the display class
# It uses the number of lines of the display to decide which line to display the message
# Most of the messages come from the language class which allow for different messages
# See files in the language sub-directory
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#       The authors shall not be liable for any loss or damage however caused.
#
#

import sys
import pdb
import datetime,time
from time import strftime

from language_class import Language
from config_class import Configuration

language = None
config = Configuration()

class Message:

    line = 1    # Line for display
    lines = 2   # Number of display lines
    width = 16  # Display width
    ipaddress = ''  # Stored IP address
    speech = False  # Speech for visually impaired or blind persons
    speech_text = ''  # Prevent text from being repeatedly spoken
    translate = None  # Language translation class   

    # Initialisation routine - Load language
    def __init__(self,radio,display,translate):
        global language
        self.radio = radio
        self.display = display
        self.translate = translate
        self.lines = display.getLines()
        self.width = display.getWidth()

        # Is speech enabled
        self.speech = config.hasSpeech()
        language = Language(self.speech)
        return

    # Get the message
    def get(self,label):
        self.line = 1
        message = ""

        if label == 'date_time':
            message = self.getDateTime(config)
            self.line = 1

        elif label == 'volume':
            if self.width < 16:
                message = language.getText('vol')
            else:
                message = language.getText('volume')
            self.line = self.lines  # Display on last line

        else:
            if label == 'muted':
                self.line = self.lines  # Display on last line
            message = language.getText(label)

        # If message get fails display label
        if len(message) < 1:
            message = label.replace('_',' ')
        message = self.translate.all(message)
        return message

    # Return date and time
    def getDateTime(self,config):
        dateFormat = config.getDateFormat()
        todaysdate = strftime(dateFormat)
        self.line = 1   # Display on line 1

        if self.width < 16:
            # Display time and day of month (8 chars)
            todaysdate = todaysdate[0:8]

        return todaysdate

    # Convert True or False to on or off text
    def toOnOff(self, value):
        if value:
            text = self.get('on')
        else:
            text = self.get('off')
    
        return text 

    # Convert True or False to yes or no text
    def toYesNo(self, value):
        if value:
            text = self.get('yes')
        else:
            text = self.get('no')
        return text 

    # Get the line the message is to be displayed on
    def getLine(self):
        return self.line

    # Get source text by source id
    def getSourceText(self,source):
        sSource = "Source error"
        sLabels = ['source_radio','source_media', 'source_airplay','source_spotify']
        try:
            sSource =  language.getText(sLabels[source])
        except:
            sSource = "Source index error"
        return sSource

    # Store the IP address for get IP
    def storeIpAddress(self,ipaddr):
        self.ipaddress = ipaddr
        return self.ipaddress
        
    # Get the IP address 
    def getIpAddress(self):
        return self.ipaddress

    # Get the Alarm setting text
    def getAlarmText(self,index):
        alarmTextStrings = ['Off','On','Repeat','Weekdays only']
        alarmText = alarmTextStrings[0]
        try:
            alarmText = alarmTextStrings[index]

        except Exception as e:
            print("message.getAlarmSetting", str(e))

        return alarmText

    # Get timer setting text
    def getTimerText(self,value):
        if value > 0:
            minutes,seconds = divmod(value,60)
            hours,minutes = divmod(minutes,60)
            if hours > 0:
                tstring = '%d:%02d:%02d' % (hours,minutes,seconds)
            else:
                tstring = '%d:%02d' % (minutes,seconds)
        else:
            tstring = 'off'
        return  tstring

    # Speak the message
    def speak(self,text,repeat=False):

        # Allow repeat of same message
        if repeat:
            self.speech_text = ''
        try: 
            if self.speech and len(text) > 1 and text != self.speech_text:
                if not self.radio.spotify.isRunning() and not self.radio.airplay.isRunning():
                    volume = self.radio.getVolume()/2
                    speech_volume_adjust = config.getSpeechVolumeAdjust()
                    volume = (volume * speech_volume_adjust/100)
                    if volume < 5:
                        volume = 5

                    self.radio.clientPause()
                    language.speak(text,volume)
                    self.speech_text = text # Prevent repeating

        except Exception as e:
            print("Error speak:", e)

        type = self.radio.getSourceType()
        if type == self.radio.source.RADIO or type == self.radio.source.MEDIA:
            self.radio.clientPlay()

        return

    # Get the volume display in blocks
    def volumeBlocks(self):
        real_volume = self.radio.getVolume()
        width = self.display.getWidth()
        nchars = width * real_volume / 100
        blocks = ''
        while nchars > 0:
            blocks = blocks + chr(0xFF)
            nchars -= 1
        return blocks

# End of message class

# Test Message class
if __name__ == '__main__':

    from display_class import Display
    display = Display()
    print("Display lines", display.getLines())
    display.init()
    message = Message(display)
    print(message.get('main_display'))
    print(message.get('loading_radio'))
    print(message.get('date_time'),message.getLine())
    print(message.get('volume'),message.getLine())
    print(message.get('muted'),message.getLine())
    print(message.get('menu_find'),message.getLine())
    sys.exit(0)

# End of test
# set tabstop=4 shiftwidth=4 expandtab
# retab
