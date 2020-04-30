#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# Raspberry Pi Internet Radio Menu Class
# $Id: get_shoutcast.py,v 1.24 2020/02/13 15:49:26 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program creates a playlist from the shoutcast top 500
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#	    The authors shall not be liable for any loss or damage however caused.
#
# See http://wiki.shoutcast.com/wiki/SHOUTcast_Radio_Directory_API

import xml.etree.ElementTree as ET
import requests
import urllib2
import os,sys,pwd
import socket
import errno
import pdb
from shutil import copy
from translate_class import Translate
from config_class import Configuration

translate = Translate()
config = Configuration()

# Search parameters
limit = 100			# Search limit
search_type = "Top500" 		# Search type   
search_value = 'country'	# Search parameter
shoutcast_key = "anCLSEDQODrElkxl"	# Shoutcast authorisation key (Must be valid)

# Used to signal radio to reload playlists
udphost = 'localhost'   # UDP Listener host default localhost
udpport = 5100	  # UDP Listener port number default 5100

# Shoutcast URLs and files ( The %s strings are replaced by search parameters)
# See http://wiki.shoutcast.com/wiki/SHOUTcast_Radio_Directory_API

# XML Request
xml_url = "http://api.shoutcast.com/legacy/%s?k=%s&limit=%s&f=xml"

pls_url = "http://yp.shoutcast.com%s?id=%s"
playlist_dir = "/var/lib/mpd/playlists"
playlist_store = "/usr/share/radio/playlists"

xml_file = "/tmp/%s.xml"
m3u_playlist = playlist_store + "/_%s.m3u"

# Create a playlist directory
def create_dir(directory):
	try:
		if not os.path.exists(directory):
			os.makedirs(directory)
	except OSError as e:
		print e
		sys.exit(1)
	return

# Get the XML file from shoutcast and save it
def getXML(xml_url,xml_file):
	response = urllib2.urlopen(xml_url)
	webContent = response.read()

	fp = open(xml_file, "w")
	for line in webContent:
		fp.write(line)
	fp.close()
	return

# Parse the XML file to extract the data to playlist
def parseXML(xml_file,pls_url,m3u_playlist):
	name = ''
	base = ''
	id = ''
	myxml = ET.parse(xml_file)
	count=0

	# there are three different base URLs - we only use the pls one
	for atype in myxml.findall('tunein'):
		base = (atype.get('base'))
		base_m3u = (atype.get('base-m3u'))	# Not used at present
		base_xspf = (atype.get('base-xspf'))	#  "    "  "     "
	for atype in myxml.findall('station'):
		try:
			# Need to encode 
			name = (atype.get('name')).encode('utf-8').strip()
		except Exception as e:
			print "Error:", e
		id = (atype.get('id'))
		pls_url_s = pls_url % (base,id)
		station_title = getStationUrl(pls_url_s,m3u_playlist)
		count += 1
	return count

# Get the station url
def getStationUrl(pls_url,m3u_playlist):
	print "Station Url:", pls_url
	url = ''
	title = ''
	m3u = []
	response = urllib2.urlopen(pls_url)
	pls = response.read()
	lines = pls.splitlines()
	for line in lines:
		try:
			if line.startswith('File'):
				x,url = line.split('=')

			elif line.startswith('Title'):
				line = translate.all(line)
				x = line.split('=')
				title = x[1]
				title = parseTitle(title)
				m3u.append('#EXTM3U')
				m3u.append('#EXTINF:-1,' + title)
				m3u.append(url + '#' + title)
				appendPlaylist(m3u_playlist,m3u)
				break
		except Exception as e:
			print "Failed to process line: " + line
			print str(e)
	return title

# Parse title of superfluous characters
def parseTitle(title):
	if title.startswith('(#'):
		x = title.split(')')
		title = x[1]
	if '|' in title:
		x = title.split('|')
		title = x[0]
	if '-' in title:
		x = title.split('-')
		title = x[0]
	if '(' in title:
		x = title.split('(')
		title = x[0]
	if '/' in title:
		x = title.split('/')
		title = x[0]
	title = title.replace('..','')
	title = title.replace(':','')
	title = title.replace('*','')
	title = title.replace('"','')
	title = title.replace('!','')
	title = title.replace('#',' ')
	title = title.lstrip()
	title = title.rstrip()
	title = capitalize(title) 
	if len(title) < 1:
		title = "Unknown"
	return title

# Capitalize first letter
def capitalize(line):
	line = line.lower()	
	return ' '.join(s[:1].upper() + s[1:] for s in line.split(' '))

# Append a new M3U entry to the playlist
def appendPlaylist(m3u_playlist,m3u):
	fp = open(m3u_playlist, "a")
	for entry in m3u:
		fp.write(entry + '\n')
	fp.close()
	return

