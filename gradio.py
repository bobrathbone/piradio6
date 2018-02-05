#!/usr/bin/env python
#
# Raspberry Pi Graphical Internet Radio 
# This program interfaces with the Music Player Daemon MPD
#
# $Id: gradio.py,v 1.166 2018/02/03 10:07:00 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#	   The authors shall not be liable for any loss or damage however caused.
#
# This program uses the SGC widget routines written by Sam Bull
# Copyright (C) SGC widget routines 2010-2013  Sam Bull
# SGC documentation: https://program.sambull.org/sgc/sgc.widgets.html
#

import os
import sys
import time
import pdb
import random
import socket
import signal
import locale
import commands
from time import strftime

# Radio imports
from log_class import Log
from radio_class import Radio
from event_class import Event
from menu_class import Menu
from rss_class import Rss
from message_class import Message
from graphic_display import GraphicDisplay

# Pygame controls
from gcontrols_class import *
from pygame.locals import *

radio = None
log = Log()
rmenu = Menu()
rss = Rss()
display = None
radioEvent = None
message = None

import pygame
from pygame.locals import *
try:
    from OpenGL.GL import *
except: pass

size = (640,480)
pygame.display.init()
pygame.font.init()
myfont = pygame.font.SysFont('freesans', 20, bold=True)
dialog = None

import sgc
from sgc.locals import *

from sgc.__init__ import __version__ as ver_no
screen = None
surface=pygame.Surface((size))

clock = pygame.time.Clock()

Atists = {} 	# Dictionary of artists

# Files for artwork extraction
pidfile = "/var/run/radiod.pid"
MpdLibDir = "/var/lib/mpd"
MusicDirectory =  MpdLibDir + "/music"
ArtworkFile = "/tmp/artwork.jpg"
artwork_file = ""	# Album artwork file name
wallpaper = ''		# Background wallpaper

# Signal SIGTERM handler
def signalHandler(signal,frame):
        global display
        global radio
        global log
        pid = os.getpid()

        print "signalHandler",signal

        log.message("Radio stopped, PID " + str(pid), log.INFO)
        radio.stop()
        exit()

# Start the radio and MPD
def setupRadio(radio):
	global radioEvent,message,display,screen
	log.message("Starting graphic radio ", log.INFO)

	# Stop the pygame mixer as it conflicts with MPD
	pygame.mixer.quit()

	radio.start()		   # Start it
	radio.loadSource()	      # Load sources and playlists

	display.setSize(size)
	message = Message(radio,display)
	return

# This routine displays the time string
def displayTimeDate(screen,myfont,radio,message):
	dateFormat = radio.config.getGraphicDateFormat()
	timedate = strftime(dateFormat)
	banner_color_name = display.config.getBannerColor()
	try:
		color = pygame.Color(banner_color_name)
	except:
		color = pygame.Color('white')

	# If streaming add the streaming indicator
	if radio.getStreaming():
		streaming = ' *'
	else:
		streaming = ''
	rowPos = display.getRowPos(1)
	font = pygame.font.SysFont('freesans', 25, bold=False)
	fontSize = font.size(timedate) 
	column = int((size[0] - fontSize[0])/2)
	renderText(timedate,font,screen,rowPos,column,color)
	return


# Display message popup
def displayPopup(screen,radio,text):
	displayPopup = TextRectangle(pygame)    # Text window
	font = pygame.font.SysFont('freesans', 30, bold=True)
	fx,fy = font.size(text + "A")
	xPos = int((size[0]/2) - (fx/2))
	yPos = size[1]/2
	xSize = fx
	ySize = fy
	color = (50,50,50)
	bcolor = (255,255,255)
	border = 4
	displayPopup.draw(screen,color,bcolor,xPos,yPos,xSize,ySize,border)
	line = 1        # Not used but required
	color = (255,255,255)
	displayPopup.drawText(screen,font,color,line,text)
	return


# Display source load
def displayLoadingSource(screen,font,radio,message):
	lcolor = getLabelColor(display.config.getDisplayLabelsColor())
	color = pygame.Color(lcolor)
	sourceName = radio.getSourceName()
	column = 7
	columnPos = display.getColumnPos(column)
	rowPos = display.getRowPos(3)
	msg = "Loading playlist " + sourceName
	renderText(msg,font,screen,rowPos,columnPos,color)
	rowPos = display.getRowPos(4)
	msg = "Updating Music Player Database"
	renderText(msg,font,screen,rowPos,columnPos,color)
	rowPos = display.getRowPos(5)
	msg = "Please wait or select different playlist"
	renderText(msg,font,screen,rowPos,columnPos,color)
	return

