#!/usr/bin/env python
#
# Raspberry Pi Radio daemon
#
# $Id: radiod.py,v 1.213 2020/04/26 09:10:40 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#	    The authors shall not be liable for any loss or damage however caused.
#

from constants import *
import os,sys
import time
import signal
import socket
import datetime
from time import strftime

import pdb
# To set break-point: pdb.set_trace()

from display_class import Display
from log_class import Log
from radio_class import Radio
from radio_daemon import Daemon
from event_class import Event
from message_class import Message
from menu_class import Menu
from rss_class import Rss
from translate_class import Translate

# For retro radio only
from status_led_class import StatusLed

translate = Translate()
radio = None
event = None
message = None
statusLed = None
log = Log()
display = Display(translate)
menu = Menu()
rss = Rss(translate)
_connecting = False

# Signal SIGTERM handler
def signalHandler(signal,frame):
	global display
	global radio
	global log
	pid = os.getpid()

	# Switch on red LED
	statusLed.set(StatusLed.ERROR)

	log.message("Radio stopped, PID " + str(pid), log.INFO)
	radio.setInterrupt()
	display.clear()
	display.out(2,"")
	if display.getLines() > 2:
		display.out(3,"")
		display.out(4,"")
	display.out(1,"Radio stopped")

	radio.stop()
	statusLed.set(StatusLed.CLEAR)
	print "\nRadio stopped"
	sys.exit(0)

# No interrupt
def no_interrupt():
	return False

# Scrolling LCD display interrupt routine
def interrupt():
	global display
	global radio
	global menu
	global message
	
	source_type = radio.getSourceType()
	menu_mode = menu.mode()

	interrupt = event.detected() or radio.getInterrupt()

	if interrupt:
		event_type = event.getType()
		event_name = event.getName()
		if event_type > 0:
			log.message('radiod.py Event detected ' + event_name + ' type ' \
					 + str(event_type), log.DEBUG)
		else:
			interrupt = False

	# Rapid display of media play progress and time
	else:
		if display.getLines() > 2:
			if source_type == radio.source.MEDIA:
				if display.getDelay() > 0:
					displayVolume(display, radio)
					time.sleep(0.1)
				else:
					if menu_mode != menu.MENU_INFO:
						display.out(4,radio.getProgress())
			else:
				displayVolume(display, radio)

				# Rapid display of time if seconds configured
				if message.get('date_time').count(':') > 1 \
					 	and menu_mode == menu.MENU_TIME\
					 	and menu_mode == menu.MENU_RSS:
					displayTimeDate(display,radio,message)
		else:
			if display.getDelay() > 0:
				displayVolume(display, radio)
				time.sleep(0.1)

	if display.hasButtons():
		display.checkButton()

	return interrupt

