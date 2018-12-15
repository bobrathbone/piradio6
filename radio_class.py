#!/usr/bin/env python
#
# Raspberry Pi Internet Radio Class
# $Id: radio_class.py,v 1.177 2018/12/04 07:59:51 bob Exp $
# 
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class uses  Music Player Daemon 'mpd' and the python-mpd library
# Use "apt-get install python-mpd" to install the library
# Modified to use python-mpd2 library mpd.wikia.com
# See: http://pythonhosted.org/python-mpd2/
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#	      The authors shall not be liable for any loss or damage however caused.
#

import os
import sys,pwd
import string
import time,datetime
import re
import SocketServer
from time import strftime
import pdb

from __init__ import __version__
from __init__ import *

from udp_server_class import UDPServer
from udp_server_class import RequestHandler
from log_class import Log
from translate_class import Translate
from config_class import Configuration
from airplay_class import AirplayReceiver
from spotify_class import SpotifyReceiver
from language_class import Language
from source_class import Source
from volume_class import Volume
from mpd import MPDClient

# MPD files
MpdLibDir = "/var/lib/mpd"
PlaylistsDirectory =  MpdLibDir + "/playlists"
MusicDirectory =  MpdLibDir + "/music"
		
# Radio files
ConfigFile = "/etc/radiod.conf"
RadioLibDir = "/var/lib/radiod"
CurrentStationFile = RadioLibDir + "/current_station"
CurrentTrackFile = RadioLibDir + "/current_track"
CurrentSourceFile = RadioLibDir + "/source"
VolumeFile = RadioLibDir + "/volume"
MixerVolumeFile = RadioLibDir + "/mixer_volume"
MixerIdFile = RadioLibDir + "/mixer_volume_id"
BoardRevisionFile = RadioLibDir + "/boardrevision"

Icecast = "/usr/bin/icecast2"

# Option values
RandomSettingFile = RadioLibDir + "/random"
TimerFile = RadioLibDir + "/timer" 
AlarmFile = RadioLibDir + "/alarm" 
StreamFile = RadioLibDir + "/streaming"

log = Log()
translate = Translate()
language = None
server = None
volume = None

Mpd = "/usr/bin/mpd"	# Music Player Daemon
Mpc = "/usr/bin/mpc"	# Music Player Client

client = MPDClient()	

ON = True
OFF = False

