#!/usr/bin/env python3
#
# $Id: record.py,v 1.37 2025/01/07 12:34:56 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program uses streamripper
# Use "apt-get install streamripper" to install streamripper
# See https://streamripper.sourceforge.net/
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.
#
import sys
import os
import pdb
import time
from time import strftime
import re
import subprocess
from subprocess import check_output
import getpass
import pwd
import stat
import signal

from pwd import *
from os import stat

from mpd import MPDClient
from log_class import Log
log = Log()
log.init('radio')

streamripper = '/usr/bin/streamripper'
useragent = "WinampMPEG/5.0"
mpc = '/usr/bin/mpc'
RadioLibDir = '/var/lib/radiod/'
MpdPlaylists = '/var/lib/mpd/playlists'
MpdMusicDir = '/var/lib/mpd/music'
StationList = RadioLibDir + 'stationlist'
pidfile = '/var/run/radio_record/record.pid'
RecordingsPlaylist = 'Recordings'
MpdPlaylistsLink = 'recordings'
mpdport = 6600

client = MPDClient()    # Create the MPD client

# =======================================
# Recorder class - Records radio streams
# =======================================
class Recorder:
    client = None
    name = None
    url  = None
    currentsong = None
    duration = 10   # Duration in minutes

    # Station details from /var/lib/radio/stationlist
    Stations = {}
    Urls = ()
    Names = ()

    log = None

    def __init__(self,logit):
        log = logit
        self._getStations()
        self.usr = getpwuid(stat("/usr/share/radio").st_uid).pw_name
        self.grp = self.usr  # Temporary only
        self.uid = getpwnam(self.usr).pw_uid
        self.gid = getpwnam(self.usr).pw_gid

    # Connect to MPD server    
    def connect(self,duration=10):
        self.duration = duration
        try:
            client.timeout = 10
            client.idletimeout = None
            client.connect("localhost", mpdport)
            self.currentsong = client.currentsong()
        except Exception as e:
            print(str(e)) 
            log.message("Record: Music player daemon not running!",log.DEBUG)
            log.message("Record: Start radio (or MPD) and re-run program",log.DEBUG)
            sys.exit(1)

    # Get current station playing from MPD
    def getCurrent(self):
        self.name = str(self.currentsong.get("name"))
        self.url = str(self.currentsong.get("file"))
        if not re.match('^http',self.url):
            msg = "Record: You can only record RADIO streams - Exiting"
            print(msg)
            log.message(msg,log.ERROR)
            sys.exit(1)

    def check_url(self,url):
        return 

    # Store and delete process pid
    def store_pid(self):
        self.pid = os.getpid()
        f = open(pidfile,"w")
        f.write(str(self.pid))
        f.close()
        os.chown(pidfile, self.uid, self.gid)
        return self.pid

    def del_pid(self):
        if os.path.exists(pidfile):
            os.remove(pidfile)

    # Start recording - duration in minutes
    def start(self,duration=10):
        duration = duration * 60 # Convert to seconds

        if not os.path.exists(directory):
            os.makedirs(directory)
    
        self.store_pid()

        # Call streamripper
        owner = getOwner('/usr/share/radio')
        record_dir = '/home/' + owner + '/Recordings' 
        cmd = "streamripper %s -u %s -l %d -d %s" % (self.url,useragent,duration,record_dir)
        print(cmd)
        log.message(cmd,log.DEBUG)
        try:
            subprocess.run(cmd, shell=True, check=True, capture_output=True, 
                     encoding='utf-8')

            uid = pwd.getpwnam(owner).pw_uid
            gid = pwd.getpwnam(owner).pw_gid
            os.chown(record_dir, uid, gid)

            # Change ownership to pi:pi (or actual user)
            for root, dirs, files in os.walk(record_dir):  
                for dir in dirs:  
                    os.chown(os.path.join(root,dir), uid, gid)
                for file in files:  
                    os.chown(os.path.join(root,file), uid, gid)

            result = "streamripper succesfully executed"
     
        except Exception as e:   
            result = "Record: streamripper exited due to user request"
            log.message(result,log.DEBUG)
            return(msg)
            
        except KeyboardInterrupt:
            print("\nCtrl-C pressed - Exiting")
            self.del_pid()
            sys.exit(0)

        self.del_pid()
        return result

    # Select a specific station 
    def select(self,station_id):
        current_id = -1

        # Play requested station otherwise use current station
        if (station_id > 0):
            idx = station_id - 1
            client.play(idx)

        status = client.status()
        current_id = int(status.get("song")) + 1
        self.name = self.currentsong.get("name")
        return self.name

    # Build a dictionary of radio stations
    def _getStations(self):
        id = 0
        for line in open(StationList,'r'):
            line = line.strip()
            if (re.match("^\[",line)):
                id += 1
                line = line.strip('[')
                (name,url) = line.split(']')
                #print(id,name,url)
                self.Stations[name] = url

        self.Urls = list(self.Stations.values())
        self.Names = list(self.Stations.keys()) 

    # Get station details by ID number from stationlist
    def getStation(self,id):
        msg = "Record: getStation " + str(id)
        log.message(msg,log.DEBUG)
        leng = len(self.Stations)
        if id < 1 or id > leng:
            station = (id,"Invalid station number, must be between 1 and " + str(leng),'')
        else:
            self.name = (self.Names[id-1])
            self.url = self.Urls[id-1]
            station = (id,self.name,self.url)
        return station

    # Returns the device name for the "gpio_ir_recv" overlay (rc0...rc6)
    # Used to load ir_keytable
    def get_ir_device(self,sName):
        global rc_device
        found = False
        for x in range(7):
            name = ''
            device = ''
            for y in range(7):
                file = sys_rc + '/rc' + str(x) + '/input' + str(y) + '/name'
                if os.path.isfile (file):
                    try:
                        f = open(file, "r")
                        name = f.read()
                        name = name.strip()
                        if (sName == name):
                            device = 'rc' + str(x)
                            rc_device = sys_rc + '/rc' + str(x)
                            found = True
                            break
                        f.close()
                    except Exception as e:
                        print(str(e))
                        log.message(e,log.ERROR)
            if found:
                break

        return device

    # Load playlist recordings (usually /home/<usr>/Recordings)
    def load(self,directory):
        try:
            # Link /home/<usr>/Recordings -> /var/lib/mpd/music/recordings
            link = MpdMusicDir + '/' + MpdPlaylistsLink
            if not os.path.islink(link):
                os.symlink(directory,link)
            client.close()
            client.disconnect() 
            client.connect("localhost",mpdport)
            status = client.status()
            client.update()
            client.load(RecordingsPlaylist) 
            client.close()
            client.disconnect()
        except Exception as e:
            print(str(e)) 
            sys.exit(1)