# Daemon class
class MyDaemon(Daemon):

	def run(self):
		signal.signal(signal.SIGTERM,signalHandler)
		signal.signal(signal.SIGHUP,signalHandler)
		log.init('radio')
		self.process()

	# Main processing loop
	def process(self):
		global event
		global radio
		global message
		global statusLed

		event = Event()	# Must be initialised here

		# Set up radio
		radio = Radio(menu,event,translate)
		if radio.config.logTruncate():
			log.truncate()
			log.message("Truncated log file",log.DEBUG)
		log.message("===== Starting radio =====",log.INFO)
		message = Message(radio,display,translate)

		# Set up status Led (Retro Radio only)
		statusLed = statusLedInitialise(statusLed)
		
		# Initialise display. The Adafruit RGB plate needs the 
		# event routine to be passed to it to handle its buttons
		display.init(callback = event)
		nlines = display.getLines()
		displayStartup(display,radio)

		# LCDs option to switch off translation
		translate_lcd = radio.config.getTranslate()
		radio.translate.setTranslate(translate_lcd)

		# For non-English  Romanize (Convert to Latin characters)
		romanize = radio.config.getRomanize()
		radio.setRomanize(romanize)  # Switch Romanisation on/off
		##rss.setRomanize(romanize)  # Switch Romanisation on/off

		ipaddr = waitForNetwork(radio,display)
		# Start radio and load source (radio, media or airplay)
		display.out(2,"Starting MPD")
		radio.start()

		# Wait for network
		if nlines > 2:
			line = 3
		else: 
			line = 2

		if len(ipaddr) < 1:
			# Switch to MEDIA if no IP address
			display.out(line,"No network")
			radio.cycleWebSource(radio.source.MEDIA)
		else:
			msg = "IP " + ipaddr
			log.message(msg, log.INFO)
			display.out(line,msg)

		time.sleep(1.25)	# Allow time to display IP address

		loadSource(display,radio)
		current_id = radio.getCurrentID()
		radio.play(current_id)

		progcall = str(sys.argv)
		log.message("Radio " +  progcall + " Version " + radio.getVersion(), log.INFO)
		log.message('Radio running pid ' + str(os.getpid()), log.INFO)

		statusLed.set(StatusLed.NORMAL)
		display.clear()	# Clear 

		# Main processing loop
		while True:
	 	    try:

			menu_mode = menu.mode()

			if radio.doUpdateLib():
				updateLibrary(display,radio,message)
				radio.play(1)

			elif menu_mode == menu.MENU_TIME:
				displayTimeDate(display,radio,message)
				if radio.muted():
					displayVolume(display,radio)
				else:
					displayCurrent(display,radio,message)

			elif menu_mode == menu.MENU_SEARCH:
				displaySearch(display,menu,message)

			elif menu_mode == menu.MENU_SOURCE:
				displaySource(display,radio,menu,message)

			elif menu_mode == menu.MENU_OPTIONS:
				displayOptions(display,radio,menu,message)

			elif menu_mode == menu.MENU_RSS:
				if display.hasScreen():
					displayRss(display,radio,message,rss)
				else:
					menu.set(menu.MENU_TIME) # Skip RSS

			elif menu_mode == menu.MENU_INFO:
				displayInfo(display,radio,message)

			elif menu_mode == menu.MENU_SLEEP:
				displaySleep(display,radio)

			# Check if the timer has expired (if so it sets an event)
			radio.checkTimer()

			# Check if the alarm has triggered (if so it sets an event)
			radio.checkAlarm()

			# If the display has buttons check if pressed (Generates an event)
			if display.hasButtons():
				display.checkButton()

			# If an event was detected go handle it
			if event.detected():
				handleEvent(event,display,radio,menu)
			else:
				# Keep the connection to MPD alive
				radio.keepAlive(10)

				# This delay must be >= to any GPIO bounce times
				time.sleep(0.2)

		    except KeyboardInterrupt:
                    	print " Stopped"
			radio.stop()
			time.sleep(1)
		    	sys.exit(0)

	# Status routines
	def status(self):
		# Get the pid from the pidfile
		try:
			pf = file(self.pidfile,'r')
			pid = int(pf.read().strip())
			pf.close()
		except IOError:
			pid = None

		if not pid:
			message = "radiod status: not running"
			log.message(message, log.INFO)
			print message
		else:
			message = "radiod running pid " + str(pid)
			log.message(message, log.INFO)
			print message
		return

	# Version
	def getVersion(self):
		myradio = Radio(menu,event)	
		return myradio.getVersion()

# End of class overrides

# Pass events to the appropriate event handler 
def handleEvent(event,display,radio,menu):
	event_type = event.getType()
	event_name = event.getName()
	menu_mode = menu.mode()

	if event_type != event.NO_EVENT:
		log.message("Event type " + str(event_type) + ' ' + event_name, log.DEBUG)

	# Retro radio RGB status LED
	statusLed.set(StatusLed.BUSY)

	# Exit from sleep if alarm fired
	if event_type == event.ALARM_FIRED:
		wakeup(radio,menu)

	# Exit from sleep if  menu button pressed
	elif menu_mode == menu.MENU_SLEEP:
		if event_type == event.MENU_BUTTON_DOWN:
			wakeup(radio,menu)

	elif event_type == event.ROTARY_SWITCH_CHANGED:
		handleSwitchChange(event,radio,menu,message)

	elif event_type == event.TIMER_FIRED:
		sleep(radio,menu)

	elif event_type == event.LOAD_RADIO or event_type == event.LOAD_MEDIA \
			   or event_type == event.LOAD_AIRPLAY \
			   or event_type == event.LOAD_SPOTIFY \
			   or event_type == event.LOAD_PLAYLIST:
		handleUdpEvent(event,display,radio,message)

	elif menu_mode == menu.MENU_SOURCE:
		handleSourceEvent(event,display,radio,menu)

	elif menu_mode == menu.MENU_SEARCH:
		handleSearchEvent(event,display,radio,menu)

	elif menu_mode == menu.MENU_OPTIONS:
		handleOptionEvent(event,display,radio,menu)

	elif event_type != event.NO_EVENT:
		handleRadioEvent(event,display,radio,menu)

	# Clear event 
	event.clear()
	statusLed.set(StatusLed.NORMAL)
	return

