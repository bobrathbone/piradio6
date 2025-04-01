#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Raspberry Pi Internet Radio playlist utility
# $Id: create_stations.py,v 1.28 2025/03/12 11:56:01 bob Exp $
#
# Create playlist files from the following url formats
#    iPhone stream files (.asx)
#    Playlist files (.pls)
#    Extended M3U files (.m3u)
#    HLS M3U8 files (.m3u8)
#    Direct media streams (no extension)
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
#         The authors shall not be liable for any loss or damage however caused.
#

import os,sys
import re
import pdb
import glob
import urllib.request, urllib.error, urllib.parse
import socket
from time import strftime
from xml.dom.minidom import parseString
from config_class import Configuration
from source_class import Source

# Output errors to STDERR
stderr = sys.stderr.write;

# File locations
PlsDirectory = '/var/lib/mpd/playlists/'
RadioDir = '/usr/share/radio/'
RadioLibDir = '/var/lib/radiod/'
StationList = RadioLibDir + 'stationlist'
DistFile =  RadioDir + 'station.urls'
TempDir = '/tmp/radio_stream_files/'
PlaylistsDir = RadioDir + 'playlists/'
config = Configuration()
ErrorUrls = []

duplicateCount = 0
TimeOut=20    # Socket time out
errorCount = 0

# Source types (There are 2 source types: Radio and Media)
RADIO = 0   # Radio usually has one playlist but can have more
MEDIA = 1   # Media can have one or more playlists with any name

# Execute system command
def execCommand(cmd):
    p = os.popen(cmd)
    return  p.readline().rstrip('\n')

# Create the initial list of files
def createList():
    if not os.path.isfile(StationList):
        print('\nCreating ' + StationList + '\n')
        execCommand ("mkdir -p " + RadioLibDir )
        print("cp " + DistFile + ' ' + StationList )
        execCommand ("cp " + DistFile + ' ' + StationList)
        print() 
    return

# Create M3U output from the title and URL
def createM3uOutput(title,url):
    lines = []    
    title = title.rstrip()
    url = url.rstrip()
    #url = url.split('#')[0] # Remove #<station name> 
    lines.append('#EXTM3U')
    lines.append('#EXTINF:-1,%s' % title)
    #lines.append(url + '#' + title) # No longer required
    lines.append(url)
    return lines

# Create M3U  playlist file
def createM3uFile(filename,output,nlines):
    global duplicateCount
    uniqueCount = 1
    if len(filename) < 1:
        filename = 'Radio'

    # Old radio playlists began with '_' (Underscore) 
    ##outfile = TempDir + '_' + filename + '.m3u' 
    outfile = TempDir + filename + '.m3u' 

    # Create unique files
    exists = True
    while exists:
        if os.path.exists(outfile):
            print("Warning: " + outfile + ' already exists')
            outfile = TempDir + filename + '[' + str(uniqueCount) + '].m3u'
            uniqueCount += 1
            duplicateCount += 1
        else:
            exists = False

    try:
        print('\nWriting ' + outfile + '\n')
        outfile = open(outfile,'w')
        for item in output:
            outfile.write(item + "\n")

        outfile.close()
    except Exception as e:
        print(str(e))
        print("Failed to create " + outfile)
    return

# Beautify HTML convert tags to lower case
def parseHTML(data):
    lcdata = ''
    for line in data:
        lcline = ''
        line = line.rstrip()
        line = line.lstrip()
        line.replace('href =', 'href=')
        length = len(line)

        if length < 1:
            continue
        tag1right = line.find('>')

        if tag1right > 1:
            start_tag = line[0:tag1right+1]
            lcline = lcline + start_tag.lower()

        tag2left = line.find('<', tag1right+1)

        if tag2left > 1:
            end_tag = line[tag2left:length]
            parameter = line[tag1right+1:tag2left]
            lcline = lcline + parameter + end_tag.lower()
        lcdata = lcdata + lcline
    return lcdata

