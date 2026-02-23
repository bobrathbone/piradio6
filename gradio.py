#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Raspberry Pi Graphical Internet Radio 
# This program interfaces with the Music Player Daemon MPD
#
# $Id: gradio.py,v 1.108 2026/02/02 05:15:48 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#      The authors shall not be liable for any loss or damage however caused.
#
# This program uses the SGC widget routines written by Sam Bull
# Copyright (C) SGC widget routines 2010-2013  Sam Bull
# SGC documentation: https://program.sambull.org/sgc/sgc.widgets.html
#
# Icons used in the graphic versions of the radio.
# Clipart library http://clipart-library.com
# IconSeeker http://www.iconseeker.com

import os
import sys
import time
import pdb
import random
import socket
import signal
import locale
import shutil
import subprocess
from time import strftime

# Radio imports
from log_class import Log
from config_class import Configuration
from radio_class import Radio
from event_class import Event
from menu_class import Menu
from rss_class import Rss
from message_class import Message
from graphic_display import GraphicDisplay
from translate_class import Translate
from artwork_class import Artwork
import traceback

# Pygame controls
from gcontrols_class import *
from pygame.locals import *

config = Configuration()
translate = Translate()
radio = None
log = Log()
rmenu = Menu()
rss = Rss(translate)
display = None
radioEvent = None
message = None
run = True
_connecting = False

import pygame
from pygame.locals import *

size = (800,480)
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

Artists = {}     # Dictionary of artists

IgnoreSearchEvents = False  # Ignore search events if artwork displayed

# Files for artwork extraction
pidfile = "/var/run/radiod.pid"
MpdLibDir = "/var/lib/mpd"
MusicDirectory =  MpdLibDir + "/music"
RadioLib =  "/var/lib/radiod"
MediaArtworkFile = "/tmp/artwork.jpg"
wallpaper = ''      # Background wallpaper
artwork_file = ""   # Album artwork file name
station_artwork_file = RadioLib + "/radio_artwork.jpg"
album_artwork_file = RadioLib + "/album_artwork.jpg"
no_image_file = "images/no_image.jpg"

# Signal SEGV and ABRT handler - Try to dump core
def signalCrash(signal,frame):
    sSig = "Unknown"
    if signal == 11:
        sSig = "SEGV"
    elif signal == 6:
        sSig = "ABRT"
    msg = "Received signal %s (%s)" %  (str(signal),sSig)
    print (msg)
    log.message(msg, log.CRITICAL)
    msg = traceback.format_exc()
    print(msg)
    fname = '/traceback_radiod'
    with open(fname, 'w') as f:
        f.write(msg)
    msg = "Dump written to %s" %  fname
    print(msg)
    log.message(msg, log.CRITICAL)
    traceback.print_stack()
    os.abort()

# Signal SIGTERM handler
def signalHandler(signal,frame):
    global display
    global radio
    global log
    pid = os.getpid()

    print("signalHandler",signal)

    log.message("Radio stopped, PID " + str(pid), log.INFO)
    radio.stop()
    exit()

# Start the radio and MPD
def setupRadio(radio):
    global radioEvent,message,display,screen
    log.message("Starting graphic radio ", log.INFO)

    # Stop the pygame mixer as it conflicts with MPD
    pygame.mixer.quit()

    radio.start()          # Start it
    radio.loadSource()        # Load sources and playlists

    return

# This routine displays the time string
def displayTimeDate(screen,myfont,radio,message):
    dateFormat = config.graphic_dateformat
    timedate = strftime(dateFormat)
    timedate = uEncode(timedate)

    try:
        color = pygame.Color(display.config.banner_color)
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

# Display message popup, bcolor is the border color
def displayPopup(screen,text,bcolor=(255,255,255)):
    text = uEncode(text)
    displayPopup = TextRectangle(pygame)    # Text window
    font = pygame.font.SysFont('freesans', 30, bold=True)
    fx,fy = font.size(text + "A")
    xPos = int((size[0]/2) - (fx/2))
    yPos = size[1]/2
    xSize = fx
    ySize = fy
    color = (50,50,50)
    border = 4
    displayPopup.draw(screen,color,bcolor,xPos,yPos,xSize,ySize,border)
    line = 1        # Not used but required
    color = (255,255,255)
    displayPopup.drawText(screen,font,color,line,text)
    pygame.display.flip()
    return

# Handle shutdown button click
def handleShutdown(screen):
    if config.shutdown:
        msg = message.get("shutdown")
        displayPopup(screen,msg,bcolor=(0,0,32))
        time.sleep(3)
        radio.shutdown()
    else:
        radio.stop()
        msg = message.get("stop")
        displayPopup(screen,msg,bcolor=(0,0,32))
        time.sleep(3)
        sys.exit(0)

# Display source load
def displayLoadingSource(screen,font,radio,message):
    lcolor = getLabelColor(display.config.display_window_labels_color)
    color = pygame.Color(lcolor)
    sourceName = radio.getSourceName()
    column = 12
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
    lcolor = getLabelColor(display.config.display_window_labels_color)
    color = pygame.Color(lcolor)
    startColumn = display.getStartColumn()
    #column = 12
    column = int(startColumn)
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
    ipaddr = ipaddr.split()[0]
    sIP = "IP address: " + ipaddr
    sHostname = 'Hostname: ' +  socket.gethostname()

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

# Encode text to UTF-8
def uEncode(text):
    string = text
    try:
        string = str(text,"utf-8") 
    except:
        pass
    return string

