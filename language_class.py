#!/usr/bin/env python3
#
# Raspberry Pi Internet Radio Class
# $Id: language_class.py,v 1.5 2025/02/16 12:53:30 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class reads the /var/lib/radio/language file for both espeech and LCD display
# The format of this file is:
#   <label>:<text>
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.

import os
import sys
import threading
from log_class import Log
import configparser

log = Log()

# System files
RadioLibDir = "/var/lib/radiod"
LanguageFile = RadioLibDir + "/language"
VoiceFile = RadioLibDir + "/voice"

class Language:

    speech = False

    # Speech text (Loaded from /var/lib/radio/language)
    LanguageText = {
        'main_display': 'Main display',
        'search_menu': 'Search menu',
        'select_source': 'Select source',
        'options_menu': 'Options menu',
        'rss_display': 'RSS display',
        'information': 'Information display',
        'the_time': 'The time is',
        'loading': 'Loading',
        'airplay': 'Airplay',
        'spotify': 'Spotify',
        'loading_radio': 'Loading radio stations',
        'updating_media': 'Updating media',
        'update_complete': 'Update complete',
        'loading_media': 'Loading media library',
        'loading_playlists': 'Loading playlists',
        'loading_playlist': 'Loading playlist',
        'starting_airplay': 'Starting Airplay',
        'starting_spotify': 'Starting Spotify',
        'waiting_for_spotify_client': 'Waiting for Spotify client',
        'waiting_for_network': 'Waiting for network',
        'radio_stations' : 'Radio stations',
        'media_library': 'Media library',
        'updatng_media': 'Updating media',
        'search': 'Search',
        'source_radio': 'Internet Radio',
        'source_media': 'Media library',
        'source_airplay': 'Airplay receiver',
        'source_soptify': 'Spotify receiver',
        'stopping_radio': 'Stopping radio',
        'current_station': 'Current station',
        'connecting': 'Connecting',
        'connected': 'Connected',
        'connection_error': 'Connection error',
        'station': 'Station',
        'track': 'Track',
        'sleep': 'Sleep',
        'on': 'on',
        'off': 'off',
        'on': 'on',
        'yes': 'yes',
        'no': 'no',
        'radio_version': 'Radio version',
        'mpd_version': 'MPD version',
        'wait': 'Please wait',
        'title_unknown': 'Title unknown',
        'track_unknown': 'Track unknown',
        'no_information': 'No information',

        # Options
        'random': 'Random',
        'consume': 'Consume',
        'repeat': 'Repeat',
        'single': 'Single',
        'reload': 'Reload',
        'timer': 'Timer',
        'alarm': 'Alarm',
        'alarmhours': 'Alarm hours',
        'alarmminutes': 'Alarm minutes',
        'streaming': 'Streaming',
        'colour': 'Colour',
        'dot': 'dot',

        # Volume and speech
        'voice': 'voice',
        'volume': 'Volume',
        'vol': 'Vol',
        'muted': 'Sound muted',

        # Menu labels
        'menu_search': 'Search',
        'menu_find': 'Find',
        'menu_source': 'Input Source',
        'menu_option': 'Menu option:',

        # Shutdown
        'stop': 'Stopping radio',
        'stopped': 'Radio stopped',
        'shutdown': 'Shutting down system',
        }

    # Initialisation routine - Load language
    def __init__(self,speech = False):
        log.init('radio')
        self.speech = speech
        self.load()
        return

    # Load language text file
    def load(self):
        if os.path.isfile(LanguageFile):
            try:
                with open(LanguageFile) as f:
                    lines = f.readlines()
                try:
                    for line in lines:
                        line = line.rstrip()    # Remove LF
                        line = line.rstrip(':') # Remove any : 
                        if line.startswith('#'):
                            continue
                        if len(line) < 1:
                            continue
                        line = line.rstrip()
                        param,value = line.split(':')
                        self.LanguageText[param] = str(value)

                except Exception as e:
                    log.message(LanguageFile + ":" + str(e), log.ERROR)

            except Exception as e:
                log.message("Error reading " + LanguageFile, log.ERROR)

        return

    # Get the text by label
    def getText(self,label):
        text = ''
        try:
            text = self.LanguageText[label] 
        except:
            log.message("language.getText Invalid label " + label, log.ERROR)
    
        text = text.lstrip()
        return text

    # Get the menu text 
    def getMenuText(self):
        menuText = []
        sLabels = ['main_display','search_menu','select_source',
               'options_menu','rss_display','information',
               'sleep',
              ]

        for label in sLabels:
            menuText.append(self.getText(label))

        return menuText

    # Get the menu text 
    def getOptionText(self):
        OptionText = []
        sLabels = [ 'random','consume','repeat','reload','timer', 'alarm',
                 'alarmhours','alarmminutes','streaming','colour',
              ]

        for label in sLabels:
            OptionText.append(self.getText(label))

        return OptionText

    # Speak message
    def speak(self,message,volume):
        if os.path.isfile(VoiceFile) and self.speech:
            try:
                message = self.purgeChars(message)
                cmd = self.execCommand("cat " + VoiceFile)
                cmd = cmd + str(volume) + " --stdout | aplay"
                cmd = "echo " +  '"' + message + '"' + " | " + cmd + " >/dev/null 2>&1"
                log.message(cmd, log.DEBUG)

                # If the first character is ! then supress the message
                if len(message) > 0 and message[0] != '!':
                    self.execCommand(cmd)
            except:
                log.message("Error reading " + VoiceFile, log.ERROR)
        else:
            log.message("No " + LanguageFile + " found!", log.ERROR)
        return

    # Remove problem characters from speech text
    def purgeChars(self,message):
        chars = ['!',':','|','*','[',']',
             '_','"','.']

        # If the first character is ! then supress the message
        message = message.lstrip()

        if message[0] == '!':
            supress = True
        else:
            supress = False
        for char in chars:
            message = message.replace(char,'')

        message = message.replace('/',' ')
        message = message.replace('-',',')
        if supress:
            message = '!' + message
        return message

    # Display text
    def displayList(self):
        for label in sorted(self.LanguageText):
            print("%s: %s" % (label, self.LanguageText[label]))
        return

    # Execute system command
    def execCommand(self,cmd):
        p = os.popen(cmd)
        return  p.readline().rstrip('\n')


# Test Language class
if __name__ == '__main__':
    language = Language()
    language.load()
    language.displayList()  
    
# End of class
# set tabstop=4 shiftwidth=4 expandtab
# retab