# Display information
def displayInfo(screen,font,radio,message):
	lcolor = getLabelColor(display.config.getDisplayLabelsColor())
	color = pygame.Color(lcolor)
	column = 7
	columnPos = display.getColumnPos(column)
	columns = display.getColumns()
	max_columns = columns - 8

	# Get info
	version = radio.getVersion()	
	MpdVersion = radio.getMpdVersion()
	sVersion = "Radio version " + version + ", MPD version " + MpdVersion
	ipaddr = message.getIpAddress()
	if len(ipaddr) < 1:
		ipaddr = message.storeIpAddress(radio.execCommand('hostname -I'))
	sIP = "IP address: " + ipaddr
	sHostname = 'Hostname: ' + socket.gethostname() 

	# Display it 
	row = 3
	rowPos = display.getRowPos(row)
	renderText(sVersion,font,screen,rowPos,columnPos,color)
	row += 1
	rowPos = display.getRowPos(row)
	renderText(sIP,font,screen,rowPos,columnPos,color)
	row += 1
	rowPos = display.getRowPos(row)
	renderText(sHostname,font,screen,rowPos,columnPos,color)
	return

# Display currently playing radio station or track
def displayCurrent(screen,font,radio,message):
	global rss_delay,rss_line
	column = 5
	columns = display.getColumns()
	max_columns = columns - 14
	search_name = radio.getSearchName()
	columnPos = display.getColumnPos(column)
	title = radio.getCurrentTitle()
	errorStr = radio.getErrorString()

	# Scroll if necessary
	linebuf = 1
	if len(title) > max_columns:
		title = display.scroll(title,linebuf,max_columns)

	linebuf += 1
	if len(search_name) > max_columns:
		search_name = display.scroll(search_name,linebuf,max_columns)

	linebuf += 1
	if len(errorStr) > max_columns:
		errorStr = display.scroll(errorStr,linebuf,max_columns)

	bitrate = radio.getBitRate()
	current_id = radio.getCurrentID()
	source_type = radio.getSourceType()

	row = 3
	lcolor = getLabelColor(display.config.getDisplayLabelsColor())
	color = pygame.Color(lcolor)
	rowPos = display.getRowPos(row)
	if source_type == radio.source.MEDIA:
		progress = radio.getProgress()
		current_artist = radio.getCurrentArtist()
		current_album = radio.getCurrentAlbum()
		row = 1
		DisplayWindow.drawText(screen,font,color,row,current_artist)
		row = 2
		DisplayWindow.drawText(screen,font,color,row,title)

		linebuf = 2
		if len(current_artist) > max_columns:
			current_artist = display.scroll(current_artist,linebuf,max)

		max = max_columns - len(progress)
		linebuf += 1
		if len(current_album) > max:
			current_album = display.scroll(current_album,linebuf,max)

		if display.getMode() == display.RSS:
			text = rss.scrollRssFeed(display)
		else:
			if len(current_album) > 0:
				text = progress + " " + current_album
			else:
				text = progress
		row = 3
		DisplayWindow.drawText(screen,font,color,row,text)
	else:

		station_name = radio.getCurrentStationName()[:max_columns]
		linebuf += 1
		if len(station_name) > max_columns:
			station_name = display.scroll(station_name,linebuf,max_columns)

		if len(title) < 1:
			title = station_name
			station_name = search_name

		if len(station_name) < 1:
			station_name = search_name

		# First row
		row = 1
		DisplayWindow.drawText(screen,font,color,row,station_name)

		# Second row
		if len(errorStr) > 0:
			station_name = errorStr
		row = 2
		DisplayWindow.drawText(screen,font,color,row,title)

		# Third row
		row = 3

		if display.getMode() == display.RSS:
			text = rss.scrollRssFeed(display)

		elif current_id < 1:
			text = "Station not found!"
		else:
			text = "Station " + str(current_id)
			if bitrate > 0:
				text = text + ' ' + str(bitrate) + 'k'

		DisplayWindow.drawText(screen,font,color,row,text)

	return

# Display Airplay info
def displayAirplay(display,radio,font):
	info = radio.getAirplayInfo()
	artist = info[0]
	title = info[1]
	album = info[2]

	lcolor = getLabelColor(display.config.getDisplayLabelsColor())
	color = pygame.Color(lcolor)
	column = 4
	columnPos = display.getColumnPos(column)
	columns = display.getColumns()
	max_columns = columns - 5

	linebuf = 1
	if len(artist) > max_columns:
		artist = display.scroll(artist,linebuf,max)

	linebuf += 1
	if len(title) > max_columns:
		title = display.scroll(title,linebuf,max)

	linebuf += 1
	if len(album) > max_columns:
		title = display.scroll(album,linebuf,max)

	row = 1
	DisplayWindow.drawText(screen,font,color,row,artist)

	row += 1
	DisplayWindow.drawText(screen,font,color,row,title)

	row += 1
	DisplayWindow.drawText(screen,font,color,row,album)

	# Display Airplay icon
	AirplayImage = Image(pygame)
	mysize = (190,190)
	path = "images/airplay_icon.png"
	xpos = screen.rect.center[0] - 95
	ypos = display.getRowPos(6.5)
	mypos = (xpos,ypos)
	AirplayImage.draw(screen,path,(mypos),(mysize))
	return

