#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Raspberry Pi Internet Radio create stationlist
# $Id: update_stationlist.py,v 1.3 2021/09/18 04:32:59 bob Exp $
#
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# Create stationlist file from Radio playlists in the MPD playlists directory
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#         The authors shall not be liable for any loss or damage however caused.
#

import pdb,os,sys,time,pwd
from time import strftime
from playlist_class import Playlist
from source_class import Source
from shutil import copyfile

# MPD files
MpdLibDir = "/var/lib/mpd"
PlaylistsDirectory =  MpdLibDir + "/playlists"
RadioLibDir = "/var/lib/radiod"
Stationlist = RadioLibDir + "/stationlist"
tmpfile = "/tmp/stationlist"

PL = Playlist('Radio')
source = Source()

# Create a list of RADIO playlists from the MPD playlists directory
def getRadioPlaylists():
    filelist = []
    for file in os.listdir(PlaylistsDirectory):
        name = file.split('.')[0]
        type = PL.getType(name)
        if type == source.RADIO:
            filelist.append(file)
    return filelist

def appendStationlist(tmpf,entries):
        tmpf.write("\n".join(entries))
            
def createStationListFile(list):
    entries = [] 
    sDate = strftime('%d, %b %Y %H:%M:%S')
    entries.append("# Station list created by %s - %s \n" % (sys.argv[0],sDate))

     # Open temporary stationlist file
    tmpf = open(tmpfile,'w')

    # Create entries from each MPD playlist in turn
    for fname in list:
        print("Creating %s playlist" % fname )
        playlist_file = PlaylistsDirectory + '/' + fname
        playlist_name = fname.split('.')[0]
        entries.append('(' + playlist_name  + ')') 
        with open(playlist_file, 'r') as f:
            for line in f:
                if line.startswith( "#EXTINF:-1,"):
                    name = line.split(',')[1]
                    name = name.rstrip()
                    name = name.replace('[','')
                    name = name.replace(']','')
                if line.startswith("http"):
                    url = line.rstrip()
                    entries.append('[' + name + '] ' + url) 
        entries.append('\n') 
        f.close()
        appendStationlist(tmpf,entries)
        entries = [] 
    tmpf.close() 


# Print usage
def usage():
    print(("Usage: sudo %s <--update> <--help>" % sys.argv[0]))
    print("Where:")  
    print("      --update forces update of %s without prompting"% Stationlist)  
    print("      --help displays this help message")
    sys.exit(2)
                 
### Main routine ####
updateStationlist = False

if pwd.getpwuid(os.geteuid()).pw_uid > 0:
    print("This program must be run with sudo or root permissions!")
    usage()
    sys.exit(1)

if len(sys.argv) >= 2:
    if '--help' == sys.argv[1]:
        usage()
        sys.exit(0)
    elif '--update' == sys.argv[1]:
        updateStationlist = True
        
try:
    list = getRadioPlaylists()
    createStationListFile(list)
except Exception as e:
    print ("Stationlist creation failed")
    print(str(e))
    sys.exit(1)

print("Successfully created stationlist file %s" % tmpfile)

if not updateStationlist:
    answer = input("\nDo you wish to copy this to the stationlist file (y/n): ") 
    if answer == 'y':
        updateStationlist = True

if updateStationlist:
    # Create backup of original stationlist file 
    copyfile(Stationlist, Stationlist + ".bak")
    print("Created backup of %s in %s" % (Stationlist, Stationlist + ".bak"))
    copyfile(tmpfile, Stationlist)
    print("Copied %s to %s" % (tmpfile, Stationlist))
    
# set tabstop=4 shiftwidth=4 expandtab
# retab