# End of Recorder class

# Get owner of the installed package
def getOwner(path):
    stat = os.stat(path)
    uid = stat.st_uid
    owner = pwd.getpwuid(uid).pw_name
    return owner

# =======================================
# Playlist creation for loading into MPD
# =======================================
class Playlist:
    
    usr = getpass.getuser()  
    playlist_file = MpdPlaylists + "/Recordings.m3u"

    def __int__():
        return

    # Create playlist omit_incomplete=True/False omit incomplete tracks
    def create(self,omit_incomplete=False,cleanup=False):
        owner = getOwner('/usr/share/radio')
        directory = '/home/' + owner + '/Recordings' 
        msg = "Record: Processing recordings directory " + directory
        print(msg)
        log.message(msg, log.DEBUG)

        if omit_incomplete:
            msg = "Record: Ommiting incomplete recordings from playlist %s" % self.playlist_file
        else:
            msg = "Record: Including incomplete recordings in playlist %s" % self.playlist_file
        print(msg)
        log.message(msg, log.DEBUG)

        count = 0

        f = open(self.playlist_file,'w')
        for path, subdirs, files in os.walk(directory):
            for name in files:
                omit = False
                track = os.path.join(path, name)
                orig_track  = track
                track = track.replace("/home/" + owner + "/Recordings/","recordings/")
                if "/incomplete/" in track and omit_incomplete:
                    omit = True

                # Omit tracks containing time stamp eg. (08-30)
                if re.search("\([0-9]", track) and re.search("[0-9]\)", track):
                    omit = True

                if cleanup and omit:
                    os.remove(orig_track)

                if omit:
                    continue
                print(track)
                f.write(track + '\n')

                count += 1
        f.close()

        msg = "Record: %d tracks written to %s" % (count,self.playlist_file)
        print(msg)
        log.message(msg, log.INFO)

    # Get owner of the installed package
    def getOwnerXX(self,path):
        stat = os.stat(path)
        uid = stat.st_uid
        owner = pwd.getpwuid(uid).pw_name
        return owner

# End of Playlist class

def usage(max):
    print("\nUsage: sudo ",sys.argv[0],"--station_id=<station number> --duration=<duration>")
    print("                 --omit_incomplete --playlist_only --directory=<directory>")
    print("                 --cleanup")
    print("\nWhere <station number> is the number of the radio stream to record")
    print("      --station_id if ommited the currently playing station will be recorded")
    print("      --omit_incomplete skip incomplete tracks when creating the playlist")
    print("      --playlist_only Only create playlist from the recordings directory. No recording")
    print("      --cleanup Remove incomplete tracks from the /home/<user>/Recordings directory")
    print("      <directory> is the location for recorded files. default /home/<user>/Recordings") 
    print("      <duration> is the length of time to record in hours:minutes") 
    print("                 Maximum recording time allowed", int(max/60), "hours", "\n")

