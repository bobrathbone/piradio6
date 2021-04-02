#!/usr/bin/env python3
#
# Raspberry Pi Spotify receiver Class
# $Id: spotify_class.py,v 1.3 2020/12/23 14:57:48 bob Exp $
#
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#       The authors shall not be liable for any loss or damage however caused.
#
# This class uses raspotify from Tom Cooper, https://github.com/dtcooper/raspotify
# and librespot from Paul Lietar, see https://github.com/librespot-org/librespot 
#
# Track information comes from the system journal. See man journalctl
# Two different formats of the journal entry are used. One for earlier versions of Raspbian
# and the other is used by Raspbian Buster or later.
#


import os,sys
import subprocess
import pdb
import threading
import select

args = ['journalctl', '--lines', '0', '--follow', '_SYSTEMD_UNIT=raspotify.service']

class SpotifyReceiver:
    running = False
    info = ''
    translate = None        # Translate class setup in __init__

    def __init__(self,translate):
        self.translate = translate
        return

    # Start Spotify
    def start(self):
        self.execCommand("sudo systemctl start raspotify")
        self.running = True
        self.startJournalWatch()
        return self.running

    # Stop Spotify
    def stop(self):
        self.execCommand("sudo systemctl stop raspotify")
        self.execCommand("killall journalctl")
        self.running = False
        return self.running

    # Is Spotify running?
    def isRunning(self):
        return self.running

    # Simple execute command
    def execCommand(self,cmd):
        p = os.popen(cmd)
        return  p.readline().rstrip('\n')

    # Return playing title information
    def getInfo(self):
        tInfo =  self.translate.all(self.info)
        if tInfo == "''":
            tInfo = ""
        return tInfo

    def startJournalWatch(self):
        t = threading.Thread(target=self.followJournal)
        t.daemon = True
        t.start()

    # Follow the journal for raspotify.service
    def followJournal(self):
        f = subprocess.Popen(args, stdout=subprocess.PIPE)
        p = select.poll()
        p.register(f.stdout)

        while True:
            line = f.stdout.readline()
            line = (line.strip())
            line = line.lstrip().decode('utf-8')

            # Old format of journal
            if "INFO:librespot" in line:
                try:
                    elements = line.split('::') 
                    self.info = elements[1] 
                except:
                    pass    

            # New Buster format of journal
            elif "librespot_playback" in line:
                try:
                    x = line.split('::') 
                    y = x[1].split('<') 
                    elements = y[1].split('>') 
                    self.info = elements[0] 
                except:
                    pass    
# End of spotify class

### Test routine ###
if __name__ == "__main__":
    import time
    spotify = SpotifyReceiver()

    print("Starting Spotify")
    spotify = SpotifyReceiver()

    try:
        spotify.start()
        while True:
            print("Track:",spotify.getInfo())
            time.sleep(2)

    except KeyboardInterrupt:
        print("Stopping Spotify")
        spotify.stop()
        sys.exit(0)
# End of test

# set tabstop=4 shiftwidth=4 expandtab
# retab

