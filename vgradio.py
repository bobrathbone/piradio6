#!/usr/bin/env python3
#
# Raspberry Pi Graphical Internet Radio
# This program interfaces with the Music Player Daemon MPD
#
# $Id: vgradio.py,v 1.17 2021/03/19 11:07:03 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#     The authors shall not be liable for any loss or damage however caused.
#
# Icons used in the graphic versions of the radio.
# Clipart library http://clipart-library.com
# IconSeeker http://www.iconseeker.com

import os,sys
import locale
import pygame
import time
import pdb
import signal
import socket
import subprocess
from time import strftime

# Pygame controls
from pygame.locals import *
from gcontrols_class import *

# Radio imports
from log_class import Log
from config_class import Configuration
from radio_class import Radio
from event_class import Event
from menu_class import Menu
from message_class import Message
from graphic_display import GraphicDisplay
from translate_class import Translate
import traceback

translate = Translate()
config = Configuration()
log = Log()
rmenu = Menu()
radio = None
radioEvent = None
message = None

# Initialise pygame
size = (800, 480)
pygame.display.init()
pygame.font.init()
myfont = pygame.font.SysFont('freesans', 20, bold=True)
screen = None
run = True
_connecting = False

# Tuner scale range
margin = 50     # Top bottom
lmargin = 30    # Left margin
rmargin = 80    # Right margin 

pidfile = "/var/run/radiod.pid"

playlist = []
plName = '' # Playlist name if more than one

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
    global message,display
    log.message("Starting graphic radio ", log.INFO)

    radio.start()         # Start it
    radio.loadSource()      # Load sources and playlists

    return

# Return the page that this station is to be displayed on
def getPage(currentID,maxStations):
    page = int(currentID/maxStations)
    if currentID % maxStations == 0 and page > 0:
               page -= 1
    return page

# Get the maximum stations labels to be displayed per page
def getMaximumLabels(display,radio): 
    maxLabels = display.config.getMaximumStations()
    plsize = radio.getPlayListLength()
    currentID = radio.getCurrentID()
    page = getPage(currentID,maxLabels)
    last_page = page + 1

    # If no playlist loaded
    if plsize < 1:
        maxLabels = 40 
    elif plsize < maxLabels * last_page:
        maxLabels = plsize - maxLabels * page  
    return maxLabels

# Draw the radio/media display window
def drawTunerSlider(tunerSlider,screen,display,currentID):
    maxLabels = getMaximumLabels(display,radio)
    range = size[0] - lmargin - rmargin
    xPos = int(range * currentID / maxLabels) + lmargin
    yPos = margin + 12
    width = 5
    ySize = size[1]-(2*margin)-12
    border = 0
    color = getColor(display.config.getSliderColor())
    bcolor = color
    tunerSlider.draw(screen,color,bcolor,xPos,yPos,width,ySize,border)
    return 

# Draw the radio/media display window
def drawVolumeScale(volumeScale,screen,volume):
    xPos = lmargin
    yPos = size[1] - margin

    # Handle 1024 x 600 screens
    if display.getRows() > 24:
        yPos -= 9
    xSize = size[0] - lmargin - rmargin/3
    ySize = size[1] - margin * 2
    volumeScale.draw(screen,xPos,yPos,xSize,ySize)
    return 

# Check that the label colour is valid
def getColor(lcolor):
    try:
        color = pygame.Color(lcolor)
    except:
        color = (255,255,255)
    return color

# Handle radio event
def handleEvent(radio,radioEvent):
    global plName
    event_type = radioEvent.getType()
    source_type = radio.getSourceType()
    msg = "radioEvent.detected " + str(event_type) + ' ' + radioEvent.getName()
    log.message(msg, log.DEBUG)

    if event_type == radioEvent.SHUTDOWN:
        radio.stop()
        print("doShutdown", config.doShutdown())
        if config.doShutdown():
            radio.shutdown() # Shutdown the system
        else:
            print("Exiting")
            sys.exit(0)

    elif event_type == radioEvent.CHANNEL_UP:
        _connecting = False
        radio.channelUp()

    elif event_type == radioEvent.CHANNEL_DOWN:
        _connecting = False
        radio.channelDown()

    elif event_type == radioEvent.VOLUME_UP:
        radio.increaseVolume()

    elif event_type == radioEvent.VOLUME_DOWN:
        radio.decreaseVolume()

    elif event_type == radioEvent.MENU_BUTTON_DOWN:
        time.sleep(0.5)
        # Is the button still held down (Shutdown)
        if not radioEvent.menuPressed():
            pageUp(display,radio)

    elif event_type == radioEvent.MUTE_BUTTON_DOWN:
        if radio.muted():
            radio.unmute()
        else:
            radio.mute()

    elif event_type == radioEvent.MPD_CLIENT_CHANGE:
        log.message("radioEvent Client Change",log.DEBUG)
        if radio.muted():
            radio.unmute()

    elif event_type == radioEvent.LOAD_RADIO or event_type == radioEvent.LOAD_MEDIA \
               or event_type == radioEvent.LOAD_AIRPLAY\
               or event_type == radioEvent.LOAD_PLAYLIST:
            
        handleSourceChange(radioEvent,radio,message)

    radioEvent.clear()
    return