# Handle normal volume and channel change events
def handleRadioEvent(event,display,radio,menu):
	global _connecting
	event_type = event.getType()
	event_name = event.getName()
	menu_mode = menu.mode()
	volume_change = False	
	nlines = display.getLines()
	displayType = display.getDisplayType()

	log.message('handleRadioEvent ' + str(event_type) + ' ' + event_name, log.DEBUG)

	if event_type == event.VOLUME_UP:
		if radio.muted():
			radio.unmute()

		log.message('Volume UP', log.DEBUG)
		radio.increaseVolume()

		# Both left and right buttons together mute radio
		if event.leftButtonPressed():
			radio.mute()
			displayVolume(display, radio)
			time.sleep(0.5)

		else:
			# Volume UP repeat
			while event.rightButtonPressed():
				radio.increaseVolume()
				displayVolume(display, radio)
				time.sleep(0.1)

		display.setDelay(15)
		volume_change = True	

	elif event_type == event.VOLUME_DOWN:
		if radio.muted():
			radio.unmute()

		log.message('Volume DOWN', log.DEBUG)
		radio.decreaseVolume()

		# Both left and right buttons together mute radio
		if event.rightButtonPressed():
			radio.mute()
			displayVolume(display, radio)
			time.sleep(0.5)
		else:
			# Volume DOWN repeat
			while event.leftButtonPressed():
				radio.decreaseVolume()
				displayVolume(display, radio)
				time.sleep(0.1)

		display.setDelay(20)
		volume_change = True	

	elif event_type == event.MUTE_BUTTON_DOWN:
		volume_change = True	
		if radio.muted():
			log.message('Unmute', log.DEBUG)
			radio.unmute()
			# Need to force line 5 to redisplay mute
			if displayType == radio.config.OLED_128x64:
				display.out(5, ' ', no_interrupt)
		else:
			log.message('Mute switch, speech ' + str(radio.config.hasSpeech()), 
					log.DEBUG)

			# If speech the mute button has to be held in for two seconds
			if radio.config.hasSpeech():
				count = 10 	# Two second wait
				while event.muteButtonPressed():
					count -= 1
					time.sleep(0.2)
					if count < 0:
						radio.mute()

				if count > 0:
					speakCurrent(message,radio)
			else:
				radio.mute()
				time.sleep(0.5) # Prevent unmute

		displayVolume(display,radio)

	if event_type == event.CHANNEL_UP:
		log.message('Channel UP', log.DEBUG)
		radio.channelUp()
		display.setDelay(0)	# Cancel delayed display of volume
		if menu_mode == menu.MENU_INFO:
			menu.set(menu.MENU_TIME)
		if radio.config.verbose():
			speakCurrent(message,radio,speak_title=False)
		_connecting = False

	elif event_type == event.CHANNEL_DOWN:
		log.message('Channel DOWN', log.DEBUG)
		radio.channelDown()
		display.setDelay(0)	# Cancel delayed display of volume
		if menu_mode == menu.MENU_INFO:
			menu.set(menu.MENU_TIME)
		if radio.config.verbose():
			speakCurrent(message,radio,speak_title=False)
		_connecting = False

	elif event_type == event.MENU_BUTTON_DOWN:
		if radio.muted():
			radio.unmute()
		handleMenuChange(display,radio,menu,message)
		display.setDelay(0)	# Cancel delayed display of volume

	elif event_type == event.SHUTDOWN:
		log.message('SHUTDOWN', log.DEBUG)
		displayStop(display,message)
		radio.stop()

		if radio.config.doShutdown(): 
			display.out(1, message.get('shutdown'))
			radio.shutdown() # Shutdown the system
		else:
			display.out(1, message.get('stopped'))
			sys.exit(0)

	# Display volume
	if volume_change:
		displayVolume(display,radio)
	return

# Handle source menu selection event
def handleSourceEvent(event,display,radio,menu):
	event_type = event.getType()
	radio.getSources()
	
	if event_type == event.UP_SWITCH:
		radio.cycleSource(UP)
		radio.setReload(True)

	elif event_type == event.DOWN_SWITCH:
		radio.cycleSource(DOWN)
		radio.setReload(True)

	elif event_type == event.MENU_BUTTON_DOWN:
		if radio.getReload():
			loadSource(display,radio)
			menu.set(menu.MENU_TIME)
			radio.setReload(False)
		else:
			handleMenuChange(display,radio,menu,message)
	else:
		 handleRadioEvent(event,display,radio,menu)

	return

# Handle search events
def handleSearchEvent(event,display,radio,menu):
	event_type = event.getType()
	source_type = radio.getSourceType()

	if event_type == event.UP_SWITCH:
		radio.getNext(UP)
		radio.setLoadNew(True)

	elif event_type == event.DOWN_SWITCH:
		radio.getNext(DOWN)
		radio.setLoadNew(True)

	elif event_type == event.LEFT_SWITCH and source_type == radio.source.MEDIA:
		radio.findNextArtist(DOWN)
		radio.setLoadNew(True)

	elif event_type == event.RIGHT_SWITCH and source_type == radio.source.MEDIA:
		radio.findNextArtist(UP)
		radio.setLoadNew(True)

	elif event_type == event.MENU_BUTTON_DOWN:
		if radio.loadNew():
			index = radio.getSearchIndex()
			radio.play(index + 1)
			menu.set(menu.MENU_TIME)
			radio.setLoadNew(False)
			displayCurrent(display,radio,message)
		else:
			handleMenuChange(display,radio,menu,message)

	else:
		 handleRadioEvent(event,display,radio,menu)
	return

