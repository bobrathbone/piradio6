#!/usr/bin/env python3
#
# Raspberry Pi Internet Radio Class
# $Id: playlist_class.py,v 1.31 2023/08/28 09:35:33 bob Exp $
#
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This class handles Music Player Daemon playlist functions
# It is mainly accessed from radio_class.py
# All attributes such has type or size must be set-up from the load function
# It also creates a search list for the radio routines
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#         The authors shall not be liable for any loss or damage however caused.
#

import pdb,sys,time
import threading
import copy
from translate_class import Translate
from source_class import Source

translate = Translate()
source = Source()

# MPD files
MpdLibDir = "/var/lib/mpd"
PlaylistsDirectory =  MpdLibDir + "/playlists"
RadioLibDir = "/var/lib/radiod"
CurrentPlaylistName = RadioLibDir + "/source_name"

RADIO = 0
MEDIA = 1

class Playlist:
    config = None

    _name = "Radio"  # Default playlist name
    _searchlist = []
    _size = 0   # Playlist size
    _type = 0   # Playlist type RADIO or MEDIA
    _plist = []

    def __init__(self,name,config):
        self.config = config
        self._name = name
        return

    # Playlist name
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self,name):
        self._name = name

    # Actual playlist (plist)
    @property
    def list(self):
        return self._plist
    
    @list.setter
    def list(self,list):
        self._plist = list

    # Playlist size
    @property
    def size(self):
        return self._size

    # Update the current playlist. This is called from the top level radio 
    # program in response to a PLAYLIST_CHANGED event
    def update(self,client):
        playlist_name = self.getName(CurrentPlaylistName)
        if self._type == RADIO:
            newlist = self.createNewRadioPlaylist(self._plist)
        else:
            newlist = self.createNewMediaPlaylist(self._plist)

        if len(newlist) > 0:
            self.writePlaylistFile(playlist_name,newlist)
            self._searchlist = self.createSearchList(client)
        else:
            # Protect playlist file if something goes wrong with client playlist
            print("No records found in new playlist %s" % playlist_name)
        return self._searchlist

    # Get the current playlist name from the radio lib directory
    def getName(self,filename):
        f = open(filename,"r")
        playlist_name = f.read()
        f.close()
        playlist_name = playlist_name.rstrip()
        return playlist_name

    # Create a playlist in MEDIA format
    def createNewMediaPlaylist(self,plist):
        newlist = []
        for line in plist:
            line = line.strip('file: ')
            newlist.append(line)
        return newlist

    # Create a playlist in RADIO format
    def createNewRadioPlaylist(self,plist):
        url = ''
        name = ''
        count = 0
        newlist = []
        for line in plist:
            line = line.strip('file: ')
            count += 1
            try:
                if line.startswith("http"):
    
                    if '#' in line:
                        x = line.split('#')
                        url = x[0]
                        name = x[1]
                    else:
                        url = line 
                        name = "Radio Station %s" % count

                    newlist.append("#EXTM3U")
                    newlist.append("#EXTINF:-1," + name)
                    newlist.append(url + '#' + name)
            except Exception as e:
                print ("failed on line",count)
                continue

        return newlist

    # Write the new RADIO playlist to the MPD playlist directory 
    def writePlaylistFile(self,playlist_name,newlist):
        playlist_file = PlaylistsDirectory + '/' + playlist_name + '.m3u'
        try:
            with open(playlist_file, 'w') as f:
                for line in newlist:
                    f.write('%s\n' % line)
                f.close()
        except Exception as e:
            print("File update failed: " + str(e))

    # Load playlist by name
    def load(self,client,name):
        try:
            self._name = name
            client.clear()
            client.load(name)
            self._plist = client.playlist()
            self._type = self.getType(name)
            self._searchlist = self.createSearchList(client)
            #print("Name=%s Type=%s Size=%s"% (self._name, self._type, self._size))
        except Exception as e:
            print("playlist.load",str(e))
        return self._searchlist

    # Create search list of tracks or stations
    def createSearchList(self,client):
        if self.config.station_names == self.config.STREAM or self._type == source.MEDIA:
            self._plist = client.playlist()
            searchlist = self._createStreamSearchList(self._plist)
        else:
            searchlist = self._createListSearch()

        self._searchlist = searchlist
        self._size = len(self._searchlist)
        return self._searchlist
        
    # Create search list from stationlist file
    _name = "Radio"
    def _createListSearch(self):
        searchlist = []
        try:
            f = open(PlaylistsDirectory + '/' + self._name + '.m3u', 'r')
            lines = f.readlines()
            f.close()
            for line in lines:
                line = line.rstrip()
                if len(line) < 1:
                    continue
                if not line.startswith('#EXTINF:'):
                    continue
                x = line.split(',')
                line = x[1]
                searchlist.append(line)

        except Exception as e:
            print("File read failed: " + str(e))

        return searchlist

    # Create search list from MPD stream
    def _createStreamSearchList(self,plist):
        searchlist = []

        for line in plist:
            line = line.strip('file: ')
            if len(line) < 1:
                continue
            if line.startswith("http") and '#' in line:
                x = line.split('#')
                url = x[0]
                name = x[1]
                name = translate.all(name)
            else:
                x = line.split('/')
                l = len(x)
                artist = x[1]
                title = x[l-1]
                if artist in title:
                    name = title
                else:
                    name = artist + ' - ' + title
            searchlist.append(name)

        self._size = len(plist)

        return searchlist

    # Return searchlist
    @property
    def searchlist(self):
        return self._searchlist

    # See if the current playlist has been changed by an external client
    def changed(self,client):
        playlist_changed = False
        try:
            plist = client.playlist()
            playlist_size = len(plist)
            if self._size == 0:
                self._size = playlist_size  # If a clear occured
            else:
                if playlist_size != self._size:
                    playlist_changed = True
                    self._size = playlist_size
                    self._plist = plist
                elif len(self._plist) > 0:
                    idx = 0
                    for line in plist:
                        if line != self._plist[idx]:
                            playlist_changed = True
                            break
                        idx += 1
            self._plist = plist
                    
        except Exception as e:
            print("playlist.changed",str(e))
            sys.exit(1)

        return playlist_changed

    # Check for playlist changes and raise event if it changes
    def _check(self,playlist_callback,client):
        time.sleep(10) # Prevent spurious events at startup time
        client.idletimeout = None
        try:
            while True:
                client.idle('playlist')
                if self.changed(client):
                    time.sleep(2) # Allow time for MPD_CLIENT_CHANGE to be handled 
                    self._plist = client.playlist()
                    playlist_callback()
        except Exception as e:
            print("playlist._check error", str(e))
            #sys.exit(1)
            pass

    # Callback for playlist size change
    def callback(self,playlist_callback,client):
        t = threading.Thread(target=self._check, args=[playlist_callback,client])
        t.daemon = True  # Important otherwise main thread won't exit
        t.start()
        return

    # Identify playlist type RADIO or MEDIA 
    def getType(self,playlist_name):
        playlist_type = source.MEDIA
        playlist_file = PlaylistsDirectory + '/' + playlist_name + '.m3u'
        typeNames = ['RADIO','MEDIA']

        # Check playlist for "#EXTM3U" definition
        count = 15  # Allow comments 15 lines max at start of file
        found = False
        try:
            f = open(playlist_file, 'r')
            while count > 0 and not found:
                line = f.readline()
                line = line.rstrip()
                if line.startswith("#EXTM3U"):
                    found = True
                    playlist_type = source.RADIO
                count -= 1

        except Exception as e:
            print("playlist.type: " + str(e))

        return playlist_type

    # Playlist type attribute
    @property
    def type(self):
        return self._type

# End of class

# Class test routine
if __name__ == "__main__":
    import mpd
    from config_class import Configuration
    config = Configuration()
    client = mpd.MPDClient()

    PL = Playlist("Radio",config)    
    print ("Playlist", PL.name)
    list = PL.createSearchList(client)
    print (PL.size)
    print (list)

    sys.exit(0)

# set tabstop=4 shiftwidth=4 expandtab
# retab
