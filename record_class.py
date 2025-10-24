#!/usr/bin/env python3
#
# $Id: record_class.py,v 1.20 2025/10/21 14:32:07 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.
#
# This program uses liquidsoap
# Use "apt-get install liquidsoap" to install liquidsoap
# See https://github.com/savonet/liquidsoap
#     https://www.liquidsoap.info/          
#
# This program also uses "record.liq". The liquidsoap project can be found on GitHub
# See: https://github.com/smoralis/liquidsoap-record/tree/main
#
# LiquidSoap only runs on Raspberry Pi OS 64-bit Bookworm, it can be installed with the following commands
#sudo apt install ffmpeg libavcodec-dev libavcodec59 libavdevice59 libavfilter8 libavformat-dev libavformat59 libavutil-dev libavutil57 libpostproc56 libswresample-dev libswresample4 libswscale-dev libswscale6 
#sudo apt install libportaudio2 libfdk-aac2 libjemalloc2 liblo7 libpcre3
#sudo dpkg -i liquidsoap_2.2.5-debian-bookworm-1_arm64.deb
#sudo vi /etc/apt/preferences.d/ffmpeg.pref 
#Insert the following
#Package: ffmpeg libavcodec-dev libavcodec59 libavdevice59 libavfilter8 libavformat-dev libavformat59 libavutil-dev libavutil57 libpostproc56 libswresample-dev libswresample4 libswscale-dev libswscale6
#Pin: origin deb.debian.org
#Pin-Priority: 1001

import sys
import os
from os import walk
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

mpc = '/usr/bin/mpc'
RadioLibDir = '/var/lib/radiod'
MpdPlaylists = '/var/lib/mpd/playlists'
MpdMusicDir = '/var/lib/mpd/music'
StationList = RadioLibDir + '/stationlist'
RecordingsPlaylist = 'Recordings'
LiquidSoap = '/usr/bin/liquidsoap'
RecordLiq = '/usr/share/radio/record.liq'
MpdPlaylistsLink = 'recordings'
mpdport = 6600

