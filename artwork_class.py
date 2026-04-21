#!/usr/bin/env python3
#
# Raspberry Pi Radio - Album artwork extraction from current URL 
#
# $Id: artwork_class.py,v 1.30 2026/04/20 08:53:07 bob Exp $
#
# Authors : Bob Rathbone and Jeff (musicalic)
# Site    : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#       The authors shall not be liable for any loss or damage however caused.
#
# Staion and album artwork is provided by the Discogs database. See https://www.discogs.com/
# The Discogs API will be found at https://www.discogs.com/developers
# The Discogs database isn't perfect and sometimes the incorrect or no artwork will be displayed
# Note: The Bob Rathbone Computer Consultancy has no control over the Discogs database

import os
import sys
import requests
import subprocess
import urllib.parse
from io import BytesIO

# To get a new token see: https://www.discogs.com/developers/#page:authentication
# https://www.discogs.com/applications/edit/113086

#Request Token URL   https://api.discogs.com/oauth/request_token
#Authorize URL   https://www.discogs.com/oauth/authorize
#Access Token URL    https://api.discogs.com/oauth/access_token
# Example "https://api.discogs.com/database/search?q='Radio&nbsp;Caroline'&key=jVQGatBjapPdPYDyWRfksecret=ZrvMKBRaMaSRAGWODIbNELrNfEfxIwou"

BASE_URL = "https://api.discogs.com/database/search?type=all&q="
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

