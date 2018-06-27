#!/usr/bin/env python
#
# Raspberry Pi Spotify receiver Class
# $Id: spotify_class.py,v 1.6 2018/06/02 07:15:52 bob Exp $
#
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#	    The authors shall not be liable for any loss or damage however caused.
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

	def __init__(self):
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
		return self.info

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
			line = line.lstrip()
			if "INFO:librespot" in line:
				elements = line.split('::') 
				try:
					self.info = elements[1]	
				except:
					pass
			
# End of spotify class

### Test routine ###
if __name__ == "__main__":
	import time
	spotify = SpotifyReceiver()

	print "Starting Spotify"
	spotify = SpotifyReceiver()

	try:
		spotify.start()
		while True:
			print "Info",spotify.getInfo()
			time.sleep(2)

	except KeyboardInterrupt:
		print "Stopping Spotify"
		spotify.stop()
		sys.exit(0)
# End of test
