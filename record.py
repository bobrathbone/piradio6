#!/usr/bin/env python3
#
# $Id: record.py,v 1.9 2024/11/28 20:07:09 bob Exp $
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
import re
import subprocess

from mpd import MPDClient

streamripper = '/usr/bin/streamripper'
useragent = "WinampMPEG/5.0"
directory = '/home/pi/Recordings' 
mpc = '/usr/bin/mpc'
RadioLibDir = '/var/lib/radiod/'
StationList = RadioLibDir + 'stationlist'

client = MPDClient()    # Create the MPD client

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

    def __init__(self):
        self._getStations()
        return

    # Connect to MPD server    
    def connect(self,duration=10):
        self.duration = duration
        try:
            client.timeout = 10
            client.idletimeout = None
            client.connect("localhost", 6600)
            self.currentsong = client.currentsong()
        except Exception as e:
            print(str(e)) 
            print("Music player daemon not running!")
            print("Start radio (or MPD) and re-run program")
            sys.exit(1)

    # Get current station playing from MPD
    def getCurrent(self):
        self.name = str(self.currentsong.get("name"))
        self.url = str(self.currentsong.get("file"))
        if not re.match('^http',self.url):
            print("Error: You can only record RADIO streams - Exiting")
            sys.exit(1)

    def check_url(self,url):
        return 

    # Start recording - duration in minutes
    def start(self,duration=10):
        duration = duration * 60 # Convert to seconds

        if not os.path.exists(directory):
            os.makedirs(directory)
    
        cmd = "streamripper %s -u %s -l %d -d %s" % (self.url,useragent,duration,directory)
        print(cmd)
        try:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, 
                     encoding='utf-8')
        except KeyboardInterrupt:
            print("\nCtrl-C pressed - Exiting")
            sys.exit(0)
        return result

    # Select a specific station 
    def select(self,station_id):
        current_id = -1
        if (station_id > 0):
            idx = station_id - 1
            client.play(idx)
            status = client.status()
            current_id = int(status.get("song")) + 1
        return current_id

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

    # Get station details by ID number
    def getStation(self,id):
        print("getStation", id)
        leng = len(self.Stations)
        if id < 1 or id > leng:
            station = None
            station = (id,"Invalid station number, must be between 1 and " + str(leng),'')
        else:
            name = (self.Names[id-1])
            url = self.Urls[id-1]
            station = (id,name,url)
            self.url = url
        return station

# End of Recorder class

def usage(max):
    print("\nUsage:", sys.argv[0], "--station_id=<station number> --duration=<duration>")
    print("\nWhere <station number> is the number of the radio stream to record")
    print("      <duration> is the length of time to record in hours:minutes") 
    print("                 Maximum recording time allowed", int(max/60), "hours")
    sys.exit(0)

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
    station_id = 1  # Radio station number
    duration = 10
    minutes = duration
    max_duration = 12 * 60  # Maximum 12 hours recording time allowed

    args = sys.argv[1:]
    for arg in args:
        params = arg.split('=')
        if params[0] == '--help' or arg == '-h':
            usage(max_duration)

        if len(params) == 2:

            param = params[0]
            value = params[1]

            if param == '--station_id' or param == '-s':
                station_id = int(value)

            elif param == '--duration' or param == '-d':
                minutes = convertDuration(value)

            else: 
                usage(max_duration)

    if minutes > max_duration:
        print("\nMaximum recording time of",int(max_duration/60), " hours exceeded")
        usage()

    print("Station",station_id)
    print("Duration",minutes,"minutes")

    record = Recorder()
    id = 16 
    station=record.getStation(station_id)
    print(station)
    result = record.start(minutes)
    sys.exit(1)

    record.connect()
    record.select(station_id)    # 0 = Default to the current station
    time.sleep(3)
    record.getCurrent()
    print("Recording:",record.name)
    print(record.url)
    result = record.start(minutes)
    print("Recording stopped:")

# End of test routine
# :set tabstop=4 shiftwidth=4 expandtab
# :retab
