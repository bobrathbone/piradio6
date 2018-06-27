#!/usr/bin/env python
#
# Raspberry Pi Internet Radio Class
# $Id: volume_class.py,v 1.16 2018/06/18 17:52:14 bob Exp $
#
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class controls volume functions
# Volume is controlled in two ways:
# 	1) Using the alsa mixer (For Spotify and Airplay)
#	2) By setting the volume in MPD (Radio and Media)
#
# In the case of Radio/Media the alsa mixer must be set back to a fairly
# high preset value such as 90%
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#	     The authors shall not be liable for any loss or damage however caused.
#

import os,sys
import time
import pdb

# Volume control files
RadioLibDir = "/var/lib/radiod"
VolumeFile = RadioLibDir + "/volume"	# MPD volume level
MixerVolumeFile = RadioLibDir + "/mixer_volume"  # Alsa mixer file

log = None

class Volume:
	volume = 0		# MPD volume level
	mixer_volume = 0	# Alsa Mixer volume level
	mixer_preset = 90	# Alsa mixer preset level (When MPD volume used)
	mixer_volume_id = 0	# Alsa mixer ID 
	speech_volume = 0	# Speech volume level
	range = 5		# Volume range (Sensitivity)

	def __init__(self, mpd_client,source,spotify,airplay,config,logging):
		global log
		self.mpd_client = mpd_client
		self.source = source
		self.config = config
		self.spotify = spotify
		self.airplay = airplay
		log = logging
		self.mixer_volume_id = config.getMixerVolumeID()
		self.mixer_preset = config.getMixerPreset()
	
		# Set up initial volume
		vol = self._getStoredVolume()
		self.speech_volume = vol
		self.set(vol)
		self.range = self.config.getVolumeRange()
		return

	# Get the volume 
	def get(self):
		if self.spotify.isRunning() or self.airplay.isRunning():
			self.mixer_volume = self._getMixerVolume()
			volume = self.mixer_volume
		else:
			self.volume = self._getMpdVolume(self.mpd_client)
			volume = self.volume
			# Don't change speech volume if muted
			if self.volume > 0:
				self.speech_volume = self.volume
		return volume
		
	# Get speech volume adjustment
	def getSpeechVolumeAdjust(self):
		return self.speech_volume

	# Get the MPD volume 
	def _getMpdVolume(self,client):
		try:
			client.ping()
			stats = client.status()
			self.volume = int(stats.get("volume"))

		except Exception as e:
			log.message("volume._getMpdVolume " + str(e),log.ERROR)
			time.sleep(2)

		return self.volume

	# Get mixer volume (This is the variable level - not the preset)
	def _getMixerVolume(self):
		volume =  self.mixer_volume
		return volume

	# Set the volume depending upon the source
	def set(self,volume,store=True):
		new_volume = 0
		if volume > 100:
			volume = 100
		elif volume < 0:
			volume = 0

		source_type = self.source.getType()

		if source_type == self.source.AIRPLAY or source_type == self.source.SPOTIFY:
			self.mixer_volume = self._setMixerVolume(volume,store)
			new_volume = self.mixer_volume	
		else:
			self._setMixerVolume(self.mixer_preset,False)
			self.volume = self._setMpdVolume(volume,store)
			new_volume = self.volume	
		return new_volume

	# Set the MPD volume level
	def _setMpdVolume(self,volume,store=True):
		try:
			self.mpd_client.setvol(volume)
			self.volume = volume
			if store:
				self.storeVolume(self.volume)
			log.message("volume._setMpdVolume " + str(self.volume), log.DEBUG)

		except Exception as e:
			log.message("volume._setVolume error vol=" \
					+ str(self.volume) + ': ' + str(e),log.ERROR)

		return self.volume
		
	# Set the Mixer volume level
	def _setMixerVolume(self,volume, store):
		cmd = "sudo amixer cset numid=" + str(self.mixer_volume_id) + \
						" -- " + str(volume) + "%"
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
                        self.execCommand("echo " + str(volume) + " > " + VolumeFile)
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

	# Increase volume using range value
	def increase(self):
		increment = 100/self.range
		volume = self._changeVolume(increment)
		return volume

	# Decrease volume using range value
	def decrease(self):
		decrement = 0 - 100/self.range
		volume = self._changeVolume(decrement)
		return volume

	# Common routine for volume increase/decrease
	def _changeVolume(self,change):
		new_volume = self.get() + change
		volume = self.set(new_volume)
		return volume

	# Get volume display value
	def displayValue(self):
		return self.get()/self.range

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
		self.set(0,store=False)
		return

	# Unmute the volume
	def unmute(self):
		volume = self._getStoredVolume()
		self.set(volume)
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

	# Execute system command
	def execCommand(self,cmd):
		p = os.popen(cmd)
		return  p.readline().rstrip('\n')

# End of class
