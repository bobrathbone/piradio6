#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Raspberry Pi Internet Radio podcast utility
# $Id: create_podcasts.py,v 1.2 2024/12/17 19:53:39 bob Exp $
#
# See Raspberry PI Radio constructors manual for instructions
#
# Author   : Bob Rathbone
# Web site : http://www.bobrathbone.com
#
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.
#

import os
import sys
import pdb
#import urllib2
import urllib.request, urllib.error, urllib.parse
import unicodedata

from xml.dom.minidom import parseString

# Output errors to STDERR
stderr = sys.stderr.write;

# File locations
PlsDirectory = '/var/lib/mpd/playlists/'
RadioLibDir = '/var/lib/radiod/'
PodList = RadioLibDir + 'podcasts'

# MPD won't load greater than 350 entries in a playlist
MAX_ENTRIES = 250   # Maximum amount of entries in a playlist

# Execute system command
def execCommand(cmd):
    p = os.popen(cmd)
    return  p.readline().rstrip('\n')

# Create the output from the title, URL, length and file number
def createPlsOutput(title,url,length,filenumber):
        output = []
        output.append('File%s=%s' % (filenumber,url))
        output.append('Title%s=%s' % (filenumber,title))
        output.append('Length%s=%s' % (filenumber,length))
        return output

# Create the PLS or M3U file
def createPlsFile(basename,output,nlines):
    global duplicateCount
    uniqueCount = 1

    # Limit very large playlists
    if nlines > MAX_ENTRIES:
        nlines = MAX_ENTRIES

        if len(basename) < 1:
                filename = 'unknown'
        plsfile = basename + '.pls'
        filename = PlsDirectory + plsfile

        try:
            print('Creating ' + filename)
            outfile = open(filename,'w')
            outfile.writelines("[playlist]\n")
            outfile.writelines("NumberOfEntries=%s\n"% nlines)
            outfile.writelines("Version=2\n")

            for item in output:
                outstr = item.encode('utf8', 'replace')
                outfile.write(outstr + "\n")
                outfile.close()

            # Load the new podcast into MPD
            print("Loading", plsfile + '\n')
            execCommand("mpc load " + plsfile)
        except:
            print("Failed to create",outfile)
        return

# Execute system command
def execCommand(cmd):
    p = os.popen(cmd)
    return  p.readline().rstrip('\n')


def parseXml(url,filename,data,count):
    global errorCount
    global warningCount
    output = []

    try:
        dom = parseString(data)
    except Exception as e:
        print("Error:",e)
        print("Error: Could not parse XML data from,", url + '\n')
        errorCount += 1
        return

    try:
        # Get all the items in the podcast
        items = dom.getElementsByTagName('item')
        filenumber = 0
        if count < 1:
            count = len(items)
        # Get the title and enclosure
        for node in items:
            filenumber += 1
            title = node.getElementsByTagName('title')[0].firstChild.nodeValue
            dtitle = title.encode('utf8', 'replace')
            print('Title',filenumber,dtitle)
            enclosure = node.getElementsByTagName('enclosure')[0]
            attributes = enclosure.attributes.items()
            url = dict(attributes).get('url') 
            length = dict(attributes).get('length') 
            type = dict(attributes).get('type') 
            durl = url.encode('utf8', 'replace')
            print(durl,length)
            output += createPlsOutput(title,url,length,filenumber)

            # Limit using count
            count -= 1
            if count < 1:
                break

            # Now create the file
            createPlsFile(filename,output,filenumber)

    except IndexError as e:
        print("Error:",e)
        print("Error parsing", url)
        errorCount += 1
        return "# DOM Error"

    return output

# Start of main routine
if __name__ == "__main__":
    if os.getuid() != 0:
        print("This program can only be run as root user or using sudo")
        sys.exit(1) 

    lineCount = 0      # Line being processed (Including comments)
    errorCount = 0    # Errors
    warningCount = 0    # Warnings
    processedCount = 0      # Processed station count
    data = ""

    # Set up playlist directory 
    if not os.path.exists(PlsDirectory):
        execCommand ("mkdir -p " + PlsDirectory )

    # Main processing loop
    for line in open(PodList,'r'):
        lineCount += 1
        lines = []

        # Skip commented out or blank lines
        line = line.rstrip()    # Remove line feed
        if line[:1] == '#':
            continue

        # Ignore blank lines
        if len(line) < 1: 
            continue

        # Check start of title defined
        elif line[:1] != '[':
            stderr("Error: Missing left bracket [ in line %s in %s\n" % (lineCount,StationList))
            format()
            errorCount += 1
            continue

        processedCount += 1
        line = line.lstrip('[')

        # Get title and URL parts
        line = line.strip()
        lineparts = line.split(']')

        # Should be 2 parts (title and url)
        if len(lineparts) != 2:
            stderr("Error: Missing right bracket [ in line %s in %s\n" % (lineCount,StationList))
            format()
            errorCount += 1
            continue

        # Get title and URL from station definition
        title = lineparts[0].lstrip()
        print(title)
        # Extract number of feeds if present
        if ':' in title:
            titleparts = title.split(':')
            title = titleparts[0]
            count = int(titleparts[1])
        else:
            count = 0   # Means get all streams

        # Get the URL
        url = lineparts[1].lstrip()

        # Get the published URL and determine its type
        print('Processing podcast ' + str(lineCount) + ': ' + url)

        # Get the published URL to the stream file
        try:
            request = urllib.request.Request(url)
            response = urllib.request.urlopen(request)
            data = response.read().decode('utf-8')
        except Exception as e:
            print("Error: Failed to retrieve ", url)
            print(str(e))
            errorCount += 1
            continue

    # Create list from data
    filename = title.replace(' ', '_') 
    parseXml(url,filename,data,count)

# End of script
# set tabstop=4 shiftwidth=4 expandtab
# retab