# Artwork handler class
class Artwork:

    discogs_key = "jVQGatBjapPdPYDyWRfk"
    discogs_password = "ZrvMKBRaMaSRAGWODIbNELrNfEfxIwou"
    
    image_file = "/var/lib/radiod/radio_image.jpg"
    no_image = "images/no_image.jpg" 
    log = None      # Logging object (See logit routine)

    def __init__(self,log=None,config=None): 
        if log != None:
            self.log = log

        if config != None:
            self.discogs_key = config.discogs_key
            self.discogs_password = config.discogs_password
            self.logit(self.discogs_key)
            self.logit(self.discogs_password)
        return

    # Log if available else print message
    def logit(self,text):
        if self.log == None:
            print(text)
        else:
            self.log.message(text,self.log.DEBUG)
                  
    def getCoverImageFromInfo(self,broadcast_info):
        coverImage = None 
        coverURL = self.getCoverURL(broadcast_info)
        if coverURL != '' and ':' in coverURL :
            coverImage = self.getCoverImageFromURL(coverURL)
        return coverImage

    # Get album information from MPD (MEDIA)
    def get_album_info(self,client):
        broadcast_info = ""
        try:
            currentsong = client.currentsong()
            artist = currentsong.get("artist")
            title = currentsong.get("title")
            album = currentsong.get("album")    # Not used
            if artist != None:
                broadcast_info = artist
            if title != None and artist != None:
                broadcast_info = broadcast_info + ' : ' + title
        except Exception as e:
            self.logit(e)
            print(e)
            broadcast_info = ""
            pass
        return broadcast_info

    # Get the broadcast info from the current radio station or track
    # If radio client not available then use subprocess.run 
    def get_broadcast_info(self,client=None):
        broadcast_info = ""
        if client == None:
            try:
                result = subprocess.run("mpc current", shell=True, capture_output=True, text=True)
                broadcast_info = result.stdout.strip()
            except Exception as e:
                self.logit(str(e))
        else:
            try:
                currentsong = client.currentsong()
                name = currentsong.get("name")
                if name == None:
                    name = ''
                title = currentsong.get("title")

                if title == None:
                    title = ''

                if name != '' and title != '':
                    broadcast_info = name + ': ' + title
                elif name == '':
                    broadcast_info = title
                else:
                    broadcast_info = name

            except Exception as e:
                self.logit(e)
                print(e)
                broadcast_info = ""
                pass
        return broadcast_info

    # Get cover artwork image from URL
    def getCoverImageFromURL(self,cover_url):
        coverImage = None
        try:
            # https://coderslegacy.com/python/load-image-from-web-url-pygame/
            response = requests.get(cover_url, headers=HEADERS)
            #response = requests.get('https://www.denofgeek.com/wp-content/uploads/2022/05/Leged-of-Zelda-Link.jpg')
            if response.status_code == 200:
                type = response.headers['content-type']
                coverImage = BytesIO(response.content)
            else:
                self.logit("ERROR: getCoverImageFromURL got error code" % response.status_code)
        except Exception as e:
            self.logit(e)
        return coverImage

    def getCoverURL(self,broadcast_info):
        # To get the art cover URL we are using the Discogs API
        cover_url = ""
        try:
            # try to extract the singer and the name of the song
            # print("Title:" ,broadcast_info)
            try:
                title = broadcast_info[broadcast_info.index(":")+1 :] 
            except:
                title = broadcast_info
            title = title.replace('-',' ')  # Remove - sign (causes lookup errors)
            title = title.replace('  ',' ')  # Remove double spaces
            title = urllib.parse.quote_plus(title)   # Convert spaces to + signs
            url = BASE_URL + title + "&key=" + self.discogs_key + "&secret=" + self.discogs_password

            # https://developer.mozilla.org/en-US/docs/Web/API/Response
            #response = requests.get(url, headers=HEADERS)  # Causes 403 error ?
            response = requests.get(url)
            type = response.headers['content-type']
            if type == 'application/json':
                data = response.json() # Python dictionary
                if len(data['results']) > 1:
                    # Extract the URL of the art cover image
                    cover_url = data['results'][0]['cover_image']
                    if not(isinstance(cover_url, str)):
                        cover_url = ""  
                    self.logit("Artwork %s" % cover_url)
        except Exception as e:
            self.logit(str(e))
        return cover_url 
    
    # Get artwork by name (eg. artist, station or track etc)
    # Example https://www.discogs.com/search?q=BBC1
    def getArtworkByName(self,name):
        coverImage = None 
        cover_url = ''
        name = urllib.parse.quote_plus(name)   # Convert spaces to + signs
        url = BASE_URL + name + "&key=" + self.discogs_key + "&secret=" + self.discogs_password
       
        try:
            #response = requests.get(url)
            response = requests.get(url, headers=HEADERS)  # Causes 403 error ?
            type = response.headers['content-type']
            if type == 'application/json':
                data = response.json() # Python dictionary
                if len(data['results']) > 1:
                    # Extract the URL of the art cover image
                    cover_url = data['results'][0]['cover_image']
                    if not(isinstance(cover_url, str)):
                        cover_url = ''
                    self.logit("Artwork %s" % cover_url)

            if cover_url != '':
                coverImage = self.getCoverImageFromURL(cover_url)

        except Exception as e:
            self.logit(str(e))
    
        return coverImage

    # Execute a system command
    def execCommand(cmd):
        p = os.popen(cmd)
        return  p.readline().rstrip('\n')

# End of Artwork class

### Main test routine ###
# Extracts the cover image url from station URL and writes it to a file

# Logging
if __name__ == "__main__":
    import time
    import shutil

    last_info = None
    artwork = Artwork(log=None)

    try:
        while True:
            broadcast_info = artwork.get_broadcast_info()
            img = artwork.getCoverImageFromInfo(broadcast_info)
            if img != None and broadcast_info != last_info:
                print(broadcast_info)
                f = open(artwork.image_file,"wb")
                f.write(img.getbuffer())
                f.close()
                print("Artwork wrote",artwork.image_file)
                last_info = broadcast_info 
            elif img == None:
                print("Artwork image not available")
                shutil.copyfile(artwork.no_image, artwork.image_file)
            time.sleep(5)

    except KeyboardInterrupt:
        print("Stopped")
        sys.exit(0)

# End of script
# set tabstop=4 shiftwidth=4 expandtab
# retab