# Handle menu stepthrough
def handleMenuChange(display,radio,menu,message):
	menu_mode = menu.cycle()
	menu_name = menu.getName()
	log.message('Menu mode ' + str(menu_mode) + ' ' + str(menu_name), log.DEBUG)
	hostname = socket.gethostname()
	ip_addr = radio.execCommand('hostname -I')

	source_type = radio.getSourceType()

	# Was the previous option to activate the alarm?
	if menu.getOption() == menu.OPTION_ALARM:
		if radio.getAlarmType() != 0:
			sleep(radio,menu)

	elif radio.optionChanged():
		menu.set(menu.MENU_TIME)
		radio.optionChangedFalse()

	elif menu_mode == menu.MENU_INFO:
		message.storeIpAddress(ip_addr)

	# In Airplay and Spotify mode only the TIME and SOURCE modes are relevant
	elif source_type == radio.source.AIRPLAY or source_type == radio.source.SPOTIFY:
		if menu_mode == menu.MENU_SEARCH:
			menu.set(menu.MENU_SOURCE)

		elif menu_mode == menu.MENU_OPTIONS:
			menu.set(menu.MENU_TIME)
		
		if source_type == radio.source.AIRPLAY:
			radio.stopAirplay()

		if source_type == radio.source.SPOTIFY:
			radio.stopSpotify()

		radio.source.cycleType(radio.source.RADIO)
		radio.setReload(True)

	if menu_mode != menu.MENU_SLEEP:
		display_mode = menu.mode()
		sMenu = menu_name.replace('_', ',')

		if display_mode == menu.MENU_RSS:
			sMenu = "Main"
		
			# Speak info if speak info true
			if radio.config.hasSpeech() and radio.config.speakInfo() :
				menu.set(menu.MENU_INFO)
				sMenu = hostname +  " IP " + str(ip_addr)
				sMenu = convertInfo(hostname,ip_addr)

		if display.hasScreen():
			sMenu = sMenu.lower()

		message.speak(sMenu)

	time.sleep(0.2)	# Prevent skipping next menu
	return menu_mode

# Convert IP address and hostname to speach string
def convertInfo(hostname,ip_addr):
	global message
	info = ""
	dot = message.get('dot')
	for i in range(len(ip_addr)):
		c = ip_addr[i]
		if  c == '.':
			info = info + ' ' + dot + '. '
		else :
			info = info + c + ' '
	info = 'Host. ' + hostname + ' IP ' + info
	return info 

# Handle menu option events
def handleOptionEvent(event,display,radio,menu):
	event_type = event.getType()
	option_index = menu.getOption()

	if event_type == event.UP_SWITCH:
		menu.getNextOption(UP)

	elif event_type == event.DOWN_SWITCH:
		menu.getNextOption(DOWN)

	elif event_type == event.LEFT_SWITCH or event_type == event.RIGHT_SWITCH:
		changeOption(event, display, radio, menu)

	elif event_type == event.MENU_BUTTON_DOWN:
		handleMenuChange(display,radio,menu,message)

	else:
		handleRadioEvent(event,display,radio,menu)

	return

# Handler for source change events from the UDP listener
def handleUdpEvent(event,display,radio,message):
	msg = ''
	event_type = event.getType()
	valid_event = True 

	# Version 1.7 of web interface
	if event_type == event.LOAD_RADIO:
		msg = message.get('loading_radio')
		display.out(2,msg)
		message.speak(msg)
		radio.cycleWebSource(radio.source.RADIO)

	# Version 1.7 of web interface
	elif event_type == event.LOAD_MEDIA:		
		msg = message.get('loading_media')
		display.out(2,msg)
		message.speak(msg)
		radio.cycleWebSource(radio.source.MEDIA)

	# Version 1.8 onwards of the web interface
	elif event_type == event.LOAD_PLAYLIST:		
		playlist = radio.getPlaylistName()
                name = playlist.replace('_', ' ')
                name = name.lstrip()
                name = name.rstrip()
                name = "%s%s" % (name[0].upper(), name[1:])
		msg = message.get('loading_playlist') + ' ' + name
		display.out(2,msg)
		message.speak(msg)
		time.sleep(1)
		radio.source.setPlaylist(playlist)

	elif event_type == event.LOAD_AIRPLAY:
		msg = message.get('starting_airplay')
		display.out(2,msg)
		message.speak(msg)
		radio.cycleWebSource(radio.source.AIRPLAY)

	elif event_type == event.LOAD_SPOTIFY:
		msg = message.get('starting_spotify')
		display.out(2,msg)
		message.speak(msg)
		radio.cycleWebSource(radio.source.SPOTIFY)
	else:
		valid_event = False
		log.message("radio.handleUdpEvent invalid event:", 
				str(event_type), log.ERROR)

	if valid_event:
		loadSource(display,radio)
	return