class Radio:
	# Player options
	RANDOM = 0
	CONSUME = 0

	# Alarm definitions
	ALARM_OFF = 0
	ALARM_ON = 1
	ALARM_REPEAT = 2
	ALARM_WEEKDAYS = 3
	ALARM_LAST = ALARM_WEEKDAYS

	# Other definitions
	LEFT = 2
	RIGHT = 3

	ONEDAYSECS = 86400	# Day in seconds
	ONEDAYMINS = 1440	# Day in minutes

	config = Configuration()
	airplay = AirplayReceiver()
	spotify = SpotifyReceiver()

	source = None	# Source (radio,media,spotify and airplay)
	audio_error = False 	# No sound device
	boardrevision = 2 # Raspberry board version type
	MpdVersion = '' # MPD version 
	udphost = 'localhost'  # Remote IR listener UDP Host
	udpport = 5100  # Remote IR listener UDP port number
	mpdport = 6600  # MPD port number
	device_error_cnt = 0	# Device error causes an abort
	isMuted = False # Is radio state "pause" or "stop"
	searchlist = []	# Search list (tracks or radio stations)
	current_id = 1	# Currently playing track or station
	current_source = 0 # Current source (index in current_class.py)
	reload = False	# Reload radio stations or player playlists
	loading_DB = False	# Loading database
	artist = ""	# Artist (Search routines)
	airplayInstalled = False # Airplay (shairport-sync) installed
	spotifyInstalled = False # Spotify (librespot) installed
	error = False 	# Stream error handling
	errorStr = ""   # Error string
	updateLib = False    # Reload radio stations or player
	interrupt = False	# Was IR remote interrupt received
	stats = None		# MPD Stats array
	currentsong = None	# Current song / station
	state = 'play'		# State (used if get state fails) 
	getIdError = False	# Prevent repeated display of ID error
	rotary_class = config.STANDARD  # Rotary class standard all alternate
	display_artist = False		# Display artist (or track) flag
	current_file = ""  		# Currently playing track or station
	option_changed = False		# Option changed
	channelChanged = True		# Used to display title
	display_playlist_number = False # Display playlist number
	speech = False			# Speech enabled yes/no
	
	# MPD Options
	random = False	# Random tracks
	repeat = False	# Repeat play
	consume = False	# Consume tracks
	single = False	# Single play

	# Radio options
	reloadlib = False	# Reload music library yes/no
	setup_wifi = False	# Set up wifi

	# Clock and timer options
	timer = 0	  # Timer on
	timerValue = 0    # Timer value in minutes
	timeTimer = 0  	  # The time when the Timer was activated in seconds 
	dateFormat = "%H:%M %d/%m/%Y"   # Date format

	alarmType = ALARM_OFF	# Alarm on
	alarmTime = "0:7:00"    # Alarm time default type,hours,minutes
	alarmTriggered = False	# Alarm fired

	stationTitle = ''		# Radio station title
	stationName = ''		# Radio station name

	search_index = 0	# The current search index
	loadnew = False	  	# Load new track from search
	streaming = False	# Streaming (Icecast) disabled

	playlists = None
	keepAliveTime = 0	# Keep alive time for MPD pings

	# Configuration files in /var/lib/radiod 
	ConfigFiles = {
 		CurrentStationFile: 1,
 		CurrentTrackFile: 1,
 		CurrentSourceFile: 0,
 		VolumeFile: 75,
 		MixerVolumeFile: 45,
 		TimerFile: 30,
		AlarmFile: "0:07:00", 
		StreamFile: "off", 
 		RandomSettingFile: 0,
		}

	# Initialisation routine
	def __init__(self, menu, event):

		if pwd.getpwuid(os.geteuid()).pw_uid > 0:
			print "This program must be run with sudo or root permissions!"
			sys.exit(1)

		log.init('radio')

		# Need to refer to options in menu
		self.menu = menu

		# Get event handler
		self.event = event
		self.setupConfiguration()
		return

	# Set up configuration files
	def setupConfiguration(self):
		# Create directory 
		if not os.path.isfile(CurrentStationFile):
			self.execCommand ("mkdir -p " + RadioLibDir )

		# Initialise configuration files from ConfigFiles list
		for file in self.ConfigFiles:
			value = self.ConfigFiles[file]
			if not os.path.isfile(file) or os.path.getsize(file) == 0:
				self.execCommand ("echo " + str(value) + " > " + file)

		# Create mount point for USB stick and link it to the music directory
		if not os.path.isfile("/media"):
			self.execCommand("mkdir -p /media")
			if not os.path.ismount("/media"):
				self.execCommand("chown pi:pi /media")
			self.execCommand("sudo ln -f -s /media /var/lib/mpd/music")

		# Create mount point for networked music library (NAS)
		if not os.path.isfile("/share"):
			self.execCommand("mkdir -p /share")
			if not os.path.ismount("/share"):
				self.execCommand("chown pi:pi /share")
			self.execCommand("sudo ln -f -s /share /var/lib/mpd/music")

		# Set up mixer ID file
		if not os.path.isfile(MixerIdFile):
			dir = os.path.dirname(__file__)
			self.execCommand("sudo " + dir + "/set_mixer_id.sh")

		self.execCommand("chown -R pi:pi " + RadioLibDir)
		self.execCommand("chmod -R 764 " + RadioLibDir)
		self.current_file = CurrentStationFile
		self.current_id = self.getStoredID(self.current_file)

		return

	# Call back routine for the IR remote
	def remoteCallback(self):
		global server
		key = server.getData()
		log.message("IR remoteCallback " + key, log.DEBUG)

		self.event.MUTE_BUTTON_DOWN
		if key == 'KEY_MUTE':
			self.event.set(self.event.MUTE_BUTTON_DOWN)

		elif key == 'KEY_VOLUMEUP' or key == 'KEY_RIGHT':
			self.event.set(self.event.RIGHT_SWITCH)

		elif key == 'KEY_VOLUMEDOWN' or key == 'KEY_LEFT':
			self.event.set(self.event.LEFT_SWITCH)

		elif key == 'KEY_CHANNELUP' or key == 'KEY_UP':
			self.event.set(self.event.UP_SWITCH)

		elif key == 'KEY_CHANNELDOWN' or key == 'KEY_DOWN':
			self.event.set(self.event.DOWN_SWITCH)

		elif key == 'KEY_MENU' or key == 'KEY_OK':
			self.event.set(self.event.MENU_BUTTON_DOWN)

		elif key == 'KEY_LANGUAGE':
			self.event.set(self.event.KEY_LANGUAGE)

		elif key == 'KEY_INFO':
			self.event.set(self.event.KEY_INFO)

		# These come from the Web CGI script
		elif key == 'MEDIA':
			self.event.set(self.event.LOAD_MEDIA)

		elif key == 'RADIO':
			self.event.set(self.event.LOAD_RADIO)

		elif key == 'AIRPLAY':
			self.event.set(self.event.LOAD_AIRPLAY)

		elif key == 'SPOTIFY':
			self.event.set(self.event.LOAD_SPOTIFY)

		elif key == 'INTERRUPT':
			self.event.set(self.event.NO_EVENT)	# To be done

		elif key == 'RELOAD_PLAYLISTS':
			self.getSources()

		else:
			log.message("radio.remoteCallBack invalid IR key " + key, log.DEBUG)

		return 


	# Set up radio configuration and start the MPD daemon
	def start(self):
		global server
		global language
		global client
		global volume

		self.config.display()
		# Get Configuration parameters /etc/radiod.conf
		self.boardrevision = self.getBoardRevision()
		self.mpdport = self.config.getMpdPort()
		self.udpport = self.config.getRemoteUdpPort()
		self.udphost = self.config.getRemoteListenHost()
		self.display_playlist_number = self.config.getDisplayPlaylistNumber()
		self.speach = self.config.hasSpeech()
		language = Language(self.speech) # language is a global
		self.rotary_class = self.config.getRotaryClass()

		# Log OS version information 
		OSrelease = self.execCommand("cat /etc/os-release | grep NAME")
		OSrelease = OSrelease.replace("PRETTY_NAME=", "OS release: ")
		OSrelease = OSrelease.replace('"', '')
		log.message(OSrelease, log.INFO)
		myos = self.execCommand('uname -a')
		log.message(myos, log.INFO)

		# Start the player daemon
		log.message("Starting MPD", log.DEBUG)
		self.execCommand("service mpd start")

		# Connect to MPD
		client = MPDClient()	# Create the MPD client
		self.connect(self.mpdport)
		client.stop()	# Wait for stations to be loaded before playing

		# Is Airplay installed (shairport-sync)
		self.airplayInstalled = self.config.getAirplay()
		if self.airplayInstalled:
			self.stopAirplay()
		log.message("self.airplayInstalled " + str(self.airplayInstalled), log.DEBUG)

		# Is Spotify installed
		self.spotifyInstalled =  os.path.isfile('/usr/bin/librespot')

		self.source = Source(client=client,airplay=self.airplayInstalled,
					spotify=self.spotifyInstalled)

		# Set up source
		self.getSources()
		sourceType = self.config.getSource()

		# Set up volume controls
		volume = Volume(client,self.source,self.spotify,self.airplay,self.config,log)

		startup_playlist = self.config.getStartupPlaylist()
		if len(startup_playlist) > 0:
			log.message("Startup playlist " + startup_playlist, log.DEBUG)
			self.source.setPlaylist(startup_playlist)

		elif self.config.loadLast():
			log.message("Load last playlist", log.DEBUG)
			self.source_index = self.getStoredSourceIndex()
			self.source.setIndex(self.source_index)
		else:
			# Load either MEDIA, RADIO, AIRPLAY or SPOTIFY depending on config
			self.source.setType(sourceType)
			log.message("Load  MEDIA/RADIO", log.DEBUG)

		# Get stored values from Radio lib directory
		self.getStoredValue(self.menu.OPTION_RANDOM)
		self.current_id = self.getStoredID(self.current_file)
		log.message("radio.start current ID " + str(self.current_id), log.DEBUG)

		volume.set(volume.getStoredVolume())

		# Alarm and timer settings
		self.timeTimer = int(time.time())
		self.alarmTime = self.getStoredAlarm()
		sType,sHours,sMinutes = self.alarmTime.split(':')
		self.alarmType = int(sType)
		if self.alarmType > self.ALARM_OFF:
			self.alarmType = self.ALARM_OFF

		# Icecast Streaming settings
		self.streaming = self.getStoredStreaming()
		if self.streaming:
			self.streamingOn()
		else:
			self.streamingOff()

		# Start the IR remote control listener
		try:
			server = UDPServer((self.udphost,self.udpport),RequestHandler)
			msg = "UDP Server listening on " + self.udphost + " port " \
				+ str(self.udpport)
			log.message(msg, log.INFO)
			server.listen(server,self.remoteCallback)
		except Exception as e:
			log.message(str(e), log.ERROR)
			log.message("UDP server could not bind to " + self.udphost
					+ " port " + str(self.udpport), log.ERROR)
		return

	# Ping the client to keep alive and 
	# to re-connect if necessary
	def pingMPD(self):
		try:
			client.ping()
		except Exception as e:
			log.message(str(e), log.ERROR)
			self.connect(self.mpdport)
		return

	# Keep MPD connection alive 
	def keepAlive(self,seconds):
		now = time.time()	
		if now > self.keepAliveTime + seconds:
			self.keepAliveTime = time.time()
			self.pingMPD()
		return

	# Connect to MPD
	def connect(self,port):
		global client,volume
		connected = False
		retry = 2
		while retry > 0:
			#client = MPDClient()	# Create the MPD client
			try:
				client.timeout = 10
				client.idletimeout = None
				client.connect("localhost", port)
				log.message("Connected to MPD port " + str(port), log.INFO)
				if volume != None:
					volume.setClient(client)
				connected = True
				retry = 0

			except Exception as e:
				log.message( 'radio.connect failed port ' + str(port) \
					+ ':'  + str(e), log.ERROR)
				time.sleep(2.5)	# Wait for interrupt in the case of a shutdown
				retry -= 1

			# Try restarting MPD
			if not connected:
				log.message('radio.connect: Restarting MPD', log.DEBUG)
				self.execCommand("sudo systemctl restart mpd")
				time.sleep(3)
				client = MPDClient()	# Create the MPD client
				self.current_id += 1 # Skip bad station
				self.setCurrentID(self.current_id)
		return connected

	# Scroll up and down between stations/tracks
	def getNext(self,direction):
		playlist = self.getPlayList()
		index = self.getSearchIndex()

		# Artist displayed then don't increment track first time in

		if not self.displayArtist():
			leng = len(playlist)
			if leng > 0:
				if direction == UP:
					index = index + 1
					if index >= leng:
						index = 0
				else:
					index = index - 1
					if index < 0:
						index = leng - 1

		self.setSearchIndex(index)
		self.setLoadNew(True)
		name = self.getStationName(index)
		if name.startswith("http:") and '#' in name: 
			url,name = name.split('#')
		msg = "radio.getNext index " + str(index) + " "+ name
		log.message(msg, log.DEBUG)

		return

	# Scroll through tracks by artist
	def findNextArtist(self,direction):
		self.setLoadNew(True)
		index = self.getSearchIndex()
		playlist = self.getPlayList()
		current_artist = self.getArtistName(index)

		found = False
		leng = len(playlist)
		count = leng
		while not found:
			if direction == UP:
				index = index + 1
				if index >= leng:
					index = 0
			else:
				index = index - 1
				if index < 1:
					index = leng - 1

			new_artist = self.getArtistName(index)
			if current_artist != new_artist:
				found = True

			count = count - 1

			# Prevent everlasting loop
			if count < 1:
				found = True
				index = self.current_id

		# If a Backward Search find start of this list
		found = False
		if direction == DOWN:
			self.current_artist = new_artist
			while not found:
				index = index - 1
				new_artist = self.getArtistName(index)
				if self.current_artist != new_artist:
					found = True
			index = index + 1
			if index >= leng:
				index = leng-1

		self.setSearchIndex(index)

		return

	# Input Source RADIO, NETWORK or MEDIA
	def getSourceType(self):
		return self.source.getType()

	def getNewSourceType(self):
		return self.source.getNewType()

	def getNewSourceName(self):
		return self.source.getNewName()

	def getSourceName(self):
		return self.source.getName()

	# Reload playlists flag
	def getReload(self):
		return self.reload

	# Reload (new) source
	def setReload(self,reload):
		log.message("radio.setReload " + str(reload), log.DEBUG)
		self.reload = reload

	# Reload music library flag
	def doUpdateLib(self):
		return self.updateLib

	def setUpdateLibOn(self):
		self.updateLib = True

	def setUpdateLibOff(self):
		self.updateLib = False

	# Load new track flag
	def loadNew(self):
		return self.loadnew

	# Setup load new source
	def setLoadNew(self,loadnew):
		log.message("radio.setLoadNew " + str(loadnew), log.DEBUG)
		self.loadnew = loadnew
		return

	# Load new source (from the web interface)
	def cycleWebSource(self,type):
		playlist = self.source.cycleType(type)
		log.message("radio.cycleWebSource (Web) " + playlist, log.DEBUG)
		return playlist

	# Cycle playlist (Used by vgradio)
	def cyclePlaylist(self,type):
		playlist = self.cycleWebSource(type)
		self.loadSource()
		return playlist

	# Get the Raspberry pi board version from /proc/cpuinfo
	def getBoardRevision(self):
		revision = 1
		with open("/proc/cpuinfo") as f:
			cpuinfo = f.read()
		rev_hex = re.search(r"(?<=\nRevision)[ |:|\t]*(\w+)", cpuinfo).group(1)
		rev_int = int(rev_hex,16)
		if rev_int > 3:
			revision = 2
		self.boardrevision = revision
		log.message("Board revision " + str(self.boardrevision), log.INFO)
		return self.boardrevision

	# Get the MPD port number
	def getMpdPort(self):
		port = 6600
		if os.path.isfile(MpdPortFile):
			try:
				port = int(self.execCommand("cat " + MpdPortFile) )
			except ValueError:
				port = 6600
		else:
			log.message("Error reading " + MpdPortFile, log.ERROR)

		return port

	# Get MPD version (Only get it from MPD initially)
	def getMpdVersion(self):
		if len(self.MpdVersion) < 1:
			sVersion = self.execCommand('mpd -V | grep Daemon')
			self.MpdVersion = sVersion.split()[3]
		return self.MpdVersion

	# Get options from MPD (synchronise with external mpd clients)
	def getMpdOptions(self,stats):
		try:
			random = int(stats.get("random"))
			self.random = self.convertToTrueFalse(random)

			repeat = int(stats.get("repeat"))
			self.repeat = self.convertToTrueFalse(repeat)

			consume = int(stats.get("consume"))
			self.consume = self.convertToTrueFalse(consume)

			single = int(stats.get("single"))
			self.single = self.convertToTrueFalse(single)

		except Exception as e:
			log.message("radio.getMpdOptions " + str(e), log.ERROR)
		return

	def getDisplayVolume(self):
		return volume.displayValue()

	# This is either the real MPD or Mixer volume
	# depending upon source type
	def getVolume(self):
		return volume.get()

	def getSpeechVolume(self):
		return volume.getMpdVolume()

	# Get speech volume
	def getSpeechVolume(self):
		return volume.getSpeechVolume()

	# Set volume (Called from the radio client or external mpd client via getVolume())
	def setVolume(self,new_volume):
		volume.set(new_volume)
		return volume.displayValue() 

	# Increase volume 
	def increaseVolume(self):
		return volume.increase()

	# Decrease volume 
	def decreaseVolume(self):
		return volume.decrease()

	def mute(self):
		volume.mute()

	# Unmute sound fuction, get stored volume
	def unmute(self):
		volume.unmute()

	# Return muted state muted = True
	def muted(self):
		return volume.muted()

	# Get mixer volume
	def getMixerVolume(self):
		return self.airplay.getMixerVolume()
		
	# Get mixer ID
	def getMixerID(self):
		return self.mixer_volume_id
		
	# Increase mixer volume
	def increaseMixerVolume(self):
		return self.airplay.increaseMixerVolume()

	# Decrease mixer volume
	def decreaseMixerVolume(self):
		return self.airplay.decreaseMixerVolume()

	# Return True if mixer is muted
	def mixerIsMuted(self):
		return self.airplay.mixerIsMuted()

	# Mute mixer 
	def muteMixer(self):
		return self.airplay.muteMixer()

	# Start MPD (Alarm mode)
	def startMPD(self):
		try:
			client.play()
		except Exception as e:
			log.message("radio.startMPD: " + str(e),log.ERROR)
		return

	# Stop MPD (Alarm mode)
	def stopMPD(self):
		try:
			client.stop()
		except Exception as e:
			log.message("radio.stopMPD: " + str(e),log.ERROR)
		return

	# Stop the radio 
	def stop(self):
		log.message("Stopping MPD",log.INFO)
		self.execCommand("sudo service mpd stop")

		if self.getSourceType() == self.source.AIRPLAY:
			self.stopAirplay()	

		elif self.getSourceType() == self.source.SPOTIFY:
			self.stopSpotify()	

		# Unmount shares
		self.execCommand("sudo umount /media > /dev/null 2>&1")
		self.execCommand("sudo umount /share > /dev/null 2>&1")

		log.message("Radio stopped",log.INFO)
		return

	# Shutdown the system if so configured
	def shutdown(self):
		log.message("Shutting down system ",log.INFO)
		self.execCommand("sudo shutdown -h now")

		# Exit radio
		exit(0) 


	# Get the stored volume
	def getStoredVolume(self):
		return self.getStoredInteger(VolumeFile,75)	

	# Store source index value
	def storeSourceIndex(self,index):
		self.execCommand ("echo " + str(index) + " > " + CurrentSourceFile)
		return

	# Store volume in volume file
	def storeVolume(self,volume):
		self.execCommand ("echo " + str(volume) + " > " + VolumeFile)
		return

	# Store mixer volume 
	def storeMixerVolume(self,volume):
		self.execCommand ("echo " + str(volume) + " > " + MixerVolumeFile)
		return

	# Set random on or off
	def setRandom(self,true_false,store=True):
		log.message("radio.setRandom " + str(true_false),log.DEBUG)
		try:
			if true_false:
				client.random(1)
				iValue = 1
			else:
				client.random(0)
				iValue = 0

			if store:
				self.storeOptionValue(self.menu.OPTION_RANDOM,iValue)

		except Exception as e:
			log.message("radio.setRandom " + str(e),log.ERROR)

		return true_false

	# Get random setting
	def getRandom(self):
		self.random =  self.getStoredValue(self.menu.OPTION_RANDOM)
		return self.random

	# Set repeat on or off
	def setRepeat(self,true_false):
		try:
			if true_false:
				client.repeat(1)
			else:
				client.repeat(0)

		except Exception as e:
			log.message("radio.setRepeat " + str(e),log.ERROR)

		return true_false

	# Set consume on or off
	def setConsume(self,true_false):
		try:
			if true_false:
				client.consume(1)
			else:
				client.consume(0)

		except Exception as e:
			log.message("radio.setConsume " + str(e),log.ERROR)

		return true_false

	# Set single on or off
	def setSingle(self,true_false):
		try:
			if true_false:
				client.single(1)
			else:
				client.single(0)

		except Exception as e:
			log.message("radio.setSingle " + str(e),log.ERROR)

		self.single = true_false
		return self.single

	# Get single on or off
	def getSingle(self):
		return self.single

	# Routine to get a option or setting stored in the radio lib directory
	# and store it in the options array
	def getStoredValue(self,option_index):
		value = None

		if option_index == self.menu.OPTION_RANDOM:
			randomValue = int(self.execCommand("cat " + RandomSettingFile) )
			value = self.convertToTrueFalse(randomValue)	

		elif option_index == self.menu.OPTION_TIMER:
			value = int(self.execCommand("cat " + TimerFile) )

		elif option_index == self.menu.OPTION_ALARM:
			value = self.execCommand("cat " + AlarmFile)

		if value == None:
			value = False

		return value


	# Routine to store a option or setting in the radio lib directory
	def storeOptionValue(self,option_index,value):
		log.message("radio.storeOptionValue index=" + str(option_index) \
			    + ' value=' + str(value) , log.DEBUG)
		file = ''

		if option_index == self.menu.OPTION_RANDOM:
			file = RandomSettingFile
			
		# Store value in Radio lib file
		if len(file) != 0:
			cmd = "echo " + str(value) + " > " + file
			self.execCommand (cmd)
			log.message(cmd, log.DEBUG)
		return value

	# Routine to convert true or false to 1(True) or 0(False)
	# used to store options - See storeOptionValue
	def convertToOneZero(self,true_false):
		if true_false: 
			iValue = 1
		else:	
			iValue = 0

		return iValue

	# Routine to convert 1 or 0 to True or False
	# used to get store options - See getStoredValue
	def convertToTrueFalse(self,iValue):
		if iValue == 1: 
			value = True
		else:	
			value = False

		return value

	# Repeat
	def getRepeat(self):
		return self.repeat

	# Consume
	def getConsume(self):
		return self.consume

	# Timer functions
	def getTimer(self):
		return self.timer

	def timerOff(self):
		self.timer = False
		self.timerValue = 0
		return self.timer

	def getTimerValue(self):
		return self.timerValue

	# Check has timer reached 0, if so fire an event
	def checkTimer(self):
		if self.timer and self.timerValue > 0:
			now = int(time.time())
			if now > self.timeTimer + self.timerValue * 60:
				self.event.set(self.event.TIMER_FIRED)
				self.timerOff()
		return 

	# Get the timer countdown value
	def getTimerCountdown(self):
		now = int(time.time())
		return  self.timeTimer + self.timerValue * 60  - now


	# Increment timer.   
	def incrementTimer(self):
		inc = 1
		if self.timerValue == 0:
			self.timerValue = self.getStoredTimer()
		if self.timerValue > 120:
			inc = 10
		self.timerValue += inc
		if self.timerValue > self.ONEDAYMINS:
			self.timerValue = self.ONEDAYMINS
		self.timeTimer = int(time.time())
		self.timer = True
		self.storeTimer(self.timerValue)
		return self.timerValue

	# Increment timer and activate
	def decrementTimer(self):
		dec = 1
		if self.timerValue > 120:
			dec = 10
		self.timerValue -= dec
		if self.timerValue < 0:
			self.timerValue = 0	
			self.timer = False
		else:
			self.timer = True
		self.timeTimer = int(time.time())
		self.storeTimer(self.timerValue)
		return self.timerValue

	# Get the stored timer value
	def getStoredTimer(self):
		return self.getStoredInteger(TimerFile,0)	

	# Store timer time in timer file
	def storeTimer(self,timerValue):
		self.execCommand ("echo " + str(timerValue) + " > " + TimerFile)
		return timerValue

	# Radio Alarm Functions
	def alarmActive(self):
		alarmActive = False
		if self.alarmType != self.ALARM_OFF:
			alarmActive = True
		return alarmActive

	# Cycle through alarm types
	def alarmCycle(self,direction):
		if direction == UP:
			self.alarmType += 1
		else:
			self.alarmType -= 1

		if self.alarmType > self.ALARM_LAST:
			self.alarmType = self.ALARM_OFF
		elif self.alarmType < self.ALARM_OFF:
			self.alarmType = self.ALARM_LAST

		if self.alarmType > self.ALARM_OFF:
			self.alarmTime = self.getStoredAlarm()
		
		sType,sHours,sMinutes = self.alarmTime.split(':')
		hours = int(sHours)
		minutes = int(sMinutes)
		self.alarmTime = '%d:%d:%02d' % (self.alarmType,hours,minutes)
		self.storeAlarm(self.alarmTime)

		return self.alarmType

	# Switch off the alarm unless repeat or days of the week
	def alarmOff(self):
		if self.alarmType == self.ALARM_ON:
			self.alarmType = self.ALARM_OFF
		return self.alarmType

	# Increment alarm time
	def incrementAlarm(self,inc):
		sType,sHours,sMinutes = self.alarmTime.split(':')
		hours = int(sHours)
		minutes = int(sMinutes) + inc
		if minutes >= 60:
			minutes = minutes - 60 
			hours += 1
		if hours >= 24:
			hours = 0
		self.alarmTime = '%d:%d:%02d' % (self.alarmType,hours,minutes)
		self.storeAlarm(self.alarmTime)
		return '%d:%02d' % (hours,minutes) 

	# Decrement alarm time
	def decrementAlarm(self,dec):
		sType,sHours,sMinutes = self.alarmTime.split(':')
		hours = int(sHours)
		minutes = int(sMinutes) - dec
		if minutes < 0:
			minutes = minutes + 60 
			hours -= 1
		if hours < 0:
			hours = 23
		self.alarmTime = '%d:%d:%02d' % (self.alarmType,hours,minutes)
		self.storeAlarm(self.alarmTime)
		return '%d:%02d' % (hours,minutes) 

	# Fire alarm if current hours/mins matches time now
	def checkAlarm(self):

		fireAlarm = False
		if self.alarmType > self.ALARM_OFF:
			sType,sHours,sMinutes = self.alarmTime.split(':')
			type = int(sType)
			hours = int(sHours)
			minutes = int(sMinutes)
			t1 = datetime.datetime.now()
			t2 = datetime.time(hours, minutes)
			weekday =  t1.today().weekday()

			if t1.hour == t2.hour and t1.minute == t2.minute and not self.alarmTriggered:
				# Is this a weekday
				if type == self.ALARM_WEEKDAYS and weekday < 5: 
					fireAlarm = True
				elif type < self.ALARM_WEEKDAYS:	
					fireAlarm = True

				if fireAlarm:
					self.alarmTriggered = fireAlarm 
					if type == self.ALARM_ON:
						self.alarmOff()
					log.message("radio.larmFired type " + str(type), log.DEBUG)
					self.event.set(self.event.ALARM_FIRED)
			else:
				self.alarmTriggered = False 

		return  fireAlarm

	# Get the stored alarm value
	def getStoredAlarm(self):
		alarmValue = '' 
		if os.path.isfile(AlarmFile):
			try:
				alarmValue = self.execCommand("cat " + AlarmFile)
			except ValueError:
				alarmValue = "0:7:00"
		else:
			log.message("Error reading " + AlarmFile, log.ERROR)
		return alarmValue

	# Store alarm time in alarm file
	def storeAlarm(self,alarmString):
		self.execCommand ("echo " + alarmString + " > " + AlarmFile)
		return

	# Get the actual alarm time
	def getAlarmTime(self):
		sType,sHours,sMinutes = self.alarmTime.split(':')
		hours = int(sHours)
		minutes = int(sMinutes)
		return '%d:%02d' % (hours,minutes) 
		
	# Get the alarm type
	def getAlarmType(self):
		if self.alarmType > self.ALARM_LAST:
			self.alarmType = self.ALARM_OFF
		return  self.alarmType

	# Cycle the alarm time setting
	def cycleAlarmValue(self, direction, option_index):
		value = 1 	# Set minutes

		# Set hours
		if option_index == self.menu.OPTION_ALARMSETHOURS:
			value = 60
		if direction == UP:
			self.incrementAlarm(value)
		else:
			self.decrementAlarm(value)
		return

	# Get the stored streaming value
	def getStoredStreaming(self):
		streamValue = "off" 
		streaming = False
		if os.path.isfile(StreamFile):
			try:
				streamValue = self.execCommand("cat " + StreamFile)
			except ValueError:
				streamValue = "off"
		else:
			log.message("Error reading " + StreamFile, log.ERROR)

		if streamValue == "on":
			streaming = True	
		else:
			streaming = False	

		return streaming

	# Toggle streaming on off
	# Stream number is 2 
	def toggleStreaming(self):
		if self.streamingAvailable():
			if self.streaming:
				self.streamingOff()
			else:
				self.streamingOn()
		else:
			self.streaming = False
			self.storeStreaming("off")

		return self.streaming

	# Switch on Icecast2 streaming
	def streamingOn(self):
		output_id = 2
		self.streaming = False
		if os.path.isfile(Icecast):
			self.execCommand("service icecast2 start")
			self.execMpcCommand("enable " + str(output_id))
			self.storeStreaming("on")
			self.streaming = True
			self.streamingStatus()
		return self.streaming

	# Switch off Icecast2 streaming
	def streamingOff(self):
		output_id = 2
		self.streaming = False
		if os.path.isfile(Icecast):
			self.execMpcCommand("disable " + str(output_id))
			self.execCommand("service icecast2 stop")
			self.storeStreaming("off")
			self.streamingStatus()
		return self.streaming

	# Display streaming status
	def streamingStatus(self):
		status = self.execCommand("mpc outputs | grep -i stream")
		if len(status)<1:
			status = "No Icecast streaming"
		log.message(status, log.INFO)
		return

	# Check if icecast streaming installed
	def streamingAvailable(self):
		fpath = "/usr/bin/icecast2"
		return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

	# Store stram on or off in streaming file
	def storeStreaming(self,onoff):
		self.execCommand ("echo " + onoff + " > " + StreamFile)
		return

	# Get the streaming value
	def getStreaming(self):
		return self.streaming

	# Option changed 
	def optionChanged(self):
		return self.option_changed

	# Indicate option changed (See radiod.py)
	def optionChangedTrue(self):
		self.option_changed = True
		return

	# Clear option changed (See radiod.py)
	def optionChangedFalse(self):
		self.option_changed = False
		return

	
	# Execute system command
	def execCommand(self,cmd):
		p = os.popen(cmd)
		return  p.readline().rstrip('\n')

	# Execute MPC comnmand via OS
	# Some commands are easier using mpc and don't have 
	# an effect adverse on performance
	def execMpcCommand(self,cmd):
		return self.execCommand(Mpc + " " + cmd)

	# Get the ID  of the currently playing track or station ID
	def getCurrentID(self):
		try:
			currentsong = self.getCurrentSong()
			pos = currentsong.get("pos")
			if pos == None:
				currentid = self.current_id
			else:
				currentid = int(pos) + 1

			# Only update if the Current ID has changed
			if self.current_id != currentid:
				log.message("radio.getCurrentID New ID " \
						+ str(currentid), log.DEBUG)
				self.current_id = currentid
				# Write to current ID file
				self.execCommand ("echo " + str(currentid) + " > " \
							+ self.current_file)
				self.search_index = self.current_id - 1
				self.getIdError = False
				self.event.set(self.event.MPD_CLIENT_CHANGE)
				self.setInterrupt() # Not being seen quick enough To Do
				
		except Exception as e:
			log.message("radio.getCurrentID: " + str(e),log.ERROR)
			if not self.getIdError:
				log.message("radio.getCurrentID failed ", log.ERROR)
				self.getIdError = True

		return self.current_id

	# Check to see if an error occured
	def gotError(self):
		return self.error

	# Get the error string if a bad channel
	def getErrorString(self):
		return self.errorStr

	# See if any error. Return True if error
	def checkStatus(self):
		try:
			status = client.status()
			errorStr = str(status.get("error"))
			if  errorStr != "None":
				if not self.error:
					log.message("checkStatus: "+ errorStr, log.DEBUG)
				self.error = True
				self.errorStr = errorStr
			else:
				errorStr = ''
				self.error = False
		except Exception as e:
			log.message("checkStatus exception: " + str(e), log.ERROR)
			self.error = True

		return self.error

	# Get the progress of the currently playing track
	def getProgress(self):
		elapsedTime = None
		durationTime = None
		elapsed = None
		duration = None
		percentage = None

		self.pingMPD()
		try:
			status = client.status()
			playtime = status.get("time")
			if playtime != None:
				elapsed,duration = playtime.split(':') 
				elapsed = int(elapsed)
				duration = int(duration)
			else:
				elapsed = 0
				duration = 0

			if elapsed > 0:
				elapsedMins = elapsed/60
				elapsedSecs = elapsed % 60
			else:
				elapsedMins = 0
				elapsedSecs = 0

			elapsedTime ="%d:%02d" % (elapsedMins,elapsedSecs)
			if duration > 0:
				durationMins = duration/60
				durationSecs = duration % 60
			else:
				durationMins = 0
				durationSecs = 0

			durationTime ="%d:%02d" % (durationMins,durationSecs)
			percent = 0
			if elapsed > 0 and duration > 0:
				percent = 100 * elapsed/duration
			percentage = "%d" % (percent) 

		except Exception as e:
			log.message("radio.getProgress " + str(e), log.ERROR)
			
		progress = str(elapsedTime) + ' ' +  str(durationTime) \
				+ ' (' + str(percentage) + '%)' 
		return progress

	# Set the new ID  of the currently playing track or station (Also set search index)
	def setCurrentID(self,newid):
		log.message("radio.setCurrentID " + str(newid), log.DEBUG)
		self.current_id = newid

		# If an error (-1) reset to 1
		if self.current_id <= 0:
			self.current_id = 1
			log.message("radio.setCurrentID reset to " + str(self.current_id), log.DEBUG)

		# Don't allow an ID greater than the playlist length
		if self.current_id >= len(self.searchlist):
			self.current_id = len(self.searchlist)
			log.message("radio.setCurrentID reset to " + str(self.current_id), log.DEBUG)
		
		self.search_index = self.current_id - 1
		self.execCommand ("echo " + str(self.current_id) + " > " + self.current_file)
		return self.current_id

	# Get stats array
	def getStats(self):
		self.pingMPD()
		try:
			stats = client.status()
			self.stats = stats # Only if above call works
			self.getMpdOptions(self.stats)	# Get options 

		except Exception as e:
			log.message("radio.getStats " + str(e), log.ERROR)

		return self.stats

	# Get current song information (Only for use within this module)
	def getCurrentSong(self):
		self.pingMPD()
		try:
			currentsong = client.currentsong()
			self.currentsong = currentsong
		except:
			# Try re-connect and status
			try:
				currentsong = client.currentsong()
				self.currentsong = currentsong
			except Exception as e:
				log.message("radio.getCurrentSong failed: " + str(e), log.ERROR)
		return self.currentsong

	# Get station name by index from search list
	def getSearchName(self):
		name = ''
		try:
			name = self.getStationName(self.search_index) 

		except Exception as e:
			log.message("radio.getSearchName: " + str(e), log.DEBUG)
			name = "Bad stream (" + str(self.current_id) + ")"

		return name

	# Get the currently playing radio station name from mpd 
	def getCurrentStationName(self):
		currentsong = self.getCurrentSong()
		try:
			name = str(currentsong.get("name"))
		except:
			name = ''

		if name == 'None':
			name = ''

		if len(name) > 0:
			name = translate.escape(name)

		# If error occured
		if self.checkStatus(): 
			time.sleep(0.5)
		return name

	# Get the title of the currently playing station or track from mpd 
	def getCurrentTitle(self):
		source_type = self.source.getType()
		name = '' 

		try:
			currentsong = self.getCurrentSong()
			title = str(currentsong.get("title"))
		except:
			title = ''

		if title == 'None':
			title = ''
		
		if len(title) > 0:
			title = translate.escape_translate(title)

		if self.channelChanged: 
			self.channelChanged = False
			if self.config.verbose():
				if source_type == self.source.RADIO:
					sSource = "Station "
				else: 
					sSource = "Track "
		
		# Log only if different  
		if title != self.stationTitle and len(title) > 0:
			self.event.set(self.event.MPD_CLIENT_CHANGE)
			log.message ("Title: " + str(title), log.DEBUG)	
			if source_type == self.source.MEDIA:
				album = self.getCurrentAlbum()
				if len(album) > 0:
					log.message ("Album: " + album, log.DEBUG)	
			
		self.stationTitle = title
		return title

	# Get the name of the current artist mpd (Music library only)
	def getCurrentArtist(self):
		try:
			currentsong = self.getCurrentSong()
			title = str(currentsong.get("title"))
			title = translate.escape(title)
			artist = str(currentsong.get("artist"))
			if str(artist) == 'None':
				artist = "Unknown artist"
			self.artist = artist
		except:
			log.message ("radio.getCurrentArtist error", log.ERROR)	
		return self.artist

	# Get the file name of the current track (Used by gradio to extract artwork)
	def getFileName(self):
		filename = ''
		try:
			currentsong = self.getCurrentSong()
			filename = str(currentsong.get("file"))
			if str(filename) == 'None':
				filename = ''
		except:
			log.message ("radio.getFileName error", log.ERROR)	
		return filename

	# Get the name of the current artist mpd (Music library only)
	def getCurrentAlbum(self):
		try:
			currentsong = self.getCurrentSong()
			album = str(currentsong.get("album"))
			if str(album) == 'None':
				album = ""
			else:
				album = translate.escape(album)
			self.album = album
		except:
			log.message ("radio.getCurrentAlbum error", log.ERROR)	
		return self.album

	# Get bit rate - aways returns 0 in diagnostic mode 
	def getBitRate(self):
		try:
			status = client.status()
			bitrate = int(status.get('bitrate'))
		except:
			bitrate = -1
		return bitrate

	# Get the last ID stored in /var/lib/radiod
	# The current_file is either current_station or current_track
	def getStoredID(self,current_file):
		current_id = self.getStoredInteger(current_file,1)	
		if current_id <= 0:
			current_id = 1
		return current_id

	# Get the currently stored source index
	def getStoredSourceIndex(self):
		return self.getStoredInteger(CurrentSourceFile,0)	

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

	# Change radio station up
	def channelUp(self):
		if self.error:
			self.clearError()

		if volume.muted():
			volume.unmute()
		new_id = self.getCurrentID() + 1
		log.message("radio.channelUp " + str(new_id), log.DEBUG)
		if new_id > len(self.searchlist):
			new_id = 1
			self.play(new_id)
		else:
			try:
				client.next()
			except:
				log.message("radio.channelUp error", log.ERROR)
				
		new_id = self.getCurrentID()
		self.setCurrentID(new_id)

		self.channelChanged = True
		return new_id

	# Change radio station down
	def channelDown(self):
		if self.error:
			self.clearError()
		if self.muted():
			self.unmute()
		new_id = self.getCurrentID() - 1
		log.message("radio.channelDown " + str(new_id), log.DEBUG)
		if new_id <= 0:
			new_id = len(self.searchlist)
			self.play(new_id)
		else:
			try:
				client.previous()
			except:
				log.message("radio.channelDown error", log.ERROR)

		new_id = self.getCurrentID()
		self.setCurrentID(new_id)

		self.channelChanged = True
		return new_id

	# Cycle the input source and/or playlist (Reload is done when Reload requested)
	def cycleSource(self, direction):
		
		sSource = self.source.cycle(direction)
		self.newType =  self.source.getNewType() 

		self.setReload(True)	
		log.message("Selected source " + sSource, log.DEBUG)

		return self.newType
 	
	# Get the new source name (radio, playlist or Airplay)
	def getNewSourceName(self):
		return self.source.getNewDisplayName()

	# This routine reloads sources/playlists  
	def getSources(self):
		log.message("radio.getSources", log.DEBUG)
		try:
			sources =  self.source.load()
		except Exception as e:
			log.message("radio.getSources " + str(e), log.ERROR)
		return sources

	# Load source. Either radio, media or airplay
	def loadSource(self):
		# Get the source type radio,media or airplay
		self.getSources()
		source_type = self.source.getNewType()
		type_name = self.source.getNewTypeName()
		source_name = self.source.getNewName()

		log.message("radio.loadSource " + source_name + ' ' + type_name, log.DEBUG)

		# Stop the currently playing source
		if source_type == self.source.RADIO or source_type == self.source.MEDIA:

			if self.airplay.isRunning():
				self.stopAirplay()

			if self.spotify.isRunning():
				self.stopSpotify()

		else:
			self.stopMPD()

		if source_type == self.source.RADIO:
			self.current_file = CurrentStationFile
			self.setRandom(False,store=False)
			self.setConsume(False)
			self.setRepeat(False)
			self.setSingle(False)
			self.loadPlaylist()
		
		elif source_type == self.source.MEDIA:
			self.current_file = CurrentTrackFile
			self.mountAll()
			self.loadPlaylist()
			self.execMpcCommand("update &")

			# If the playlist is empty then load media
			# Else simply load the playlist
			if self.getCurrentID() < 1:
				self.updateLibrary()
				self.play(1)
			self.setSingle(False)

		elif source_type == self.source.AIRPLAY:
			if not self.airplay.isRunning():
				self.startAirplay()

		elif source_type == self.source.SPOTIFY:
			if not self.spotify.isRunning():
				self.startSpotify()

		if source_type == self.source.RADIO or source_type == self.source.MEDIA:
			# Create a list for search
			self.searchlist = self.createSearchList()
			self.current_id = self.getStoredID(self.current_file)
			self.search_index = self.current_id - 1
			self.play(self.current_id)

		# Set volume
		volume.set(volume.getStoredVolume())

		# Save the new source type and index
		self.source_index = self.source.setNewType()
		self.source.setIndex(self.source_index)
		self.storeSourceIndex(self.source_index)
		return

	# Load playlist (Media or Radio)
	def loadPlaylist(self):
		source_type = self.source.getNewType()
		playlist = self.source.getNewName()

		msg = "Load playlist " + playlist + " type " + str(source_type)
		log.message(msg, log.DEBUG)

		try:
			client.clear()
			client.load(playlist)
			if len(client.playlist()) < 1:
				log.message("Playlist " + playlist + " is empty", log.ERROR)
				##self.currentID = 0

		except:
			log.message("radio.loadPlaylist failed to load " + playlist, log.ERROR)
		return


	# Get the playlist dictionary
	def getPlaylists(self):
		return self.source.getPlaylists()		

	# Update music library 
	def updateLibrary(self):

		if len(client.playlist()) < 1:
			status = client.status()
			try:
				update_id = int(status.get("updating_db"))
				self.loading_DB = True
			except:
				update_id = 0
			#log.message("radio.updateLibrary updating_db " + str(update_id) \
			#		+ " loading_DB " + str(self.loading_DB), log.DEBUG)
			if update_id < 1:
				self.mountAll()
				log.message("Updating MPD database ", log.DEBUG)
				self.execMpcCommand("update")
		else:
			self.loading_DB = False
		self.setUpdateLibOff() # Check TO DO
		return

	# Play a new track using search index
	def playNew(self,index):
		self.setLoadNew(False)
		self.play(index + 1)
		return

	# Play a track number  (Starts at 1)
	def play(self,number):
		log.message("radio.play " + str(number), log.DEBUG)
		log.message("radio.play Playlist len " + str(len(self.searchlist)), log.DEBUG)
		if number > 0 and number <= len(self.searchlist):
			self.current_id = number
			self.setCurrentID(self.current_id)
		else:	
			log.message("play invalid station/track number "+ str(number), log.ERROR)
			self.setCurrentID(1)

		# Client play function starts at 0 not 1
		log.message("Play station/track number "+ str(self.current_id), log.DEBUG)
		try:
			client.play(self.current_id-1)
			self.checkStatus()
		except Exception as e:
			log.message("radio.play FAILED id=" + str(self.current_id), log.ERROR)
			log.message("radio.play " + str(e), log.ERROR)
			self.current_id += 1
			self.clearErrorString() # Clear any error message
		#self.clearErrorString() # Clear any error message
		return self.current_id

	# Clear streaming and other errors
	def clearError(self):
		log.message("radio.clearError", log.DEBUG)
		try:
			client.clearerror()
			self.error = False 
		except:
			log.message("radio.clearError failed", log.ERROR)
		return

	def clearErrorString(self):
		self.errorStr = ''
		return

	# Get list of tracks or stations
	def getPlayList(self):
		return self.searchlist

	# Get playlist length
	def getPlayListLength(self):
		return len(self.searchlist)

	# Create search list of tracks or stations
	def createSearchList(self):
		log.message("radio.createSearchList", log.DEBUG)
		list = []
		line = ""
		cmd = "playlist"	
		p = os.popen(Mpc + " " + cmd)
		while True:
			line =  p.readline().strip('\n')
			if line.__len__() < 1:
				break
			line = translate.escape(line)
			if line.startswith("http:") and '#' in line: 
				url,line = line.split('#')
			list.append(line)
		
		if list == None:
			self.searchlist = []
		else:
			self.searchlist = list

		log.message("radio.createSearchList length " + str(len(self.searchlist)), log.DEBUG)
		return self.searchlist

	# Get the length of the current list
	def getListLength(self):
		return len(self.searchlist)	

	# Display artist True or False
	def displayArtist(self):
		return self.display_artist

	def setDisplayArtist(self,dispArtist):
		self.display_artist = dispArtist

	# Set Search index
	def getSearchIndex(self):
		return self.search_index

	def setSearchIndex(self,index):
		self.search_index = index
		return

	# Get Radio station name by Index (Used in search routines)
	def getStationName(self,index):
		stationName = ""
		source_type = self.source.getType()

		if source_type == self.source.RADIO:
			stationName = "No stations found"
		else:
			stationName = "No tracks found"
		try:
			if len(self.searchlist) > 0:
				stationName = self.searchlist[index] 

			if stationName != self.stationName and len(stationName) > 0:
				log.message ("Station " + str(index+1) + ": " \
					+ str(stationName), log.DEBUG)	
				self.stationName = stationName
		except:
			log.message("radio.getStationName bad index " + str(index), log.ERROR)
		return stationName

	# Get track name by Index
	def getTrackNameByIndex(self,index):
		if len(self.searchlist) < 1:
			track = "No tracks"
		else:
			sections = self.searchlist[index].split(' - ')
			leng = len(sections)
			if leng > 1:
				track = sections[1]
			else:
				track = "No track"
			track = translate.escape(track)
		if str(track) == 'None':
			track = "Unknown track"
		return track

	# Get artist name by Index
	def getArtistName(self,index):
		if len(self.searchlist) < 1:
			artist = "No playlists"
		else:
			sections = self.searchlist[index].split(' - ')
			leng = len(sections)
			if leng > 1:
				artist = sections[0]
			else:
				artist = "Unknown artist"
			artist = translate.escape(artist)
		return artist

	# Version number
	def getVersion(self):
		return __version__

	# Set an interrupt received
	def setInterrupt(self):
		self.interrupt = True
		return

	# See if interrupt received from IR remote control
	def getInterrupt(self):
		interrupt = self.interrupt or self.airplay.getInterrupt()
		self.interrupt =  False
		return interrupt

	# Start Airplay
	def startAirplay(self):
		self.execMpcCommand("stop")
		started = self.airplay.start()
		log.message("radio.startAirplay " + str(started), log.DEBUG)
		if not started:
			log.message("radio.startAirplay FAILED" , log.ERROR)
			self.execMpcCommand("play")
		return started

	# Stop Airplay
	def stopAirplay(self):
		self.airplay.stop()
		return

	# Get Airplay information
	def getAirplayInfo(self):
		return self.airplay.info()

	# Start Spotify
	def startSpotify(self):
		self.execMpcCommand("stop")
		log.message("radio.startSpotify ", log.DEBUG)
		started = self.spotify.start()
		if not started:
			log.message("radio.startSpotify FAILED" , log.ERROR)
			self.execMpcCommand("play")
		return started
	
	# Stop Spotify
	def stopSpotify(self):
		log.message("radio.stopSpotify ", log.DEBUG)
		self.spotify_runnig = self.spotify.stop()
		return

	# Get Spotify current stream title
	def getSpotifyInfo(self):
		return self.spotify.getInfo()

	# Mount the USB stick
	def mountUsb(self):
		usbok = False
		if os.path.exists("/dev/sda1"):
			device = "/dev/sda1"
			usbok = True

		elif os.path.exists("/dev/sdb1"):
			device = "/dev/sdb1"
			usbok = True

		if usbok:
			if not os.path.ismount('/media'):
				log.message("Mounting " + device, log.DEBUG)
				self.execCommand("/bin/mount -o rw,uid=1000,gid=1000 " \
					+ device + " /media")
				log.message(device + " mounted on /media", log.DEBUG)
			else:
				log.message("Media already mounted", log.DEBUG)
		else:
			msg = "No USB stick found!"
			log.message(msg, log.WARNING)
		return

	# Mount any remote network drive
	def mountShare(self):
		if os.path.exists("/var/lib/radiod/share"):
			myshare = self.execCommand("cat /var/lib/radiod/share")
			if myshare[:1] != '#':
				if not os.path.ismount('/share'):
					self.execCommand(myshare)
					log.message(myshare,log.DEBUG)
				else:
					log.message("Network share already mounted", log.DEBUG)
		return

	# Remount media on /var/lib/mpd/music
	def mountAll(self):
		self.unmountAll()
		self.mountUsb()
		self.mountShare()
		return

	# Unmount all drives
	def unmountAll(self):
		if os.path.ismount('/media'):
			# Un-mount USB stick
			self.execCommand("sudo /bin/umount /media 2>&1 >/dev/null")
		if os.path.ismount('/share'):
			self.execCommand("sudo /bin/umount /share 2>&1 >/dev/null")
		return

	# Pause the client for speach facility (See message_class)
	def clientPause(self):
		client.pause()
		return

	# Restart the client after speach finished
	def clientPlay(self):
		client.play()
		return

	# Get language text
	def getLangText(self,label):
		return language.getText(label)
	
	# Detect audio error
	def audioError(self):
		return self.audio_error

	def updatingDB(self):
		return self.loading_DB

	# Toggle option value
	def toggleOptionValue(self,option_index):

		log.message("radio.toggleValue index " + str(option_index), log.DEBUG)
		if option_index == self.menu.OPTION_RANDOM:
			value = self.toggle(self.random)
			self.setRandom(value)
			self.random = value
			if self.random:
				iValue = 1
			else:
				iValue = 0
			self.storeOptionValue(self.menu.OPTION_RANDOM,iValue)

		elif option_index == self.menu.OPTION_CONSUME:
			value = self.toggle(self.consume)
			self.consume = value
			self.setConsume(value)

		elif option_index == self.menu.OPTION_REPEAT:
			value = self.toggle(self.repeat)
			self.repeat = value
			self.setRepeat(value)

		elif option_index == self.menu.OPTION_SINGLE:
			value = self.toggle(self.single)
			self.single = value
			self.setSingle(value)

		elif option_index == self.menu.OPTION_RELOADLIB:
			value = self.toggle(self.reloadlib)
			self.reloadlib = value

		elif option_index == self.menu.OPTION_WIFI:
			value = self.toggle(self.setup_wifi)
			self.setup_wifi = value

		elif option_index == self.menu.OPTION_STREAMING:
			value = self.toggle(self.streaming)
			self.streaming = value	
			if self.streaming:
				self.streamingOn()
			else:
				self.streamingOff()

		else:
			value = False

		return value

	# Toggle between True and False
	def toggle(self,option_value):
		if option_value:
			option_value = False
		else:
			option_value = True
		return option_value

	# Translate on/off (Used by gradio)
	def setTranslate(self,true_false):
		log.message("setTranslate " + str(true_false), log.DEBUG)
		translate.setTranslate(true_false)

	# Return option value indexed by menu class options
	def getOptionValue(self,option_index):
			
		if option_index == self.menu.OPTION_RANDOM:
			value = self.random

		elif option_index == self.menu.OPTION_CONSUME:
			value = self.consume

		elif option_index == self.menu.OPTION_REPEAT:
			value = self.repeat

		elif option_index == self.menu.OPTION_SINGLE:
			value = self.single

		elif option_index == self.menu.OPTION_RELOADLIB:
			value = self.reloadlib

		elif option_index == self.menu.OPTION_WIFI:
			value = self.setup_wifi

		elif option_index == self.menu.OPTION_STREAMING:
			value = self.streaming

		elif option_index == self.menu.OPTION_ALARM:
			value = self.getAlarmType()

		elif option_index == self.menu.OPTION_ALARMSETHOURS \
				or option_index == self.menu.OPTION_ALARMSETMINS:
			value = self.getAlarmTime()

		elif option_index == self.menu.OPTION_TIMER:
			value = self.getTimerCountdown()

		else: 	
			value = False

		return value

