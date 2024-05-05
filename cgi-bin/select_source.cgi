#!/usr/bin/env python3
# Raspberry Pi Radio
# $Id: select_source.cgi,v 1.4 2023/11/08 09:43:19 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#      The authors shall not be liable for any loss or damage however caused.
#
# This CGI script sends UDP commands from the Web Interface to the radio daemon
#
import sys
import time
import datetime
import cgi
import subprocess
import socket
import errno

# Import config from radio directory
sys.path.insert(0,'/usr/share/radio')
from web_config_class import Configuration
config = Configuration()

CurrentTrackFile = "/var/lib/radiod/current_track"


udphost = 'localhost'   # Radio Listener UDP host default localhost
udpport = 5100          # Radio Listener UDP port number default 5100

# Execute system command
def exec_cmd(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    return output

# Send message data to radio program
def udpSend(data):
    global udpport
    global udphost

    try:
        clientsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        clientsocket.settimeout(3)
        data = data.encode('utf-8')
        clientsocket.sendto(data, (udphost, udpport))
        data = clientsocket.recv(100).strip()
        data = data.decode('utf-8')

    except socket.error as e:
        err = e.args[0]
        if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
                print ("<p/>IR remote udpSend no data")
        else:
            # Errors such as timeout
            print("<p/>Remote udpSend " + str(e))

    return data

# Load radio
def load_playlist(playlist):
    return udpSend("PLAYLIST:"+playlist)

# Load Airplay
def load_airplay():
    return udpSend("AIRPLAY")

# Load Spotify
def load_spotify():
    return udpSend("SPOTIFY")

# Main routine
if __name__ == '__main__':
    print("Content-type: text/html\r\n\r\n")
    print("<!DOCTYPE html>")

    # Get configuration
    udpport = config.getRemoteUdpPort()
    udphost = config.getRemoteUdpHost()

    # Create instance of FieldStorage
    form = cgi.FieldStorage()
    source = str(form.getvalue('source'))
    
    if source == "None":
        source = "_Radio"
    
    sourceStr = source.replace('_',' ')
    sourceStr = sourceStr.lstrip()
    sourceStr = sourceStr.capitalize()
    print("Source <b>%s</b> selected\n" % sourceStr)

    if source == "airplay":
        reply = load_airplay()
    elif source == "spotify":
        reply = load_spotify()
    else:
        reply = load_playlist(source)
    if len(reply) > 0:
        print ("<p>Remote server replied " + reply + "</p>")
    else:
        print ("<p>No reply from remote server</p>")

    sys.exit(0)

# End of CGI script
# set tabstop=4 shiftwidth=4 expandtab
# retab