# Display left arrow (Position on first station/track)
def drawLeftArrow(display,screen,LeftArrow):
	mysize = (30,30)
	xPos = display.getColumnPos(50.5)
	yPos = display.getRowPos(9)
	myPos = (xPos,yPos)
	path = "images/arrow_left_double.png"
	LeftArrow.draw(screen,path,(myPos),(mysize))
	return 

# Display right arrow (Position on first station/track)
def drawRightArrow(display,screen,RightArrow):
	mysize = (30,30)
	xPos = display.getColumnPos(50.5)
	yPos = display.getRowPos(11.75)
	myPos = (xPos,yPos)
	dir = os.path.dirname(__file__)
	path = "images/arrow_right_double.png"
	RightArrow.draw(screen,path,(myPos),(mysize))
	return 

# Display Artwork
def displayArtwork(screen,display,path):
	ArtworkImage = Image(pygame)
	mysize = (190,190)
	xPos = screen.rect.center[0] - 95
	yPos = display.getRowPos(6.5)
	myPos = (xPos,yPos)
	ArtworkImage.draw(screen,path,(myPos),(mysize),currentdir=False)
	return ArtworkImage

# This routine renders the new text ready to be drawn
def renderText(text,myfont,screen,row,column,color):
	textsurface = myfont.render(text, False, (color))
	screen.blit(textsurface,(column,row))
	return

# Get artwork from track
def getArtWork(radio):
	artwork = ""
	if os.path.isfile(ArtworkFile):
		os.remove(ArtworkFile)
	filename = radio.getFileName()
	filename = MusicDirectory + '/' + filename
	cmd = 'ffmpeg -i ' + '"' + filename + '" ' + ArtworkFile + ' > /dev/null 2>&1'
	radio.execCommand(cmd)
	if os.path.isfile(ArtworkFile):
		artwork = ArtworkFile
		log.message("Artwork " + artwork, log.DEBUG)
	return artwork

# Handle radio event
def handleEvent(radio,radioEvent):
	global artwork_file
	artwork_file = ''
	event_type = radioEvent.getType()
	source_type = radio.getSourceType()
	msg = "radioEvent.detected " + str(event_type) + ' ' + radioEvent.getName()
	log.message(msg, log.DEBUG)
	
	if event_type == radioEvent.SHUTDOWN:
		radio.stop()
		print "doShutdown", radio.config.doShutdown()
		if radio.config.doShutdown():
			radio.shutdown() # Shutdown the system
		else:
			sys.exit(0)

	elif event_type == radioEvent.CHANNEL_UP:
		radio.channelUp()
		if source_type == radio.source.MEDIA:
			artwork_file = getArtWork(radio)

	elif event_type == radioEvent.CHANNEL_DOWN:
		radio.channelDown()
		if source_type == radio.source.MEDIA:
			artwork_file = getArtWork(radio)

	elif event_type == radioEvent.VOLUME_UP:
		radio.increaseVolume()

	elif event_type == radioEvent.VOLUME_DOWN:
		radio.decreaseVolume()

	elif event_type == radioEvent.MUTE_BUTTON_DOWN:
		if radio.muted():
			radio.unmute()
		else:
			radio.mute()

	elif event_type == radioEvent.MPD_CLIENT_CHANGE:
		log.message("radioEvent Client Change",log.DEBUG)
		if source_type == radio.source.MEDIA:
			artwork_file = getArtWork(radio)
		
	elif event_type == radioEvent.LOAD_RADIO or event_type == radioEvent.LOAD_MEDIA \
			   or event_type == radioEvent.LOAD_AIRPLAY:
		handleSourceChange(radioEvent,radio,message)

	radioEvent.clear()
	return

# Display dialog with OK button
def displayDialog(title):
	global dialog
	btn_ok = sgc.Button(label="OK", pos=(30,60))
	dialog = sgc.Dialog(widget=btn_ok, title=title)
	btn_ok.onclick = hideDialog()
	dialog.rect.center = screen.rect.center
	dialog.add(order=9)
	return

def hideDialog():
	global dialog
	if dialog != None:
		dialog.remove()
	return

# Handler for source change events (also from the web interface)
def handleSourceChange(event,radio,message):
	msg = ''
	event_type = event.getType()

	if event_type == event.LOAD_RADIO:
		msg = message.get('loading_radio')
		message.speak(msg)
		radio.cycleWebSource(radio.source.RADIO)

	elif event_type == event.LOAD_MEDIA:
		msg = message.get('loading_media')
		message.speak(msg)
		radio.cycleWebSource(radio.source.MEDIA)

	elif event_type == event.LOAD_AIRPLAY:
		msg = message.get('starting_airplay')
		message.speak(msg)
		if display.config.getAirplay():
			radio.cycleWebSource(radio.source.AIRPLAY)

	new_source = radio.getNewSourceType()
	log.message("loadSource new type = " + str(new_source), log.DEBUG)
	if new_source >= 0:
		radio.loadSource()
	return

