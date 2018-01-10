#!/usr/bin/env python
#
# Raspberry Pi Airplay receiver Class
# $Id: airplay_class.py,v 1.9 2017/12/01 12:55:09 bob Exp $
#
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class uses  shairport-sync from the following Github repository
# https://github.com/mikebrady/shairport-sync.git
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#	     The authors shall not be liable for any loss or damage however caused.
#

import os
import sys
import pwd
import pwd
import pdb
import time
import ConfigParser
import socket

from log_class import Log
from config_class import Configuration
from translate_class import Translate

# Airplay (shairport-sync) pipe and files
AirplayDir = "/tmp/shairport"
AirplayInfo = AirplayDir + "/info"
AirplayMetadata =  AirplayDir + "/metadata"
AirplayPipe = "/tmp/shairport-sync-metadata"
ShairportReader = "/usr/local/bin/shairport-sync-metadata-reader"

# Stored mixer volume
RadioLibDir = "/var/lib/radiod"
MixerVolumeFile = RadioLibDir + "/mixer_volume"

log = Log()
translate = Translate()
config = Configuration()

class AirplayReceiver:

	mixerVolume = 100 # Mixer volume 
	saveMixerVolume = 0 # Saved Mixer volume for mute functions 
	mixerPreset = 100 # Mixer preset volume 
	mixerMuted = False # Mixer muted yes no
	AirplayRunning = False
	hostname = None
	title = 'Uknown title'
	interrupt = False
	pipeExists = False 

	# Initialisation routine
	def __init__(self):
		if pwd.getpwuid(os.geteuid()).pw_uid > 0:
			print "This program must be run with sudo or root permissions!"
			sys.exit(1)

		log.init('radio')
		self.setupConfiguration()
		return

	# Set up configuration files
	def setupConfiguration(self):
		return

	# Start Airlpay
	def start(self):
		log.message("Starting Airplay", log.DEBUG)
		self.hostname = socket.gethostname()
		if not os.path.isfile(MixerVolumeFile) or os.path.getsize(MixerVolumeFile) == 0:
				self.execCommand ("echo " + str(100) + " > " + MixerVolumeFile)

		if os.path.exists(AirplayPipe):
			log.message("Deleting old pipe " + AirplayPipe, log.DEBUG)
			self.execCommand("sudo rm -f " + AirplayPipe) 	# Delete old pipe

		self.execCommand("sudo mkdir -p " + AirplayDir) # Make airplay info directory
		self.execCommand("sudo chmod o+w " + AirplayDir) 
		self.execCommand("sudo touch " + AirplayMetadata) 
		self.execCommand("sudo chmod o+w " + AirplayMetadata) 
		
		# Start the airplay service
		cmd = "sudo service shairport-sync start"
		log.message(cmd, log.DEBUG)
		self.execCommand(cmd)
		time.sleep(0.5)	 # Allow shairport-sync to start-up

		# setup mixer volume etc
		self.setMixerVolume(self.getStoredMixerVolume())
		self.airplay_scrolling = 0
		self.AirplayRunning = True
		log.message("Airplay running "+ str(self.AirplayRunning), log.DEBUG)
		return self.AirplayRunning

	# Set up processing of metadata pipe
	def setupPipe(self):
		if os.path.exists(AirplayPipe):
			cmd = 'cat ' + AirplayPipe + ' | ' + ShairportReader \
				+ ' > ' +  AirplayMetadata + ' &'
			log.message(cmd, log.DEBUG)
			self.execCommand(cmd)
			self.pipeExists = True 
		else:
			self.pipeExists = False 

		return self.pipeExists

	# Stop Airlpay
	def stop(self):
		log.message("Stopping Airplay", log.DEBUG)
		pid_shairport = 0 
		try:
			pid_shairport = int(self.execCommand("pidof shairport-sync"))
		except:
			log.message("Airplay (shairport-sync) not running", log.DEBUG)
		if pid_shairport > 0: 
			self.execCommand("sudo service shairport-sync stop")
			time.sleep(1)
			# Safety precaution to stop accidentally deleting complete file system
			if len(AirplayDir) > 8:
				self.execCommand("rm -f " + AirplayDir + "/*")
		self.execCommand("sudo killall -q  cat")
		self.execCommand("sudo killall -q  shairport-sync-metadata-reader")
		self.AirplayRunning = False
		return self.AirplayRunning

	# Is Airplay running
	def isRunning(self):
		return self.AirplayRunning

	# Airplay information scrolling - decides which line to control
	def scroll(self):
		scroll = self.airplay_scrolling
		self.airplay_scrolling += 1
		if self.airplay_scrolling > 2:
			self.airplay_scrolling = 0
		return scroll

	# Get metadata info from reader string (called by info routine)
	def extractData(self,data):
		elements = data.split('"')
		sInfo = elements[1]
		return sInfo

	# Get Airplay metadata information
	def info(self):
		artist = 'Unknown artist'
		title = 'Unknown title'
		if self.hostname == 'None':
			self.hostname = ''
		album = 'Airplay:' + str(self.hostname)

		if not self.pipeExists:
			self.setupPipe()

		info = []

		if os.path.isfile(AirplayMetadata):
			cmd = "tail -8 " + AirplayMetadata + " > " + AirplayInfo
			self.execCommand(cmd)

		if os.path.isfile(AirplayInfo):
			with open(AirplayInfo) as f:
				for line in f:
					if len(line) < 4:
						next
					if line.startswith("Title:"):
						title =  self.extractData(line)
					elif line.startswith("Album Name:"):
						album = self.extractData(line)
					elif line.startswith("Artist:"):
						artist = self.extractData(line)

		info.append(translate.all(artist))
		info.append(translate.all(title))
		info.append(translate.all(album))

		if title != self.title:
			self.interrupt = True
			self.title = title
		else:
			self.interrupt =  False

		return info

	# Get interrupt (Title has changed)
	def getInterrupt(self):
		interrupt = self.interrupt
		self.interrupt = False
		return interrupt

	# Get mixer volume
	def getMixerVolume(self):
		volume =  self.mixerVolume
		return volume

	# Increase mixer volume
	def increaseMixerVolume(self):
		volume = self.mixerVolume
		range = config.getVolumeRange()
		volume += int(100/range)
		self.mixerVolume = self.setMixerVolume(volume)
		return self.mixerVolume

	# Decrease mixer volume
	def decreaseMixerVolume(self):
		volume = self.mixerVolume
		range = config.getVolumeRange()
		volume -= int(100/range)
		self.mixerVolume = self.setMixerVolume(volume)
		return self.mixerVolume

	# Set mixer volume
	def setMixerVolume(self,volume):
		if volume > 100:
			volume = 100
		if volume < 0:
			volume = 0

		mixer_volume_id = config.getMixerVolumeID()
		cmd = "sudo amixer cset numid=" + str(mixer_volume_id) + " -- " + str(volume) + "%"
		log.message(cmd,log.DEBUG)
		self.execCommand(cmd)

		if volume > 0:
			self.mixerMuted = False
		else:
			self.mixerMuted = True

		# Store Airplay mixer volume level
		self.mixerVolume = volume
		self.storeMixerVolume(self.mixerVolume)
		return self.mixerVolume

	# Is mixer muted
	def mixerIsMuted(self):
		return self.mixerMuted

	# Mute the mixer
	def muteMixer(self):
		self.saveMixerVolume = self.mixerVolume  
		self.setMixerVolume(0)
		self.mixerMuted = True
		return self.mixerVolume

	# unmute the mixer
	def unmuteMixer(self):
		self.setMixerVolume(self.saveMixerVolume)
		self.mixerMuted = False
		return self.mixerVolume

	# Get the stored mixer volume
	def getStoredMixerVolume(self):
		volume = 100
		if os.path.isfile(MixerVolumeFile):
			try:
				volume = int(self.execCommand("cat " + MixerVolumeFile) )
			except ValueError:
				volume = 100
		else:
			log.message("Error reading " + MixerVolumeFile, log.ERROR)

		return volume

	# Store mixer volume
	def storeMixerVolume(self, volume):
		if volume > 100:
			volume = 100
		if volume < 0:
			volume = 0

		try:
			self.execCommand("echo " + str(volume) + " > " + MixerVolumeFile) 
		except:
			log.message("Error writing " + MixerVolumeFile, log.ERROR)

		return volume

	# Get the mixer preset (Sound cards)
	def setMixerPreset(self):
		mixer_preset = config.getMixerPreset()

		# If preset=0 (On-board audio) do not change mixer level as this is done by MPD
		if mixer_preset != 0:
			log.message("Set mixer preset volume " + str(mixer_preset), log.DEBUG)
			self.setMixerVolume(mixer_preset)
		return mixer_preset

	# Execute system command
	def execCommand(self,cmd):
		p = os.popen(cmd)
		return  p.readline().rstrip('\n')

# End of class

### Test routine ###
if __name__ == "__main__":
	print "Test airplay_class.py"
	airplay = AirplayReceiver()
	airplay.start()
	airplay.setMixerVolume(70)
	time.sleep(4)
	airplay.setMixerVolume(90)
	time.sleep(4)
	airplay.setMixerVolume(80)
	time.sleep(4)
	airplay.muteMixer()
	time.sleep(4)
	airplay.unmuteMixer()
	time.sleep(4)
	airplay.stop()

	# Exit
	sys.exit(0)