# Get XML/HTML parameter
def getParameter(line):
    tag1right = line.find('>')
    tag2left = line.find('<', tag1right+1)
    parameter = line[tag1right+1:tag2left]
    return parameter


# Create a M3U file from an ASX(XML) file
def parseAsx(title,url,data,filenumber):
    global errorCount
    global warningCount
    global ErrorUrls

    output = ""
    lcdata = parseHTML(data)

    try:
        dom = parseString(lcdata)
    except Exception as e:
        errorCount += 1
        msg = "Error:" + e
        ErrorUrls.append(msg)
        print("ERROR: " +  msg)
        msg = "Could not parse XML data from,", url + '\n'
        print("ERROR: " +  msg)
        ErrorUrls.append(msg)
        return

    try:
        # If title undefined in the station list get it from the file
        if len(title) < 1:
            titleTag = dom.getElementsByTagName('title')[0].toxml()
            title = getParameter(titleTag)

    except:
        print("Warning: Title not found in " + url)
        pass

    finally:
        try:
            urlTag = dom.getElementsByTagName('ref')[0].toxml()
            url = urlTag.replace('<ref href=\"','').replace('\"/>','')
            urls = url.split('?')
            url = urls[0]
            title = title.rstrip()
            url = url.rstrip()
            print("Title: " + title)
            m3ufile = title.replace(' ','_')

            if checkStream(plsurl,lineCount):
                m3ufile = title.replace(' ','_')
                output = createM3uOutput(title,url)
            else:
                output = ""
        except IndexError as e:
            errorCount += 1
            msg = "Error:" + e
            ErrorUrls.append(msg)
            print("ERROR: " +  msg)
            msg = "Could not parse XML data from,", url + '\n'
            print("ERROR: " +  msg)
            ErrorUrls.append(msg)
            return "# DOM Error" 

    return output

# Create filename from URL
def createFileName(title,url):
    if len(title) > 0:
        name = title
        name = name.replace('.',' ')
        name = name.replace(' ','_')
    else:
        try:
            urlparts = url.rsplit('/',1)
            site = urlparts[0]
            siteparts = site.split('/')
            name = siteparts[2]
            siteparts = name.split(':')
            name = siteparts[0]
        except:
            name = url
        name = name.replace('www.','')
        name = name.replace('.com','')
        name = name.replace('.','_')

    name = name.replace('__','_')
    return name

# Create default title 
def createTitle(url):
    urlparts = url.rsplit('/',1)
    site = urlparts[0]
    siteparts = site.split('/')
    name = siteparts[2]
    siteparts = name.split(':')
    title = siteparts[0]
    return title

# Direct radio stream (MP3 AAC etc)
def parseDirect(title,url,filenumber):
    url = url.replace('(stream)', '')
    if len(title) < 1:
        title = createTitle(url)
    print("Title: " + title)
    output = createM3uOutput(title,url)
    return output

# Identify playlist type RADIO or MEDIA by file contents
def getPlaylistType(playlist_name):
    playlist_type = MEDIA
    playlist_file = PlsDirectory + '/' + playlist_name 
    typeNames = ['RADIO','MEDIA']

    # Check playlist for "#EXTM3U" definition
    count = 10  # Allow comments 10 lines max at start of file
    found = False
    try:
        f = open(playlist_file, 'r')
        while count > 0 and not found:
            line = f.readline()
            line = line.rstrip()
            if line.startswith("#EXTM3U"):
                found = True
                playlist_type = RADIO
            count -= 1
        f.close()

    except Exception as e:
        msg = "getPlaylistType:" + str(e)
        print(msg)

    #print("Processing",playlist_file,typeNames[playlist_type])
    return playlist_type

