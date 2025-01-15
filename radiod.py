#!/usr/bin/env python3
#
# Raspberry Pi Radio daemon
#
# $Id: radiod.py,v 1.169 2025/01/15 12:27:36 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#       The authors shall not be liable for any loss or damage however caused.
#

from constants import *
import os,sys,pwd
import time
import signal
import socket
import datetime
import subprocess
from time import strftime
import RPi.GPIO as GPIO

import pdb
# To set break-point: pdb.set_trace()
import traceback

from config_class import Configuration
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

config = Configuration()
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
newMenu = True  # Speed up initial display if new menu entered
ignoreEvent = False # Ignore up/down button after double button menu press
pidfile = '/var/run/radiod.pid'
_volume = -1
save_rss_line = ''

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
    fname = '/traceback_radiod'
    with open(fname, 'w') as f:
        f.write(traceback.format_exc())
    msg = "Dump written to %s" %  fname
    print(msg)
    log.message(msg, log.CRITICAL)
    traceback.print_stack()
    os.abort()

def displayStopped():
    pid = os.getpid()
    msg = message.get('stopped')
    log.message(msg+ " PID  " + str(pid), log.INFO)
    radio.setInterrupt()
    display.clear()
    display.out(2,"")
    if display.getLines() > 2:
        display.out(3,"")
        display.out(4,"")
    display.out(1,msg)

# Signal SIGTERM handler
def signalHandler(signal,frame):
    global display
    global radio
    global log

    # Switch on red LED
    statusLed.set(StatusLed.ERROR)

    displayStopped()
    radio.stop()
    statusLed.set(StatusLed.CLEAR)
    msg = message.get('stopped')
    print ("\n" + msg)
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
        if source_type == radio.source.MEDIA:
            if display.getDelay() > 0:
                displayVolume(display, radio)
            else:
                if menu_mode != menu.MENU_INFO:
                    display.out(4,radio.getProgress())
        else:
            # Display time every during every interrupt checkn for
            # fast display of time configured with seconds 
            if menu_mode == menu.MENU_TIME or menu_mode == menu.MENU_RSS:
                displayTimeDate(display,radio,message)

    if display.hasButtons():
        display.checkButton()

    return interrupt