# Display currently playing radio station or track
def displayCurrent(screen,font,radio,message):
    global _connecting
    global rss_delay,rss_line
    column = 5
    columns = display.getColumns()
    startColumn = display.getStartColumn()
    max_columns = int(columns - startColumn * 2)
    columnPos = display.getColumnPos(column)

    search_name = radio.getSearchName(True)
    search_name = uEncode(search_name)

    title = radio.getCurrentTitle()
    title = uEncode(title)

    errorStr = ''
    if radio.gotError():
        errorStr = radio.getErrorString()

    # Scroll title if necessary
    linebuf = 1
    if len(title) > max_columns:
        # Cannot scroll long titles and RSS together
        if display.getMode() == display.RSS:
            title = title[:max_columns]
        else:
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
    lcolor = getLabelColor(display.config.display_window_labels_color)
    color = pygame.Color(lcolor)
    rowPos = display.getRowPos(row)

    if source_type == radio.source.MEDIA:
        progress = radio.getProgress()

        current_artist = radio.getCurrentArtist()
        current_artist = uEncode(current_artist)
        current_album = radio.getCurrentAlbum()
        current_album = uEncode(current_album)

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
            text = uEncode(text)
        else:
            if len(current_album) > 0:
                text = progress + " " + current_album
            else:
                text = progress
        row = 3
        DisplayWindow.drawText(screen,font,color,row,text)
    else:
        # Radio station display
        station_name = radio.getCurrentStationName()[:max_columns]
        linebuf += 1
        if len(station_name) > max_columns:
            station_name = display.scroll(station_name,linebuf,max_columns)

        if len(title) < 1:
            title = message.get('title_unknown')
            station_name = search_name

        if len(station_name) < 1:
            station_name = search_name

        # First row
        row = 1
        
        DisplayWindow.drawText(screen,font,color,row,search_name)

        # Second row
        row = 2
        if len(errorStr) > 0:
            title = errorStr
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
                text = text + ": " + str(bitrate) + 'Kb'
                _connecting = False
            else:
                if len(errorStr) > 0:
                    text = text + ': ' + message.get('connection_error')
                    
                elif not _connecting:
                    text = text + ': ' + message.get('connecting')
                    _connecting = True
                else:
                   text = message.get('no_information')

        DisplayWindow.drawText(screen,font,color,row,text)

    return

# Display Spotify information and logo
def displaySpotify(display,radio,font):
    lcolor = getLabelColor(display.config.display_window_labels_color)
    color = pygame.Color(lcolor)
    columns = display.getColumns()
    max_columns = columns - 20

    row = 1
    text = "Spotify receiver running"
    DisplayWindow.drawText(screen,font,color,row,text)

    row += 1
    info = radio.getSpotifyInfo()
    
    if len(info) < 1:
        info = message.get('waiting_for_spotify_client')
    else:
        elements = info.split('"')
        if len(elements) >= 3:
            info = elements[1]
        
    if len(info) > max_columns:
        info = display.scroll(info,2,max_columns)

    DisplayWindow.drawText(screen,font,color,row,info)

    sHostname = 'Raspotify: ' + socket.gethostname() 
    row += 1
    DisplayWindow.drawText(screen,font,color,row,sHostname)

    # Display Spotify icon
    rows = display.getRows()
    SpotifyImage = Image(pygame)
    if rows < 20:
        mysize = (196,55)
        ypos = display.getRowPos(6.5)
    else:
        mysize = (390,110)
        ypos = display.getRowPos(8.5)

    xpos = screen.rect.center[0] - mysize[0]/2 
    path = "images/spotify_logo.png"
    mypos = (xpos,ypos)
    SpotifyImage.draw(screen,path,(mypos),(mysize))
    return

# Display Airplay info
def displayAirplay(display,radio,font):
    info = radio.getAirplayInfo()
    artist = info[0]
    title = info[1]
    album = info[2]

    lcolor = getLabelColor(display.config.display_window_labels_color)
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
    rows = display.getRows()
    if rows < 20:
        mysize = (90,90)
        ypos = display.getRowPos(6.2)
    else:
        mysize = (190,190)
        ypos = display.getRowPos(6.5)

    path = "images/airplay_icon.png"
    xpos = screen.rect.center[0] - mysize[0]/2
    mypos = (xpos,ypos)
    AirplayImage.draw(screen,path,(mypos),(mysize))
    return

# Display left arrow (Position on first station/track)
def drawLeftArrow(display,screen,LeftArrow):
    mysize = (30,30)
    startColumn = display.getStartColumn()
    xPos = display.getColumnPos(startColumn + 48.5)
    yPos = display.getRowPos(9)
    myPos = (xPos,yPos)
    path = "images/arrow_left_double.png"
    LeftArrow.draw(screen,path,(myPos),(mysize))
    return 

# Display right arrow (Position on first station/track)
def drawRightArrow(display,screen,RightArrow):
    mysize = (30,30)
    startColumn = display.getStartColumn()
    xPos = display.getColumnPos(startColumn + 48.5)
    yPos = display.getRowPos(11.75)
    myPos = (xPos,yPos)
    dir = os.path.dirname(__file__)
    path = "images/arrow_right_double.png"
    RightArrow.draw(screen,path,(myPos),(mysize))
    return 

