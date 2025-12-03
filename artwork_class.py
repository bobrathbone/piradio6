#!/usr/bin/env python3
#
# Raspberry Pi Radio - Album artwork extraction from current URL 
#
# $Id: artwork_class.py,v 1.20 2025/12/03 07:15:21 bob Exp $
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

import sys
import requests
import subprocess
import urllib.parse
from io import BytesIO

API_DISCOGS_TOKEN = "SkLpyuNUuVTglclfwrvdBuxiucbjCFwMaXKLsAOg"
BASE_URL = "https://api.discogs.com/database/search?q="
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}

# Artwork handler class
class Artwork:
    
    image_file = "/var/lib/radiod/radio_image.jpg"
    no_image = "images/no_image.jpg" 
    log = None      # Logging object (See logit routine)

    def __init__(self,log=None): 
        if log != None:
            self.log = log
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
        if coverURL != None and ':' in coverURL :
            coverImage = self.getCoverImageFromURL(coverURL)
        return coverImage

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
                title = currentsong.get("title")
                if name != None and title != None:
                    broadcast_info = name + ': ' + title
                elif name != None:
                    broadcast_info = name
            except Exception as e:
                self.logit(e)
                print(e)
                broadcast_info = ""
                pass
        return broadcast_info

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
            try:
                title = broadcast_info[broadcast_info.index(":")+1 :] 
            except:
                title = broadcast_info
            # Build the url following this pattern:
            # https://api.discogs.com/database/search?q=Rose%20Laurens%20-%20Quand%20Tu%20Pars%20(12%60%60%20Version)&token=SkLpyuNUuVTglclfwrvdBuxiucbjCFwMaXKLsAOg
            # https://mojoauth.com/escaping/url-escaping-in-python/
            url = BASE_URL + urllib.parse.quote_plus(title) + "&token=" + API_DISCOGS_TOKEN
            # https://developer.mozilla.org/en-US/docs/Web/API/Response
            response = requests.get(url, headers=HEADERS)
            type = response.headers['content-type']
            if type == 'application/json':
                data = response.json() # Python dictionary
                if len(data['results']) > 1:
                    # Extract the URL of the art cover image
                    cover_url = data['results'][0]['cover_image']
                    if not(isinstance(cover_url, str)):
                        cover_url = None
                    self.logit("Artwork %s" % cover_url)
        except Exception as e:
            self.logit(str(e))
        return cover_url 

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