# Handle source type radio buttons
def handleSourceEvent(event,radio,display):
	if event.gui_type == "select":
		if event.widget is widget.select_list:
		 	display.setSearchMode(display.SEARCH_LIST)
		elif event.widget is widget.select_playlists:
		 	display.setSearchMode(display.SEARCH_PLAYLIST)
		elif event.widget is widget.select_artists:
			if radio.source.getType() == radio.source.MEDIA:
				display.setSearchMode(display.SEARCH_ARTISTS)
			else:
				# Force back to list
				widget.select_list.activate()
		display.setMode(display.MAIN)
	return display.getSearchMode()

# Handle search event (Search window click)
def handleSearchEvent(radio,event,SearchWindow,display,searchID):
	global Artists

	if event.type == pygame.MOUSEBUTTONDOWN:
		# Event in the search window (Not the slider) 
		if SearchWindow.clicked(event):
			idx = SearchWindow.index()
			searchID = selectNew(radio,display,widget,Artists,searchID,SearchWindow,idx)

		elif SearchWindow.slider.clicked(event):
			searchID = SearchWindow.slider.getPosition()

	# Search window slider dragged
	elif SearchWindow.slider.dragged(event):
		searchID = SearchWindow.slider.getPosition()
	return searchID

# Draw the radio/media display window
def drawDisplayWindow(surface,screen,display):
	# Create display window for radio/media information
	DisplayWindow = TextRectangle(pygame)
	xPos = display.getColumnPos(6)
	yPos = display.getRowPos(3)	
	xSize = display.getColumnPos(47)
	ySize = display.getRowPos(3)	
	border = 4
	wcolor = getLabelColor(display.config.getDisplayWindowColor())
	color = pygame.Color(wcolor)
	bcolor = (25,25,25) 	# Border colour
	DisplayWindow.draw(screen,color,bcolor,xPos,yPos,xSize,ySize,border)
	return DisplayWindow

# Search ID is between 1 and len of the search array
def setSearchID(array,searchID):
	newID = searchID
	if newID < 1:
		newID = 1
	elif newID > len(array):
		newID = len(array)
	return newID

# Draw Up Icon
def drawUpIcon(display,screen,upIcon):
	xPos = display.getColumnPos(50)
	yPos = display.getRowPos(7)
	upIcon.draw(screen,xPos,yPos)
	return 

# Draw Down Icon
def drawDownIcon(display,screen,downIcon):
	xPos = display.getColumnPos(50)
	yPos = display.getRowPos(13.5)
	downIcon.draw(screen,xPos,yPos)
	return 

# Draw Equalizer Icon
def drawEqualizerIcon(display,screen,equalizerIcon,draw_equalizer_icon):
	if draw_equalizer_icon:
		xPos = display.getColumnPos(50)
		yPos = display.getRowPos(16.3)
		equalizerIcon.draw(screen,xPos,yPos)
	return 

# Check that the label colour is valid 
def getLabelColor(lcolor):
	try:
		pygame.Color(lcolor)
	except:
		lcolor = 'white'
	return lcolor

# Draw option buttons (Random,Repeat and Consume)
def drawOptionButtons(display,screen,radio,RandomButton,RepeatButton,ConsumeButton,SingleButton):
	lcolor = getLabelColor(display.config.getLabelsColor())
	row = 13.5
	xPos = display.getColumnPos(3)
	yPos = display.getRowPos(row)
	label = "Random"
	RandomButton.draw(screen,xPos,yPos,label,lcolor)
	row += 1.3
	yPos = display.getRowPos(row)
	label = "Repeat"
	RepeatButton.draw(screen,xPos,yPos,label,lcolor)
	row += 1.3
	yPos = display.getRowPos(row)
	label = "Consume"
	ConsumeButton.draw(screen,xPos,yPos,label,lcolor)
	row += 1.3
	yPos = display.getRowPos(row)
	label = "Single"
	SingleButton.draw(screen,xPos,yPos,label,lcolor)
	return 