# Display Artwork
def displayArtwork(screen,display,path):
    #radio.getCurrentID()    # Make sure seek is complete
    # Get size of original image and get ratio of height to width
    OrigImage = pygame.image.load(path)
    size = OrigImage.get_size() 
    ratio = size[0]/size[1]

    # Define new image
    ArtworkImage = Image(pygame)
    rows = display.getRows()
    if rows > 20:
        # Artwork rows adjusted to match search window size
        if config.search_window_rows < 9:
            mysize = (220,220)
        else:
            mysize = (242,242)
    else:
        mysize = (160,160)

    # Restore ratio of original image
    mysize = (int(mysize[0] * ratio), mysize[1]) 

    # Limit size of of artwork
    ratio1 = 0.28
    ratio2 = 0.85
    desktop_info = pygame.display.Info()
    screen_width = desktop_info.current_w
    xLimit1 = int(screen_width * ratio1)
    xLimit2 = int(screen_width * ratio2)
    xPos = int(screen.rect.center[0] - (mysize[0]/2))
    if xPos < xLimit1:
        xPos = xLimit1
    if xLimit1 + mysize[0] > xLimit2:
        mysize = (xLimit2 - xLimit1, mysize[1])
    
    yPos = display.getRowPos(6.3)
    myPos = (xPos,yPos)
    # The following instruction is a temporary workaround for the problem 
    # of a bad image not being displayed.
    ArtworkImage.draw(screen,no_image_file,(myPos),(mysize),currentdir=False)
    # A good image will overwriite the no image available artwork above
    ArtworkImage.draw(screen,path,(myPos),(mysize),currentdir=False)
    return ArtworkImage

# This routine renders the new text ready to be drawn
def renderText(text,myfont,screen,row,column,color):
    textsurface = myfont.render(text, False, (color))
    screen.blit(textsurface,(column,row))
    return

# Return artwork from current station or track 
# The first artwork is from the station, subsequent are track/artist artwork
def getArtwork(station_artwork=False):
    if source_type == radio.source.MEDIA:
        artwork_file = getMediaArtwork(radio)
    else:
        artwork_file = getRadioArtwork(station_artwork)
    return artwork_file

# Handle artwork change. The first artwork is the station artwork. 
# Subsequent requests are for the album artwork (controlled by station_artwork)
def getRadioArtwork(station_artwork=False):
    global last_info
    last_info = None
    broadcast_info = artwork.get_broadcast_info(radio.client)
    log.message(broadcast_info, log.DEBUG)
    #shutil.copyfile(no_image_file, artwork_file)
    img = artwork.getCoverImageFromInfo(broadcast_info)
    artwork_file = album_artwork_file
    if img != None and broadcast_info != last_info:
        if station_artwork:
            artwork_file = station_artwork_file
            #print("station_artwork_file",station_artwork_file)
        else:
            artwork_file = album_artwork_file
            #print("album_artwork_file",album_artwork_file)

        f = open(artwork_file,"wb")
        f.write(img.getbuffer())
        f.close()
        log.message("getRadioArtwork wrote %s" % artwork_file, log.DEBUG)
        last_info = broadcast_info
    elif img == None:
        if os.path.exists(station_artwork_file):
            try:
                shutil.copyfile(station_artwork_file, artwork_file)
            except Exception as e:
                print(str(e))
                pass
    if artwork_file == "":
        shutil.copyfile(no_image_file, artwork_file)

    return artwork_file

# Get artwork from track
def getMediaArtwork(radio):
    artwork = ""
    if os.path.isfile(MediaArtworkFile):
        os.remove(MediaArtworkFile)
    filename = radio.getFileName()
    filename = MusicDirectory + '/' + filename
    cmd = 'ffmpeg -i ' + '"' + filename + '" ' + MediaArtworkFile + ' > /dev/null 2>&1'
    radio.execCommand(cmd)
    if os.path.isfile(MediaArtworkFile):
        artwork = MediaArtworkFile
        log.message("Artwork " + artwork, log.DEBUG)
    return artwork