# Handler for source change events (also from the web interface)
def handleSourceChange(event,radio,message):
    global playlist,sliderIndex,sliderIndex,plName
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

    # Version 1.8 onwards of the web interface
    elif event_type == event.LOAD_PLAYLIST:
        playlistName = radio.getPlaylistName()
        name = playlistName.replace('_', ' ')
        name = name.lstrip()
        name = name.rstrip()
        name = "%s%s" % (name[0].upper(), name[1:])
        plName = name
        radio.source.setPlaylist(playlistName)
        radio.loadSource()

        playlist = radio.getPlayList()
        listIndex = 0   # Playlist index
        sliderIndex = 0
        radio.setCurrentID(1)

    if event_type != event.LOAD_PLAYLIST:
        new_source = radio.getNewSourceType()
        log.message("loadSource new type = " + str(new_source), log.DEBUG)
        if new_source >= 0:
            radio.loadSource()
    return

# Handle keyboard key event See https://www.pygame.org/docs/ref/key.html
def handleKeyEvent(key,display,radio,radioEvent):
    global run
    if key == K_KP_PLUS or  key == K_PLUS:
        radioEvent.set(radioEvent.VOLUME_UP)

    elif key == K_KP_MINUS  or  key == K_MINUS:
        radioEvent.set(radioEvent.VOLUME_DOWN)

    # Shift "=" is capital A
    if  key == K_EQUALS and pygame.key.get_mods() & pygame.KMOD_SHIFT:
        radioEvent.set(radioEvent.VOLUME_UP)

    if key == K_DOWN:
        radioEvent.set(radioEvent.CHANNEL_DOWN)

    elif key == K_UP:
        radioEvent.set(radioEvent.CHANNEL_UP)

    elif key == K_LEFT:
        radioEvent.set(radioEvent.VOLUME_DOWN)

    elif key == K_RIGHT:
        radioEvent.set(radioEvent.VOLUME_UP)

    elif key == K_m:
        radioEvent.set(radioEvent.MUTE_BUTTON_DOWN)

    elif key == K_PAGEUP:
        pageUp(display,radio)

    elif key == K_PAGEDOWN:
        pageDown(display,radio)

    elif key == K_ESCAPE:
        radio.stop()
        quit()

    elif event.key == K_x and display.config.switchPrograms():
        dir = os.path.dirname(__file__)
        os.popen("sudo " + dir + "/gradio.py&")
        run = False

    elif event.key == K_q:
        mods = pygame.key.get_mods()
        if mods & pygame.KMOD_CTRL:
            radioEvent.set(radioEvent.SHUTDOWN)
    return key

# Calculate the ID from the clicked scale position
def calculateID(radio,listIndex):
    pos = pygame.mouse.get_pos()
    mPos = pos[0] - lmargin 
    range = size[0] - lmargin - rmargin
    maxLabels = getMaximumLabels(display,radio)
    newID = int(maxLabels * mPos/range) + 1
    if newID < 1:
        newID = 1
    elif newID > maxLabels:
        newID = maxLabels   
    return newID + listIndex

# This routine displays the title or bit rate
def displayTimeDate(screen,radio,message):
    dateFormat = config.getGraphicDateFormat()
    timedate = strftime(dateFormat)
    banner_color_name = display.config.getBannerColor()
    try:
        color = pygame.Color(banner_color_name)
    except:
        color = pygame.Color('white')
    font = pygame.font.SysFont('freesans', 16, bold=False)
    fontSize = font.size(timedate)
    xPos = int((size[0] - fontSize[0])/2)
    yPos = 10
    textsurface = font.render(timedate, False, (color))
    screen.blit(textsurface,(xPos,yPos))
    return

# Encode text to UTF-8
def uEncode(text):
        string = text
        try:
                string = str(text,"utf-8")
        except:
                pass
        return string

