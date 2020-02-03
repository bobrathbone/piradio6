#!/usr/bin/env python
#
# Diagnostic to Raspberry Pi Display current stream using MPD library
# $Id: display_current.py,v 1.2 2019/01/22 08:07:09 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program uses  Music Player Daemon 'mpd' and the python-mpd library
# Use "apt-get install python-mpd" to install the Python MPD library
# See http://mpd.wikia.com/wiki/Music_Player_Daemon_Wiki
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#             The authors shall not be liable for any loss or damage however caused.
#

import sys
from mpd import MPDClient
client = MPDClient()    # Create the MPD client

client.timeout = 10
client.idletimeout = None

try:
	client.connect("localhost", 6600)
except:
	print "Music player daemon not running!"
	print "Start radio (or MPD) and re-run program"
	sys.exit(1)

currentsong = client.currentsong()

print ""
if len(currentsong) > 0:
	for text in currentsong:
		print text + ": " + str(currentsong.get(text))

	current_id = int(currentsong.get("pos")) + 1
	print "current_id", current_id
else:
	print "No current song"

print ""
print "Status"
status = client.status()
for text in status:
	print text + ": " + str(status.get(text))

print ""
stats = client.stats()
for text in stats:
	print text + ": " + str(stats.get(text))

print "Bit rate", status.get('bitrate')

# End of program