# Convert hh:mm to minutes
def convertDuration(duration):
    try:
        (hours,minutes) = duration.split(':')
    except:
        minutes = int(duration)
        return minutes
    if minutes == '':
        minutes = int(hours) * 60
    else:
        minutes = int(hours) * 60 + int(minutes)
    return minutes

# Class test routine
if __name__ == "__main__":
    import getpass
    from time import strftime

    pid = os.getpid()
    msg = sys.argv[0] + " running, pid " + str(pid)
    log.message(msg, log.INFO)

    station_id = 0  # Radio station number
    duration = ''    # Read /var/lib/radiod/recording file to get duration
    minutes = duration
    max_duration = 12 * 60  # Maximum 12 hours recording time allowed
    omit_incomplete = False
    playlist_only = False
    load_playlist = True
    cleanup = False

    RadioLibDir = "/var/lib/radiod"
    RecordingDurationFile = RadioLibDir + "/recording"

    if os.getuid() != 0:
        print("This program can only be run as root user or using sudo")
        usage(max_duration)
        sys.exit(1)

    # Default directory
    owner = getOwner('/usr/share/radio')
    directory = '/home/' + owner + '/Recordings' 

    def getDurationFile():
        try:
            f = open(RecordingDurationFile,'r')
            duration = f.read()
            f.close
        except:
            duration = '0:02'
        return duration

    # Signal handler
    def signalHandler(sig,frame):
        if sig == signal.SIGHUP:
            msg = "Record: Received signal SIGHUP"
            print(msg)
            log(msg,log.DEBUG)
            pid = int(check_output(["pidof","streamripper"]))
            if pid > 0:
                msg = "Record: Sending HUP to %d" % pid
                log(msg,log.DEBUG)
                os.kill(pid, signal.SIGHUP)
    
    args = sys.argv[1:]
    msg = "Record: args %s" % args
    print(msg)
    log.message(args, log.DEBUG)

    for arg in args:
        params = arg.split('=')
        if len(params) == 2:

            param = params[0]
            value = params[1]

            if param == '--station_id' or param == '-i':
                station_id = int(value)

            elif param == '--duration' or param == '-d':
                duration = value

            elif param == '--directory':
                directory = param

        elif params[0] == '--help' or arg == '-h':
            usage(max_duration)
            sys.exit(0)

        elif params[0] == '--omit_incomplete' or arg == '-o':
            omit_incomplete = True

        elif params[0] == '--playlist_only' or arg == '-p':
            playlist_only = True

        elif params[0] == '--cleanup' or arg == '-c':
            cleanup = True

        else: 
            usage(max_duration)
            sys.exit(0)

    signal.signal(signal.SIGHUP,signalHandler)
    if len(duration) < 1:
        duration = getDurationFile()

    minutes = convertDuration(duration)
    if minutes > max_duration:
        print("\nMaximum recording time of",int(max_duration/60), " hours exceeded")
        usage()

    os.makedirs(directory, exist_ok=True)
    uid = pwd.getpwnam(owner).pw_uid
    gid = pwd.getpwnam(owner).pw_gid
    os.chown(directory, uid, gid)
        
    if playlist_only:
        # Don't record - only make playlist
        playlist = Playlist()
        playlist.create(omit_incomplete,cleanup)
        sys.exit(0)

    print("Directory",directory)
    print("Duration",minutes,"minutes")
    if station_id > 0:
        print("Station",station_id)
    else:
        print("Record current station")

    record = Recorder(log)

    # Record requested station
    if station_id != 0: 
        station=record.getStation(station_id)
        print(station)
        msg = "Record: Recording station %s" % station[1]
        log.message(msg, log.INFO)
        print(station)
        result = record.start(minutes)
        log.message(result,log.DEBUG)
        name = record.name

    else:
        # Record current station
        record.connect()
        name = record.select(station_id)    # 0 = Default to the current station
        time.sleep(3)
        record.getCurrent()
        msg = "Record: Recording %s, url: %s" % (name,record.url)
        print(msg)
        log.message(msg,log.DEBUG)
        result = record.start(minutes)
        print(result)
        log.message(result,log.DEBUG)

    msg = "Record: Finished recording %s" % name
    print(msg)
    log.message(msg,log.DEBUG)

    # Create playlist in /var/lib/mpd/playlists directory
    playlist = Playlist()
    playlist.create(omit_incomplete)

    if load_playlist or cleanup:
        msg = "Record: Loading %s playlist" % RecordingsPlaylist
        print(msg)
        log.message(msg,log.INFO)
        record.load(directory)

    msg = sys.argv[0] + " succesfully completed, pid " + str(pid)
    print(msg)
    log.message(msg, log.INFO)
    sys.exit(0)

# End of test routine
# :set tabstop=4 shiftwidth=4 expandtab
# :retab