# Copy temporary playlist file MPD playlist directory
def copyPlaylist(m3u_playlist,count,install):
	print "Created",count,"records in",m3u_playlist
	choice = ''

	# Convert to radio naming convention

	if not install:
		prompt = "Do you wish to copy this playlist to " + playlist_dir + " [y/n]: "
		while choice == '':
			choice = raw_input(prompt)
			if choice == 'y':
				install = True
	if install:
		try:
			copy(m3u_playlist,playlist_dir)
			print "Copied", m3u_playlist, "to", playlist_dir
			udpSend('RELOAD_PLAYLISTS')
		except Exception as e:
			print str(e)
	return

# Send button data to radio program
def udpSend(command):
	global udpport
	global udphost
	data = ''

	try:
		clientsocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		clientsocket.settimeout(3)
		clientsocket.sendto(command, (udphost, udpport))
		data = clientsocket.recv(100).strip()
		clientsocket.close()

	except socket.error, e:
		err = e.args[0]
		if err == errno.EAGAIN or err == errno.EWOULDBLOCK:
			print "udpSend no data: " + str(e)
		else:
			# Errors such as timeout
			print "udpSend: " + str(e)

	if len(data) > 0:
		print "Reload playlists: " + data
	return data

# Usage
def usage(prog):
	print "\nUsage: sudo %s id=<id> limit=<limit> search=\"<string>\"|genre=\"<genre>\" install " % prog
	print "\tWhere:\t<id> is a valid shoutcast ID."
	print "\t\t<limit> is the maximum stations that will be returned (default 100)."
	print "\t\t<string> is the string to search the shoutcast database."
	print "\t\t<genre> is the genre search string."
	print "\t\tinstall - Install playlist to MPD without prompting."
	print "\n\tSee http://www.shoutcast.com for availble genres.\n"
	return

# Main routine
if __name__ == "__main__":
	install = False  # Copy parameter
	create_dir(playlist_store)

	shoutcast_key = config.getShoutcastKey()
	udpport = config.getRemoteUdpPort()
	udphost = config.getRemoteUdpHost()
	print "Shoutcast UDP connect host " + udphost + " port " + str(udpport)

	# Check if running as root (sudo)
	if pwd.getpwuid(os.geteuid()).pw_uid > 0:
		print "This program must be run with sudo or root permissions!"
		usage(sys.argv[0])
		sys.exit(1)

	# Process command line parameters
	genre_specified = False
	search_specified = False
	for arg in sys.argv: 	
		if arg == sys.argv[0]:
			continue

		elif arg == 'install':
			install = True

		elif '=' in arg:
			x = arg.split('=')
			param = x[0]
			value = x[1]
			if param == 'key':
				shoutcast_key = value
			elif param == 'limit':
				limit = str(value)
			elif param == 'search':
				search_type = 'stationsearch'
				search_value = value
				search_specified = True
			elif param == 'genre':
				search_type = 'genresearch'
				search_value = value
				genre_specified = True
		elif arg == '-h' or arg == 'help' or arg == '--help':
			usage(sys.argv[0])
			sys.exit(0)
	
		else :
			print "Invalid parameter:",arg
			usage(sys.argv[0])

	if genre_specified and search_specified:
		print "Error: You cannot specify genre and search together" 
		usage(sys.argv[0])
		sys.exit(1)

	# Replace special characters.
	search_value = search_value.replace(' ','+')
	search_value = search_value.replace('&','%26')

	print "Extracting shoutcast stations:", search_type
	xml_url = xml_url % (search_type,shoutcast_key,limit) 

	if search_type == 'stationsearch' or search_type == 'genresearch':
		fname = search_value.replace(' ','_')
		xml_file_s = xml_file % fname
		m3u_playlist_s = m3u_playlist % fname

		if search_type == 'stationsearch':
			xml_url = xml_url + '&search=' + search_value
		elif search_type == 'genresearch':
			xml_url = xml_url + '&genre=' + search_value
	else:
		xml_file_s = xml_file % search_type
		m3u_playlist_s = m3u_playlist % search_type

	m3u_playlist_s = m3u_playlist_s.replace('+','_') 
	print "Processing URL:",xml_url
	
	try:
		open(m3u_playlist_s,'w').close()
		getXML(xml_url,xml_file_s)
		count = parseXML(xml_file_s,pls_url,m3u_playlist_s)

		if count > 0:
			copyPlaylist(m3u_playlist_s,count,install)
		else:
			print "No stations found for search: " + search_value

	except KeyboardInterrupt:
		print "\nInterrupted by user. Exiting."

	except Exception as e:
		print str(e)

	sys.exit(0)

# End of main routine