# Daemon class
class MyDaemon(Daemon):

    def run(self):
        signal.signal(signal.SIGTERM,signalHandler)
        signal.signal(signal.SIGHUP,signalHandler)
        signal.signal(signal.SIGSEGV,signalCrash)
        signal.signal(signal.SIGABRT,signalCrash)
        log.init('radio')
        self.process()

    # Main processing loop
    def process(self):
        global event
        global radio
        global message
        global statusLed
        global newMenu

        event = Event(config) # Must be initialised here

        # Set up radio
        if config.log_creation_mode:
            log.truncate()
        log.message("===== Starting radio =====",log.INFO)
        radio = Radio(menu,event,translate,config,log)
        message = Message(radio,display,translate)

        log.message("Python version " + str(sys.version_info[0]) ,log.INFO)

        # Set up status Led (Retro Radio only)
        statusLed = statusLedInitialise(statusLed)
        
        # Initialise display. The Adafruit RGB plate needs the 
        # event routine to be passed to it to handle its buttons
        display.init(callback = event)
        nlines = display.getLines()
        displayStartup(display,radio)

        # LCDs option to switch translation on/off. Switch off for OLEDs
        if display.isOLED():
            radio.translate.setTranslate(False)
            radio.setRomanize(False)  # Switch Romanisation off
        else:

            # For non-English  Romanize (Convert to Latin characters)
            romanize = radio.config.romanize
            radio.setRomanize(romanize)  # Switch Romanisation on/off

        ipaddr = radio.waitForNetwork()
        # Start radio and load source (radio, media or airplay)
        display.out(2,"Starting MPD")
        radio.start()

        # Wait for network
        if nlines > 2:
            line = 3
        else: 
            line = 2
        if len(ipaddr) < 1 and config.no_internet_switch:
            # Switch to MEDIA if no IP address
            msg = "No Internet"
            display.out(line,msg)
            log.message(msg, log.ERROR)       
            try:
                radio.cycleWebSource(radio.source.MEDIA)
            except:
                log.message("Error trying to load media", log.ERROR)       
                pass
        else:
            if len(ipaddr) < 1:
                msg = "No Internet"
            else:
                msg = "IP " + ipaddr
            log.message(msg, log.INFO)
            display.out(line,msg)

        time.sleep(2)    # Allow time to display IP address

        loadSource(display,radio)
        current_id = radio.getCurrentID()
        radio.play(current_id)

        progcall = str(sys.argv)
        log.message("Radio " +  progcall + " Version " + radio.getVersion(), log.INFO)
        log.message('Radio running pid ' + str(os.getpid()), log.INFO)

        statusLed.set(StatusLed.NORMAL)
        display.refreshVolumeBar()

        # Main processing loop
        while True:

            try:
                menu_mode = menu.mode()

                if radio.doUpdateLib():
                    updateLibrary(display,radio,message)
                    radio.play(1)

                elif menu_mode == menu.MENU_TIME:
                    displayTimeDate(display,radio,message)
                    displayCurrent(display,radio,message)
                    displayVolume(display,radio)

                elif menu_mode == menu.MENU_SEARCH:
                    displaySearch(display,menu,message)

                elif menu_mode == menu.MENU_SOURCE:
                    displaySource(display,radio,menu,message)

                elif menu_mode == menu.MENU_OPTIONS:
                    displayOptions(display,radio,menu,message)

                elif menu_mode == menu.MENU_RSS:
                    if display.hasScreen():
                        displayRss(display,radio,message,rss)
                        displayVolume(display,radio)
                    else:
                        menu.set(menu.MENU_TIME) # Skip RSS

                elif menu_mode == menu.MENU_INFO:
                    if display.getDelay() > 0:
                        displayVolume(display, radio)
                    else:
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
            
                radio.displayVuMeter()

                # Keep MPD connection alive
                radio.ping()

                # Recover from no Internet connection 
                source_type = radio.getSourceType()
                if len(ipaddr) < 1 and source_type == radio.source.RADIO:
                    ipaddr = radio.get_ip()

                # When volume switches or rotary encoder operated display
                # message scrolling is suppressed for a few seconds to speed
                # up the volume change operation.
                d = display.decrementDelay()
                if d < 1:
                    display.noScrolling(False)
                else:    
                    display.noScrolling(True)
    
                displayBacklight(radio,menu,display)

                # Check if streamripper is rocording
                self.recording = radio.isRecording()

                # This delay is important and should be more than switch bounce times
                time.sleep(0.025)

            except KeyboardInterrupt:
                print ("Stopped")
                displayStopped()
                radio.stop()
                time.sleep(1)
                sys.exit(0)

    # End of main while loop

    # Status routines
    def status(self):
        # Get the pid from the pidfile
        try:
            pf = open(self.pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None

        if not pid:
            message = "radiod status: not running"
            log.message(message, log.INFO)
            print(message)
        else:
            message = "radiod running pid " + str(pid)
            log.message(message, log.INFO)
            print(message)

    # Version
    def getVersion(self):
        myradio = Radio(menu,event,None,config,log)    
        return myradio.getVersion()

    # Build
    def getBuild(self):
        myradio = Radio(menu,event,None,config,log)    
        return myradio.getBuild()

# End of class overrides

# Pass events to the appropriate event handler 
def handleEvent(event,display,radio,menu):
    global ignoreEvent
    event_type = event.getType()
    event_name = event.getName()
    menu_mode = menu.mode()
    displayType = display.getDisplayType()

    # Retro radio RGB status LED
    statusLed.set(StatusLed.BUSY)

    if event_type != event.NO_EVENT:
        log.message("Event type " + str(event_type) + ' ' + event_name, log.DEBUG)

    # Used when double button menu pressed to prevent extraneous events
    if ignoreEvent:
        event_type = event.set(event.NO_EVENT)
        ignoreEvent = False

    # Exit from sleep if alarm fired
    if event_type == event.ALARM_FIRED:
        wakeup(radio,menu)

    # If both up and down pressed together convert
    # to menu pressed (if no separate menu switch eg. Pirate Audio ST7789TFT)
    elif (event_type == event.UP_SWITCH or event_type == event.DOWN_SWITCH) \
            and displayType == radio.config.ST7789TFT:
        time.sleep(0.4)
        count = 7
        while event.downButtonPressed() and event.upButtonPressed:
            time.sleep(0.1)
            count -= 1
            if count < 0:
                event_type = event.set(event.MENU_BUTTON_DOWN)
                ignoreEvent = True
                time.sleep(0.2)
                break

    # Exit from sleep if  menu button pressed
    if menu_mode == menu.MENU_SLEEP:
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

    elif event_type == event.MPD_CLIENT_CHANGE:
        log.message("handleEvent Client Change",log.DEBUG)

    elif event_type == event.PLAY:
        play_number = event.getPlayNumber() 
        log.message("handleEvent Play " + str(play_number),log.DEBUG)
        radio.play(play_number)

    elif event_type != event.NO_EVENT:
        handleRadioEvent(event,display,radio,menu)

    # Clear event 
    event.clear()
    statusLed.set(StatusLed.NORMAL)

# Handle normal volume and channel change events
def handleRadioEvent(event,display,radio,menu):
    global _connecting
    event_type = event.getType()
    event_name = event.getName()
    menu_mode = menu.mode()
    volume_change = False   
    nlines = display.getLines()
    displayType = display.getDisplayType()

    vDelay = 60

    log.message('handleRadioEvent ' + str(event_type) + ' ' + event_name, log.DEBUG)

    if event_type == event.VOLUME_UP:

        log.message('Volume UP', log.DEBUG)
        radio.setInterrupt()
        display.noScrolling(True)
        radio.increaseVolume()

        # Both left and right buttons together mute radio
        if config.user_interface == config.BUTTONS:
            if event.leftButtonPressed():
                mute(radio,display)
                displayVolume(display, radio)
                time.sleep(0.3)

            else:
                # Volume UP repeat
                while event.rightButtonPressed():
                    radio.increaseVolume()
                    displayVolume(display, radio)
                    time.sleep(0.1)

        display.refreshVolumeBar()
        volume_change = True    

    elif event_type == event.VOLUME_DOWN:

        log.message('Volume DOWN', log.DEBUG)
        radio.setInterrupt()
        display.noScrolling(True)
        radio.decreaseVolume()

        # Both left and right buttons together mute radio
        if config.user_interface == config.BUTTONS:
            if event.rightButtonPressed():
                mute(radio,display)
                displayVolume(display, radio)
                time.sleep(0.3)
            else:
                # Volume DOWN repeat
                while event.leftButtonPressed():
                    radio.decreaseVolume()
                    displayVolume(display, radio)
                    time.sleep(0.1)

        display.refreshVolumeBar()
        volume_change = True    

    elif event_type == event.MUTE_BUTTON_DOWN:
        volume_change = True    
        if radio.muted():
            log.message('Unmute', log.DEBUG)
            radio.unmute()
            # Need clear line 5 on the OLED_128x64 display
            if displayType == radio.config.OLED_128x64:
                display.out(5, ' ', no_interrupt)
            display.refreshVolumeBar()
            if display.getLines() == 4:
                display.out(4, "", no_interrupt)
        else:
            log.message('Mute switch, speech ' + str(radio.config.speech), 
                    log.DEBUG)

            # If speech the mute button has to be held in for two seconds
            if radio.config.speech:
                count = 10  # Two second wait
                while event.muteButtonPressed():
                    count -= 1
                    time.sleep(0.2)
                    if count < 0:
                        mute(radio,display)

                if count > 0:
                    speakCurrent(message,radio)
            else:
                mute(radio,display)

        time.sleep(0.5) # Prevent unmute
        displayVolume(display,radio)

    elif event_type == event.CHANNEL_UP:
        log.message('Channel UP', log.DEBUG)
        radio.channelUp()
        display.setDelay(0) # Cancel delayed display of volume
        if menu_mode == menu.MENU_INFO:
            menu.set(menu.MENU_TIME)
        if radio.config.verbose:
            speakCurrent(message,radio,speak_title=False)
        _connecting = False
        display.refreshVolumeBar()

    elif event_type == event.CHANNEL_DOWN:
        log.message('Channel DOWN', log.DEBUG)
        radio.channelDown()
        display.setDelay(0) # Cancel delayed display of volume
        if menu_mode == menu.MENU_INFO:
            menu.set(menu.MENU_TIME)
        if radio.config.verbose:
            speakCurrent(message,radio,speak_title=False)
        _connecting = False
        display.refreshVolumeBar()

    elif event_type == event.MENU_BUTTON_DOWN:
        if radio.muted():
            radio.unmute()
            
        handleMenuChange(display,radio,menu,message)
        display.refreshVolumeBar()

    elif event_type == event.RECORD_BUTTON:
        log.message('RECORD_BUTTON event received', log.DEBUG)
        radio.handleRecordKey(event_type)

    elif event_type == event.PLAYLIST_CHANGED:
        log.message('event PLAYLIST_CHANGED', log.DEBUG)
        print('PLAYLIST_CHANGED event received')
        radio.handlePlaylistChange()

    elif event_type == event.SHUTDOWN:
        log.message('event SHUTDOWN', log.DEBUG)
        displayStop(display,message)
        radio.stopMpdDaemon()
        if radio.config.shutdown: 
            display.out(1, message.get('shutdown'))
            display.backlight('shutdown_color')
            radio.shutdown() # Shutdown the system
        else:
            display.out(1, message.get('stopped'))
            cmd = radio.config.execute
            if len(cmd) > 3:
                GPIO.cleanup()
                msg = "Executing %s" % cmd
                log.message(msg, log.INFO)

                # Stop UDP server thread
                radio.server.stop()
                try:
                    execCommand(cmd + ' &')
                except Exception as e:
                    print(str(e))

                sys.exit(0)


        msg = "Exiting! process %s" % os.getpid()
        print(msg)
        log.message(msg, log.INFO)
        sys.exit(0)

    # Display volume
    if volume_change:
        display.setDelay(vDelay)
        #displayVolume(display,radio)

# Handle source menu selection event
def handleSourceEvent(event,display,radio,menu):
    display.setDelay(0) # Cancel delayed display of volume
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
    time.sleep(0.06) # Prevent skipping

# Handle menu stepthrough
def handleMenuChange(display,radio,menu,message):
    global newMenu,_volume
    newMenu = True
    current_menu = menu.get() # Needed for alarm check 
    menu_mode = menu.cycle()
    menu_name = menu.getName()

    log.message('Menu mode ' + str(menu_mode) + ' ' + str(menu_name), log.DEBUG)
    if display.getLines() >= 4:
        _volume = -1 # Force volume to always be displayed on new menu

    hostname = socket.gethostname()
    ip_addr = radio.get_ip()

    source_type = radio.getSourceType()

    # Was the previous option to activate the alarm?
    if menu.getOption() == menu.OPTION_ALARM and current_menu == menu.MENU_OPTIONS:
        if radio.getAlarmType() != 0:
            sleep(radio,menu)

    elif radio.optionChanged():
        menu.set(menu.MENU_TIME)
        radio.optionChangedFalse()

    elif menu_mode == menu.MENU_INFO:
        message.storeIpAddress(ip_addr)

        # Force volume display when first returning to TIME display
        if display.getLines() > 2:
            display.setDelay(1)

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
        radio.getDisplayVolume()    # XXXXXXXXXX

    if menu_mode != menu.MENU_SLEEP:
        display_mode = menu.mode()
        sMenu = menu_name.replace('_', ',')

        if display_mode == menu.MENU_RSS:
            sMenu = "Main"
        
            # Speak info if speak info true
            if radio.config.speech and radio.config.speak_info:
                menu.set(menu.MENU_INFO)
                sMenu = hostname +  " IP " + str(ip_addr)
                sMenu = convertInfo(hostname,ip_addr)

        if display.hasScreen():
            sMenu = sMenu.lower()

        message.speak(sMenu)

    time.sleep(0.2) # Prevent skipping next menu
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

    elif option_index == menu.OPTION_RECORD_DURATION:
        if event_type == event.RIGHT_SWITCH:
            inc = 5
        else:
            inc = -5
        radio.incrementRecordDuration(inc)

    elif option_index == menu.OPTION_RELOADLIB:
        if radio.toggleOptionValue(option_index):
            radio.setUpdateLibOn()
        else:
            radio.setUpdateLibOff()
    else:
        radio.toggleOptionValue(option_index) 

    # Indicate option has changed
    radio.optionChangedTrue()


# Handle timer event , put radio to sleep 
def sleep(radio,menu):
    log.message("Sleep", log.INFO)
    mute(radio,display)
    menu.set(menu.MENU_SLEEP)
    display.setDelay(10)

# Handle alarm event , put radio to sleep 
def wakeup(radio,menu):
    log.message("Alarm fired", log.INFO)
    radio.unmute()
    menu.set(menu.MENU_TIME)
    menu.setOption(menu.OPTION_RANDOM)

# Mute radio
def mute(radio,display):
    radio.mute()

################ Display Routines ############

# Display startup
def displayStartup(display,radio):
    nlines = display.getLines()
    pid = os.getpid()
    ipaddr = radio.get_ip()
    version = radio.getVersion()
    msg = message.get('radio_version')

    display.out(1,msg + " " + version)
    if nlines > 2:
        display.out(2,"Radio PID " + str(pid))
        display.out(3,message.get("waiting_for_network"))
        msg = message.get('mpd_version')
        display.out(4, msg + " " + radio.getMpdVersion())
    else:
        display.out(2,"Waiting for network")

    time.sleep(1)

# Display time and if width > 40 chars display station/artist name
def displayTimeDate(display,radio,message):
    msg = message.get('date_time')
    
    width = display.getWidth()

    # Small displays drop day of the week, ignore width
    if width < 16:
        msg = msg[0:5] 
    else:
        msg = msg[0:width]

    # If streaming add the streaming indicator
    if radio.getStreaming() and width > 16:
        streaming = '+'
    else:
        streaming = ''

    # If recording add the recording indicator
    if radio.isRecording():
        recording_ind = '*'
    else:
        recording_ind = ''

    dtype = config.getDisplayType()

    # Display time/date double size if using oled_class
    if dtype == config.OLED_128x64:
        display.setFontScale(2)
    
    if width >= 40: 
        sourceType = radio.getSourceType()
        if sourceType == radio.source.RADIO:
            search_name = radio.getSearchName()
            if len(msg + " " + search_name) > width:
                msg = msg[:5]
            msg = msg + " " + search_name 
            display.out(1,msg[:width])

        elif sourceType == radio.source.MEDIA:
            artist = radio.getCurrentArtist()
            if len(msg + " " + artist) > width:
                msg = msg[:5]
            msg = msg + " " + artist 
            display.out(1,msg[:width])
    else:
        display.out(message.getLine(),msg + recording_ind + streaming)

    if dtype == config.OLED_128x64:
        display.setFontScale(1)

# Display the search menu
def displaySearch(display,menu,message):
    global newMenu
    index = radio.getSearchIndex()
    source_type = radio.getSourceType()
    current_id = radio.getCurrentID()
    lines = display.getLines()  

    sSearch = 'menu_search'
    if display.getWidth() < 16:
        sSearch = 'menu_find'

    display.out(1, message.get(sSearch) + ':' + str(index+1), interrupt)

    if source_type == radio.source.MEDIA:
        current_artist = radio.getArtistName(index)
        current_track = radio.getTrackNameByIndex(index)

        if lines > 2:
            display.out(2,current_artist[0:50],interrupt)
            display.out(3,current_track,interrupt)

            if display.getDelay() > 0:
                displayVolume(display, radio)
            else:
                display.out(4,radio.getProgress(),interrupt)
                message.speak(str(index+1) + ' ' +  current_artist[0:50])
        else:
            if display.getDelay() > 0 and source_type != radio.source.MEDIA:
                displayVolume(display, radio)
            else:
                info = current_artist[0:50] + ': ' + current_track
                display.out(2,info,interrupt)
                message.speak(str(index+1) + ' ' +  current_artist[0:50])

    elif source_type == radio.source.RADIO:
        ## search_station = radio.getStationName(index)
        search_station = radio.getSearchName()
        search_station = search_station.lstrip('"')
        search_station = search_station.rstrip('"')

        if lines > 2:
            display.out(2,search_station[0:30],interrupt)
            currentStation = message.get('current_station') + ':' + str(current_id)
            display.out(3, currentStation  ,interrupt)
            displayVolume(display, radio)
            message.speak(str(index+1) + ' ' +  search_station[0:50])
        else:
            if display.getDelay() > 0:
                displayVolume(display, radio)
            else:
                display.out(2,search_station[0:30],interrupt)
                message.speak(str(index+1) + ' ' +  search_station[0:50])

    newMenu = False

# Display the source menu
def displaySource(display,radio,menu,message):
    global newMenu
    index = radio.getSearchIndex()
    current_id = radio.getCurrentID()
    lines = display.getLines()  
    sSource = radio.getNewSourceName()
    station = radio.getSearchName()

    display.out(1, message.get('menu_source') + ':', no_interrupt)

    if lines > 2:
        display.out(2, sSource, no_interrupt)
        display.out(3, station ,interrupt)
        displayVolume(display, radio)
    else:
        if display.getDelay() > 0:
            displayVolume(display, radio)
        else:
            display.out(2, sSource, no_interrupt)

    message.speak(sSource)
    newMenu = False

# Display backlight colours for screens with RGB colours
# Displays without that capability simply ignore these instructions
def displayBacklight(radio,menu,display):
    mode = menu.mode()
    if radio.muted():
        display.backlight('mute_color')
    elif mode == menu.MENU_TIME:
            display.backlight('bg_color')
    elif mode == menu.MENU_SEARCH:
        display.backlight('search_color')
    elif mode == menu.MENU_SOURCE:
        display.backlight('source_color')
    elif mode == menu.MENU_OPTIONS:
        display.backlight('menu_color')
    elif mode == menu.MENU_RSS:
        display.backlight('news_color')
    elif mode == menu.MENU_INFO:
        display.backlight('info_color')
    elif mode == menu.MENU_SLEEP:
        display.backlight('sleep_color')

# Display the options menu
def displayOptions(display,radio,menu,message):
    global newMenu
    sText = ''  # Speech text
    option_index = menu.getOption()
    option_value = radio.getOptionValue(option_index)
    source_type = radio.getSourceType()
    
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

    elif option_index == menu.OPTION_RECORD_DURATION:
        text = option_value

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
        elif source_type == radio.source.RADIO:
            displayVolume(display, radio)

    # Only speak message if on/off yes/no etc
    if len(sText) > 0:
        message.speak(option_name + ' ' + sText)

    time.sleep(0.2) # Prevent skipping of options
    newMenu = False

# Display the RSS feed
def displayRss(display,radio,message,rss):
    global newMenu,save_rss_line
    lwidth = None
    dwidth = display.getWidth() 
    if newMenu:
        lwidth = display.getWidth()

    source_type = radio.getSourceType()
    displayTimeDate(display,radio,message)


    nLines = display.getLines()
    if display.getDelay() == 0:
        rss_line = rss.getFeed()
        save_rss_line = rss_line
    else:
        rss_line = save_rss_line

    if nLines > 4:
        plName = radio.getSourceName()
        current_id = radio.getCurrentID()
        plsize = radio.getPlayListLength()
        msg = "Station %d/%d" % (current_id,plsize)
        display.out(4,msg[0:dwidth],interrupt)

    line = 2

    if nLines > 2:
        line = 3
        if source_type == radio.source.MEDIA:
            name = radio.getCurrentArtist()
        else:
            name = radio.getSearchName()
        display.out(2,name[0:dwidth],interrupt)

    if display.getDelay() == 0:
        display.out(line,rss_line[0:lwidth],interrupt,rssfeed=True)
    else:
        displayVolume(display, radio)

    if len(rss_line) <= dwidth:
        time.sleep(0.5)

    newMenu = False

# Display the information menu
def displayInfo(display,radio,message):
    global newMenu

    displayType = display.getDisplayType()
    nLines = display.getLines()
    lwidth = None

    if newMenu:
        lwidth = display.getWidth()
    ipaddr = message.getIpAddress()
    if len(ipaddr) < 1:
        ipaddr = radio.get_ip()
        ipaddr = message.storeIpAddress(ipaddr)
    version = radio.getVersion()
    build = radio.getBuild()
    nlines = display.getLines()
    #msg = message.get('radio_version') + ' ' + version
    msg = message.get('radio_version') + ' ' + build
    
    display.out(1, msg, interrupt )

    if nlines > 2:
        if display.getDelay() > 0:
            displayVolume(display, radio)
        else:
            msg = 'Hostname: ' + socket.gethostname()
            display.out(4,msg,interrupt)

        display.out(2, 'IP:' + ipaddr, interrupt )
        msg = 'MPD version ' + radio.getMpdVersion()
        display.out(3, msg, interrupt )

    else:
        msg = 'IP:%s %s' % (ipaddr,socket.gethostname())
        display.out(2, msg, interrupt )

    if nLines >= 5 and displayType == radio.config.ST7789TFT:
        msg = radio.OSname + ' ' + radio.arch
        display.out(5,msg)

    display.update()    
    newMenu = False


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

# Display stop radio 
def displayStop(display,message):
    display.backlight('shutdown_color')
    display.out(1, message.get('stop'))
    display.out(2, ' ')
    if display.getLines() > 2:
        display.out(3, ' ')
        display.out(4, ' ')

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

    
# Display current playing selection or station
def displayCurrent(display,radio,message):
    global _connecting, newMenu

    lwidth = None
    if newMenu:
        lwidth = display.getWidth()

    # get details of currently playing source
    current_id = radio.getCurrentID()
    sourceType = radio.getSourceType()
    plsize = radio.getPlayListLength()

    errorString = ''
    if radio.gotError():
        errorString = radio.getErrorString()

    if sourceType == radio.source.RADIO:
        station_name = radio.getCurrentStationName()
        search_name = radio.getSearchName()
        title = radio.getCurrentTitle()
        bitrate = radio.getBitRate()
        station = search_name   # Name from our playlists
        name = station_name # Name sent with the stream

        if len(title) > 0:
            name = title    # Sometimes title is used

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
            display.out(2,station[0:lwidth],interrupt)
            if len(errorString) > 0:
                display.out(3,errorString[0:lwidth],interrupt)
            else:
                display.out(3,name[0:lwidth],interrupt)

            if nLines > 4:
                plName = radio.getSourceName()
                plName = plName.replace('_','')
                current_id = radio.getCurrentID()
                plsize = radio.getPlayListLength()
                msg = "Station %d/%d %s" % (current_id,plsize,plName)
                display.out(4,msg[0:lwidth],interrupt)

            displayType = display.getDisplayType()
            if nLines >= 5 and displayType == radio.config.ST7789TFT:
                msg = "Bit rate: %dK" % radio.getBitRate()
                display.out(5,msg)
        else:
            # For 2 lines display volume if changed
            if display.getDelay() > 0:
                displayVolume(display, radio)
            elif len(errorString) > 0:
                display.out(2,errorString[0:lwidth],interrupt)
            else:
                lwidth = display.getWidth()

                # Support for 40 character LCDs
                if lwidth >= 40:

                    if radio.muted():
                        details = message.get('muted')
                    else:
                        details = title
                        if len(title) < 1 :
                            sStation = message.get('station')
                            title = message.get('no_information')
                            current_id = radio.getCurrentID()
                            details = sStation + " " + str(current_id) + ": " + title
                    display.out(2,details,interrupt)
                else:
                    details = station + ': ' + name
                    display.out(2,details[0:lwidth],interrupt)

    elif sourceType == radio.source.MEDIA:
        # If no playlist then try reloading library
        if current_id < 1:
            log.message("No current ID found", log.DEBUG)
            updateLibrary(display,radio,message)

        artist = radio.getCurrentArtist()
        title = radio.getCurrentTitle()

        if display.getLines() > 2:
            display.out(2,artist[0:lwidth],interrupt)
            display.out(3,title[0:lwidth],interrupt)

            if display.getDelay() > 0:
                displayVolume(display, radio)
            else:
                display.out(4,radio.getProgress()[0:lwidth],interrupt)

        else:
            if display.getDelay() > 0:
                displayVolume(display, radio)
            else:
                lwidth = display.getWidth()
                # 40 character LCD
                if lwidth >= 40:
                    details = title
                else:
                    details = artist + ': ' + title
                display.out(2,details,interrupt)

    elif sourceType == radio.source.AIRPLAY:
        displayVolume(display, radio)
        displayAirplay(display,radio)

    elif sourceType == radio.source.SPOTIFY:
        displaySpotify(display,radio)

    #display.update()
    newMenu = False

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

# Display Spotify information
def displaySpotify(display,radio):
    info = radio.getSpotifyInfo()
    displayType = display.getDisplayType()

    if displayType == radio.config.ST7789TFT and len(info) < 1:
        display.drawSplash("images/spotify.png",1.5)
    else:
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
            #display.out(4,"Volume:Use spotify")
        else:
            if display.getDelay() > 0:
                displayVolume(display, radio)
                time.sleep(0.1)
            else:
                display.out(2,info,interrupt)


# Display volume on correct line. NB. Do not call with an interrupt
# otherwise a recursive error will occur as the this 
# routine is also called from the interrupt routine
def displayVolume(display,radio):
    menu_mode = menu.mode()
    # Display volume only if not in Info mode
    _displayVolume(display,radio)
    if menu_mode != menu.MENU_INFO or display.getDelay() > 0:
        if display.isOLED():
            _displayOledVolume(display,radio)
        else:
            _displayVolume(display,radio)
    
# LCD volume display routine
def _displayVolume(display,radio):
    global _volume
    msg = ''
    mute_line = 0
    volume = radio.getDisplayVolume()
    if radio.muted():
        msg = message.get('muted')
        mute_line = display.getMuteLine()
        radio.getVolume() # Check if volume changed by external client
    else:
        msg = message.get('volume') + ' ' + str(volume)
        tTimer = radio.getTimerCountdown()
        
        if tTimer > 0 and display.getWidth() > 8:
            msg = msg + ' ' + message.getTimerText(tTimer)
    
        elif radio.config.display_blocks:
            msg = message.volumeBlocks()
    if volume != _volume:
        if mute_line > 0:
            line = mute_line
        else:
            line = message.getLine()
        display.out(line, msg, no_interrupt)
        _volume = volume

# The OLEDs have a special volume display bar on the last line
def _displayOledVolume(display,radio):
    dtype = config.getDisplayType()
    if radio.muted():
        msg = message.get('muted')
        radio.getVolume() # Check if volume changed by external client
        if dtype == config.ST7789TFT:
            display.out(5, msg, no_interrupt)
        else:
            # SSD1306 and OLED_128x64
            display.out(display.getLines(), msg, no_interrupt)
    else:
        volume = radio.getDisplayVolume()
        if radio.config.display_blocks:
            #if dtype == config.ST7789TFT:
            #    display.out(5, " ", no_interrupt)
            volume = radio.getVolume() # Real volume
            display.volume(volume)
        else:
            displayVolume = radio.getDisplayVolume()
            msg = message.get('volume') + ' ' + str(displayVolume)
            display.out(display.getLines(), msg, no_interrupt)

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
    print("usage: %s start|stop|restart|status|version|build|nodaemon" % sys.argv[0])

# End of class

### Main routine ###
if __name__ == "__main__":
    from constants import __version__, build

    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    if 'version' == sys.argv[1]:
        print('Version',__version__)
        sys.exit(0)

    if 'build' == sys.argv[1]:
        print('Build',build)
        sys.exit(0)

    if pwd.getpwuid(os.geteuid()).pw_uid > 0:
        print ("This program must be run with sudo or root permissions!")
        sys.exit(1)

    daemon = MyDaemon(pidfile)
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
        elif 'build' == sys.argv[1]:
            daemon.build()
        elif 'nodaemon' == sys.argv[1]:
            daemon.nodaemon()
        else:
            print("Unknown command: " + sys.argv[1])
            usage()
            sys.exit(2)
        sys.exit(0)
    else:
        # Note - do not include nodaemon in the list of possibilities
        usage()
        sys.exit(2)

# End of script
# set tabstop=4 shiftwidth=4 expandtab
# retab