# Handle radio event
def handleEvent(radio,radioEvent):
    global _connecting
    global artwork_file
    artwork_file = ''
    event_type = radioEvent.getType()
    source_type = radio.getSourceType()
    msg = "radioEvent.detected " + str(event_type) + ' ' + radioEvent.getName()
    log.message(msg, log.DEBUG)
    
    if event_type == radioEvent.SHUTDOWN:
        radio.stop()
        if config.shutdown:
            radio.shutdown() # Shutdown the system
        else:
            print("radioEvent.SHUTDOWN")
            sys.exit(0)

    elif event_type == radioEvent.CHANNEL_UP:
        radio.channelUp()
        artwork_file = getArtwork(True)
        _connecting = False

    elif event_type == radioEvent.CHANNEL_DOWN:
        radio.channelDown()
        artwork_file = getArtwork(True)
        _connecting = False

    elif event_type == radioEvent.VOLUME_UP:
        if radio.muted():
            radio.unmute()
        radio.increaseVolume()

    elif event_type == radioEvent.VOLUME_DOWN:
        if radio.muted():
            radio.unmute()
        radio.decreaseVolume()

    elif event_type == radioEvent.MENU_BUTTON_DOWN:
        time.sleep(0.5)
        # Is the button still held down (Shutdown)
        if not radioEvent.menuPressed():
            mode = display.cycleMode()

    elif event_type == radioEvent.MUTE_BUTTON_DOWN:
        if radio.muted():
            radio.unmute()
        else:
            radio.mute()
        time.sleep(0.5)     # Prevent unmute

    elif event_type == radioEvent.RECORD_BUTTON:
        log.message('RECORD_BUTTON event received', log.DEBUG)
        radio.handleRecordKey(event_type)

    elif event_type == radioEvent.MPD_CLIENT_CHANGE:
        log.message("radioEvent Client Change",log.DEBUG)
        artwork_file = getArtwork()

    elif event_type == radioEvent.LOAD_RADIO or event_type == radioEvent.LOAD_MEDIA \
               or event_type == radioEvent.LOAD_AIRPLAY\
               or event_type == radioEvent.LOAD_SPOTIFY\
               or event_type == radioEvent.LOAD_PLAYLIST:
        handleSourceChange(radioEvent,radio,message)

    elif event_type == radioEvent.PLAYLIST_CHANGED:
        log.message('PLAYLIST_CHANGED event received', log.DEBUG)
        radio.handlePlaylistChange()

    elif event_type == radioEvent.MPD_VOLUME_CHANGE:
        volume = radio.volume.get()
        msg = "handleEvent Volume Changed %d" % volume
        log.message(msg,log.DEBUG)
        radio.volume.storeVolume(volume)

    elif event_type == radioEvent.PLAY:     # Raised by IR RC PLAY_nn event
        log.message('PLAY event received', log.DEBUG)
        pl_length = radio.getPlayListLength()
        play_number = radio.getPlayNumber()
        if play_number <= pl_length:
            radio.play(play_number)
            display.setMode(display.MAIN)

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
        if display.config.airplay:
            radio.cycleWebSource(radio.source.AIRPLAY)

    elif event_type == event.LOAD_SPOTIFY:
        msg = message.get('starting_spotify')
        message.speak(msg)
        radio.cycleWebSource(radio.source.SPOTIFY)

    # Version 1.8 onwards of the web interface
    elif event_type == radioEvent.LOAD_PLAYLIST:
        playlist = radio.getPlaylistName()
        name = playlist.replace('_', ' ')
        name = name.lstrip()
        name = name.rstrip()
        name = "%s%s" % (name[0].upper(), name[1:])
        print(name)
        radio.source.setPlaylist(playlist)
        radio.loadSource()
        
    if event_type != radioEvent.LOAD_PLAYLIST:
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
def handleSearchEvent(radio,event,SearchWindow,display,searchID,largeDisplay):
    global Artists
    global artwork_file
    if event.type == pygame.MOUSEBUTTONDOWN and not IgnoreSearchEvents:
        # Event in the search window (Not the slider) 
        if SearchWindow.clicked(event):
            log.message("SearchWindow.clicked", log.DEBUG)
            idx = SearchWindow.index()
            current_id = radio.getCurrentID()
            # Workaround to prevent reloading same station that is already playing
            if idx + 1 != current_id:
                searchID = selectNew(radio,display,widget,Artists,searchID,SearchWindow,idx)
            artwork_file = getArtwork(True)

        elif largeDisplay and SearchWindow.slider.clicked(event):
            searchID = SearchWindow.slider.getPosition()

    # Search window slider dragged
    elif largeDisplay and SearchWindow.slider.dragged(event) and not IgnoreSearchEvents:
        searchID = SearchWindow.slider.getPosition()
    return searchID

# Draw the radio/media display window
def drawDisplayWindow(surface,screen,display):
    # Create display window for radio/media information
    DisplayWindow = TextRectangle(pygame)
    cols = display.getColumns()
    startColumn = display.getStartColumn()
    xPos = display.getColumnPos(startColumn)
    yPos = display.getRowPos(3) 
    xSize = display.getColumnPos(cols - startColumn * 2)
    ySize = display.getRowPos(3)    
    border = 4
    wcolor = getLabelColor(display.config.display_window_color)
    color = pygame.Color(wcolor)
    bcolor = (25,25,25)     # Border colour
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
    startColumn = display.getStartColumn()
    rows = display.getRows()
    if rows < 20:
        xPos = display.getColumnPos(startColumn)
        yPos = display.getRowPos(6.5)
    else:
        xPos = display.getColumnPos(startColumn + 48)
        yPos = display.getRowPos(7)
    upIcon.draw(screen,xPos,yPos)
    return 

# Draw Down Icon
def drawDownIcon(display,screen,downIcon):
    startColumn = display.getStartColumn()
    rows = display.getRows()
    if rows < 20:
        xPos = display.getColumnPos(startColumn + 34.2)
        yPos = display.getRowPos(6.5)
    else:
        xPos = display.getColumnPos(startColumn + 48)
        yPos = display.getRowPos(13.5)
    downIcon.draw(screen,xPos,yPos)
    return 

# Draw switch program icon
def drawSwitchIcon(display,screen,switchIcon):
    xPos = size[0]-50
    yPos = 5
    switchIcon.draw(screen,xPos,yPos)
    return

# Draw Equalizer Icon
def drawEqualizerIcon(display,screen,equalizerIcon):
    xPos = 10
    yPos = 90
    equalizerIcon.draw(screen,xPos,yPos)
    return 

# Draw Shutdown Icon
def drawShutdownIcon(display,screen,shutdownIcon,largeDisplay):
    if largeDisplay:
        xPos = 10
        yPos = 10
    else:
        xPos = 5
        yPos = 20
    shutdownIcon.draw(screen,xPos,yPos)
    return 