# Display currently playing radio station 
def displayTitle(screen,radio,message,plsize):
    global _connecting
    title = radio.getCurrentTitle()
    title = uEncode(title)

    if len(title) < 1:
        current_id = radio.getCurrentID()
        bitrate = radio.getBitRate()
        if int(bitrate) > 0:
            title = "Station %s/%s: Bitrate %sk" % (current_id,plsize,bitrate)
            _connecting = False
        else:
            if not _connecting:
                eMsg = message.get('connecting')
                title = "Station %s/%s: %s" % (current_id,plsize,eMsg)
                _connecting = True
            else:
                title = message.get('no_information')
    else:
        title = title[0:80]
        
    font = pygame.font.SysFont('freesans', 12, bold=False)
    fontSize = font.size(title)
    xPos = int((size[0] - fontSize[0])/2)
    yPos = size[1] - 20
    color = pygame.Color('white')
    textsurface = font.render(title, False, (color))
    screen.blit(textsurface,(xPos,yPos))
    return

# Display playlist name if more than one
def displayPlaylistName(screen,plName):
    if len(plName) > 0:
        plName = plName.replace('_',' ')
        plName = plName.lstrip()
        font = pygame.font.SysFont('freesans', 12, bold=False)
        xPos = 10
        yPos = 13
        color = pygame.Color('white')
        textsurface = font.render(plName, False, (color))
        screen.blit(textsurface,(xPos,yPos))
    return

# Display page number and total
def displayPagePosition(page,maxStations,plsize):
    try:
        nPages = int(plsize/maxStations) + 1
        page = page + 1
    except:
        nPages = 0
        page = 0
    font = pygame.font.SysFont('freesans', 15, bold=False)
    xPos = size[0] - int(margin * 1.1)
    ypos = yPos = size[1] - int(font.size('A')[1] * 1.2)
    color = pygame.Color('white')
    text = str(page) + '/' + str(nPages)
    textsurface = font.render(text, False, (color))
    screen.blit(textsurface,(xPos,yPos))
    return

# Display message popup
def displayPopup(screen,radio,text):
    text = uEncode(text)
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
    line = 1    # Not used but required
    color = (255,255,255)
    displayPopup.drawText(screen,font,color,line,text)
    pygame.display.flip()
    return

# Display the radio station name
def displayStationName(screen,radio):
    sname = uEncode(radio.getSearchName()[0:40])
    font = pygame.font.SysFont('freesans', 20, bold=True)

    displayRect = TextRectangle(pygame)     # Blank out background
    displayWindow = TextRectangle(pygame)   # Text window
    color = (0,0,0)
    bcolor = (0,0,0)
    height = 28
    leng = len(sname)
    fx,fy = font.size(sname + "A")
    width = fx
    xPos = int((size[0]/2) - (width/2))
    yPos = 37
    xSize = width
    ySize = height
    border = 0
    displayRect.draw(screen,color,bcolor,xPos,yPos-5,xSize,ySize,border)
    displayWindow.draw(screen,color,bcolor,xPos,yPos,xSize,ySize,border)

    line = 1    # Not used but required
    color = (255,230,153)
    displayWindow.drawText(screen,font,color,line,sname)
    return displayWindow

# Display the station names on the scale 
def drawScaleNames(screen,radio,playlist,index,maxLabels,lmargin):
    lines = float(6)
    chars_per_line = float(110)
    maxLabels = float(maxLabels)
    try:
        tSize = int(chars_per_line/float(maxLabels/lines))
    except:
        tSize = 30
    clip =  screen.get_clip()
    font = pygame.font.SysFont('freesans', 11, bold=False)
    color = getColor(display.config.getScaleLabelsColor())
    plsize = len(playlist)
    range = size[0] - lmargin - rmargin
    xInc= int(range / maxLabels)
    firstLine = 75
    rows = display.getRows()
    xPos = 35

    # Handle 1024x600 screens
    if rows > 24:
        yInc = 71
        firstLine = 95
    else:
        # All other smaller sizes
        yInc = 57
        firstLine = 75

    yPos = firstLine 
    screen.set_clip(xPos,0,size[0]-rmargin,size[1])
    x = 0
    lineInc = 1
    while x < maxLabels:
        try:
            text = uEncode(playlist[index])
        except:
            break
        text = text[0:tSize]
        textsurface = font.render(text, False, (color))
        line = (xPos,yPos)
        screen.blit(textsurface,line)
        index += 1
        x += 1
        lineInc += 1
        if lineInc > 6:
            yPos = firstLine
            lineInc = 1
        else:
            yPos += yInc
        xPos += xInc

    # Restore original surface
    screen.set_clip(clip)
    return