# Create M3U file from PLS in the temporary directory
def parsePls(title,url,lines,filenumber):
    plstitle = ''
    plsurl = ''

    for line in lines:
        if line.startswith('Title1='):
            titleline =  line.split('=')
            plstitle = titleline[1]
        
        if line.startswith('File1='):
            fileline =  line.split('=')
            plsurl = fileline[1]

    # If title undefined in the station list get it from the file
    if len(title) < 1:
        if  len(plstitle) > 1:
            title = plstitle
        else: 
            title = createTitle(url)
            m3ufile = createFileName(title,url)

    print("Title: " + title)
    if checkStream(plsurl,lineCount):
        m3ufile = title.replace(' ','_')
        output = createM3uOutput(title,plsurl)
    else:
        output = ""
    return output

# Parse M3U file to PLS output
def parseM3u(title,url,lines,filenumber):
    global lineCount
    info = 'Unknown' 
    output = []
    
    for line in lines:
        line = line.replace('\r','')
        line = line.replace('\n','')

        # Skip UDP protocol (Not supported)
        if line.startswith('udp:'):
            next

        # Save stream URL
        if line.startswith('http:'):
            url = line

        elif line.startswith('#EXTINF:'):
            info = line
            
    if len(title) < 1:
        title = info
    
    if len(title) < 1:
        filename = createFileName(title,url)
    else:
        filename = title.replace(' ','_')

    print("Title: " + title)
    if checkStream(url,lineCount):
        output.append('#EXTM3U')
        output.append('#EXTINF:-1,%s'% title)
        output.append('%s#%s'% (url,title))
    else:
        output = ''    
    return output

# Usage message 
def usage():
    stderr("\nUsage: sudo %s [--delete_old] [--no_delete] [--input_file=<input file>] [--help]\n" % sys.argv[0])
    stderr("\tWhere: --delete_old   Delete old playlists\n")
    stderr("\t       --force        Force update of MPD playlists\n")
    stderr("\t       --no_delete    Don't delete old playlists\n")
    stderr("\t       --input_file=<input_file>  Use alternative input file\n")
    stderr("\t       --help     Display help message\n\n")
    return

# Station definition help message
def format():
    stderr ("Start a playlist with the name between brackets. For example:\n")
    stderr ("(BBC Radio Stations)\n")
    stderr ("This will create a radio playlist called _BBC_Radio_Stations.m3u\n")
    stderr ("\nThe above is followed by station definitions which take the following format:\n")
    stderr ("\t[title] http://<url>\n")
    stderr ("\tExample:\n")
    stderr ("\t[BBC Radio 3] http://bbc.co.uk/radio/listen/live/r3.asx\n\n")
    return

# Timeout alarm
def handler(signum, frame):
    raise IOError("The page is taking too long to read")

# Check if Embedded stream is OK
def checkStream(url,lineCount):
    global errorCount
    success = False
    # Get the stream file
    try:
        socket.setdefaulttimeout(TimeOut)
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req)
        data = response.read(50) # Just read 50 bytes
        success = True
    except:
        errorCount += 1
        msg = "Failed to retrieve [" +title + "] " + url + " on line " + str(lineCount)
        print("ERROR: "+ msg)
        ErrorUrls.append(msg)
    return success

# Start of MAIN script

if os.getuid() != 0:
    print ("This program can only be run as root user or using sudo")
    usage()
    sys.exit(1)

deleteOld =  False
noDelete  =  False
forceUpdate = False

if len(sys.argv) > 1:
    for i in range(1,len(sys.argv)):
        param = sys.argv[i]
        if param == '--delete_old':
            deleteOld  = True

        elif param == '--force':
            forceUpdate  = True

        elif param == '--no_delete':
            noDelete  = True

        elif param.find('--input_file=') != -1:
            arry = param.split('=')
            StationList=(arry[1])

        elif param == '--help':
            usage()
            format()
            sys.exit(0)
        else:
            stderr("Invalid parameter %s\n" % param)
            usage()
            sys.exit(1)

# Create station URL list
createList()

# Temporary directory - if it exists then delete all pls files from it
execCommand ("mkdir -p " + TempDir )
execCommand ("rm -f " + TempDir + '*' )