# Draw Icecast Icon
def drawIcecastIcon(display,screen,enabled,largeDisplay):
    if largeDisplay:
        xPos = size[0]-50
        yPos = 90
    else:
        xPos = size[0]-30
        yPos = 60
    icecastIcon.draw(screen,xPos,yPos,enabled)
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
    lcolor = getLabelColor(display.config.labels_color)
    row = 13.5
    startColumn = display.getStartColumn()
    xPos = display.getColumnPos(startColumn + 1)
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
    wsize = 30
    SearchWindow = ScrollBox(pygame,display)
    cols = display.getColumns()
    rows = display.getRows()
    xPos = display.getColumnPos((cols/2)-(wsize/2))
    yPos = display.getRowPos(7)
    xSize = display.getColumnPos(wsize)
    if rows < 20:
        lines = 1
    else:
        lines = config.search_window_rows
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
        textArray = getPlaylists()  # Get playlists 
    else:
        textArray = radio.getPlayList() # Current playlist contents
    
    source_type = radio.source.getType()

    if search_mode == display.SEARCH_ARTISTS and source_type == radio.source.MEDIA:
        previous = '' 
        for i in range (len(textArray)):

            line = textArray[i]
            # split off artist names
            line = line.replace(' - ','|',1)
            array = line.split('|')    
            artist = uEncode(array[0].lstrip())
            
            # Create <artist>:<first track index> entry in Artists array
            if artist != previous:
                previous = artist
                Artists[artist] = i  # Add to artists array 

        # Build an array of artist for display
        textArray = []
        for artist in Artists.keys():
            textArray.append(artist)
        
        textArray.sort(key=str.lower)  # Sort in place, key=str.lower is important

    else:
        for i in range (len(textArray)):
            textArray[i] = uEncode(textArray[i])
            if search_mode == display.SEARCH_PLAYLIST:
                textArray[i] = textArray[i].rstrip()
                if textArray[i] == "_spotify":
                    textArray[i] = "Spotify"
                elif textArray[i] == "_airplay":
                    textArray[i] = "Airplay"

            # Remove codec extensions 
            if source_type == radio.source.MEDIA:
                textArray[i] = removeCodecs(textArray[i])

    searchID = setSearchID(textArray,searchID) 
    idx = int(searchID - 1)

    iLeng = len(textArray)
    if iLeng > 0:
        #if search_mode == display.SEARCH_ARTISTS and source_type == radio.source.MEDIA:
        #    textArray = textArray.sort()
        SearchWindow.drawText(screen,font,color,textArray[idx:])
        lcolor = getLabelColor(display.config.labels_color)
        scolor = getLabelColor(display.config.slider_color)
        if rows >= 20:
            SearchWindow.slider.setPosition(searchID,iLeng,scolor,lcolor)
        else:
            SearchWindow.setRange(iLeng)

    return SearchWindow

# Remove codecs eg. .wma .mpr3 etc. from artist/track name
def removeCodecs(name):
    codecs = config.codecs
    codec_arr = codecs.split(" ")
    for codec in codec_arr:
        codec = codec.replace('"','')
        codec = "." + codec
        name = name.replace(codec," ")
    return name

# Get the playlists for search display
def getPlaylists():
    plist = []
    playlists = radio.getPlaylists()
    values = list(playlists.keys())
    idx = 0

    # Replace underscores with spaces
    for idx in range(len(values)):
        name = values[idx]
        if name[0] == '_':

        # Temporary fix to display old pre version 7.3 names
            oldname = True
        else:
            oldname = False
        values[idx] = values[idx].replace('_',' ')
        values[idx] = values[idx].lstrip()
        
        plname = uEncode(values[idx])
        if  oldname:
            plname = '_' + plname
        plist.append(plname)
    return plist

# Create Channel Up button (Also exits Airplay)
def drawChannelUpButton(source_type,sgc,display):
    # Set button label
    if source_type == radio.source.AIRPLAY:
        label = "Exit\nAirplay"

    elif source_type == radio.source.SPOTIFY:
        label = "Exit\nSpotify"

    elif source_type == radio.source.MEDIA:
        label = "Track\nUp"

    else:
        label = "Station\nUp"

    startColumn = display.getStartColumn()
    rows = display.getRows()
    columns = display.getColumns()
    if rows < 20:
        xPos = display.getColumnPos(startColumn)
    else:
        xPos = display.getColumnPos(startColumn + 10.5)
    yPos = display.getRowPos(rows-5)
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

    startColumn = display.getStartColumn()
    columns = display.getColumns()
    rows = display.getRows()

    if rows < 20:
        xPos = display.getColumnPos(startColumn + 30)
    else:
        xPos = display.getColumnPos(startColumn + 41)
    yPos = display.getRowPos(rows-5)
    ChannelDownButton = sgc.Button(label=label, pos=(xPos,yPos))
    ChannelDownButton.add(order=2)
    return ChannelDownButton

# Get pid
def getPid():
    pid = None
    if os.path.exists(pidfile): 
        pf = open(pidfile,'r')
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
            print(msg)
            exit()
        except:
            os.remove(pidfile)
    # Write the pidfile
    pid = str(os.getpid())
    pf = open(pidfile,'w')
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
            widget.select_list.activate()
            searchID = Artists.get(artistKey) + 1
            radio.play(searchID)
    else:
        # Radio selection
        radio.play(searchID + idx)
    if radio.muted():
        radio.unmute()

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
    global run

    # Shift "=" is capital A 
    if  key == K_EQUALS and pygame.key.get_mods() & pygame.KMOD_SHIFT:
        radioEvent.set(radioEvent.VOLUME_UP)

    if key == K_KP_PLUS or key == K_PLUS:
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

    elif event.key == K_x and display.config.switch_programs:
        dir = os.path.dirname(__file__)
        os.popen("sudo " + dir + "/vgradio.py&")
        run = False

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
    elif source_type == radio.source.SPOTIFY:
        uplabel = "Exit\nSpotify"
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
    cmd_file = open(RadioLib + '/' + equalizer_cmd,"r")
    for line in cmd_file: 
        if line.startswith('lxterminal'):
            log.message(line,log.DEBUG)
            radio.execCommand(line)
            break
    return

# Set draw equalizer true/false
def displayEqualizerIcon(display):
    if display.config.fullscreen:
        draw_equalizer_icon = False
    else:
        draw_equalizer_icon = True
    return draw_equalizer_icon

# Display search type as a string (Small screens)
def displaySearchType(screen,search_mode,yPos,xPos):
    sTypes = ['List','Playlists','Artists']
    sType = sTypes[search_mode]
    font = pygame.font.SysFont('freesans', 24)
    font.set_bold(True)
    color = pygame.Color('steelblue')
    fontSize = font.size(sType) 
    xPos += 35
    yPos += 5
    renderText(sType,font,screen,yPos,xPos,color)
    return
    