# Display left arrow (Position on first station/track)
def drawLeftArrow(display,screen,LeftArrow):
    mysize = (30,30)
    rows = display.getRows()
    if rows > 24:
        yPos = 44
    else:
        yPos = 32
    xPos = 15
    myPos = (xPos,yPos)
    path = "images/arrow_left_double.png"
    LeftArrow.draw(screen,path,(myPos),(mysize))
    return

# Display right arrow (Position on first station/track)
def drawRightArrow(display,screen,RightArrow):
    mysize = (30,30)
    rows = display.getRows()
    columns = display.getColumns()
    #xPos = 755
    xPos = display.getColumnPos(columns - 3)
    #yPos = 32
    if rows > 24:
        yPos = 44
    else:
        yPos = 32
    myPos = (xPos,yPos)
    dir = os.path.dirname(__file__)
    path = "images/arrow_right_double.png"
    RightArrow.draw(screen,path,(myPos),(mysize))
    return


# Draw Up Icon
def drawUpIcon(display,screen,upIcon):
    xPos = size[0]-margin
    yPos = 80
    upIcon.draw(screen,xPos,yPos)
    return

# Draw Down Icon
def drawDownIcon(display,screen,downIcon):
    xPos = size[0]-margin
    yPos = size[1] - 120
    downIcon.draw(screen,xPos,yPos)
    return

# Draw switch program icon
def drawSwitchIcon(display,screen,switchIcon):
    xPos = size[0]-margin
    yPos = 150
    switchIcon.draw(screen,xPos,yPos)
    return

# Draw Equalizer Icon
def drawEqualizerIcon(display,screen,equalizerIcon):
    columns = display.getColumns()
    rows = display.getRows()
    xPos = display.getColumnPos(columns - 4)
    if rows > 25:
        yPos = display.getRowPos(int(rows*0.67))
    else:
        yPos = display.getRowPos(int(rows*0.62))
    equalizerIcon.draw(screen,xPos,yPos)
    return

# Page up through playlist
def pageUp(display,radio):
    global playlist,plName
    currentID = radio.getCurrentID()
    plsize = radio.getPlayListLength()
    maxLabels = display.config.getMaximumStations()
    page = getPage(currentID,maxLabels)
    newID = ((page + 1) * maxLabels) + 1 
    
    # Cycle through playlist
    if newID > plsize:
        plName = radio.cyclePlaylist(0)
        playlist = radio.getPlayList()
        newID = 1 
    radio.play(newID)
    return newID

# Page down through playlist
def pageDown(display,radio):
    currentID = radio.getCurrentID()
    maxLabels = display.config.getMaximumStations()
    page = getPage(currentID,maxLabels)

    # If first page go to last sation in the playlist
    if page < 1:
        newID = radio.getPlayListLength()
    else:
        newID = ((page - 1) * maxLabels) + maxLabels 
        
    radio.play(newID)
    if radio.getCurrentID() != newID:
        radio.channelDown()
    return newID

# Get pid
def getPid():
     pid = None
     if os.path.exists(pidfile):
          pf = open(pidfile,'r')
          pid = int(pf.read().strip())
     return pid

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

# Open equalizer window
def openEqualizer(radio,equalizer_cmd):
    #dir = os.path.dirname(__file__)
    dir = "/usr/share/radio"
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

# Stop program if stop specified on the command line
def stop():
     pid = getPid()
     if pid != None:
          os.kill(pid, signal.SIGHUP)
     exit(0)