# Handle menu step through
def handleSwitchChange(event,radio,menu,message):
	switch_value = event.getRotarySwitch()
	new_menu = menu.MENU_TIME

	if switch_value == 2:
		speakCurrent(message,radio)
	elif switch_value == 3:
		new_menu = menu.MENU_SEARCH
	elif switch_value == 4:
		new_menu = menu.MENU_SOURCE
	elif switch_value == 5:
		new_menu = menu.MENU_OPTIONS

	menu.set(new_menu)
	
	if switch_value >= 3:
		menu_name = menu.getName()
		sMenu = menu_name.replace('_', ',')
		sMenu = sMenu.lower()
		message.speak(sMenu)
	return

# Change the selected option
def changeOption(event, display, radio, menu):
	event_type = event.getType()
	option_index = menu.getOption()
	
	if option_index == menu.OPTION_ALARM:
		if event_type == event.RIGHT_SWITCH:
			radio.alarmCycle(UP)
		elif event_type == event.LEFT_SWITCH:
			radio.alarmCycle(DOWN)

	elif option_index == menu.OPTION_ALARMSETHOURS or option_index == menu.OPTION_ALARMSETMINS:
		if event_type == event.RIGHT_SWITCH:
			radio.cycleAlarmValue(UP, option_index)
		else:
			radio.cycleAlarmValue(DOWN, option_index)

	elif option_index == menu.OPTION_TIMER:
		if event_type == event.RIGHT_SWITCH:
			radio.incrementTimer()
		else:
			radio.decrementTimer()

	elif option_index == menu.OPTION_WIFI:
		radio.toggleOptionValue(option_index)

	elif option_index == menu.OPTION_RELOADLIB:
		if radio.toggleOptionValue(option_index):
			radio.setUpdateLibOn()
		else:
			radio.setUpdateLibOff()
	else:
		radio.toggleOptionValue(option_index) 

	# Indicate option has changed
	radio.optionChangedTrue()

	return

# Handle timer event , put radio to sleep 
def sleep(radio,menu):
	log.message("Sleep", log.INFO)
	radio.mute()
	menu.set(menu.MENU_SLEEP)
	display.setDelay(10)
	return

# Handle alarm event , put radio to sleep 
def wakeup(radio,menu):
	log.message("Alarm fired", log.INFO)
	radio.unmute()
	menu.set(menu.MENU_TIME)
	return

################ Display Routines ############

# Display startup
def displayStartup(display,radio):
	nlines = display.getLines()
	pid = os.getpid()
	ipaddr = radio.execCommand('hostname -I')
	version = radio.getVersion()

	if nlines > 2:
		display.out(1,"Radio version " + version)
		display.out(2,"Radio PID " + str(pid))
		display.out(3,"Waiting for network")
		display.out(4,"MPD Version " + radio.getMpdVersion())
	else:
		display.out(1,"Radio version " + version)
		display.out(2,"Waiting for network")

	time.sleep(1)
	return

# Wait for the network
def waitForNetwork(radio,display):
	ipaddr = ""
	waiting4network = True
	count = 10

	while waiting4network:
		ipaddr = execCommand('hostname -I')
		time.sleep(1)
		count -= 1
		if (count < 0) or (len(ipaddr) > 1):
			waiting4network = False
	return ipaddr

# Display time
def displayTimeDate(display,radio,message):
	msg = message.get('date_time')
	width = display.getWidth()

	# Small displays drop day of the week
	if width < 16:
		msg = msg[0:5] 

	# If streaming add the streaming indicator
	if radio.getStreaming() and width > 16:
		streaming = '*'
	else:
		streaming = ''
	display.setFont(2)
	display.out(message.getLine(),msg + streaming)
	display.setFont(1)
	return

# Display the search menu
def displaySearch(display,menu,message):
	index = radio.getSearchIndex()
	source_type = radio.getSourceType()
	current_id = radio.getCurrentID()
	lines = display.getLines()	

	sSearch = 'menu_search'
	if display.getWidth() < 16:
		sSearch = 'menu_find'

	display.backlight('search_color')
	display.out(1, message.get(sSearch) + ':' + str(index+1), interrupt)

	if source_type == radio.source.MEDIA:
		# pdb.set_trace() #DEBUG
		current_artist = radio.getArtistName(index)
		current_track = radio.getTrackNameByIndex(index)

		if lines > 2:
			display.out(2,current_artist[0:50],interrupt)
			display.out(3,current_track,interrupt)

			if display.getDelay() > 0:
				displayVolume(display, radio)
				time.sleep(0.1)
			else:
				display.out(4,radio.getProgress(),interrupt)
				message.speak(str(index+1) + ' ' +  current_artist[0:50])
		else:
			if display.getDelay() > 0:
				displayVolume(display, radio)
				time.sleep(0.1)
			else:
				info = current_artist[0:50] + ': ' + current_track
				display.out(2,info,interrupt)
				message.speak(str(index+1) + ' ' +  current_artist[0:50])

	elif source_type == radio.source.RADIO:
		search_station = radio.getStationName(index)
		search_station = search_station.lstrip('"')
		search_station = search_station.rstrip('"')

		if lines > 2:
			display.out(2,search_station[0:30],interrupt)
			currentStation = message.get('current_station') + ':' + str(current_id)
			display.out(3, currentStation  ,interrupt)
			message.speak(str(index+1) + ' ' +  search_station[0:50])
		else:
			if display.getDelay() > 0:
				displayVolume(display, radio)
				time.sleep(0.1)
			else:
				display.out(2,search_station[0:30],interrupt)
				message.speak(str(index+1) + ' ' +  search_station[0:50])

	return 

