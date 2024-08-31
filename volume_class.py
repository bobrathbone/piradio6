#!/usr/bin/env python3
#
# Raspberry Pi Internet Radio Class
# $Id: volume_class.py,v 1.30 2024/08/09 10:51:36 bob Exp $
#
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class controls volume functions
# Volume is controlled in two ways:
#   1) Using the alsa mixer (For Spotify and Airplay)
#   2) By setting the volume in MPD (Radio and Media)
#
# In the case of Radio/Media the alsa mixer must be set back to a fairly
# high preset value such as 90%
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.
#

import os,sys
import time
import pdb
from constants import *

# Volume control files
RadioLibDir = "/var/lib/radiod"
VolumeFile = RadioLibDir + "/volume"    # MPD volume level
MixerVolumeFile = RadioLibDir + "/mixer_volume"  # Alsa mixer file
MixerIdFile = RadioLibDir + "/mixer_volume_id"  # Alsa mixer volume ID 

log = None

class Volume:
    volume = 0      # MPD volume level
    last_volume = 0 # Used to check if volume changed
    mixer_volume = 0    # Alsa Mixer volume level
    mixer_preset = 90   # Alsa mixer preset level (When MPD volume used)
    mixer_volume_id = 0 # Alsa mixer ID 
    speech_volume = 0   # Speech volume level
    OK=0            # Volume status OK
    ERROR=1         # Error status
    status = OK     # Volume get status
    mpd_client = None   # MPD client interface object
    audio_device = "headphones"     # Audio device headphones, DAC, bluetooth etc
    mixer_device = ""           # Default "" or "-D bluealsa"

    def __init__(self, mpd_client,source,spotify,airplay,config,logging):
        global log
        self.mpd_client = mpd_client
        self.source = source
        self.config = config
        self.spotify = spotify
        self.airplay = airplay
        log = logging
        self.mixer_volume_id = self.getMixerVolumeID()
        self.mixer_preset = config.mixer_preset
    
        # Set up initial volume
        vol = self._getStoredVolume()
        self.speech_volume = vol
        self.audio_device = self.config.audio_out


        # Are we using bluetooth?
        if self.audio_device == "bluetooth":
            self.mixer_device  = "-D bluealsa"
        return

    # Get either the mpd volume or mixer volume
    def get(self):
        if self.spotify.isRunning() or self.airplay.isRunning():
            self.mixer_volume = self._getMixerVolume()
            volume = self.mixer_volume
        else:
            volume = self._getMpdVolume(self.mpd_client)

            # Store new volume if it is changed by external client (mpc) 
            if volume != self.last_volume:
                self.volume = volume 
                self.last_volume = volume 
                if not self.muted():
                    self.storeVolume(self.volume)

            # Don't change speech volume if muted
            if self.volume > 0:
                self.speech_volume = self.volume
        return volume   # This is either MPD or mixer volume
        
    # Get speech volume adjustment
    def getSpeechVolumeAdjust(self):
        return self.speech_volume

    # Get the MPD volume 
    def _getMpdVolume(self,mpd_client):
        try:
            status = mpd_client.status()
            vol = int(status.get("volume"))
            self.volume = vol   # Won't be reached if exception
            self.status = self.OK

        except Exception as e:
            log.message("volume._getMpdVolume " + str(e),log.ERROR)
            self.status = self.ERROR
            time.sleep(1)
        return self.volume

    # Get MPD volume status (and reset to OK)
    def getStatus(self):
        status = self.status
        self.status = self.OK
        return status

    # Get mixer volume (This is the variable level - not the preset)
    def _getMixerVolume(self):
        return self.mixer_volume

    # Set the volume depending upon the source
    # Store volume setting if not muting (store=True/False)
    def set(self,volume,store=True):
        new_volume = 0
        log.message("volume.set " + str(volume) + ' store ' + str(store), log.DEBUG)
        if volume > 100:
            volume = 100
        elif volume < 0:
            volume = 0
        source_type = self.source.getType()

        if source_type == self.source.AIRPLAY or source_type == self.source.SPOTIFY:
            self.mixer_volume = self._setMixerVolume(volume,store)
            new_volume = self.mixer_volume  
        else:
            # If MPD set mixer back to preset (usually 100%) amd set MPD volume
            self._setMixerVolume(self.mixer_preset,False)
            self.volume = self._setMpdVolume(self.mpd_client,volume,store)
            new_volume = self.volume    

        return new_volume

    # Set the MPD volume level
    def _setMpdVolume(self,mpd_client,newvolume,store=True):
        volume = int(newvolume) 
        log.message("volume._setMpdVolume " + str(volume) + ' store ' + str(store), log.DEBUG)
        if volume < 0:  
            volume = 0

        if self.volume != volume and store and volume > 0:
            log.message("volume._setMpdVolume " + str(volume), log.DEBUG)
            self.storeVolume(self.volume)
        try:
            mpd_client.setvol(volume)
            self.volume = volume

        except Exception as e:
            log.message("volume._setMpdVolume error vol=" \
                    + str(self.volume) + ': ' + str(e),log.ERROR)

        return self.volume
        
    # Set the Mixer volume level
    def _setMixerVolume(self,volume,store):
        
        # Restore alsamixer settings (Restore Waveshare DAC headphone mixer setting)

        if self.mixer_volume_id > 0: 
            log.message("volume._setMixerVolume " + str(volume), log.DEBUG) 
            cmd = "sudo amixer " + self.mixer_device + " cset numid=" + str(self.mixer_volume_id) \
                                  + " " + str(volume) + "%"
            log.message(cmd, log.DEBUG)
            self.execCommand(cmd)

            self.mixer_volume = volume
            
            if store:
                self._storeMixerVolume(volume)  
        return self.mixer_volume

    # Store the vloume in /var/lib/radiod
    def storeVolume(self,volume):
        source_type = self.source.getType()
        if source_type == self.source.AIRPLAY or source_type == self.source.SPOTIFY:
            self._storeMixerVolume(volume)  
        else:
            self._storeVolume(volume)   
        return

    # Store MPD volume level 
    def _storeVolume(self, volume):
        if volume > 100:
                volume = 100
        if volume < 0:
                volume = 0

        try:
                with open(VolumeFile, 'w') as f:
                    f.write(str(volume))
                    f.close()
        except:
                log.message("Error writing " + VolumeFile, log.ERROR)

        return volume

    # Store mixer volume
    def _storeMixerVolume(self, volume):
        if volume > 100:
                volume = 100
        if volume < 0:
                volume = 0

        try:
                self.execCommand("echo " + str(volume) + " > " + MixerVolumeFile)
        except:
                log.message("Error writing " + MixerVolumeFile, log.ERROR)

        return volume

    # Get stored volume 
    def getStoredVolume(self):
        return self._getStoredVolume()

    # Mixer volume file 
    def restoreMpdMixerVolume(self):
        self.mixer_preset = config.getMixerPreset()
        self._setMixerVolume(self.mixer_preset,False)
        return
    
    # Get stored volume
    def _getStoredVolume(self):
        source_type = self.source.getType()

        if source_type == self.source.AIRPLAY or source_type == self.source.SPOTIFY:
            self.mixer_volume = self.getStoredInteger(MixerVolumeFile,75)
            volume = self.mixer_volume
        else:
            self.volume = self.getStoredInteger(VolumeFile,75)
            volume = self.volume
        return volume   

    # Get mixer volume ID
    def getMixerVolumeID(self):
        self.mixer_volume_id = self.getStoredInteger(MixerIdFile,0)
        return self.mixer_volume_id

    # Increase volume using configiuration range value
    def increase(self):
        increment = int(100/self.config.volume_range)
        volume = self._changeVolume(self.mpd_client,increment)
        return volume

    # Decrease volume using range value
    def decrease(self):
        decrement = int(0 - 100/self.config.volume_range)
        volume = self._changeVolume(self.mpd_client,decrement)
        return volume

    # Common routine for volume increase/decrease
    def _changeVolume(self,mpd_client,change):
        new_volume = self.get() + change
        if new_volume < abs(change):
            new_volume = abs(change)
        volume = self.set(new_volume)
        return volume

    # Get volume display value
    def displayValue(self):
        value = float(self.get()/float(100)) * float(self.config.volume_range)
        return int(value)

    # Get the integer value stored in /var/lib/radiod
    # filename is the name any file in the lib directory
    # default_value is the value to be returned if the file read fails
    def getStoredInteger(self,filename,default_value):
        if os.path.isfile(filename):
            try:
                    value = int(self.execCommand("cat " + filename) )
            except ValueError:
                    value = int(default_value)
        else:
            log.message("Error reading " + filename, log.ERROR)
            value = int(default_value)
        return value

    # Mute the volume (Do not store volume setting in /var/lib/radio)
    def mute(self):
        source_type = self.source.getType()
        mute_action = self.config.mute_action

        self.set(0,store=False)
        if source_type == self.source.RADIO or source_type == self.source.MEDIA:
            try:
                if mute_action == PAUSE or source_type == self.source.MEDIA:
                    log.message("volume.mute MPD pause",log.DEBUG)
                    self.mpd_client.pause() # Streaming continues

                elif mute_action == STOP:
                    log.message("volume.mute MPD stop",log.DEBUG)
                    self.mpd_client.stop()  # Streaming stops
            except:
                pass
        return

    # Unmute the volume
    def unmute(self):
        source_type = self.source.getType()
        volume = self._getStoredVolume()
        if source_type == self.source.AIRPLAY or source_type == self.source.SPOTIFY:
            store = True
            if volume == 0:
                volume = 90
            self.mixer_volume = self._setMixerVolume(volume,store)
        else:
            if volume < 1:
               volume = 5
            self.set(volume)
            try:
                self.mpd_client.play()
            except:
                pass
        return

    # Is sound muted
    def muted(self):
        isMuted = True
        source_type = self.source.getType()

        if source_type == self.source.AIRPLAY or source_type == self.source.SPOTIFY:
            if self.mixer_volume > 0:
                isMuted = False

        else:
            if self.volume > 0:
                isMuted = False
        return isMuted

    # Refresh client if re-connection occured
    def setClient(self,mpd_client):
        self.mpd_client = mpd_client
        return

    # Execute system command
    def execCommand(self,cmd):
        p = os.popen(cmd)
        return  p.readline().rstrip('\n')

# End of class

def displayFile(filename):
    with open(filename) as f:
        s = f.read()
        s = s.rstrip()
        return s

if __name__ == "__main__":

    from time import strftime
    
    dateformat = "%H:%M %d/%m/%Y"
    sDate = strftime(dateformat)
    print("Volume class configuration %s" % sDate)
    print("===========================================")
    print("VolumeFile " + VolumeFile + " = " + displayFile(VolumeFile))
    print("MixerVolumeFile " + MixerVolumeFile + " = " + displayFile(MixerVolumeFile))
    print("MixerIdFile " + MixerIdFile + " = " + displayFile(MixerIdFile))

# End of script

# set tabstop=4 shiftwidth=4 expandtab
# retab