# Open the list of URLs 
timedate = strftime("%Y/%m/%d, %H:%M:%S")
print("Creating M3U files from " + StationList + ' ' + timedate + '\n')

lineCount = 0        # Line being processed (Including comments)
errorCount = 0        # Errors
duplicateCount = 0    # Duplicate file names
warningCount = 0    # Warnings
processedCount = 0    # Processed station count

# Copy user stream files to temporary directory 

if os.path.exists(PlaylistsDir + '*.m3u'):
    print("Copying user M3U files from " + PlaylistsDir + " to " + TempDir + '\n')
    execCommand ("cp -f " +  PlaylistsDir + '*.m3u ' + TempDir )

# Playlist file name
filename = ''
m3u_output = []
filenumber = 1
writeFile = False
url = ''

# Remove any old temp files
execCommand ("rm -f " + TempDir + "/*.m3u" )

# Main processing loop
for line in open(StationList,'r'):
    lineCount += 1
    lines = []
    newplaylist = ''

    # Set url types to False
    isASX = False
    isM3U = False
    isPLS = False
    isAAC = False

    # Skip commented out or blank lines
    line = line.rstrip()    # Remove line feed
    if line[:1] == '#' or len(line[:1]) < 1:
        continue

    # Handle playlist definition in () brackets
    elif line[:1] == '(':
        newplaylist = line.strip('(')       # Remove left bracket
        newplaylist = newplaylist.strip(')') # Remove right  bracket
        playlistname = newplaylist
        newplaylist = newplaylist.replace(' ', '_')

        if len(filename) > 0:
            writeFile = True
        else:
            msg = 'Creating new playlist ' + playlistname
            print(msg)
            print('=' * len(msg))
            filename = newplaylist
            filenumber = 1
            continue

    if len(line) < 1 or writeFile:
        if len(filename) < 1 and len(url) > 0:
            filename = createFileName(title,url)
        if len(filename) > 0 and len(m3u_output) > 0:
            createM3uFile(filename,m3u_output,filenumber-1)
            filenumber = 1
            m3u_output = []
            filename = ''
            url = ''

        if len(newplaylist) > 0:
            filename = newplaylist    
            msg = 'Creating new playlist ' + newplaylist
            print(msg)
            print('=' * len(msg))
            continue

        if writeFile and len(line) > 0:
            writeFile = False
        else:
            continue

    processedCount += 1

    # Check start of title defined
    if line[:1] != '[':
        stderr("ERROR: Missing left bracket [ in line %s in %s\n" % (lineCount,StationList))
        format()
        errorCount += 1
        msg = "Missing left bracket [ in line %s" % lineCount
        print("ERROR: " + msg)
        ErrorUrls.append(msg)
        continue

    line = line.lstrip('[')

    # Get title and URL parts
    line = line.strip()
    lineparts = line.split(']')

    # Should be 2 parts (title and url)
    if len(lineparts) != 2:
        stderr("ERROR: Missing right bracket [ in line %s in %s\n" % (lineCount,StationList))
        format()
        errorCount += 1
        msg = "Missing right bracket ] in line %s" % lineCount
        print("ERROR: " + msg)
        ErrorUrls.append(msg)
        continue

    # Get title and URL from station definition
    title = lineparts[0].lstrip()
    url = lineparts[1].lstrip()

    # Get the published URL and determine its type
    print ('')
    print('Processing line ' + str(lineCount) + ': ' + url)

    # Extended M3U (MPEG 3 URL) 
    if url.endswith('.m3u'):
        isM3U = True

    # Advanced Stream Redirector (ASX)
    elif url.endswith('.asx') or '.asx?' in url:
        isASX = True

    # Playlist format
    elif url.endswith('.pls') or '.pls?' in url:
        isPLS = True

    # Advanced Audio Coding stream (Don't retrieve any URL)
    else:
        # Remove redundant (stream) parameter 
        isAAC = True
        try:
            url = url.replace('(stream)', '')
            code = urllib.request.urlopen(url).getcode()

            iCode = int(code)
            if int(code) != 200:
                errorCount += 1
                msg = "Remote server returned error code " + iCode + " on line " + str(lineCount)
                print("ERROR: " + msg)
                ErrorUrls.append(msg)
                continue

            if len(filename) < 1:
                filename = createFileName(title,url)
                writeFile = True
            filenumber += 1
            m3u_output += parseDirect(title,url,filenumber)

        except:
            errorCount += 1
            msg = "Failed to retrieve [" +title + "] " + url + " on line " + str(lineCount)
            print("ERROR: " + msg)
            ErrorUrls.append(msg)
        continue

    # Get the published URL to the stream file
    try:
        socket.setdefaulttimeout(TimeOut)
        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req)
        data = response.read()
        # Create list from data
        data = data.decode('utf-8') # data should be bytes
        lines = data.split('\n')
        firstline = lines[0].rstrip()
    except Exception as e:
        errorCount += 1
        msg = "Failed to retrieve [" +title + "] " + url + " on line " + str(lineCount)
        print("ERROR: " + msg)
        print("...." + str(e))
        ErrorUrls.append(msg)
        continue

    # process lines according to URL type
    if isPLS:
        m3u_output += parsePls(title,url,lines,filenumber)
        if len(m3u_output) < 1:
            continue

    elif isM3U:
        m3u_output += parseM3u(title,url,lines,filenumber)
        if len(m3u_output) < 1:
            continue

    elif isASX:
        if firstline.startswith('<ASX'):
            m3u_output += parseAsx(title,url,lines,filenumber)
            if len(m3u_output) < 1:
                continue
        else:
            print(url,"didn't return XML data")
            continue

    if len(filename) < 1:
        filename = createFileName(title,url)
        writeFile = True

    filenumber += 1