# Display the source menu
def displaySource(display,radio,menu,message):
	menu_mode = menu.mode()
		
	display.out(1, message.get('menu_source') + ':', interrupt)
	sSource = radio.getNewSourceName()
	station = radio.getSearchName()
	
	display.backlight('source_color')

	# If 4 or 5 lines then display current station/track title
	if display.getLines() > 2:
		display.out(2, sSource, no_interrupt)
		display.out(3,station,interrupt)
	else:
		display.out(2, sSource, no_interrupt)

	# Speak source
	message.speak(sSource)
	return 

# Display the options menu
def displayOptions(display,radio,menu,message):
	sText = ''	# Speech text
	option_index = menu.getOption()
	option_value = radio.getOptionValue(option_index)
	source_type = radio.getSourceType()
	
	display.backlight('menu_color')
	display.out(1, message.get('menu_option'))
	
	if option_index == menu.OPTION_RELOADLIB:
		text = message.toYesNo(option_value)
		sText = text

	elif option_index == menu.OPTION_ALARM:
		text = message.getAlarmText(option_value)

	elif option_index == menu.OPTION_ALARMSETHOURS or  option_index == menu.OPTION_ALARMSETMINS:
		text = option_value

	elif option_index == menu.OPTION_TIMER:
		text = message.getTimerText(option_value)

	elif option_index == menu.OPTION_WIFI:
		text = message.toYesNo(option_value)
		sText = text

	else:
		# Default handling of on/off options such as random,repeat etc
		text = message.toOnOff(option_value)
		sText = text

	# Display option on line 2
	option_name = menu.getOptionName(option_index)
	display.out(2, option_name + ':' + str(text), interrupt)
	
	if display.getLines() > 2:
		name = radio.getSearchName()
		display.out(3,name,interrupt)
		if source_type == radio.source.MEDIA:
			display.out(4,radio.getProgress(),interrupt)

	# Only speak message if on/off yes/no etc
	if len(sText) > 0:
		message.speak(option_name + ' ' + sText)

	time.sleep(0.2)	# Prevent skipping of options
	return 

# Display the RSS feed
def displayRss(display,radio,message,rss):
	source_type = radio.getSourceType()
	displayTimeDate(display,radio,message)
	rss_line = rss.getFeed()
	line = 2

	if display.getLines() > 2:
		line = 3
		if source_type == radio.source.MEDIA:
			name = radio.getCurrentArtist()
		else:
			name = radio.getSearchName()
		display.out(2,name,interrupt)

	display.out(line,rss_line,interrupt)
	return

# Display the information menu
def displayInfo(display,radio,message):
	ipaddr = message.getIpAddress()
	if len(ipaddr) < 1:
		ipaddr = message.storeIpAddress(radio.execCommand('hostname -I'))
	version = radio.getVersion()
	nlines = display.getLines()
	display.backlight('info_color')
	msg = message.get('radio_version') + ' '
	display.out(1, msg + version, interrupt )
	if nlines > 2:
		display.out(2, 'IP: ' + ipaddr, interrupt )
		MpdVersion = radio.getMpdVersion()
		display.out(3, 'MPD version ' + MpdVersion, interrupt )

		if display.getDelay() > 0:
			displayVolume(display, radio)
			time.sleep(0.1)
		else:
			msg = 'Hostname: ' + socket.gethostname()
			display.out(4,msg,interrupt)
	else:
		sHost = ' ' + socket.gethostname()
		display.out(2, 'IP: ' + ipaddr + sHost, interrupt )
	return 


# Display sleep 
def displaySleep(display,radio):

	displayTimeDate(display,radio,message)
	nlines = display.getLines()

	display.backlight('sleep_color')
	if display.getDelay() > 0:
		display.out(2, message.get('sleep'), interrupt )
		time.sleep(0.1)
	else:

		# Display alarm setting if set
		if radio.getAlarmType() != 0:
			sAlarmTime =  radio.getAlarmTime()
			display.out(2, 'Alarm:' + sAlarmTime, interrupt )
		else:
			display.out(2, ' ', interrupt )

	if nlines > 2:
		display.out(3, ' ', interrupt )
		display.out(4, ' ', interrupt )
	return

