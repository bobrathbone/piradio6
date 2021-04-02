#!/usr/bin/env python3
#
# Raspberry Pi Radio 
# The source class handles loading of sources and playlists from
# the /var/lib/mpd/source.directory including the radio playlist
# or indicates that airplay needs to be loaded (see radio_class.py)
#
# $Id: source_class.py,v 1.2 2020/12/23 14:57:48 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#      The authors shall not be liable for any loss or damage however caused.
#
# Playlists for MPD are stored in /var/lib/mpd/source.directory
# All MPD playlists have the .m3u file extension
# Airplay and Spotify are not part of MPD and are not associated with playlists
# however they is stored as a pseudo playlists called _airplay_ and _spotify_ 
# respectively for the purpose of searching through the available sources   

import os,sys,pwd
from log_class import Log
from mpd import MPDClient
from constants import *
import pdb

log = Log()

# Definitions
PlaylistsDir = "/var/lib/mpd/playlists"
mpdport = 6600  # MPD port number

class Source:

    client = None   # MPD client
    playlists = {}  # Dictionary of playlists and their types
    index = 0   # Index of current playlist/source
    new_index = 0   # Index of new playlist/source
    mpdport = 6600  # MPD port

    # Source types (There are 4 source types)
    RADIO = 0   # Radio usually has one playlist but can have more
    MEDIA = 1   # Media can have one or more playlists with any name
    AIRPLAY = 2 # Airplay is not part of MPD and has no associated playlists
    SPOTIFY = 3 # Spotify is not part of MPD and has no associated playlists

    typeNames = ['RADIO','MEDIA','AIRPLAY','SPOTIFY']
    
    type = RADIO

    # Initialise. The airplay parameter adds a dummy entry 
    # to the list of playlists
    def __init__(self, client=client, airplay=False, spotify=False):
        self.airplay = airplay
        self.spotify = spotify
        self.client = client
        self.mpdport = mpdport
        log.init('radio')
        return

    # Load the source.
    def load(self):
        log.message("source.load", log.DEBUG)

        try:
            # Get the list of playlists from MPD
            mylist = self.client.listplaylists()
            
            for i,info in enumerate(mylist):
                playlist = info['playlist']
                type = self.getPlaylistType(playlist)
                self.playlists[playlist] = type
                
            if len(self.playlists) > 0:
                msg = "Loaded " + str(len(self.playlists)) + \
                         " playlists from " + PlaylistsDir
                log.message(msg, log.DEBUG)
            else:
                log.message("No playlists found in " + PlaylistsDir, log.ERROR)

            # If airplay create a 'dummy' playlist
            if self.airplay:
                self.playlists['_airplay_'] = self.AIRPLAY

            # If spotify create a 'dummy' playlist
            if self.spotify:
                self.playlists['_spotify_'] = self.SPOTIFY

        except Exception as e:
            log.message("source.load: " + str(e), log.DEBUG)

        if len(self.playlists) < 1:
            self.playlists = {'No playlists': 0}
        
        log.message(self.playlists, log.DEBUG)

        return self.playlists
    
    # Get current playlist
    def current(self):
        playlist = ''
        try: 
            playlist = list(self.playlists.keys())[self.index]
        except:
            log.message("Error getting current playlist" + str(self.index), log.DEBUG)
        return playlist

    # This routine cycles through sources/playlists of the same type
    # The event comes from the Web interfaces which only has three buttons
    # namely radio,media or airplay
    def cycleType(self, type):
        newtype = -1
        idx = self.index 
        playlist = self.getName()
        while type != newtype: 
            self.cycle(UP)
            newtype = self.getNewType()
            if idx == self.new_index:
                break
        if type == newtype: 
            playlist = self.getNewName()
        return playlist

    # Cycle through playlist
    def cycle(self, direction):
        newplaylist = ''

        if direction == UP:
            self.new_index += 1
        else:
            self.new_index -= 1

        if self.new_index > len(self.playlists)-1:
            self.new_index = 0

        elif self.new_index < 0:
            self.new_index = len(self.playlists)-1

        try:
            newplaylist = list(self.playlists.keys())[self.new_index]
        except:
            log.message("Error cycling playlist" + str(self.new_index), log.DEBUG)
        return newplaylist

    # Set new source type (from radio class) 
    def setNewType(self):
        self.index = self.new_index
        return self.index

    # Set source index
    def setIndex(self,index):
        index = self.checkIndex(index)
        self.index = index
        self.new_index = index
        return self.index

    # Set playlist index by name 
    def setPlaylist(self,playlist):
        idx = 0
        index = 0
        pl = playlist.lower()
        for name,value in self.playlists.items():
            name = name.lower()
            if name == pl:
                index = idx
                break
            idx += 1    
        self.setIndex(index)
        return 

    # Get source index
    def getIndex(self):
        return self.index

    # Get the playlist name for loading into MPD
    def getName(self):
        playlist = list(self.playlists.keys())[self.index]
        return playlist

    # Get the new playlist name for loading into MPD
    def getNewName(self):
        playlist = list(self.playlists.keys())[self.new_index]
        return playlist

    # Get the name for displayng on screen 
    def getDisplayName(self): 
        return self._getDisplayName(self.index)

    def getNewDisplayName(self): 
        return self._getDisplayName(self.new_index)

    def _getDisplayName(self,index): 
        index = self.checkIndex(index)
        playlist = list(self.playlists.keys())[self.index]
        playlist = playlist.replace('_', ' ')
        playlist = playlist.lstrip()
        playlist = playlist.rstrip()
        playlist = "%s%s" % (playlist[0].upper(), playlist[1:])
        playlist = playlist[:1].upper() + playlist[1:]
        return playlist

    # Get playlist type. RADIO, MEDIA, AIRPLAY or SPOTIFY
    def getType(self):
        return self._getType(self.index)

    # Set the type RADIO, MEDIA, AIRPLAY or SPOTIFY
    def setType(self,type):
        idx = 0
        newtype = -1
        playlist = self.getName()
        while type != newtype: 
            self.cycle(UP)
            newtype = self.getNewType()
            if idx == self.new_index:
                break
        if type == newtype: 
            return playlist

    # Routine to load O!MPD web interface library
    def loadOmpdLibrary(self):
        self.setType(self.MEDIA)
        playlists = self.load()
        currentsong = self.client.currentsong()
        path = str(currentsong.get("file"))
        path = path.lstrip('/')
        mount_point = path.split('/')[0]
        if mount_point == "media":
            playlist = "USB_Stick"
        elif mount_point == "share":
            playlist = "Network"
        else: 
            playlist = "Unknown"

        if playlist == "Unknown":
            playlist = self.cycleType(self.MEDIA)
        self.type = self.MEDIA
        return  playlist

    # Return the new type (radio, media or airplay)
    def getNewType(self):
        return self._getType(self.new_index)

    # Get playlist type Name. RADIO, MEDIA or AIRPLAY
    def getTypeName(self):
        return self.typeNames[self.index]
    
    # Get NEW playlist type Name. RADIO, MEDIA or AIRPLAY
    def getNewTypeName(self):
        return self.typeNames[self.getNewType()]
    
    # Get new playlist type. RADIO, MEDIA,AIRPLAY or SPOTIFY
    # This routine is only used during loading the available playlists
    def getPlaylistType(self,playlist):
        type = self.MEDIA
    
        if playlist == '_airplay_':
            type = self.AIRPLAY     

        if playlist == '_spotify_':
            type = self.SPOTIFY     

        elif playlist[0] == '_':
            type = self.RADIO   
            
        return type

    # Get the playlists dictionary
    def getPlaylists(self):
        return self.playlists

    # Get new playlist type. RADIO, MEDIA, AIRPLAY or SPOTIFY
    def _getType(self,index):
    
        index = self.checkIndex(index)
        type = list(self.playlists.values())[index]

        return type

    # Return list of sources
    def getList(self):
        return self.typeNames

    # Protect the routines from a bad index value
    def checkIndex(self,index):
        leng = len(self.playlists)
        if index > leng - 1:
            msg = "source.checkIndex index " + str(index) \
                 + " > " + str(leng)
            log.message(msg, log.ERROR)
            self.index = 0
            self.new_index = 0
        else:
            self.index = index
        return self.index

# End of sources class

### Test routine ###
if __name__ == "__main__":
    
    
    if pwd.getpwuid(os.geteuid()).pw_uid > 0:
        print("This program must be run with sudo or root permissions!")
        sys.exit(1)

    client = mpd.MPDClient()
    client.connect("localhost", 6600)

    print("Test Source Class")
    source = Source(client=client,airplay=True)
    airplay = True  # Simulate airplay
    source.load()
    print(source.current())
    print()
    print(source.getDisplayName())
    print(source.cycle(UP),'type',str(source.getNewType()))
    print(source.cycle(UP),'type',str(source.getNewType()))
    print(source.cycle(UP),'type',str(source.getNewType()))
    print(source.cycle(UP),'type',str(source.getNewType()))
    print("New", source.getNewName())
    print()
    print(source.cycle(DOWN),source.getNewType())
    print(source.getName(),'type', source.getNewType())
    print(source.cycle(UP),'type',str(source.getNewType()))
    sys.exit(0)

# End of test program

# set tabstop=4 shiftwidth=4 expandtab
# retab

