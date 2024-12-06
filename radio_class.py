#!/usr/bin/env python3
#
# Raspberry Pi Internet Radio Class
# $Id: radio_class.py,v 1.169 2024/12/06 15:50:53 bob Exp $
# 
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class uses  Music Player Daemon 'mpd' and the python3-mpd library
# Use "apt-get install python3-mpd" to install the library
# See: https://pypi.org/project/python-mpd2/
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#         The authors shall not be liable for any loss or damage however caused.
#

import os
import sys
import string
import time,datetime
import re
import socket
import socketserver
import platform
from time import strftime
from os import stat
from pwd import *
import pdb
import subprocess
import signal

from constants import __version__
from constants import *

from udp_server_class import UDPServer
from udp_server_class import RequestHandler
from log_class import Log
from airplay_class import AirplayReceiver
from spotify_class import SpotifyReceiver
from language_class import Language
from source_class import Source
from volume_class import Volume
from playlist_class import Playlist
from record import Recorder
import mpd

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
SourceNameFile = RadioLibDir + "/source_name"
VolumeFile = RadioLibDir + "/volume"
MixerVolumeFile = RadioLibDir + "/mixer_volume"
MixerIdFile = RadioLibDir + "/mixer_volume_id"
BoardRevisionFile = RadioLibDir + "/boardrevision"

# Recording PID details
PidDir = '/var/run/radio_record'
record_pidfile = PidDir + '/record.pid'
ireventd_pidfile = '/var/run/ireventd.pid'

Icecast = "/usr/bin/icecast2"

# Option values
RandomSettingFile = RadioLibDir + "/random"
TimerFile = RadioLibDir + "/timer" 
AlarmFile = RadioLibDir + "/alarm" 
StreamFile = RadioLibDir + "/streaming"
RecordingDurationFile = RadioLibDir + "/recording"

log = None
language = None

Mpd = "/usr/bin/mpd"    # Music Player Daemon
Mpc = "/usr/bin/mpc"    # Music Player Client

# Error codes 
NO_ERROR = 0
MPD_STREAM_ERROR = 1
MPD_NO_CONNECTION = 2
MPD_ERROR = 3
INTERNET_ERROR = 4
MPD_EMPTY_PLAYLIST = 5

ON = True
OFF = False