# End of Radio Class

### Test routine ###
if __name__ == "__main__":
	print "Test radio_class.py"
	radio = Radio()
	print "MPD version",radio.getMpdVersion() 
	radio.mountUsb()
	print  "Version",radio.getVersion()
	print "Board revision", radio.getBoardRevision()
	iColor = radio.config.getBackColor('bg_color')
	colorName = config.getBackColorName(iColor)
	print 'bg_color',colorName, iColor

	# Start radio and load the radio stations
	i2c_address = radio.config.getI2Caddress()
	print "I2C address", hex(i2c_address)
	radio.start()
	radio.loadSource()
	radio.play(1)
	current_id = radio.getCurrentID()
	index = current_id - 1
	print "Current ID ", current_id 
	print "Station",current_id,":", radio.getStationName(index)
	print "Bitrate", radio.getBitRate()

	# Test volume controls
	print "Stored volume", radio.getStoredVolume()
	radio.setVolume(15)
	radio.increaseVolume()
	radio.decreaseVolume()
	radio.getVolume()
	time.sleep(5)
	print "Mute"
	radio.mute()
	time.sleep(3)
	print "Unmute"
	radio.unmute()
	print "Volume", radio.getVolume()
	time.sleep(5)
	# Test channel functions
	current_id = radio.channelUp()
	print "Channel up"
	index = current_id - 1
	print "Station",current_id,":", radio.getStationName(index)
	time.sleep(5)
	current_id = radio.channelDown()
	print "Channel down"
	index = current_id - 1
	print "Station",current_id,":", radio.getStationName(index)

	# Check state
	#print "State  " +  radio.getState()

	# Check timer
	print "Set Timer 1 minute"
	radio.storeTimer(1)

	# Exit 
	print "Exit test"
	sys.exit(0)
	
# End of __main__ routine