# Display stop radio 
def displayStop(display,message):
	display.backlight('shutdown_color')
	display.out(1, message.get('stop'))
	display.out(2, ' ')
	if display.getLines() > 2:
		display.out(3, ' ')
		display.out(4, ' ')
	return

# Load new source selected (RADIO, MEDIA, AIRPLAY or SPOTIFY)
def loadSource(display,radio):
	new_source = radio.getNewSourceType()
	log.message("loadSource new type = " + str(new_source), log.DEBUG)

	firstline = 1
	secondline = 2
	if display.getLines() > 2:
		firstline = 2
		secondline = 3
	
	msg = message.get('loading') + ':'
	display.out(firstline,msg)

	if new_source == radio.source.RADIO:
		msg = message.get('radio_stations')
		display.out(secondline,msg)
		msg = message.get('loading_radio')
		message.speak(msg)

	elif new_source == radio.source.MEDIA:
		msg = message.get('media_library')
		display.out(secondline,msg)
		msg = message.get('loading_media')
		message.speak(msg)
		current = radio.execMpcCommand("current")
		if len(current) < 1:
			log.message("loadSource error no playlist", log.ERROR)

	elif new_source == radio.source.AIRPLAY:
		msg = message.get('airplay')
		display.out(secondline,msg)
		msg = message.get('starting_airplay')
		message.speak(msg)

	elif new_source == radio.source.SPOTIFY:
		msg = "Spotify"
		display.out(secondline,msg)
		msg = message.get('starting_spotify')
		message.speak(msg)

	else:
		msg = "Invalid source type " + str(new_source)
		display.out(2,msg)
		time.sleep(3)
		new_source = -1

	if new_source >= 0:
		radio.loadSource()

	return
	
	
# Display current playing selection or station
def displayCurrent(display,radio,message):
	global _connecting
	# get details of currently playing source
	current_id = radio.getCurrentID()
	sourceType = radio.getSourceType()
	plsize = radio.getPlayListLength()

	display.backlight('bg_color') 
	errorString = ''
	if radio.gotError():
		errorString = radio.getErrorString()

	if sourceType == radio.source.RADIO:
		station_name = radio.getCurrentStationName()
		search_name = radio.getSearchName()
		title = radio.getCurrentTitle()
		bitrate = radio.getBitRate()
		station = search_name 	# Name from our playlists
		name = station_name	# Name sent with the stream

		if len(title) > 0:
			name = title	# Sometimes title is used

		if len(name) < 1 or station == name:
			name = message.get('station') + ' ' + str(current_id)
			if bitrate > 0:
				name = name + ' ' + str(bitrate) +'k'
				_connecting = False
			else:
				if not _connecting:
					eMsg = message.get('connecting')
					name = " %s/%s: %s" % (current_id,plsize,eMsg)
					_connecting = True
				else:
					name = message.get('no_information')

		nLines = display.getLines()
		if nLines > 2:
			displayVolume(display, radio)
			station = station.lstrip ('"')
			station = station.rstrip ('"')
			display.out(2,station,interrupt)
			if len(errorString) > 0:
				display.out(3,errorString,interrupt)
			else:
				display.out(3,name,interrupt)
			if nLines > 4:
				plName = radio.getSourceName()
				plName = plName.replace('_','')
				current_id = radio.getCurrentID()
				plsize = radio.getPlayListLength()
				msg = "Station %d/%d %s" % (current_id,plsize,plName)
				display.out(4,msg,interrupt)
		else:
			if display.getDelay() > 0:
				displayVolume(display, radio)
				time.sleep(0.1)
			elif len(errorString) > 0:
				display.out(2,errorString,interrupt)
			else:
				details = station + ': ' + name
				display.out(2,details,interrupt)

	elif sourceType == radio.source.MEDIA:
		# If no playlist then try reloading library
		if current_id < 1:
			log.message("No current ID found", log.DEBUG)
			updateLibrary(display,radio,message)

		artist = radio.getCurrentArtist()
		title = radio.getCurrentTitle()

		if display.getLines() > 2:
			display.out(2,artist,interrupt)
			display.out(3,title,interrupt)

			if display.getDelay() > 0:
				displayVolume(display, radio)
				time.sleep(0.1)
			else:
				display.out(4,radio.getProgress(),interrupt)

		else:
			if display.getDelay() > 0:
				displayVolume(display, radio)
				time.sleep(0.1)
			else:
				details = artist + ': ' + title
				display.out(2,details,interrupt)

	elif sourceType == radio.source.AIRPLAY:
		displayVolume(display, radio)
		displayAirplay(display,radio)

	elif sourceType == radio.source.SPOTIFY:
		displaySpotify(display,radio)

	return