# Main routine
if __name__ == "__main__":

    signal.signal(signal.SIGTERM,signalHandler)
    signal.signal(signal.SIGHUP,signalHandler)
    signal.signal(signal.SIGSEGV,signalCrash)
    signal.signal(signal.SIGABRT,signalCrash)

    picWallpaper = None

    locale.setlocale(locale.LC_ALL, '')

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
    log.message("locale " + str(locale.getdefaultlocale()), log.DEBUG)

    # Prevent LCD version of program starting
    os.popen("systemctl disable radiod")

    # See if alraedy running
    pid = checkPid(pidfile)

    # Stop the pygame mixer as it conflicts with MPD
    pygame.mixer.quit()

    font = pygame.font.SysFont('freesans', 13)
    display = GraphicDisplay(font)
    size = display.getSize()

    if display.config.fullScreen():
        flags = FULLSCREEN|DOUBLEBUF
    else:
        flags = DOUBLEBUF

    # Setup radio
    log.init('radio')
    if config.logTruncate():
        log.truncate()

    log.message("===== Graphic radio (vgradio.py) started ===", log.INFO)
    radioEvent = Event(config)    # Add radio event handler
    radio = Radio(rmenu,radioEvent,translate,config,log)  # Define radio
    log.message("Python version " + str(sys.version_info[0]) ,log.INFO)

    # Set up the screen
    size = config.getSize()
    try:
        screen = pygame.display.set_mode(size,flags)
    except Exception as e:
        msg = "vgradio screen size error:  " + str(e)
        print (msg)
        log.message(msg, log.ERROR)
        msg = "Fatal error - exiting"
        print (msg)
        log.message(msg, log.ERROR)
        sys.exit(1)

    log.message("DEBUG 2 radio.waitForNetwork()",log.DEBUG)
    ipaddr = radio.waitForNetwork()

    # Hide mouse if configured
    if display.config.fullScreen() and not display.config.displayMouse():
        pygame.mouse.set_cursor((8,8),(0,0),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0))

    # Paint screen background (Keep at start of draw routines)
    dir = os.path.dirname(__file__)
    wallpaper = dir + '/images/scale.jpg'     # Background wallpaper
    wcolor =(0,0,0)
    if len(wallpaper) > 1:
        picWallpaper=pygame.image.load(wallpaper)
        screen.blit(pygame.transform.scale(picWallpaper,size),(0,0))
    else:
        screen.fill(Color(wcolor))

    # If screen is too small report and exit to gradio
    if display.getRows() < 20:
        msg = "Screen size is too small!"
        print(msg)
        displayPopup(screen,radio,msg)
        time.sleep(7)
        dir = os.path.dirname(__file__)
        os.popen("sudo " + dir + "/gradio.py&")
        sys.exit(1)

    message = Message(radio,display,translate)
    text = message.get('loading_radio')

    displayPopup(screen,radio,text)
    surface=pygame.Surface((size))

    # Set up Xauthority for root user
    radio.execCommand("sudo cp /home/pi/.Xauthority /root/")

    # Prevent LCD version from running and disable it
    os.popen("sudo systemctl stop radiod")
    os.popen("sudo systemctl disable radiod")

    # Switch off character translation
    radio.translate.setTranslate(False) # Switch on text translation

    # Initialise radio
    setupRadio(radio)

    # Set up window title
    window_title = display.getWindowTitle(radio)
    pygame.display.set_caption(window_title)

    tunerSlider = TunerScaleSlider(pygame)
    currentID = radio.getCurrentID()
    drawTunerSlider(tunerSlider,screen,display,currentID)
    tunerSlider.drawScale(screen,size,lmargin,rmargin)
    
    # Create screen controls
    volume = radio.getVolume()
    volumeScale = VolumeScale(pygame)
    drawVolumeScale(volumeScale,screen,volume)
    volumeScale.drawSlider(screen,volume,lmargin)
    displayWindow = displayStationName(screen,radio)
    LeftArrow = Image(pygame)
    RightArrow = Image(pygame)
    drawLeftArrow(display,screen,LeftArrow)
    drawRightArrow(display,screen,RightArrow)
    upIcon = UpIcon(pygame)
    downIcon = DownIcon(pygame)
    switchIcon = SwitchIcon(pygame)
    equalizerIcon = EqualizerIcon(pygame)
    drawUpIcon(display,screen,upIcon)
    drawDownIcon(display,screen,downIcon)
    if display.config.switchPrograms():
        drawSwitchIcon(display,screen,switchIcon)
    MuteButton = MuteButton(pygame)
    MuteButton.draw(screen,display,(size[0]-(rmargin/2)-5,size[1]/2),
                    radio.muted(), size=(35,35))
    draw_equalizer_icon = displayEqualizerIcon(display)
    
    if draw_equalizer_icon:
        drawEqualizerIcon(display,screen,equalizerIcon)

    playlist = radio.getPlayList()
    maxLabels = getMaximumLabels(display,radio)
    maxStations = display.config.getMaximumStations()
    listIndex = 0   # Playlist index
    keyPress = -1
    sliderIndex = 0
    plName = radio.source.getName()

    # Screen saver times
    screenBlank = False
    screenMinutes = display.config.screenSaverTime()
    if screenMinutes > 0:
        blankTime = int(time.time()) + screenMinutes*60
    else:
        blankTime = 0

    # Start of main processing loop
    while run:

        # Blank screen after blank time exceeded
        if screenMinutes > 0 and int(time.time()) > blankTime:
            screenBlank = True

        # Reset the draw equalizer icon flag
        if int(subprocess.getoutput('pidof %s |wc -w' % "alsamixer")) < 1:
            draw_equalizer_icon = displayEqualizerIcon(display)
            if draw_equalizer_icon:
                equalizerIcon.enable()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                radio.stop()
                quit()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                blankTime = int(time.time()) + screenMinutes*60

                if screenBlank:
                    screenBlank = False

                elif tunerSlider.clicked(event):
                    radio.unmute()
                    newID = calculateID(radio,listIndex)
                    radio.play(newID)

                elif volumeScale.clicked(event):
                    volume = volumeScale.getVolume()
                    radio.setVolume(volume)

                elif LeftArrow.clicked():
                    radio.unmute()
                    pageDown(display,radio)

                elif RightArrow.clicked():
                    radio.unmute()
                    pageUp(display,radio)

                elif upIcon.clicked():
                    radio.unmute()
                    radioEvent.set(radioEvent.CHANNEL_UP)
                    
                elif downIcon.clicked():
                    radio.unmute()
                    radioEvent.set(radioEvent.CHANNEL_DOWN)

                elif draw_equalizer_icon and equalizerIcon.clicked():
                    openEqualizer(radio,"equalizer.cmd")
                    draw_equalizer_icon = False
                    equalizerIcon.disable()
                    
                elif display.config.switchPrograms() and switchIcon.clicked():
                    dir = os.path.dirname(__file__)
                    os.popen("sudo " + dir + "/gradio.py&")
                    run = False
                    break

                elif MuteButton.pressed():
                    radioEvent.set(radioEvent.MUTE_BUTTON_DOWN)

            elif event.type == pygame.MOUSEMOTION:
                if volumeScale.dragged(event):
                    volume = volumeScale.getVolume()
                    radio.setVolume(volume)

            elif event.type == KEYDOWN:
                blankTime = int(time.time()) + screenMinutes*60
                if screenBlank:
                    screenBlank = False
                else:
                    keyPress = handleKeyEvent(event.key,display,
                                radio,radioEvent)


        # Handle radio events
        if radioEvent.detected():
            log.message("radioEvent.detected", log.DEBUG)
            handleEvent(radio,radioEvent)

        # These must be drawn first so that they are hidden
        tunerSlider.drawScale(screen,size,lmargin,rmargin)
        volume = radio.getVolume()
        drawVolumeScale(volumeScale,screen,volume)
        
        # Paint screen background (Keep at start of draw routine)
        if picWallpaper == None:
            picWallpaper = pygame.image.load(wallpaper)
        screen.blit(pygame.transform.scale(picWallpaper,size),(0,0))

        # Display the radio details
        if display.config.displayDate():
            displayTimeDate(screen,radio,message)

        displayPlaylistName(screen,plName)

        # Scrolling station names
        currentID = radio.getCurrentID()
        page = getPage(currentID,maxStations)
        maxLabels =  getMaximumLabels(display,radio) 
        sliderIndex = (currentID -  maxStations * page) - 1
        listIndex = (page * maxStations)

        drawTunerSlider(tunerSlider,screen,display,sliderIndex)
        drawScaleNames(screen,radio,playlist,listIndex,maxLabels,lmargin)

        displayStationName(screen,radio)
        drawLeftArrow(display,screen,LeftArrow)
        drawRightArrow(display,screen,RightArrow)
        drawUpIcon(display,screen,upIcon)
        drawDownIcon(display,screen,downIcon)
        
        if draw_equalizer_icon:
            drawEqualizerIcon(display,screen,equalizerIcon)

        if display.config.switchPrograms():
            drawSwitchIcon(display,screen,switchIcon)

        volumeScale.drawSlider(screen,volume,lmargin)
        MuteButton.draw(screen,display,(size[0]-(rmargin/2)-7,(size[1]/2)-18),
                        radio.muted(), size=(35,35))

        # Display title and page position
        plsize = len(playlist)
        if display.config.displayTitle():
            displayTitle(screen,radio,message,plsize)
        displayPagePosition(page,maxStations,plsize)
    
        if screenBlank and display.config.fullScreen(): 
            screen.fill(Color(0,0,0))

        pygame.display.flip()

    # End of main while loop

# End of program
# set tabstop=4 shiftwidth=4 expandtab
# retab