# Draw the radio/media display window
def drawSearchWindow(surface,screen,display,searchID):
	# Create display window for radio/media information
	global Artists
	textArray=[]
	Artists = {}
	SearchWindow = ScrollBox(pygame)
	xPos = display.getColumnPos(14)
	yPos = display.getRowPos(7)	
	xSize = display.getColumnPos(30)
	lines = 8
	ySize = display.getRowPos(lines)	
	border = 3
	color = (200,200,200)
	bcolor = (25,25,25)
	SearchWindow.draw(screen,color,bcolor,lines,xPos,yPos,xSize,ySize,border)

	# Add playlist to search window
	font = pygame.font.SysFont('freesans', 20, bold=True)
	color = (0,0,0)

	# Display list, playlist artists
	id = 1
	idx = 0
	search_mode = display.getSearchMode()
	if search_mode == display.SEARCH_PLAYLIST:
		textArray = getPlaylists()	# Get playlists
	else:
		textArray = radio.getPlayList()	# Current playlist contents
	
	source_type = radio.source.getType()

	if search_mode == display.SEARCH_ARTISTS and source_type == radio.source.MEDIA:
		previous = '' 
		for i in range (len(textArray)):
			line = textArray[i]
			if '/' in line:
				vals = line.split('/')	
				line = vals[len(vals)-1]
			vals = line.split(' - ')	
			artist = vals[0].lstrip()
			
			if artist != previous:
				previous = artist
				Artists[artist] = i  # Add to artists array 
		textArray = sorted(Artists.keys())

	searchID = setSearchID(textArray,searchID) 
	idx = searchID - 1

	iLeng = len(textArray)
	if iLeng > 0:
		SearchWindow.drawText(screen,font,color,textArray[idx:])
		lcolor = getLabelColor(display.config.getLabelsColor())
		scolor = getLabelColor(display.config.getSliderColor())
		SearchWindow.slider.setPosition(searchID,iLeng,scolor,lcolor)

	return SearchWindow

# Get the playlists for search display
def getPlaylists():
	list = []
	playlists = radio.getPlaylists()
	values = playlists.keys()
	idx = 0

	# Replace underscores with spaces
	for idx in range(len(values)):
		values[idx] = values[idx].replace('_',' ')
		values[idx] = values[idx].lstrip()
		list.append(values[idx])
	return list

# Create Channel Up button (Also exits Airplay)
def drawChannelUpButton(source_type,sgc,display):
	# Set button label
	if source_type == radio.source.AIRPLAY:
		label = "Exit\nAirplay"
	elif source_type == radio.source.MEDIA:
		label = "Track\nUp"
	else:
		label = "Station\nUp"

	column = 14
	xPos = display.getColumnPos(column)
	yPos = display.getRowPos(16)
	ChannelUpButton = sgc.Button(label=label, pos=(xPos,yPos))
	ChannelUpButton.add(order=1)
	return ChannelUpButton

# Channel Down button
def drawChannelDownButton(source_type,sgc,display):
	# Set button label
	if source_type == radio.source.MEDIA:
		label = "Track\nDown"
	else:
		label = "Station\nDown"

	column = 34
	xPos = display.getColumnPos(column)
	yPos = display.getRowPos(16)
	ChannelDownButton = sgc.Button(label=label, pos=(xPos,yPos))
	ChannelDownButton.add(order=2)
	return ChannelDownButton

# Get pid
def getPid():
	pid = None
	if os.path.exists(pidfile):	
		pf = file(pidfile,'r')
		pid = int(pf.read().strip())
	return pid

# Stop program if stop specified on the command line
def stop():
	pid = getPid()
	if pid != None:
		os.kill(pid, signal.SIGHUP)
	exit(0)

# Check if program already running
def checkPid(pidfile):
	pid = getPid()
	if pid != None:
		try:
			os.kill(pid, 0)
			msg =  "Error: gradio or radiod already running, pid " + str(pid)
			log.message(msg,log.ERROR)
			print msg
			exit()
		except Exception as e:
			os.remove(pidfile)
	# Write the pidfile
	pid = str(os.getpid())
	pf = file(pidfile,'w')
	pf.write(pid + '\n')
	pf.close()
	return pid	


# Return ID of selected item from the search window 
def selectNew(radio,display,widget,Artists,searchID,SearchWindow,idx):
	id = radio.getCurrentID()
	search_mode = display.getSearchMode()
	if search_mode == display.SEARCH_PLAYLIST:
		radio.source.setIndex(searchID + idx - 1)
		radio.loadSource()
		widget.select_list.activate()
		searchID = radio.setCurrentID(1)
		display.setSearchMode(display.SEARCH_LIST)

	elif search_mode == display.SEARCH_ARTISTS:
		if Artists != None:
			artistKey = SearchWindow.getText(idx)
			print "Key=",str(artistKey)
			widget.select_list.activate()
			searchID = Artists.get(artistKey) + 1
			radio.play(searchID)

	else:
		# Radio selection
		radio.play(searchID + idx)

	display.setMode(display.MAIN)
	return searchID
		