# Display current playing selection or station
def speakCurrent(message,radio, speak_title=True):
	title = ''
	source_type = radio.getSourceType()
	id = radio.getCurrentID()

	if speak_title:
		title = radio.getCurrentTitle()
	
	if source_type == radio.source.RADIO:
		station = radio.getCurrentStationName()
		sStation = message.get('station')
		msg = sStation + ' ' + str(id) + ',' + station  +  ',' + title
		message.speak(msg,repeat=True)
	
	elif source_type == radio.source.MEDIA:
		artist = radio.getCurrentArtist()
		sTrack = message.get('track')
		msg = sTrack + ' ' + str(id) + ',' + artist  +  ',' + title
		message.speak(msg,repeat=True)
	return

# Display Airplay info
def displayAirplay(display,radio):
	info = radio.getAirplayInfo()
	artist = info[0]
	title = info[1]
	album = info[2]

	if display.getLines() > 2:
		display.out(2,artist,interrupt)
		display.out(3,title + ': ' + album, interrupt)
	else:
		track = artist + ': ' + title + ': ' + album
		display.out(2,track,interrupt)
	return

# Display Spotify information
def displaySpotify(display,radio):
	info = radio.getSpotifyInfo()

	if len(info) < 1:
		info = message.get('waiting_for_spotify_client')
	else:
		info = info.replace("player:","Spotify:")
	elements = info.split('"')
	if len(elements) >= 3:
		info = elements[1]

	if display.getLines() > 2:
		hostname = socket.gethostname()
		display.out(2,"Spotify: " + hostname,interrupt)
		display.out(3,info,interrupt)
	else:
		if display.getDelay() > 0:
			displayVolume(display, radio)
			time.sleep(0.1)
		else:
			display.out(2,info,interrupt)
	return


# Display volume only if not in Info mode
def displayVolume(display,radio):
	menu_mode = menu.mode()
	if menu_mode != menu.MENU_INFO or display.getDelay() > 0:
		_displayVolume(display,radio)
	return
	
def _displayVolume(display,radio):
	menu_mode = menu.mode()
	msg = ''
	displayType = display.getDisplayType()
	if radio.muted():
		display.backlight('mute_color')
		msg = message.get('muted')
	else:
		volume = radio.getDisplayVolume()
		msg = message.get('volume') + ' ' + str(volume)
		tTimer = radio.getTimerCountdown()
		
		if tTimer > 0 and display.getWidth() > 8:
			msg = msg + ' ' + message.getTimerText(tTimer)
	
		elif radio.config.displayVolumeBlocks():
			msg = message.volumeBlocks()

	# Display on correct line. NB. Do not call with an interrupt
	# otherwise a recursive error will occur as the this 
	# routine is also called from the interrupt routine

	# The OLED has a special volume display bar on the last line
	if displayType == radio.config.OLED_128x64 \
			and radio.config.displayVolumeBlocks():
		if radio.muted():
			display.volume(0)
			display.out(5, msg, no_interrupt)
		else:
			volume = radio.getVolume() # Real volume
			display.volume(volume)
	else:
		display.out(message.getLine(), msg, no_interrupt)

	return

# Update media library
def updateLibrary(display,radio,message):
	log.message("Updating media library", log.INFO)

	firstLine = 1
	secondLine = 2
	if display.getLines() > 2:
		firstLine = 2
		secondLine = 3

	display.out(firstLine,message.get('updating_media'))
	display.out(secondLine,message.get('wait'))
	radio.updateLibrary(force=True)
	display.out(secondLine,message.get('update_complete'))
	time.sleep(1)
	menu.set(menu.MENU_TIME) # Return to main display
	return

# Configure RGB status LED
def statusLedInitialise(statuLed):
	rgb_red = radio.config.getRgbLed('rgb_red')
	rgb_green = radio.config.getRgbLed('rgb_green')
	rgb_blue = radio.config.getRgbLed('rgb_blue')
	statusLed = StatusLed(rgb_red,rgb_green,rgb_blue)
	statusLed.set(StatusLed.BUSY)
	return statusLed

# Execute system command
def execCommand(cmd):
	p = os.popen(cmd)
	result = p.readline().rstrip('\n')
	return result

def usage():
	print "usage: %s start|stop|restart|status|version|nodaemon" % sys.argv[0]
	return

# End of class

### Main routine ###
if __name__ == "__main__":
	daemon = MyDaemon('/var/run/radiod.pid')
	if len(sys.argv) == 2:
		if 'start' == sys.argv[1]:
			daemon.start()
		elif 'stop' == sys.argv[1]:
			os.system("service mpd stop")
			daemon.stop()
		elif 'restart' == sys.argv[1]:
			daemon.restart()
		elif 'status' == sys.argv[1]:
			daemon.status()
		elif 'nodaemon' == sys.argv[1]:
			daemon.nodaemon()
		elif 'version' == sys.argv[1]:
			print 'Version',daemon.getVersion()
		else:
			print "Unknown command: " + sys.argv[1]
			usage()
			sys.exit(2)
		sys.exit(0)
	else:
		# Note - do not include nodaemon in the list of possibilities
		usage()
		sys.exit(2)

# End of script