# Search type cycle icon
def displaySearchCycleIcon(display,screen,searchCycleIcon,search_mode):
    xPos = size[0]/2 - 40
    yPos = display.getRowPos(8.5)
    searchCycleIcon.draw(screen,xPos,yPos)
    displaySearchType(screen,search_mode,yPos,xPos)
    return 

# Exit the program only
def quit():
    radio.stop()
    if os.path.isfile(pidfile):
        os.remove(pidfile)
    sys.exit(0)

# Main routine
if __name__ == "__main__":
    signal.signal(signal.SIGTERM,signalHandler)
    signal.signal(signal.SIGHUP,signalHandler)
    signal.signal(signal.SIGSEGV,signalCrash)
    signal.signal(signal.SIGABRT,signalCrash)
    
    log.init('radio')

    picWallpaper = None
    # Check we have a desktop
    try:
        os.environ['DISPLAY']
    except:
        print("This program requires an X-Windows desktop")
        sys.exit(1)

    # Do not override locale settings
    try:
        locale.setlocale(locale.LC_ALL, '')
    except:
        pass
    log.message("locale " + str(locale.getlocale()), log.DEBUG)

    font = pygame.font.SysFont('freesans', 13)
    display = GraphicDisplay(font)
    size = display.config.screen_size

    if display.config.fullscreen:
        flags = FULLSCREEN|DOUBLEBUF
    else:
        flags = DOUBLEBUF

    radioEvent = Event(config)        # Add radio event handler

    if config.log_creation_mode:
        log.truncate()

    log.message("===== Graphic radio (gradio.py) started ==", log.INFO)
    radio = Radio(rmenu,radioEvent,translate,config,log)  # Define radio
    size = config.screen_size
    log.message("Python version " + str(sys.version_info[0]) ,log.INFO)

    ipaddr = radio.waitForNetwork()
    
    try:
        screen = sgc.surface.Screen((size),flags)
    except Exception as e:
        msg = "gradio screen size error:  " + str(e)
        print (msg)
        log.message(msg, log.ERROR)
        msg = "Fatal error - exiting"
        print (msg)
        log.message(msg, log.CRITICAL)
        sys.exit(1)

    # Hide mouse if configured
    if display.config.fullscreen and not display.config.display_mouse:
        pygame.mouse.set_cursor((8,8),(0,0),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0))


    # Prevent LCD version from running and disable it
    os.popen("sudo systemctl stop radiod")
    os.popen("sudo systemctl disable radiod")

    pid = checkPid(pidfile)

    progcall = str(sys.argv)
    log.message("Radio " +  progcall + " Version " + radio.getVersion(), log.INFO)
    log.message("gradio running, pid " + str(pid), log.INFO)


    # see https://www.webucator.com/blog/2015/03/python-color-constants-module/
    # Paint screen background (Keep at start of draw routines)
    wallpaper = display.config.wallpaper
    if len(wallpaper) > 1:
        picWallpaper=pygame.image.load(wallpaper)
        screen.blit(pygame.transform.scale(picWallpaper,size),(0,0))
    else:
        wcolor = display.config.window_color
        try:
            screen.fill(Color(wcolor))
        except:
            log.message("Invalid window_color " + wcolor, log.ERROR)
            wcolor = "blue"
            screen.fill(Color(wcolor))

    message = Message(radio,display,translate)
    text = message.get('loading_playlists')
    displayPopup(screen,text)

    # Set up Xauthority for root user
    radio.execCommand("sudo cp /home/pi/.Xauthority /root/")

    radio.translate.setTranslate(False) # Switch off text translation

    setupRadio(radio)
    artwork = Artwork(log=log)

    maxRows = display.getRows()
    largeDisplay = True
    if maxRows < 20 :
        largeDisplay = False

    # Set up window title
    window_title = display.getWindowTitle(radio)
    pygame.display.set_caption(window_title)

    draw_equalizer_icon = False
    if largeDisplay:
        draw_equalizer_icon = displayEqualizerIcon(display)

    # Create SGC widgets
    labels_color_name = display.config.labels_color
    try:
        label_col = pygame.Color(labels_color_name)
    except:
        log.message("Invalid labels_color " + labels_color_name, log.ERROR)
        label_col = pygame.Color('white')

    startColumn = display.getStartColumn()
    widget = Widgets(sgc,radio,display,startColumn,label_col)

    # Draw the Up/Down buttons
    source_type = radio.getSourceType()
    ChannelUpButton = drawChannelUpButton(source_type,sgc,display)
    ChannelDownButton = drawChannelDownButton(source_type,sgc,display)
    volume = radio.getVolume()
    widget.VolumeSlider.value = volume
    current_volume = 0
    search_mode = display.getSearchMode()

    # Create screen controls
    MuteButton = MuteButton(pygame)
    upIcon = UpIcon(pygame)
    downIcon = DownIcon(pygame)
    searchCycleIcon = SearchCycleIcon(pygame)
    LeftArrow = Image(pygame)
    RightArrow = Image(pygame)
    switchIcon = SwitchIcon(pygame)
    equalizerIcon = EqualizerIcon(pygame)
    shutdownIcon = ShutdownIcon(pygame)
    icecastIcon = IcecastIcon(pygame)
    drawUpIcon(display,screen,upIcon)
    drawDownIcon(display,screen,downIcon)
    drawLeftArrow(display,screen,LeftArrow)
    drawRightArrow(display,screen,RightArrow)
    if draw_equalizer_icon:
        drawEqualizerIcon(display,screen,equalizerIcon)

    if display.config.switch_programs:
        drawSwitchIcon(display,screen,switchIcon)

    if config.display_shutdown_button:
        drawShutdownIcon(display,screen,shutdownIcon,largeDisplay)

    # Icecast icon
    draw_icecast_icon = os.path.exists("/usr/bin/icecast2") and config.display_icecast_button
    if draw_icecast_icon:
        icecast_enabled = radio.getStoredStreaming()
        drawIcecastIcon(display,screen,icecast_enabled,largeDisplay)

    # Option buttons
    if largeDisplay:
        RandomButton = OptionButton(pygame)
        RepeatButton = OptionButton(pygame)
        ConsumeButton = OptionButton(pygame)
        SingleButton = OptionButton(pygame)
        drawOptionButtons(display,screen,radio,RandomButton,RepeatButton,
                    ConsumeButton,SingleButton)
        RandomButton.activate(radio.getRandom())
    else:
        displaySearchCycleIcon(display,screen,searchCycleIcon,search_mode)

    # Create display window for radio/media information
    id = radio.getCurrentID()   # Search window index
    searchID = id
    DisplayWindow = drawDisplayWindow(surface,screen,display)
    SearchWindow = drawSearchWindow(surface,screen,display,id)
    ArtworkImage = None

    # Screen saver times
    screenBlank = False
    screenMinutes = display.config.screen_saver
    if screenMinutes > 0:
        blankTime = int(time.time()) + screenMinutes*60
    else:
        blankTime = 0

    source_type = radio.getSourceType()
    artwork_file = getArtwork(True)

    # Main processing loop
    while run:
        tick = clock.tick(30)
        source_type = radio.getSourceType()

        # Blank screen after blank time exceeded
        if screenMinutes > 0 and int(time.time()) > blankTime:
            screenBlank = True

        # Reset the draw equalizer icon flag
        if largeDisplay:
            if int(subprocess.getoutput('pidof %s |wc -w' % "alsamixer")) < 1:
                draw_equalizer_icon = displayEqualizerIcon(display)
                if draw_equalizer_icon:
                    equalizerIcon.enable()

        # Handle Widget events
        for event in pygame.event.get():
            # Send event to widgets
            sgc.event(event)
            if event.type == GUI:

                blankTime = int(time.time()) + screenMinutes*60
                if screenBlank:
                    screenBlank = False

                elif event.widget_type is sgc.Button:
                    print("Button event",event.gui_type)

                # Radio source type buttons
                elif event.widget_type is sgc.Radio:
                    if event.gui_type == "select":
                        artwork_file = ''
                        new_source = handleSourceEvent(event,radio,display)
                        if new_source != display.SEARCH_LIST:
                            searchID = 1

                elif event.widget_type is sgc.Switch:
                    print("Switch Event ",event.gui_type)

                elif event.widget_type is sgc.Combo:
                    log.message("sgc.Combo", log.DEBUG)
                    radio.source.cycleType(widget.sourceCombo.selection)
                    radio.setReload(True)

                # Up and down channel/track buttons
                if event.widget is ChannelUpButton and event.gui_type == "click":
                    if source_type == radio.source.AIRPLAY or source_type == radio.source.SPOTIFY:
                        radio.source.cycleType(radio.source.RADIO)
                        radio.setReload(True)
                    else: 
                        radio.unmute()
                        radioEvent.set(radioEvent.CHANNEL_UP)

                elif event.widget is ChannelDownButton and event.gui_type == "click":
                    if source_type != radio.source.AIRPLAY:
                        radio.unmute()
                        radioEvent.set(radioEvent.CHANNEL_DOWN)

                display.setMode(display.MAIN)

            if event.type == pygame.MOUSEBUTTONDOWN:

                blankTime = int(time.time()) + screenMinutes*60
                if screenBlank:
                    screenBlank = False

                elif DisplayWindow.clicked(event):
                    mode = display.cycleMode()

                elif upIcon.clicked():
                    searchID -= 1
                    if searchID < 1:
                        if largeDisplay:
                            srange = SearchWindow.slider.getRange()
                        else:
                            srange = SearchWindow.getRange()
                        searchID = srange

                elif downIcon.clicked():
                    if largeDisplay:
                        srange = SearchWindow.slider.getRange()
                    else:
                        srange = SearchWindow.getRange()
                    searchID += 1
                    if searchID > srange:
                        searchID = 1

                elif display.config.switch_programs and largeDisplay and switchIcon.clicked():
                    if radio.spotify.isRunning():
                        radio.spotify.stop()
                    dir = os.path.dirname(__file__)
                    os.popen("sudo " + dir + "/vgradio.py&")
                    run = False
                    break

                elif LeftArrow.clicked():
                    searchID = 1

                elif RightArrow.clicked():
                    searchID = SearchWindow.slider.getRange()

                elif draw_equalizer_icon and equalizerIcon.clicked():
                    openEqualizer(radio,"equalizer.cmd")
                    draw_equalizer_icon = False
                    equalizerIcon.disable()

                elif config.display_shutdown_button and shutdownIcon.clicked():
                    handleShutdown(screen) 

                elif draw_icecast_icon and icecastIcon.clicked():
                    if radio.getStoredStreaming():
                        radio.streamingOff()
                    else:
                        radio.streamingOn()

                elif largeDisplay and RandomButton.clicked(event):
                    if RandomButton.isActive():
                        radio.setRandom(False)
                        RandomButton.activate(False)
                    else:
                        radio.setRandom(True)
                        RandomButton.activate(True)

                elif largeDisplay and RepeatButton.clicked(event):
                    if RepeatButton.isActive():
                        radio.setRepeat(False)
                        RepeatButton.activate(False)
                    else:
                        radio.setRepeat(True)
                        RepeatButton.activate(True)

                elif largeDisplay and ConsumeButton.clicked(event):
                    if ConsumeButton.isActive():
                        radio.setConsume(False)
                        ConsumeButton.activate(False)
                    else:
                        radio.setConsume(True)
                        ConsumeButton.activate(True)

                elif largeDisplay and SingleButton.clicked(event):
                    if SingleButton.isActive():
                        radio.setSingle(False)
                        SingleButton.activate(False)
                    else:
                        radio.setSingle(True)
                        SingleButton.activate(True)

                elif not largeDisplay and searchCycleIcon.clicked():
                    search_mode = display.cycleSearchMode()
                    if search_mode == display.SEARCH_ARTISTS and\
                             source_type != radio.source.MEDIA:
                        search_mode = display.SEARCH_LIST
                        display.setSearchMode(search_mode)
                    searchID = 1

                elif MuteButton.pressed():
                    if radio.muted():
                        widget.VolumeSlider.label = "Volume"
                        radio.unmute()
                    else:
                        radio.mute()
                        widget.VolumeSlider.label = "Muted"
                
                # Event in the search window or artwork image clicked
                elif source_type != radio.source.AIRPLAY and source_type != radio.source.SPOTIFY:
                    if ArtworkImage != None and len(artwork_file) > 0:
                        if ArtworkImage.clicked() and event.type == pygame.MOUSEBUTTONDOWN:
                            artwork_file = ''
                    searchID = handleSearchEvent(radio,event,
                            SearchWindow,display,searchID,largeDisplay)
                    IgnoreSearchEvents = False  

                # Display window mouse down changes display mode
            # Temporary exit on ESC key during development
            elif event.type == KEYDOWN:
                if largeDisplay:
                    srange = SearchWindow.slider.getRange()
                    searchID = handleKeyEvent(event.key,radioEvent,searchID,srange)
                    toggleOption(radio,event.key,RandomButton,RepeatButton,
                        ConsumeButton,SingleButton,widget)

                blankTime = int(time.time()) + screenMinutes*60
                if screenBlank:
                    screenBlank = False

                elif event.key == K_RETURN:
                    searchID = selectNew(radio,display,widget,Artists,searchID,SearchWindow,0)

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
                    radio.setVolume(volume)
                    current_volume = volume 

        # Detect radio events
        if radioEvent.detected():
            log.message("radioEvent.detected", log.DEBUG)
            handleEvent(radio,radioEvent)
        elif radio.getReload():
            displayLoadingSource(screen,myfont,radio,message)
            radio.loadSource()      # Load new source
            radio.setReload(False) 

        # Pick up external volume changes
        volume = radio.getVolume()
        if current_volume != volume:
            widget.VolumeSlider.value = volume
            current_volume = volume

        # Start of screen paint routines
        # Paint screen background (Keep at start of draw routines)
        if len(wallpaper) > 1:
            if picWallpaper == None:
                picWallpaper=pygame.image.load(wallpaper)
            screen.blit(pygame.transform.scale(picWallpaper,size),(0,0))
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

        elif source_type == radio.source.SPOTIFY:
            displaySpotify(display,radio,myfont)

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
                    IgnoreSearchEvents = True
                else:
                    SearchWindow = drawSearchWindow(surface,screen,display,searchID)

                # Display the information window
                if display.getMode() == display.INFO:
                    displayInfo(screen,myfont,radio,message)
                else:
                    displayCurrent(screen,myfont,radio,message)

        # Draw options and other controls
        cols = display.getColumns()
        rows = display.getRows()
        xPos = display.getColumnPos((cols/2)-2)
        yPos = display.getRowPos(rows - 4)
        if len(artwork_file) < 1 or largeDisplay:
            MuteButton.draw(screen,display,(xPos,yPos),radio.muted())

        # Draw navigation buttons if no artwork displayed
        if len(artwork_file) < 1:
            if source_type == radio.source.RADIO or source_type == radio.source.MEDIA:
                drawUpIcon(display,screen,upIcon)
                drawDownIcon(display,screen,downIcon)
                if largeDisplay:
                    drawLeftArrow(display,screen,LeftArrow)
                    drawRightArrow(display,screen,RightArrow)

        if display.config.switch_programs and largeDisplay:
            drawSwitchIcon(display,screen,switchIcon)

        if draw_equalizer_icon:
            drawEqualizerIcon(display,screen,equalizerIcon)

        if config.display_shutdown_button:
            drawShutdownIcon(display,screen,shutdownIcon,largeDisplay)

        if draw_icecast_icon:
            icecast_enabled = radio.getStoredStreaming()
            drawIcecastIcon(display,screen,icecast_enabled,largeDisplay)

        if source_type == radio.source.RADIO or source_type == radio.source.MEDIA:
            if largeDisplay:
                drawOptionButtons(display,screen,radio,RandomButton,RepeatButton,
                            ConsumeButton,SingleButton)
                RandomButton.activate(radio.getRandom())
            else:
                if len(artwork_file) < 1:
                    displaySearchCycleIcon(display,screen,searchCycleIcon,search_mode)
                    #displaySearchType(screen,search_mode)

        # Update SGC and pygame displays (required by SGC)
        sgc.update(tick)

        # Screen blanking
        if screenBlank and display.config.fullscreen:
            screen.fill(Color(0,0,0))

        # Update display
        pygame.display.flip()

        radio.checkClientChange()

    # End of while loop

# End of program
# set tabstop=4 shiftwidth=4 expandtab
# retab
