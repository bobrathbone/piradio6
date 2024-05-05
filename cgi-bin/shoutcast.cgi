#!/usr/bin/env python3
# Raspberry Pi Radio
# $Id: shoutcast.cgi,v 1.3 2023/01/02 17:57:37 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#      The authors shall not be liable for any loss or damage however caused.
#
# This CGI script sends Shoutcast commands from the Web Interface to the radio daemon
# 

import sys
import time
import datetime
import cgi
import subprocess

# Execute system command
def exec_cmd(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
    (output, err) = p.communicate()
    return output

# Main routine
if __name__ == '__main__':
    print("Content-type: text/html\r\n\r\n")

    # Create instance of FieldStorage
    form = cgi.FieldStorage()
    type = str(form.getvalue('type')).lower()
    limit = str(form.getvalue('limit'))
    value = str(form.getvalue('value')).lower()
    value = value.replace(' ','+')

    if type == "stationsearch":
        searchcmd = " search=" + value
    elif type == "genresearch":
        searchcmd = " genre=" + value
    else:
        searchcmd = ""  # Top500 is the default

    # Set default limit
    if limit == 'None':
        limit = str(10)
    if value == 'None':
        value = ''

    # Import config from radio directory
    radio_dir = '/usr/share/radio'
    sys.path.insert(0,radio_dir)

    cmd = "sudo " + radio_dir + "/get_shoutcast.py install " + searchcmd + " limit=" + limit
    print ("<br/>" + cmd)

    # Call the program
    result = exec_cmd(cmd)
    result = result.decode("utf-8")
    lines = result.split('\n')

    leng = len(lines)
    print ("<br/>" + lines[0])
    print ("<br/>" + lines[1])
    print ("<br/>" + lines[leng-3])
    print ("<br/>" + lines[leng-2])
    print ("<br/>You can now load new playlist into the radio")

    sys.exit(0)

# End of CGI script
# set tabstop=4 shiftwidth=4 expandtab
# retab