# End of for line 

# Write last file
if len(filename) < 1:
    filename = createFileName(title,url)
if len(filename) > 0 and len(m3u_output) > 0:
    createM3uFile(filename,m3u_output,filenumber-1)
    
print("Processed %s station URLs from %s" % (processedCount,StationList))

# Copy files from temporary directory to playlist directory
oldfiles = glob.glob(PlsDirectory + '/*.m3u')
nOld = len(oldfiles)
if nOld > 0:
    if not deleteOld and not noDelete:
        stderr("There are %s old radio playlist files in the %s directory.\n" \
             % (nOld,PlsDirectory))
        answer = input("Do you wish to remove the old radio playlists y/n: ")
        if answer == 'y':
            deleteOld = True

    if deleteOld:
        stderr ("\nRemoving %s old Radio playlists from directory %s\n"\
             % (nOld,PlsDirectory))

        for filename in os.listdir(PlsDirectory):
            playlist = os.path.join(PlsDirectory, filename)
            # checking if it is a file
            if os.path.isfile(playlist):
                type = getPlaylistType(filename)
                if type is RADIO:
                    cmd = "rm -f " + playlist
                    execCommand (cmd)
                    print("Removed playlist", playlist)
    else:
        print ("Old playlist files not removed")

# Copy new playlist(s) to MPD playlists directory
copiedCount = len(os.listdir(TempDir))
print("\nCopying %s new playlist file(s) to directory %s" % (copiedCount,PlsDirectory))

# List new playlists
for file in os.listdir(TempDir):
    print (file, "copied")
execCommand ("cp -f " + TempDir + '* ' + PlsDirectory )

# Create summary report
print("\nNew radio playlist file will be found in " + PlsDirectory)

if errorCount > 0:
    print(str(errorCount) + " error(s)")
    for line in ErrorUrls:
        print('\t' + line)
else:
    print("No errors found")

if duplicateCount > 0:
    print(str(duplicateCount) + " duplicate file name(s) found and renamed.")

warningCount += duplicateCount
if warningCount > 0:
    print(str(warningCount) + " warning(s)")

# End of script

# set tabstop=4 shiftwidth=4 expandtab
# retab
