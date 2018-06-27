#!/usr/bin/python
# $Id: select_source.cgi,v 1.3 2018/03/23 09:40:04 bob Exp $
import shutil;
import sys;
import os;
import logging
import cgi
import time
import socket
import errno
from subprocess import call 

# Import modules for CGI handling 
import cgi, cgitb 

# Create instance of FieldStorage 
form = cgi.FieldStorage() 
source = str(form.getvalue('source'))

# Import config from radio directory
sys.path.insert(0,'/usr/share/radio')
from web_config_class import Configuration
config = Configuration()

CurrentTrackFile = "/var/lib/radiod/current_track"


udphost = 'localhost'   # Radio Listener UDP host default localhost
udpport = 5100          # Radio Listener UDP port number default 5100

# Send message data to radio program
def udpSend(data):
	global udpport
	global udphost
	log("Remote control daemon udpSend " + data)

	try:
		clientsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		clientsocket.settimeout(3)
		clientsocket.sendto(data, (udphost, udpport))
		data = clientsocket.recv(100).strip()

	except socket.error, e:
		err = e.args[0]
		if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
			print "<p>IR remote udpSend no data</p>"
		else:
			# Errors such as timeout
			log ("IR remote udpSend " + str(e))

	if len(data) > 0:
		log ("remote udpSend " + data)
	return data

def write_html_header():
    print "Content-type:text/html\r\n\r\n"
    print "<html>";
    print "<head>";
    print "<title>Radio web interface</title>";
    print "<META HTTP-EQUIV=\"Pragma\" CONTENT=\"no-cache\">";
    print "<META HTTP-EQUIV='refresh' CONTENT='2;URL=../snoopy.html'>"
    print "<link rel='stylesheet' type='text/css' href='/basic-noise.css' title='Basic Noise' media='all' />"
    print "</head>";
    print "<body>";
    return;

def write_html_footer():
    print "</body>";
    print "<head>";
    print "<META HTTP-EQUIV=\"Pragma\" CONTENT=\"no-cache\">";
    print "</head>";
    print "</html>";
    return;

# Execute system command
def exec_cmd(cmd):
	p = os.popen(cmd)
	result = p.readline().rstrip('\n')
	return result

# Load if new source selected
def load_media():
	udpSend("MEDIA")
	print "<h1>Loading media library</h1>"
	dirList=os.listdir("/var/lib/mpd/music")
	for fname in dirList:
		print "<h3>",fname,"</h3>"
	return

# Load radio
def load_radio():
	udpSend("RADIO")
	print "<h1>Loading radio stations</h1>"
	dirList=os.listdir("/var/lib/mpd/playlists")
	for fname in dirList:
		print "<h3>",fname,"</h3>"
	return

# Load Airplay
def load_airplay():
	udpSend("AIRPLAY")
	print "<h1>Loading Airplay</h1>"
	return

# Get the last ID stored in /var/lib/radiod
def get_stored_id():
        current_id = 1
        if os.path.isfile(CurrentTrackFile):
                current_id = int(exec_cmd("cat " + CurrentTrackFile) )
        return current_id

def log(message):
	sys.stderr.write(message + "\n")
	return

# Create HTML header
log("Radio select_source.cgi source=" + source)

# Get configuration
udpport = config.getRemoteUdpPort()
udphost = config.getRemoteUdpHost()


write_html_header();

if source == "radio":
	load_radio()
elif source == "media":
	load_media()
elif source == "airplay":
	load_airplay()
else:
	log ("Invalid source:" + source )

write_html_footer()
 
# End of script

