#!/usr/bin/env python
# $Id: shoutcast.cgi,v 1.4 2018/03/23 09:50:05 bob Exp $
import shutil;
import sys;
import os;
import subprocess
import logging
import cgi
import pwd
import time
import socket
import getpass
import errno
from subprocess import call 

# Import modules for CGI handling 
import cgi, cgitb 

# Create instance of FieldStorage 
form = cgi.FieldStorage() 
search = str(form.getvalue('search'))
value = str(form.getvalue('value'))
limit = str(form.getvalue('Limit'))
if limit == 'None':
	limit = str(10)
if value == 'None':
	value = ''

# Import config from radio directory
radio_dir = '/usr/share/radio'
sys.path.insert(0,radio_dir)

def write_html_header():
    print "Content-type:text/html\r\n\r\n"
    print "<html>";
    print "<head>";
    print "<title>Create shoutcast playlist</title>";
    print "<META HTTP-EQUIV=\"Pragma\" CONTENT=\"no-cache\">";
    print "<META HTTP-EQUIV='refresh' CONTENT='20;URL=../snoopy.html'>"
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
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        (output, err) = p.communicate()
        return output

def log(message):
	sys.stderr.write(message + "\n")
	return

# Create HTML header

write_html_header();

search = search.lower()
value = value.lower()

print "<h2>Create shoutcast playlist </h2>"
print "<h3>Search type: " + search + "</h3>"
print "<h3>Limit: " + limit + "</h3>"
print "<h3>Search string:" + value + "</h3>"

if search == "stationsearch":
	searchcmd = " search=" + value
elif search == "genresearch": 
	searchcmd = " genre=" + value
else:
	searchcmd = "" 	# Top500 is the default

cmd = "sudo " + radio_dir + "/get_shoutcast.py install " + searchcmd + " limit=" + limit
print "<h3>" + cmd + "</h3>"
log("Radio shoutcast.cgi command: " + cmd)


# Create the playlist
result = exec_cmd(cmd)
lines = result.split('\n')

leng = len(lines)
print "<h3>"
print "<br/>" + lines[0]
print "<br/>" + lines[1]
print "<br/>" + lines[leng-3]
print "<br/>" + lines[leng-2]
print "</h3>"
print "<h3>You can now load new playlist into the radio</h3>"

print "<form>"
print "<p style=\"margin-left:20px;\">&nbsp;<input type=\"button\" value=\"Go back\" onclick=\"history.back()\"></p>"
print "</form>"

write_html_footer()
 
# End of script