# Radio class
class Radio:
    translate = None    # Translate object
    spotify = None      # Spotify object
    server = None
    ir_pid = -1         # IR event daemon process pid
    record_pid = -1     # Recording process pid

    client = mpd.MPDClient()    
    volume = 0

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

    ONEDAYSECS = 86400  # Day in seconds
    ONEDAYMINS = 1440   # Day in minutes

    config = None
    pivumeter = None

    source = None   # Source (radio,media,spotify and airplay)
    audio_error = False     # No sound device
    boardrevision = 2 # Raspberry board version type
    MpdVersion = '' # MPD version 
    udphost = 'localhost'  # Remote IR listener UDP Host
    udpport = 5100  # Remote IR listener UDP port number
    mpdport = 6600  # MPD port number
    device_error_cnt = 0    # Device error causes an abort
    isMuted = False # Is radio state "pause" or "stop"
    searchlist = [] # Search list (tracks or radio stations)
    current_id = 1  # Currently playing track or station
    current_source = 0 # Current source (index in current_class.py)
    reload = False  # Reload radio stations or player playlists
    loading_DB = False  # Loading database
    artist = "" # Artist (Search routines)
    airplayInstalled = False # Airplay (shairport-sync) installed
    spotifyInstalled = False # Spotify (librespot) installed
    error = False   # Stream error handling
    errorCode = NO_ERROR # Error qualifier
    updateLib = False    # Reload radio stations or player
    interrupt = False   # Was IR remote interrupt received
    stats = None        # MPD Stats array
    currentsong = None  # Current song / station
    state = 'play'      # State (used if get state fails) 
    getIdError = False  # Prevent repeated display of ID error
    display_artist = False      # Display artist (or track) flag
    current_file = ""       # Currently playing track or station
    option_changed = False      # Option changed
    channelChanged = True       # Used to display title
    display_playlist_number = False # Display playlist number
    speech = False          # Speech enabled yes/no
    last_direction = UP     # Last search direction
    skipped_bad = True      # Skipped bad channel/track
    mpd_restart_count = 3       # MPD restart count
    internet_check_delay = 0    # Prevent too many Internet checks
    error_display_delay = 0     # Delay before clearing error messages
    playlist_size = 0           # For checking changes to the playlist
    PL = None                   # Playlist class
    ip_addr = ''                # Local IP address
    OSrelease = ''              # OS Release 
    
    # MPD Options
    random = False  # Random tracks
    repeat = False  # Repeat play
    consume = False # Consume tracks
    single = False  # Single play

    # Radio options
    reloadlib = False   # Reload music library yes/no

    # Clock and timer options
    timer = 0     # Timer on
    timerValue = 0    # Timer value in minutes
    timeTimer = 0     # The time when the Timer was activated in seconds 
    dateFormat = "%H:%M %d/%m/%Y"   # Date format

    alarmType = ALARM_OFF   # Alarm on
    alarmTime = "0:7:00"    # Alarm time default type,hours,minutes
    alarmTriggered = False  # Alarm fired

    recordDuration = "1:25" # Record duration in hours:minutes

    stationTitle = ''       # Radio station title
    stationName = ''        # Radio station name
    playlistName = 'Radio'     # Initial playlist name

    search_index = 0    # The current search index
    loadnew = False     # Load new track from search
    streaming = False   # Streaming (Icecast) disabled

    playlists = None
    bluetooth_retry = 3 # Retry count for bluetooth connection

    pingTime = 0        # Reduce amount of pings
    pingDelay = 15      # Delay between pings in seconds
    recordTime = 0      # Reduce amount of recording checks
    recordDelay = 4     # Delay between recording checks in seconds

    connected = False   # Connection status
    recording = False   # Recording station

    # Configuration files in /var/lib/radiod 
    ConfigFiles = {
        CurrentStationFile: 1,
        CurrentTrackFile: 1,
        CurrentSourceFile: 0,
        SourceNameFile: "Radio",
        VolumeFile: 75,
        MixerVolumeFile: 90,
        TimerFile: 30,
        AlarmFile: "0:07:00", 
        StreamFile: "off", 
        RandomSettingFile: 0,
        RecordingDurationFile: "1:05",   # Hours:Minutes
        }

    # Error strings 
    errorStrings = ['No error','MPD stream error','MPD connection error',
                    'MPD error','No Internet','Empty playlist']

    # Initialisation routine
    def __init__(self, menu, event, translate, config, logobj):
        global log
        log = logobj
        pid = os.getpid()
        log.message("Initialising radio pid %d" % pid, log.INFO)
        self.config = config

        # Get user installation name from a well known installed file or direct
        self.usr = getpwuid(stat("/usr/share/radio").st_uid).pw_name
        log.message("Login name %s" % self.usr, log.INFO)
        self.grp = self.usr  # Temporary only
        self.uid = getpwnam(self.usr).pw_uid
        self.gid = getpwnam(self.usr).pw_gid
        msg = "User:%s(%s)  Group:%s(%s)" % (self.usr,self.uid,self.grp,self.gid)
        log.message(msg, log.INFO)

        if self.config.pivumeter:
            from pivumeter_class import PiVumeter
            self.pivumeter = PiVumeter()

        self.PL = Playlist('Radio',self.config)     # Playlist class 
        self.translate = translate
        self.airplay = AirplayReceiver(translate)
        self.spotify = SpotifyReceiver(translate)

        if getpwuid(os.geteuid()).pw_uid > 0:
            print("This program must be run with sudo or root permissions!")
            sys.exit(1)

        # Need to refer to options in menu
        self.menu = menu

        # Get event handler
        self.event = event
        
        self.setupConfiguration()

        # Mount all media drives
        self.unmountAll()
        self.mountAll()
        return

    # This routine starts the MPD socket listener (mpd.socket) which accepts
    # client requests and starts the MPD service (mpd.service) as required
    def startMpdSocket(self):
        log.message("Starting service mpd.socket", log.DEBUG)
        self.execCommand("sudo systemctl start mpd.socket")

    def restartMpd(self):
        log.message("Restarting service mpd.service", log.DEBUG)
        self.execCommand("sudo systemctl restart mpd.service")

    # Set up configuration files
    def setupConfiguration(self):
        # Create directory 
        if not os.path.isfile(CurrentStationFile):
            self.execCommand ("mkdir -p " + RadioLibDir )

        # Initialise configuration files from ConfigFiles list
        for file in self.ConfigFiles:
            value = self.ConfigFiles[file]
            if not os.path.isfile(file) or os.path.getsize(file) == 0:
                f = open(file,'w')
                f.write(str(value))
                f.close()

        # Create pid run directory for the record program
        if not os.path.isdir(PidDir):
            os.mkdir(PidDir)
            os.chown(PidDir, self.uid, self.gid)

        # Link /var/lib/mpd/music/media to /media/<user>
        cmd = "rm -f /var/lib/mpd/music/media"
        self.execCommand(cmd)
        cmd = "sudo ln -s /media/" + self.usr + " /var/lib/mpd/music/media"
        self.execCommand(cmd)

        # Create mount point for networked music library (NAS)
        if not os.path.isfile("/share"):
            self.execCommand("mkdir -p /share")
            if not os.path.ismount("/share"):
                os.chown('/share', self.uid, self.gid)
            self.execCommand("sudo ln -f -s /share /var/lib/mpd/music")

        self.execCommand("chown -R " + self.usr + ":" + self.grp + " " + RadioLibDir)
        self.execCommand("chmod -R 764 " + RadioLibDir)
        self.current_file = CurrentStationFile
        self.current_id = self.getStoredID(self.current_file)

        return

    # Set up Alsa mixer ID file
    def setMixerId(self,MixerIdFile):
        dir = os.path.dirname(__file__)
        cmd = "sudo " + dir + "/scripts/set_mixer_id.sh  >/dev/null 2>&1"
        log.message(cmd, log.DEBUG)
        self.execCommand(cmd)

    # Do we need to update the mixer ID
    # If it doesn't exist or the id is 0 then update
    def needMixerUpdate(self,MixerIdFile):
        id = 0
        update = False
        audio_out = self.config.audio_out
        if audio_out == 'bluetooth':
            update = False

        elif os.path.isfile(MixerIdFile):
            id = self.getStoredInteger(MixerIdFile,0)   
            if id < 1:
                update = True
            else:
                if not self.config.audio_config_locked:
                    update = True
        else:
            update = True

        log.message("radio.setMixerId for  %s %s " % (audio_out,str(update)), log.DEBUG)
        return update

    # Get IP address 
    def get_ip(self):
        if len(self.ip_addr) < 7:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0)
            try:
                # Google DNS
                s.connect(('8.8.8.8', 1))
                self.ip_addr = s.getsockname()[0]
            except Exception:
                IP = ''
            finally:
                s.close()
        return self.ip_addr

    # Wait for the network
    # If using comitup ignore address
    def waitForNetwork(self):
        ipaddr = ""
        waiting4network = True
        count = 30
        while waiting4network:
            ipaddr = self.get_ip()
            count -= 1
            if (count < 0) or (len(ipaddr) > 3):
                # Don't use Comitup web address
                if not self.config.comitup_ip in ipaddr:
                    waiting4network = False
            else:
                time.sleep(0.5)
        return ipaddr

    def handleRecordKey(self,key):
        print(key,"received")
        
        if not self.recording:
            self.ir_pid = self.getPid(ireventd_pidfile)
            try:
                # This causes the IR daemon to switch on the activity LED
                os.kill(int(self.ir_pid), signal.SIGUSR1)
            except:
                pass

        source_type = self.source.getType()
        if os.path.isfile(record_pidfile):
            f = open(record_pidfile,'r')
            pid = f.read()
            f.close()
            try:
                os.kill(int(pid), signal.SIGHUP)
            except Exception as e:
                print(str(e))
            time.sleep(2)
            os.remove(record_pidfile)
            msg = "Stopped recording %s" % self.stationName
        elif source_type == self.source.RADIO:
            cmd = "/usr/share/radio/record.py"
            params = "--duration=1:00"
            try:
                print(cmd,params)
                subprocess.Popen([cmd,params],shell=True)
                msg = "Started recording %s" % self.stationName
            except Exception as e:
                print(str(e))
        else:
            msg = "Record request ignored - Not listening to a radio stream"

        print(msg)
        log.message(msg, log.INFO)

    # If recording station, signal the ireventd to switch on activity LED
    def isRecording(self):
        now = time.time()
        if now > self.recordTime + self.recordDelay:
            self.recordTime = now
            self.ir_pid = self.getPid(ireventd_pidfile)

            # Is the IR remote control daemon running
            if self.ir_pid > 0:
                record_pid = self.getPid(record_pidfile)
                if record_pid != self.record_pid:
                    self.record_pid = record_pid 
                    if self.record_pid < 1:
                        log.message("Recording has stopped",log.DEBUG)
                        self.recording = False
                    else:
                        log.message("Recording is running PID " + str(self.record_pid),log.DEBUG)
                        self.recording = True

                if self.record_pid > 1:
                    try:
                        # This causes the IR daemon to switch on the activity LED
                        os.kill(int(self.ir_pid), signal.SIGUSR1)
                    except:
                        pass
                else:
                    try:
                        # This causes the IR daemon to switch off the activity LED
                        os.kill(int(self.ir_pid), signal.SIGUSR2)
                    except:
                        print(str(e))
                        pass

        return self.recording

    # Get the pid from a pidfile
    def getPid(self,pidfile):
        pid = -1
        if os.path.isfile(pidfile):
            try:
                f = open(pidfile,'r')
                pid = f.read()
                f.close()
            except Exception as e:
                print(str(e))
                pass
        return int(pid)

    # Call back routine for the IR remote and Web Interface
    def remoteCallback(self):
        key = self.server.getData()
        set_interrupt = True
        response = 'OK'

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

        elif key == 'KEY_EXIT' or key == 'KEY_POWER':
            self.event.set(self.event.SHUTDOWN)

        elif key == 'KEY_RECORD':
            self.handleRecordKey(key)

        # These messages come from the Web CGI script
        elif key == 'MEDIA':
            self.event.set(self.event.LOAD_MEDIA)

        elif key == 'RADIO':
            self.event.set(self.event.LOAD_RADIO)

        elif key == 'RELOAD_PLAYLISTS':
            self.getSources()

        elif 'PLAY_' in key:    
            x = key.split('_')
            play_number = int(x[1])
            self.event.set(self.event.play(play_number))
            self.event.set(self.event.PLAY)
            if self.volume.muted():
                self.volume.unmute()

        elif 'PLAYLIST:' in key:    # This event comes from the Web interface
            key_array = key.split(':')
            playlistName = key_array[1]

            # LIBRARY is sent my O!MPD web interface
            if playlistName == "LIBRARY":
                # Load O!MPD library (Network or USB stick)
                log.message("radio.remoteCallBack OMPD set MEDIA" , log.DEBUG)
                self.mountAll()
                playlistName = self.source.loadOmpdLibrary();
                self.client.load(playlistName)
                self.searchlist = self.PL.searchlist
                log.message("Loaded O!MPD playlist " + playlistName, log.DEBUG)
            else:
                self.playlistName = playlistName
                self.event.set(self.event.LOAD_PLAYLIST)
    
            self.getCurrentID() 

        elif key == 'AIRPLAY':
            self.event.set(self.event.LOAD_AIRPLAY)

        elif key == 'SPOTIFY':
            self.event.set(self.event.LOAD_SPOTIFY)

        elif key == 'INTERRUPT':
            self.event.set(self.event.NO_EVENT) # To be done

        elif key == 'IR_REMOTE':    # IR Remote test message
            self.event.set(self.event.NO_EVENT) # To be done

        else:
            log.message("radio.remoteCallBack invalid IR key " + key, log.DEBUG)
            set_interrupt = False
            response = "Invalid " + key

        # Interrupt scrolling display
        if set_interrupt:
            self.setInterrupt()

        return response 

    #  Get LOAD_PLAYLIST event playlist name
    def getPlaylistName(self):
        return self.playlistName

    # Set up radio configuration and start the MPD daemon
    def start(self):
        global language

        self.config.display()
        # Get Configuration parameters /etc/radiod.conf
        self.boardrevision = self.getBoardRevision()
        self.mpdport = self.config.mpdport
        self.udpport = self.config.remote_control_port
        self.udphost = self.config.remote_listen_host
        self.display_playlist_number = self.config.display_playlist_number
        self.speech = self.config.speech
        language = Language(self.speech) # language is a global

        # Log OS version information 
        self.arch = platform.architecture()[0]
        OSrelease = self.execCommand("cat /etc/os-release | grep NAME")
        OSrelease = OSrelease.replace("PRETTY_NAME=", "OS release: ")
        self.OSrelease = OSrelease.replace('"', '')
        log.message(self.OSrelease + ' ' + self.arch, log.INFO)
        (x,self.OSname) = self.OSrelease.split('(')
        self.OSname = self.OSname.replace(')','')
        self.OSname = self.OSname.title()
        myos = self.execCommand('uname -a')
        log.message(myos, log.INFO)

        # Connect bluetooth device if configured
        self.connectBluetoothDevice()

        # Start the MPD socket service
        self.startMpdSocket()

        # Connect to MPD
        self.client = mpd.MPDClient()   # Create the MPD client
        self.connect(self.mpdport)

        # Is Airplay installed (shairport-sync)
        self.airplayInstalled = self.config.airplay
        if self.airplayInstalled:
            self.stopAirplay()
        log.message("self.airplayInstalled " + str(self.airplayInstalled), log.DEBUG)

        # Is Spotify installed
        self.spotifyInstalled =  os.path.isfile('/usr/bin/librespot')

        self.source = Source(client=self.client,airplay=self.airplayInstalled,
                    spotify=self.spotifyInstalled)

        # Set up source/playlist depending upon startup=<source> in /etc/radiod.conf
        self.getSources()
        sourceType = self.config.source

        # Set up volume controls
        self.volume = Volume(self.client,self.source,self.spotify,
                self.airplay,self.config,log)
        self.volume.setClient(self.client)

        startup_playlist = self.config.startup_playlist
        self.PL.name = startup_playlist
        log.message("Startup playlist " + startup_playlist, log.DEBUG)
        sources = ['RADIO', 'MEDIA', 'AIRPLAY', 'SPOTIFY']

        if self.config.load_last:
            log.message("Load last playlist", log.DEBUG)
            self.source_index = self.getStoredSourceIndex()
            self.source.setIndex(self.source_index)

        elif startup_playlist in sources:
            # Load either MEDIA, RADIO, AIRPLAY or SPOTIFY depending on config
            self.source.setType(sourceType)
            log.message("Load  MEDIA/RADIO", log.DEBUG)

        elif len(startup_playlist) > 1:
            log.message("Startup playlist " + startup_playlist, log.DEBUG)
            self.source.setPlaylist(startup_playlist)

        else: 
            # Default to any radio playlist
            self.source.setType(self.source.RADIO)

        # Get stored values from Radio lib directory
        self.getStoredValue(self.menu.OPTION_RANDOM)
        self.current_id = self.getStoredID(self.current_file)
        log.message("radio.start current ID " + str(self.current_id), log.DEBUG)

        self.volume.set(self.volume.getStoredVolume())

        # Restore alsamixer settings (alsa-state/alsa-store services 
        # not working in Bookworm)
        # Temporary workaround until above services fixed
        cmd = "/usr/sbin/alsactl --no-ucm restore"
        log.message(cmd, log.DEBUG)
        self.execCommand(cmd)   

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
            self.server = UDPServer((self.udphost,self.udpport),RequestHandler)
            msg = "UDP Server listening on " + self.udphost + " port " \
                + str(self.udpport)
            log.message(msg, log.INFO)
            self.server.listen(self.server,self.remoteCallback)
        except Exception as e:
            log.message(str(e), log.ERROR)
            log.message("UDP server could not bind to " + self.udphost
                    + " port " + str(self.udpport), log.ERROR)

        # Configure the audio device from audio_out parameter in the configuration
        audio_out = self.config.audio_out
        if not self.config.audio_config_locked:
            if len(audio_out) > 1 and audio_out != 'bluetooth':
                dir = os.path.dirname(__file__)
                self.execCommand(dir + '/scripts/configure_audio_device.sh 2>&1 >/dev/null')

        # Set up mixer ID file hardware ID in mpd.conf and /etc/asound
        # Run set_mixer_id.sh script each startup as this might change
        # when connecting and disconnecting HDMIs. Likewise the card number
        if self.needMixerUpdate(MixerIdFile):
            self.setMixerId(MixerIdFile)

        # Set-up Playlist callback
        self.setupPlaylistCallback()
        return

    # Connect to MPD
    def connect(self,port):
        connected = False
        retry = 2
        while retry > 0:
            try:
                self.client.timeout = self.config.client_timeout
                self.client.idletimeout = None
                self.client.connect("localhost", port)
                # Wait for stations to be loaded before playing
                self.client.stop()
                log.message("Connected to MPD port " + str(port), log.INFO)
                ##if self.volume != None:
                #self.volume.setClient(self.client)
                connected = True
                retry = 0

            except mpd.ConnectionError as e:
                log.message( 'radio.connection error port ' + str(port) \
                    + ':'  + str(e), log.ERROR)
                self.setError(MPD_NO_CONNECTION)
                self.setInterrupt()

            except Exception as e:
                log.message( 'radio.connect failed port ' + str(port) \
                    + ': '  + str(e), log.ERROR)
                time.sleep(2.5) # Wait for interrupt in the case of a shutdown
                if "Already connected" in str(e):
                    connected = True
                    retry = 0
            retry -= 1

        self.connected = connected
        return self.connected

    # Connect Bluetooth device. Re-pair device if necessary
    def connectBluetoothDevice(self):
        connectBT = True
        connected = False

        # Check to see if bluetooth configured
        audio_out = self.config.audio_out
        bluetooth_device=self.config.bluetooth_device
        if bluetooth_device == "00:00:00:00:00:00" or len(bluetooth_device) != 17\
                                or audio_out != "bluetooth": 
            connectBT = False

        if os.path.isfile("/usr/bin/bluetoothctl") and connectBT:
            log.message("Connecting Bluetooth device " + bluetooth_device, log.DEBUG)
            cmd = "bluetoothctl power on"
            os.system(cmd)
            
            cmd = "bluetoothctl info " + bluetooth_device + " >/dev/null 2>&1"

            # Re-pair Bluetooth device if no info for device
            if os.system(cmd) != 0:
                log.message("Re-pairing Bluetooth device " 
                    + bluetooth_device, log.DEBUG)
                cmd = "bluetoothctl remove " + bluetooth_device
                os.system(cmd)
                cmd = "bluetoothctl power on "
                os.system(cmd)
                # Scan for 10 seconds
                cmd = "bluetoothctl --timeout 10 scan on"
                os.system(cmd)
                # Re-pair the device
                cmd = "bluetoothctl pair " + bluetooth_device
                os.system(cmd)
                cmd = "bluetoothctl trust " + bluetooth_device
                os.system(cmd)
                cmd = "bluetoothctl connect " + bluetooth_device
                os.system(cmd)
                if os.system(cmd) == 0:
                    connected = True
            else:
                retry = 4
                cmd = "bluetoothctl connect " + bluetooth_device
                while retry > 0:
                    if os.system(cmd) == 0:
                        log.message("Connected Bluetooth device " + bluetooth_device,log.DEBUG) 
                        connected = True
                        retry = 0
                    else:
                        log.message("Failed to connect Bluetooth device "+bluetooth_device,log.DEBUG)
                        connected = False
                        time.sleep(2)
                        retry -= 1
        return  connected

    # Restart MPD
    def stopMpdDaemon(self):    
        log.message('radio.stopMpdDaemon: Stopping MPD', log.DEBUG)
        pid = self.getStoredInteger("/var/run/mpd/pid",0)   
        self.execCommand("sudo systemctl stop mpd.socket")
        self.execCommand("sudo systemctl stop mpd.service")
        return pid

    # Scroll up and down between stations/tracks
    def getNext(self,direction):
        self.last_direction = direction # Store direction
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

    # Get MPD version (Only get it from MPD initially)
    def getMpdVersion(self):
        if len(self.MpdVersion) < 1:
            sVersion = self.execCommand('mpd -V | grep Daemon')
            try:
                self.MpdVersion = sVersion.split()[3]
            except:
                sError = self.execCommand('mpd -V 2>&1 | head -1')
                msg = "radio.getMpdVersion " + sError 
                print(msg)
                log.message(msg,log.CRITICAL)
                sys.exit(1)
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
        return self.volume.displayValue()

    # This is either the real MPD or Mixer volume
    # depending upon source type
    def getVolume(self):
        vol_status = self.volume.getStatus()
        if vol_status != self.volume.OK:
                log.message("radio.getVolume no connection" , log.DEBUG)
                self.setError(MPD_NO_CONNECTION)
                self.setInterrupt()
                self.reconnect(self.client)
                self.play(self.current_id)
                self.setVolume(self.getStoredVolume())
                self.connectBluetoothDevice()

        return self.volume.get()

    # Set volume (Called from the radio client or external mpd client via getVolume())
    # Also called from gradiod.py and vgradiod.py
    def setVolume(self,new_volume):
        if self.volume.muted():
            self.volume.unmute()
        self.volume.set(new_volume)
        return self.volume.displayValue() 

    # Increase volume 
    def increaseVolume(self):
        if self.error:  # If error re-connect Bluetooth
            self.connectBluetoothDevice()
            self.clearError()
            try:
                self.client.play()
            except:
                pass

        if self.muted():
            self.unmute()
        return self.volume.increase()

    # Decrease volume 
    def decreaseVolume(self):
        if self.error:  # If error re-connect Bluetooth
            self.connectBluetoothDevice()
            self.clearError()
            try:
                self.client.play()
            except:
                pass

        if self.muted():
            self.unmute()
        return self.volume.decrease()

    def mute(self):
        self.volume.mute()

    # Unmute sound fuction, get stored volume
    def unmute(self):
        if self.error:  # If error re-connect Bluetooth
            self.connectBluetoothDevice()
            self.clearError()
        self.volume.unmute()

    # Ping MPD server to keep client connected
    def ping(self):
        now = time.time()
        if now > self.pingTime + self.pingDelay:
            self.pingTime = now
            try:
                self.client.ping()
            except Exception as e:
                log.message("radio.ping: " + str(e),log.ERROR)
                pass

    # Return muted state muted = True
    def muted(self):
        self.ping()
        return self.volume.muted()

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

    # Start MPD self.client (Alarm mode) - not used
    def startMpdClient(self):
        try:
            self.client.play()
        except Exception as e:
            log.message("radio.startMpdClient: " + str(e),log.ERROR)
        return

    # Stop MPD (Alarm mode)
    def stopMpdClient(self):
        try:
            self.client.stop()
        except Exception as e:
            log.message("radio.stopMpdClient: " + str(e),log.ERROR)
        return

    # Stop the radio 
    def stop(self):
        self.execCommand("sudo systemctl stop mpd")
        
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
        self.execCommand(self.config.shutdown_command)

        # Exit radio
        exit(0) 


    # Get the stored volume
    def getStoredVolume(self):
        return self.getStoredInteger(VolumeFile,75) 

    # Store source index value and name
    def storeSource(self,index):
        sname = self.source.current()   # Used by new web interface
        self.execCommand ("echo " + str(index) + " > " + CurrentSourceFile)
        self.execCommand ("echo " + sname + " > " + SourceNameFile)
        return

    # Set random on or off
    def setRandom(self,true_false,store=True):
        log.message("radio.setRandom " + str(true_false),log.DEBUG)
        try:
            if true_false:
                self.client.random(1)
                iValue = 1
            else:
                self.client.random(0)
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
                self.client.repeat(1)
            else:
                self.client.repeat(0)

        except Exception as e:
            log.message("radio.setRepeat " + str(e),log.ERROR)

        return true_false

    # Set consume on or off
    def setConsume(self,true_false):
        try:
            if true_false:
                self.client.consume(1)
            else:
                self.client.consume(0)

        except Exception as e:
            log.message("radio.setConsume " + str(e),log.ERROR)

        return true_false

    # Set single on or off
    def setSingle(self,true_false):
        try:
            if true_false:
                self.client.single(1)
            else:
                self.client.single(0)

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
            randomValue = int(self.getStoredParameter(RandomSettingFile))
            value = self.convertToTrueFalse(randomValue)    

        elif option_index == self.menu.OPTION_TIMER:
            value = int(self.getStoredParameter(TimerFile))

        elif option_index == self.menu.OPTION_ALARM:
            value = self.getStoredParameter(AlarmFile)

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
        self.storeParameter(AlarmFile,self.alarmTime)

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
        self.storeParameter(AlarmFile,self.alarmTime)
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
        self.storeParameter(AlarmFile,self.alarmTime)
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
                if int(t1.second) < 5:  # Only trigger alarm once 
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
        alarmValue = self.getStoredParameter(AlarmFile)
        if alarmValue == None:
            alarmValue = "0:7:00"
        return alarmValue

    # Store a parameter in /var/lib/radiod/<file>
    def storeParameter(self,file,parameter):
        ret = False
        try:
            f = open(file,'w')
            f.write(parameter)
            f.close()
            ret = True
        except Exception as e:
            print(str(e))
            log.message(str(e), log.ERROR)
        return ret

    # Get parameter stored in /var/lib/radiod/<file>
    def getStoredParameter(self,file):
        parameter = None
        try:
            f = open(file,'r')
            parameter = f.read()
            f.close()
        except Exception as e:
            print(str(e))
            log.message(str(e), log.ERROR)
        return parameter

    # Get the record duration
    def getRecordDuration(self):
        return self.recordDuration
        
    # Increment recording duration time
    def incrementRecordDuration(self,inc):
        hours_max = 11
        max = hours_max * 60
        duration = self.recordDuration.split(':')
        hours = int(duration[0])
        minutes = int(duration[1]) + hours * 60

        # If under a minute inc/dec by 1
        if hours < 1 and minutes < 10:
            if inc < 0:
                inc = -1
            else :
                inc = 1
        elif hours > 4:
            if inc < 0:
                inc = -15
            else :
                inc = 15

        minutes += inc

        if minutes > max:
            minutes = 1
        elif minutes <= 0:
            minutes = max
        hours = int(minutes / 60)
        minutes = minutes % 60

        sDuration = '%d:%02d' % (hours,minutes)
        self.recordDuration = sDuration
        self.storeParameter(RecordingDurationFile,sDuration)
        print(sDuration)
        return sDuration

    # Get the alarm type
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
        value = 1   # Set minutes

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
        streamValue = self.getStoredParameter(StreamFile)
        streaming = self.convertToTrueFalse(streamValue)
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
        status = self.execCommand("mpc outputs|grep -i stream|grep -i enabled")
        if len(status)>1:
            msg = "Icecast streaming enabled"
        else:
            msg = "Icecast streaming disabled"
        log.message(msg, log.INFO)
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
        try:
            p = os.popen(cmd)
            result =  p.readline().rstrip('\n')
        except Exception as e:
            print(cmd) 
            msg = "radio.execCommand: " + str(cmd)
            log.message(msg,log.ERROR)
            print(str(e))
            log.message(str(e),log.ERROR)
            result = ""
        return result 

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
                if self.errorCode == 0:
                    log.message("radio.getCurrentID error id: " + str(pos),log.ERROR)
                msg = "Empty playlist %s" % self.source.getNewName()
                self.setError(MPD_EMPTY_PLAYLIST,text=msg)
                self.setInterrupt()
                
            else:
                currentid = int(pos) + 1

            # Only update if the Current ID has changed by another client
            if self.current_id != currentid:
                log.message("radio.getCurrentID New ID " \
                        + str(currentid) + " id:" + str(self.current_id),
                         log.DEBUG)
                self.current_id = currentid
                # Write to current ID file
                self.execCommand ("echo " + str(currentid) + " > " \
                            + self.current_file)
                self.search_index = self.current_id - 1
                self.getIdError = False
                self.event.set(self.event.MPD_CLIENT_CHANGE)
                self.setInterrupt() 
                
        except Exception as e:
            log.message("radio.getCurrentID: " + str(e),log.ERROR)
            if not self.getIdError:
                log.message("radio.getCurrentID failed ", log.ERROR)
                self.getIdError = True

        return self.current_id

    # Check to see if an error occured
    def gotError(self):
        return self.error

    # Error string (displayed by title routine)
    def setError(self,code, text=None):
        self.error = True
        self.errorCode = code
        if text != None:
            self.errorStrings[code] = text
        self.error_display_delay = time.time() # Set delay for display

    # Get the error string if a bad channel
    def getErrorString(self):
        return self.errorStrings[self.errorCode]

    # See if any error. Return True if error
    def checkStatus(self):
        if not self.checkInternet():
            return self.error

        try:
            status = self.client.status()
            errorStr = str(status.get("error"))
            if  errorStr != "None":
                if not self.error:
                    log.message("checkStatus: "+ errorStr, log.DEBUG)
                self.setError(MPD_STREAM_ERROR,errorStr)
                self.setInterrupt()
        except Exception as e:
            log.message("checkStatus exception: " + str(e), log.ERROR)
            self.setError(MPD_STREAM_ERROR,str(e))
            if "Not connected" in str(e) :
                self.reconnect(self.client)
                self.setError(MPD_NO_CONNECTION,str(e))
            self.setInterrupt()

        return self.error

    # Get the progress of the currently playing track
    def getProgress(self):
        elapsedTime = None
        durationTime = None
        elapsed = None
        duration = None
        percentage = None

        try:
            status = self.client.status()
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
    # Store the new id in /var/lib/radiod
    def setCurrentID(self,new_id):
        connectError = False
        log.message("radio.setCurrentID newid=" + str(new_id) +
                " current_id="+ str(self.current_id), log.DEBUG)

        # Validity checks
        if new_id  <= 0:
            new_id = 1
        elif new_id > len(self.searchlist):
            new_id = len(self.searchlist)

        self.current_id = new_id

        # Set up the search index
        self.search_index = self.current_id - 1

        # Save the new ID in /var/lib/radiod
        log.message("radio.setCurrentID set to " + str(self.current_id), log.DEBUG)
        self.execCommand ("echo " + str(self.current_id) + " > " + self.current_file)

        return self.current_id

    # Get stats array
    def getStats(self):
        try:
            stats = self.client.status()
            self.stats = stats # Only if above call works
            self.getMpdOptions(self.stats)  # Get options 

        except Exception as e:
            log.message("radio.getStats " + str(e), log.ERROR)

        return self.stats

    # Get current song information (Only for use within this module)
    def getCurrentSong(self):
        try:
            currentsong = self.client.currentsong()
            self.currentsong = currentsong
        except:
            # Try re-connect and status
            try:
                currentsong = self.client.currentsong()
                self.currentsong = currentsong
            except Exception as e:
                log.message("radio.getCurrentSong failed: " + str(e), log.ERROR)
        return self.currentsong

    # Get station name by index from search list
    def getSearchName(self):
        name = ''
        try:
            name = self.getStationName(self.search_index) 
            if len(name) > 0:
                name = self.translate.all(name)

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
            name = self.translate.all(name)

        # If error occured
        if self.checkStatus(): 
            time.sleep(0.5)
            if "Failed to open" in self.getErrorString():
                log.message ("radio.getCurrentStationName audio output error",
                             log.ERROR) 
                try:
                    self.connectBluetoothDevice()
                    self.client.play()
                    log.message ("radio.getCurrentStationName play",log.DEBUG)
                except:
                    log.message ("radio.getCurrentStationName play failed", log.DEBUG)
                    pass
        return name

    # Get the title of the currently playing station or track from mpd 
    # The title is also used to display errors
    def getCurrentTitle(self):
        if self.errorCode > 0:
            errorStr = self.errorStrings[self.errorCode]
            log.message (errorStr, log.ERROR)
            now = int(time.time())
            if now > self.error_display_delay + 10:
                self.clearError() 
                self.error_display_delay = now
            return errorStr  

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
            title = self.translate.all(title)

        if self.channelChanged: 
            self.channelChanged = False
            if self.config.verbose:
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
            artist = str(currentsong.get("artist"))
            artist = self.translate.all(artist) 
            title = str(currentsong.get("title"))
            title = self.translate.all(title)
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
                album = self.translate.all(album)
            self.album = album
        except:
            log.message ("radio.getCurrentAlbum error", log.ERROR)  
        return self.album

    # Get bit rate - aways returns 0 in diagnostic mode 
    def getBitRate(self):
        try:
            status = self.client.status()
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

    # Store integer value in file
    def storeIntegerValue(self,value,sFile):
        fp = open(sFile, "w")
        fp.write(str(value))
        fp.flush()
        fp.close()
        return value 

    # Get the currently stored source index
    def getStoredSourceIndex(self):
        return self.getStoredInteger(CurrentSourceFile,0)   

    # Get the integer value stored in /var/lib/radiod by storeIntegerValue()
    # filename is the name any file in the lib directory
    # default_value is the value to be returned if the file read fails
    def getStoredInteger(self,filename,default_value,loggit=True):
        if os.path.isfile(filename):
            try:
                fp = open(filename, "r")
                value = int(fp.read())
                fp.close()
            except ValueError:
                value = int(default_value)
        else:
            if loggit:
                log.message("Error reading " + filename, log.ERROR)
                value = int(default_value)
        return value

    # Change radio station/track Up
    def channelUp(self):
        self.last_direction = UP
        self.current_id = self._changeChannel(UP)
        return self.current_id

    # Change radio station/track Up
    def channelDown(self):
        self.last_direction = DOWN
        self.current_id = self._changeChannel(DOWN)
        return self.current_id

    # Change radio station up
    def _changeChannel(self,direction):
        new_id = self.getCurrentID()
        skip_value = 1  # Skip increment decrement

        if direction == UP:
            mesg = "radio.channelUp "
            new_id += 1
        else:
            mesg = "radio.channelDown "
            new_id -= 1
            
        if self.error:
            log.message(mesg + "clearError " + str(self.error), log.DEBUG)
            self.clearError()

        log.message(mesg + str(new_id), log.DEBUG)
        self.current_id = self.play(new_id)
        self.channelChanged = True

        if self.volume.muted():
            self.volume.unmute()

        return self.current_id

    # Cycle the input source and/or playlist (Reload is done when Reload requested)
    def cycleSource(self, direction):
        
        sSource = self.source.cycle(direction)
        self.newType =  self.source.getNewType() 

        self.setReload(True)    
        log.message("Selected source " + sSource, log.DEBUG)

        return self.newType
    
    # Get the new source name (radio, playlist or Airplay)
    def getNewSourceName(self):
        return self.source.getDisplayName()

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
        sources = self.getSources()
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
            self.stopMpdClient()

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
            self.searchlist = self.PL.searchlist
            self.current_id = self.getStoredID(self.current_file)
            self.play(self.current_id)

        # Set volume
        self.volume.set(self.volume.getStoredVolume())

        # Save the new source type and index
        self.source_index = self.source.setNewType()
        self.source.setIndex(self.source_index)
        self.storeSource(self.source_index)
        return

    def loadPlaylist(self):
        source_type = self.source.getNewType()
        type_name  = self.source.getNewTypeName()
        pname = self.source.getNewName()

        msg = "Load playlist " + pname + " type " + str(source_type) + " " + type_name
        log.message(msg, log.DEBUG)

        try:
            self.PL.load(self.client,pname)
            if self.PL.size < 1:
                log.message("Playlist " + pname + " is empty", log.ERROR)
                self.current_id = 0
        except:
            log.message("radio.loadPlaylist failed to load " + pname, log.ERROR)
        return

    # Get the playlist dictionary (Contains all playlist names and types)
    def getPlaylists(self):
        return self.source.getPlaylists()       

    def reloadCurrentPlaylist(self):
        log.message("Reloading current playlist", log.INFO)
        plist = self.client.playlist()

    # Update music library 
    def updateLibrary(self,force=False):
        try:
            if len(self.client.playlist()) < 1 or force :
                status = self.client.status()
                try:
                    update_id = int(status.get("updating_db"))
                    self.loading_DB = True
                except:
                    update_id = 0
                if update_id < 1:
                    self.mountAll()
                    log.message("Updating MPD database ", log.INFO)
                    self.execMpcCommand("update")
                    playlist = self.source.getName()
                    log.message("Loading playlist " + playlist, log.INFO)
                    self.execMpcCommand("load " + playlist)
            else:
                self.loading_DB = False
            self.setUpdateLibOff() # Check TO DO
        except Exception as e:
                log.message("radio.updateLibrary error" +
                    str(self.current_id) + " :" + str(e), log.ERROR)
        return

    # Play a new track using search index
    def playNew(self,index):
        self.setLoadNew(False)
        self.play(index + 1)
        return

    # Check if there is an internet connection by checking Google 
    # Typically this is a reliable service such as Google 
    def checkInternet(self):
        success = False
        iTime = time.time()
        host = self.config.internet_check_url
        port = self.config.internet_check_port
        timeout = self.config.internet_timeout

        # Disable if no Internet URL defined
        if len(host) < 1:
            return True

        if iTime > self.internet_check_delay + 1.5:
            self.internet_check_delay = iTime
            try:
                socket.setdefaulttimeout(timeout)
                socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
                if self.gotError() and self.errorCode == INTERNET_ERROR:
                    self.setInterrupt()
                    log.message("Internet reconnected", log.INFO)
                    time.sleep(0.5)
                    self.clearError()
                    if not self.connected:
                        self.connect(self.udpport)
                        self.volume.setClient(self.client)
                    self.play(self.current_id)
                success = True
            except socket.error as e:
                if not self.gotError():
                    log.message("No Internet connection: " + str(e), log.ERROR)
                    log.message("Tried " + host + " port " + str(port) , log.ERROR)
                    self.setError(INTERNET_ERROR)
                    self.ip_addr = ''
                    self.setInterrupt()
                time.sleep(1)
        else:
            success = True

        return success

    # Play a track or station id  (Starts at 1)
    def play(self,id):
        log.message("radio.play " + str(id), log.DEBUG)

        new_id = id
        if new_id > len(self.searchlist):
            new_id = 1
        elif new_id < 1:
            new_id = len(self.searchlist)

        # Check if RADIO or MEDIA
        sourceType = self.source.getType()
        if sourceType == self.source.RADIO:
            self.current_id = self.play_radio(new_id) 
        elif sourceType == self.source.MEDIA:
            self.current_id = self.play_media(new_id) 

        # Update current file and search index
        self.storeIntegerValue (self.current_id,self.current_file)
        self.search_index = self.current_id - 1

        return self.current_id

    # Parse error into something the user can understand
    def parseError(self,errorMessage):
        msg = errorMessage
        if errorMessage.find('#'):
            arr =  errorMessage.split('#')
            if len(arr) > 1:
                msg = arr[1]
       
        if msg == 'timed out':
            name = self.getSearchName()
            msg = name + ': ' + msg 
        return msg

    # Play radio stream id  (Starts at 1)
    def play_radio(self,id):
        log.message("radio.play_radio " + str(id), log.DEBUG)
        new_id = id

        # Client play function starts at 0 not 1

        if self.last_direction == UP:
            skip_value = 1
        else:
            skip_value = -1

        retry = 3
        msg = ''

        # If Internet OK skip bad channel otherwise stay on current station
        while self.checkInternet():

            try:
                # Client play starts from 0
                self.client.play(new_id-1)
                success = True
                self.current_id = new_id
                log.message("radio.play_radio success id=" + str(self.current_id), log.DEBUG)
                break

            except Exception as e:
                log.message("radio.play_radio error id=" +
                        str(new_id) + " :" + str(e), log.ERROR)
                retry  -= 1
                if retry < 0:
                    break
                new_id  += skip_value
                log.message("radio.play: Skipping to station " + 
                        str(new_id),log.DEBUG)
                self.reconnect(self.client)

                # If error we want to display this on the screen
                errMsg = self.parseError(str(e))
                self.setError(MPD_STREAM_ERROR,errMsg)
                self.setInterrupt()

        # End of while

        return self.current_id

    # Play media stream id  (Starts at 1)
    def play_media(self,id):
        log.message("radio.play_media " + str(id), log.DEBUG)
        new_id = id
        try:
            # Client play starts from 0
            self.client.play(new_id-1)
            self.current_id = new_id
            self.clearError()
            log.message("radio.play_media success id=" + str(self.current_id), log.DEBUG)

        except Exception as e:
            log.message("radio.play_media error id=" +
                    str(new_id) + " :" + str(e), log.ERROR)
            self.setError(MPD_STREAM_ERROR,"Media error:" + str(e))
            self.setInterrupt()

        return self.current_id

    # Timeouts due to a bad URL cause corruption of the client
    # stats and status dictionaries. Disconnect and reconnect to
    # reset the client
    def reconnect(self,client):
        log.message("radio.reconnect",log.DEBUG)
        try:
            self.client.disconnect() 
        except:
            pass

        # Re-connect
        self.client = mpd.MPDClient()   # Create the MPD client
        try:
            time.sleep(0.5)
            self.client.connect("localhost", self.mpdport)
            self.connected = True
        except Exception as e:
            log.message("radio.disconnect connect error: " +
                 str(e), log.ERROR)
            self.connected = False

        # Pass new client to volume class
        self.volume.setClient(self.client)
        return self.connected

    # Clear error and set NO_ERROR 
    def clearError(self):
        log.message("radio.clearError", log.DEBUG)
        self.error = False
        self.errorCode = NO_ERROR
        return

    # Get list of tracks or stations
    def getPlayList(self):
        return self.searchlist

    # Get playlist length
    def getPlayListLength(self):
        return len(self.searchlist)

    # Handle the PLAYLIST_CHANGED event and update the searchlist
    def handlePlaylistChange(self):
        log.message("radio.handlePlaylistChange", log.DEBUG)
        self.searchlist = self.PL.update(self.client)
        log.message("Created new searchlist " + str(len(self.searchlist)), 
                        log.DEBUG)
        
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
        except Exception as e:
            log.message("radio.getStationName " + str(e), log.ERROR)
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
        if str(track) == 'None':
            track = "Unknown track"
        return track

    # Get artist name by Index
    def getArtistName(self,index):
        if len(self.searchlist) < 1:
            artist = "No playlists"
        else:
            artist = "Unknown artist"
            try:
                sections = self.searchlist[index].split(' - ')
                leng = len(sections)
                if leng > 1:
                    artist = sections[0]
            except:
                pass
        return artist
            

    # Version number
    def getVersion(self):
        return __version__

    # Build number
    def getBuild(self):
        return build

    def getArchitecture(self):
        arch = self.execCommand("getconf LONG_BIT")
        return arch

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

    # Mount the USB stick, Note if using a bootable USB drive sda1/2 are alread mounted
    def mountUsb(self):
        usbok = False
        if os.path.exists("/dev/sdb1"):
            device = "/dev/sdb1"
            usbok = True

        elif os.path.exists("/dev/sda1"):
            device = "/dev/sda1"
            usbok = True

        if usbok:
            mountpoint = '/media/' + self.usr 
            if not os.path.ismount(mountpoint):
                self.execCommand("/bin/mount -o rw,uid=1000,gid=1000 " \
                    + device + " " + mountpoint)
                log.message("Mounted " + device + " on " +  mountpoint, log.DEBUG)
            else:
                log.message("Media already mounted on " + mountpoint, log.DEBUG)
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

    # Unmount mount points /media/<user> and /share
    def unmountAll(self):
        mountpoint = "/media/" + self.usr
        if os.path.ismount(mountpoint):
            # Un-mount USB stick
            self.execCommand("sudo /bin/umount " + mountpoint + " 2>&1 >/dev/null")
        if os.path.ismount('/share'):
            self.execCommand("sudo /bin/umount /share 2>&1 >/dev/null")
        return

    # Pause the client for speach facility (See message_class)
    def clientPause(self):
        try:
            self.client.pause()
        except Exception as e:
            log.message("radio.clientPause: " + str(e), log.ERROR)
        return

    # Restart the client after speech finished
    def clientPlay(self):
        try:
            self.client.play()
        except Exception as e:
            log.message("radio.clientPlay: " + str(e), log.ERROR)
            self.reconnect(self.client)
        return

    # Get language text
    def getLangText(self,label):
        return language.getText(label)
    
    # Detect audio error
    def audioError(self):
        return self.audio_error

    # Update the MPD playlist
    def updatingDB(self):
        return self.loading_DB

    # See if the current playlist has been changed by an external client
    def playlistHasChanged(self):
        playlist_changed = False
        plist = self.client.playlist()
        playlist_size = len(plist)
        if self.playlist_size == 0:
            self.playlist_size = playlist_size
        else:
            if playlist_size != self.playlist_size:
                playlist_changed = True
                print ("Playlist size changed",len(plist))
                self.playlist_size = playlist_size
        return playlist_changed

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

    # Translate on/off 
    def setTranslate(self,true_false):
        log.message("setTranslate " + str(true_false), log.DEBUG)
        self.translate.setTranslate(true_false)

    # Romanize Russian  on/off 
    def setRomanize(self,true_false):
        log.message("Romanize " + str(true_false), log.INFO)
        self.translate.setRomanize(true_false)

    # Display Pimoroni pivumeter (PHat Beat) if configured
    def displayVuMeter(self):
        if self.config.pivumeter:
            vol = self.pivumeter.getVolume()
            self.pivumeter.display(vol)

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

        elif option_index == self.menu.OPTION_STREAMING:
            value = self.streaming

        elif option_index == self.menu.OPTION_ALARM:
            value = self.getAlarmType()

        elif option_index == self.menu.OPTION_ALARMSETHOURS \
                or option_index == self.menu.OPTION_ALARMSETMINS:
            value = self.getAlarmTime()

        elif option_index == self.menu.OPTION_TIMER:
            value = self.getTimerCountdown()

        elif option_index == self.menu.OPTION_RECORD_DURATION:
            value = self.getRecordDuration()

        else:   
            value = False

        return value

    # Setup the playlist callback
    def setupPlaylistCallback(self):
        # Cannot use existing MPD client in a thread so create new
        newclient = mpd.MPDClient()   # Create the MPD client
        newclient.connect("localhost", self.mpdport)
        self.PL.callback(self.playlistChange,newclient)

    # This is the actual playlist callback to update changed playlists
    # It raises a PLAYLIST_CHANGE event if enabled by update_playlists
    def playlistChange(self):
        if self.config.update_playlists:
            self.event.set(self.event.PLAYLIST_CHANGED)
            print("event.PLAYLIST_CHANGED sent!")

# End of Radio Class

# set tabstop=4 shiftwidth=4 expandtab
# retab