# Keyboard toggle radio options
def toggleOption(radio,key,RandomButton,RepeatButton,ConsumeButton,SingleButton,widget):
	true_false = True
	if key == K_r:
		if radio.getRandom():
			true_false = False
		RandomButton.activate(true_false)
		radio.setRandom(true_false)

	if key == K_t:
		if radio.getRepeat():
			true_false = False
		RepeatButton.activate(true_false)
		radio.setRepeat(true_false)

	if key == K_c:
		if radio.getConsume():
			true_false = False
		ConsumeButton.activate(true_false)
		radio.setConsume(true_false)

	if key == K_s:
		if radio.getSingle():
			true_false = False
		SingleButton.activate(true_false)
		radio.setSingle(true_false)

	elif key == K_l:
		widget.select_list.activate()

	elif key == K_p:
		widget.select_playlists.activate()

	elif key == K_a:
		widget.select_artists.activate()

	elif key == K_m:
		if radio.muted():
			radio.unmute()
		else:
			radio.mute()
	return

# Handle keyboard key event See https://www.pygame.org/docs/ref/key.html
def handleKeyEvent(key,radioEvent,searchID,srange):
	if key == K_KP_PLUS or  key == K_PLUS:
	    radioEvent.set(radioEvent.VOLUME_UP)

	elif key == K_KP_MINUS  or  key == K_MINUS:
	    radioEvent.set(radioEvent.VOLUME_DOWN)

	elif key == K_PAGEUP:
	    radioEvent.set(radioEvent.CHANNEL_UP)

	elif key == K_PAGEDOWN:
	    radioEvent.set(radioEvent.CHANNEL_DOWN)

	elif key == K_DOWN:
	    searchID += 1

	elif key == K_UP:
	    searchID -= 1

	elif key == K_LEFT:
	    searchID = 1

	elif key == K_RIGHT:
	    searchID = srange

	elif key == K_ESCAPE:
	    quit()

	elif event.key == K_q:
	    mods = pygame.key.get_mods()
	    if mods & pygame.KMOD_CTRL:
		    radioEvent.set(radioEvent.SHUTDOWN)

	if searchID > srange:
		searchID = srange
	elif searchID < 1:
		searchID = 1
	return searchID

# This routine changes the labels display between Station and Track
def displayLabels(radio,ChannelUpButton,ChannelDownButton):
	if source_type == radio.source.AIRPLAY:
		uplabel = "Exit\nAirplay"
		downlabel = "   \n    "
	elif source_type == radio.source.MEDIA:
		uplabel = "Track\nUp"
		downlabel = "Track\nDown"
	else:
		uplabel = "Station\nUp"
		downlabel = "Station\nDown"

	# Re-display new label
	ChannelUpButton.newLabel(uplabel)
	ChannelDownButton.newLabel(downlabel)
	return

# Open equalizer window
def openEqualizer(radio,equalizer_cmd):
	dir = os.path.dirname(__file__)
	cmd_file = open(dir + '/' + equalizer_cmd,"r")
	for line in cmd_file: 
		if line.startswith('lxterminal'):
			radio.execCommand(line)
			break
	return

# Set draw equalizer true/false
def displayEqualizerIcon(display):
	if display.config.fullScreen():
		draw_equalizer_icon = False
	else:
		draw_equalizer_icon = True
	return draw_equalizer_icon

# Exit the program only
def quit():
	radio.stop()
	if os.path.isfile(pidfile):
		os.remove(pidfile)
	sys.exit(0)