# Output formats. See https://github.com/smoralis/liquidsoap-record
# -format the -format parameter isn't strictly necessary as it defaults to the correct
# file extension. It can however be used to change the file extension name if necessary
format_aac = "-transcode 1 -samplerate 44100 -format mp4 -codec aac -bitrate 320k"
format_mp3 = "-transcode 1 -samplerate 44100 -format mp3 -codec libmp3lame"
format_flac = "-transcmt_aacde 1 -samplerate 44100 -format flac -codec flac"
format_opus = "-transcode 1 -samplerate 48000 -format opus -codec libopus -bitrate 128k"

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
    format = ""
    PL = None
    station_id = 0

    # Station details from /var/lib/radio/stationlist
    Stations = {}
    Urls = ()
    Names = ()

    def __init__(self,logit,PL):
        log = logit
        self.PL = PL
        self._getStations()
        self.usr = getpwuid(stat("/usr/share/radio").st_uid).pw_name
        self.grp = self.usr  # Temporary only
        self.uid = getpwnam(self.usr).pw_uid
        self.gid = getpwnam(self.usr).pw_gid

    # Connect to MPD server    
    def connect(self):
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

    # Get the currently playing station ID
    def getCurrentId(self):
        id = 0
        if self.currentsong != None:
            id =  self.currentsong.get('pos')
        return id

    # Disconnect
    def disconnect(self):
        try:
            self.client.disconnect()
        except:
            pass
        
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

    # Set output file format cmmand line options
    def set_format_opts(self,format):
        if format == "mp3": 
            format_opts = format_mp3
        elif format == "aac": 
            format_opts = format_aac
        elif format == "flac": 
            format_opts = format_flac
        elif format == "opus": 
            format_opts = format_opus
        else:
            # Default codec if none specified 
            format_opts = ""
        return format_opts
            
    # Start recording - duration in minutes
    def start(self,name,url,duration,config):

        format_opts = self.set_format_opts(config.record_format)
        loglevel = config.record_log
            
        duration = duration * 60 # Convert to seconds
        owner = self.getOwner('/usr/share/radio')
        record_dir = '/home/' + owner + '/'  + "Recordings"

        if not os.path.exists(record_dir):
            os.makedirs(record_dir)

        # Set ownership and permissions
        uid = pwd.getpwnam(owner).pw_uid
        gid = pwd.getpwnam(owner).pw_gid
        os.chown(record_dir, uid, gid)
        os.chmod(record_dir,0o766) # Allow RW access to anyone
    
        try:
            self.connect()    # Connect to client
        except:
            pass

        tstart = time.time()

        # Need to run liquidsoap as a non-root user (set by owner usually pi) 
        cmd = "sudo -u %s %s %s -- -url %s -timeout %d -dir %s -station \"%s\" -keep 1 -log %d %s" %\
              (owner,LiquidSoap,RecordLiq,url,duration,record_dir,name,loglevel,format_opts)
        print(cmd)
        log.message(cmd,log.DEBUG)

        try:
            subprocess.run(cmd, shell=True, check=True, capture_output=False,encoding='utf-8')

            uid = pwd.getpwnam(owner).pw_uid
            gid = pwd.getpwnam(owner).pw_gid
            os.chown(record_dir, uid, gid)

            # Change ownership to pi:pi (or actual user)
            cmd = "sudo chown -R %s:%s %s" % (uid,gid,record_dir)
            print(cmd)
            log.message(cmd,log.DEBUG)
            subprocess.run(cmd, shell=True, check=True, capture_output=False,encoding='utf-8')

            result = "Record: liquidsoap succesfully executed"
     
        except Exception as e:   
            result = "Record: liquidsoap exited due to user request!"
            log.message(result,log.DEBUG)
            
        except KeyboardInterrupt:
            print("\nCtrl-C pressed - Exiting")
            self.del_pid()
            sys.exit(0)

        except Excepion as e:
            print("Error",e)
            sys.exit(0)

        tfinish =  time.time()
        ttime = self.elapsed_time(tstart,tfinish)
        msg = ("Record: Elapsed time %d Hours %d Minutes %d Seconds" % (ttime[0],ttime[1],ttime[2]))
        print(msg)
        log.message(msg,log.DEBUG)
        self.renameDirs(record_dir,owner)
        return result

    # Get elapsed time
    def elapsed_time(self,tstart,tfinish):
        delta = int(tfinish - tstart)
        hours = int(delta / 3600)
        minutes = int(int(delta - hours*3600)/60)
        seconds = int(delta - hours * 3600 - minutes * 60)
        ttime = (hours,minutes,seconds)
        return ttime

    # Select a specific station 
    def select(self,station_id):
        current_id = -1

        # Play requested station otherwise use current station
        if (station_id > 0):
            idx = station_id - 1
            client.play(idx)

        try:
            status = client.status()
            current_id = int(status.get("song")) + 1
            self.name = self.currentsong.get("name")
        except: 
            msg = "Record: Music player daemon not running!"
            print(msg)
            log.message(msg,log.DEBUG)
            msg = "Record: Start radio (or MPD) and re-run program"
            print(msg)
            log.message(msg,log.DEBUG)
            sys.exit(1)
        return self.name

    # Build a dictionary of radio stations
    def _getStations(self):
        id = 0
        for line in open(StationList,'r'):
            line = line.strip()
            if (re.match("^\\[",line)):
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

    # Get owner of the installed package
    def getOwner(self,path):
        stat = os.stat(path)
        uid = stat.st_uid
        owner = pwd.getpwuid(uid).pw_name
        return owner

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
            client.clear()
            client.load(RecordingsPlaylist) 
            client.update()
            client.play()
            client.close()
            client.disconnect()
        except Exception as e:
            print(str(e)) 
            sys.exit(1)

    # Rename directories called 'Recordings" or 'None' to Station_<station_id>
    def renameDirs(self,record_dir,owner):
        name = "Recordings"

        if self.station_id < 1:
            self.station_id = int(self.getCurrentId()) + 1
            station=self.getStation(self.station_id)   # Returns tuple(id,name,url)
        dirs = []

        for (dirpath, dirnames,filenames) in walk(record_dir):
            dirs.extend(dirnames)
            break

        for dir in dirs:
            print(dir)
            if dir == 'Recordings' or dir == 'None':
                station_name = station[1]
                new_dir = '/home/' + owner + '/' + name + '/' + station_name
                if not os.path.isdir(new_dir):
                    os.mkdir(new_dir)

                # Copy the files from the None/Recordings directory to the new directory
                cmd = "cp -r " + record_dir + "/" + dir + "/* " +  "\'" + new_dir + "/\'"
                print(cmd)
                log.message(cmd,log.DEBUG)
                subprocess.run(cmd, shell=True, check=True, capture_output=False,encoding='utf-8')

                # Change ownership
                cmd = "chown -R %s:%s '%s'" % (owner,owner,new_dir)
                print(cmd)
                log.message(cmd,log.DEBUG)
                subprocess.run(cmd, shell=True, check=True, capture_output=False,encoding='utf-8')
    
                # Remove old Recordings or None directory
                cmd = "rm -rf " + record_dir + "/" + dir
                print(cmd)
                log.message(cmd,log.DEBUG)
                subprocess.run(cmd, shell=True, check=True, capture_output=False,encoding='utf-8')

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

# End of Recorder class

# Class test routine
if __name__ == "__main__":
    import os
    from record_class import Recorder
    from log_class import Log
    from playlist_class import Playlist
    from config_class import Configuration

    if getpwuid(os.geteuid()).pw_uid > 0:
        print("This program must be run with sudo or root permissions!")
        sys.exit(1)
    
    PlaylistsDir = "/var/lib/mpd/playlists"
    name = "Recordings"
    record_dir = "/home/pi/Recordings"
    duration = 5    # Duration in minutes

    log = Log()
    config = Configuration()
    PL = Playlist(name,config,log)
    url = "http://sc3.radiocaroline.net:8030/listen.m3u8"
    playlist_file = PlaylistsDir + '/' + name + '.m3u'

    record = Recorder(log,PL)
    record.start(name,url,duration,config)
    PL.createRecordPlaylist(playlist_file,config)
    
# End of test routine
# :set tabstop=4 shiftwidth=4 expandtab
# :retab