# Main routine
if __name__ == "__main__":
	# Do not override locale settings
	locale.setlocale(locale.LC_ALL, '')

	font = pygame.font.SysFont('freesans', 13)
	display = GraphicDisplay(font)

	if display.config.fullScreen():
		flags = FULLSCREEN|DOUBLEBUF|RESIZABLE
	else:
		flags = 0
	screen = sgc.surface.Screen((size),flags)  

	log.init('radio')
	# Stop command
	if len(sys.argv) > 1 and sys.argv[1] == 'stop':
		os.popen("sudo service mpd stop")
		stop()

	os.popen("systemctl stop radiod")

	pid = checkPid(pidfile)

	log.message("gradio running, pid " + str(pid), log.INFO)

	signal.signal(signal.SIGTERM,signalHandler)

	# see https://www.webucator.com/blog/2015/03/python-color-constants-module/
	# Paint screen background (Keep at start of draw routines)
	wallpaper = display.config.getWallPaper()
	if len(wallpaper) > 1:
		pic=pygame.image.load(wallpaper)
		screen.blit(pygame.transform.scale(pic,size),(0,0))
	else:
		wcolor = display.config.getWindowColor()
		try:
			screen.fill(Color(wcolor))
		except:
			log.message("Invalid window_color " + wcolor, log.ERROR)
			wcolor = "blue"
			screen.fill(Color(wcolor))

	text = "Loading Radio Stations"
	displayPopup(screen,radio,text)
	pygame.display.flip()

	radioEvent = Event()	    # Add radio event handler
	radio = Radio(rmenu,radioEvent)  # Define radio

	# Set up Xauthority for root user
	radio.execCommand("sudo cp /home/pi/.Xauthority /root/")

	setupRadio(radio)
	radio.setTranslate(True)	# Switch off text translation

	version = radio.getVersion()
	caption = display.config.getWindowTitle() 
	caption = caption.replace('%V',version)
	pygame.display.set_caption(caption)

	draw_equalizer_icon = displayEqualizerIcon(display)

	# Create SGC widgets
	labels_color_name = display.config.getLabelsColor()
	try:
		label_col = pygame.Color(labels_color_name)
	except:
		log.message("Invalid labels_color " + labels_color_name, log.ERROR)
		label_col = pygame.Color('white')

	widget = Widgets(sgc,radio,display,label_col)

	# Draw the Up/Down buttons
	source_type = radio.getSourceType()
	ChannelUpButton = drawChannelUpButton(source_type,sgc,display)
	ChannelDownButton = drawChannelDownButton(source_type,sgc,display)
	volume = radio.getVolume()
	widget.VolumeSlider.value = volume
	current_volume = 0

	# Create screen controls
	MuteButton = MuteButton(pygame)
	upIcon = UpIcon(pygame)
	downIcon = DownIcon(pygame)
	LeftArrow = Image(pygame)
	RightArrow = Image(pygame)
	equalizerIcon = EqualizerIcon(pygame)
	drawUpIcon(display,screen,upIcon)
	drawDownIcon(display,screen,downIcon)
	drawLeftArrow(display,screen,LeftArrow)
	drawRightArrow(display,screen,RightArrow)
	drawEqualizerIcon(display,screen,equalizerIcon,draw_equalizer_icon)

	# Option buttons
	RandomButton = OptionButton(pygame)
	RepeatButton = OptionButton(pygame)
	ConsumeButton = OptionButton(pygame)
	SingleButton = OptionButton(pygame)
        drawOptionButtons(display,screen,radio,RandomButton,RepeatButton,
				ConsumeButton,SingleButton)
        RandomButton.activate(radio.getRandom())

	# Create display window for radio/media information
	id = radio.getCurrentID()	# Search window index
	searchID = id
	DisplayWindow = drawDisplayWindow(surface,screen,display)
	SearchWindow = drawSearchWindow(surface,screen,display,id)
        ArtworkImage = None

	# Main processing loop
	while True:
	    tick = clock.tick(30)
	    source_type = radio.getSourceType()

	    # Reset the draw equalizer icon flag
	    if int(commands.getoutput('pidof %s |wc -w' % "alsamixer")) < 1:
		draw_equalizer_icon = displayEqualizerIcon(display)
		if draw_equalizer_icon:
			equalizerIcon.enable()

	    # Handle Widget events
	    for event in pygame.event.get():
		# Send event to widgets
		sgc.event(event)
		if event.type == GUI:
		    if event.widget_type is sgc.Button:
			print "Button event",event.gui_type

		    # Radio source type buttons
		    elif event.widget_type is sgc.Radio:
			if event.gui_type == "select":
				artwork_file = ''
				new_source = handleSourceEvent(event,radio,display)
				if new_source != display.SEARCH_LIST:
					searchID = 1

		    elif event.widget_type is sgc.Switch:
			print "Switch Event ",event.gui_type

		    elif event.widget_type is sgc.Combo:
			log.message("sgc.Combo", log.DEBUG)
			radio.source.cycleType(widget.sourceCombo.selection)
			radio.setReload(True)

		    # Up and down channel/track buttons
		    if event.widget is ChannelUpButton and event.gui_type == "click":
			if source_type == radio.source.AIRPLAY:
				radio.source.cycleType(radio.source.RADIO)
				radio.setReload(True)
			else: 
				radioEvent.set(radioEvent.CHANNEL_UP)

		    elif event.widget is ChannelDownButton and event.gui_type == "click":
			if source_type != radio.source.AIRPLAY:
				radioEvent.set(radioEvent.CHANNEL_DOWN)

		    display.setMode(display.MAIN)

		if event.type == pygame.MOUSEBUTTONDOWN:

		# Display window mouse down changes display mode
			if DisplayWindow.clicked(event):
				mode = display.cycleMode()

			elif upIcon.clicked():
				searchID -= 1
				if searchID < 1:
					searchID = 1

			elif downIcon.clicked():
				srange = SearchWindow.slider.getRange()
				searchID += 1
				if searchID > srange:
					searchID = srange

			elif LeftArrow.clicked():
				searchID = 1

			elif RightArrow.clicked():
				searchID = SearchWindow.slider.getRange()

			elif draw_equalizer_icon and equalizerIcon.clicked():
				openEqualizer(radio,"equalizer.cmd")
				draw_equalizer_icon = False
				equalizerIcon.disable()

			elif RandomButton.clicked(event):
				if RandomButton.isActive():
					radio.setRandom(False)
					RandomButton.activate(False)
				else:
					radio.setRandom(True)
					RandomButton.activate(True)

			elif RepeatButton.clicked(event):
				if RepeatButton.isActive():
					radio.setRepeat(False)
					RepeatButton.activate(False)
				else:
					radio.setRepeat(True)
					RepeatButton.activate(True)

			elif ConsumeButton.clicked(event):
				if ConsumeButton.isActive():
					radio.setConsume(False)
					ConsumeButton.activate(False)
				else:
					radio.setConsume(True)
					ConsumeButton.activate(True)

			elif SingleButton.clicked(event):
				if SingleButton.isActive():
					radio.setSingle(False)
					SingleButton.activate(False)
				else:
					radio.setSingle(True)
					SingleButton.activate(True)

			if MuteButton.pressed():
			    if radio.muted():
				widget.VolumeSlider.label = "Volume"
				radio.unmute()
			    else:
				radio.mute()
				widget.VolumeSlider.label = "Muted"
		    
	    	# Temporary exit on ESC key during development
		elif event.type == KEYDOWN:
			print "Key", event.key
			srange = SearchWindow.slider.getRange()
			searchID = handleKeyEvent(event.key,radioEvent,searchID,srange)
			toggleOption(radio,event.key,RandomButton,RepeatButton,
				ConsumeButton,SingleButton,widget)
			if event.key == K_RETURN:
				searchID = selectNew(radio,display,widget,Artists,
						searchID,SearchWindow,0)
			elif event.key == K_d:
				mode = display.cycleMode()

			elif event.key == K_e and draw_equalizer_icon:
				openEqualizer(radio,"equalizer.cmd")
				draw_equalizer_icon = False

		# Window quit stops the radio
		elif event.type == QUIT:
		    quit()

		else:
		    volume =  int(widget.VolumeSlider.value)
		    if volume != current_volume:
			radio.setRealVolume(volume)


		# Event in the search window or artwork image clicked
		if source_type != radio.source.AIRPLAY:
			if ArtworkImage != None and len(artwork_file) > 0:
				if ArtworkImage.clicked():
					print "Artwork click"
			else:
				searchID = handleSearchEvent(radio,event,SearchWindow,
								display,searchID)
	    # Detect radio events
	    if radioEvent.detected():
		log.message("radioEvent.detected", log.DEBUG)
		handleEvent(radio,radioEvent)
	    elif radio.getReload():
		displayLoadingSource(screen,myfont,radio,message)
		radio.loadSource()      # Load new source
		radio.setReload(False) 
	    else:
		# Keep the connection to MPD alive
		radio.keepAlive(10)

	    # Pick up external volume changes
	    volume = radio.getVolume()
	    if current_volume != volume:
		widget.VolumeSlider.value = volume
		current_volume = volume

	    # Paint screen background (Keep at start of draw routines)
	    if len(wallpaper) > 1:
		    pic=pygame.image.load(wallpaper)
		    screen.blit(pygame.transform.scale(pic,size),(0,0))
	    else:
		    screen.fill(Color(wcolor))

            surface=pygame.Surface((size))

	    # Display the radio details
	    displayTimeDate(screen,myfont,radio,message)

	    # Display Up Down labels
	    displayLabels(radio,ChannelUpButton,ChannelDownButton)

	    DisplayWindow = drawDisplayWindow(surface,screen,display)

	    if source_type == radio.source.AIRPLAY:
		displayAirplay(display,radio,myfont)
	    else:
		if radio.getCurrentID() < 1 and source_type == radio.source.MEDIA:
		 	display.setSearchMode(display.SEARCH_PLAYLIST)
			widget.select_playlists.activate()
			SearchWindow = drawSearchWindow(surface,screen,display,id)
			displayLoadingSource(screen,myfont,radio,message)
			radio.updateLibrary()
		else:
			if len(artwork_file) > 0:
				ArtworkImage = displayArtwork(screen,display,artwork_file)
			else:
				SearchWindow = drawSearchWindow(surface,screen,display,searchID)

			# Display the information window
			if display.getMode() == display.INFO:
				displayInfo(screen,myfont,radio,message)
			else:
				displayCurrent(screen,myfont,radio,message)

	    # Draw options and other controls
	    xPos = display.getColumnPos(26)
	    yPos = display.getRowPos(18)
	    MuteButton.draw(screen,display,(xPos,yPos),radio.muted())

	    # Draw navigation buttons if no artwork displayed
	    if len(artwork_file) < 1:
		    drawUpIcon(display,screen,upIcon)
		    drawDownIcon(display,screen,downIcon)
		    drawLeftArrow(display,screen,LeftArrow)
		    drawRightArrow(display,screen,RightArrow)

	    if draw_equalizer_icon:
		    drawEqualizerIcon(display,screen,equalizerIcon,draw_equalizer_icon)
	    drawOptionButtons(display,screen,radio,RandomButton,RepeatButton,
					ConsumeButton,SingleButton)
	    RandomButton.activate(radio.getRandom())

	    # Update SGC and pygame displays
	    sgc.update(tick)
	    pygame.display.flip()

	# End of while loop

# End of program
