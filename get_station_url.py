#!/usr/bin/env python
#!/usr/bin/env python3
#
# Raspberry Pi Radio - DISCOGs datbase data extraction 
#
# $Id: get_station_url.py,v 1.2 2026/03/12 09:26:03 bob Exp $
#
# Author : Bob Rathbone 
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
#
# This software requires discogs_client
# sudo mv /usr/lib/python3.13/EXTERNALLY-MANAGED /usr/lib/python3.13/EXTERNALLY-MANAGED.old
# pip3 install python3_discogs_client
#
# Note: The Bob Rathbone Computer Consultancy has no control over the Discogs database

import discogs_client
import requests
import sys

KEY = "jVQGatBjapPdPYDyWRfk"
SECRET="ZrvMKBRaMaSRAGWODIbNELrNfEfxIwou"
BASE_URL = "https://api.discogs.com/database/search?q="

def get_discogs_url(entity_type, query):
    """
    Fetches the Discogs resource URL for the first search result.
    
    entity_type: 'artist', 'release', or 'label'
    query: search string
    token: your Discogs personal access token
    """
    try:
        # Authenticate with Discogs
        #breakpoint()

        # Perform search
        request_url = BASE_URL + query + "&key=" + KEY + "&secret=" + SECRET
        response = requests.get(request_url)
        print(response.status_code)
        
        if response.status_code != 200:
            print(f"Error return code %d" % response.status_code)
            return None

        type = response.headers['content-type']
        print(type)
        data = response.json()
        #print(data)
        # Get the first match
        
        #breakpoint()
        cover_url = data['results'][0]['cover_image']
        #cover_url = data['results'][0]['resource_url']
        #item = data['results'][0]['master_url']
        #return item.url  # This is the Discogs web URL
        return cover_url

    except Exception as e:
        print("Error:",str(e))
        return None


if __name__ == "__main__":
    # Example usage
    if len(sys.argv) != 3:
        print("Usage: python get_discogs_url.py <entity_type> <query> ")
        print("Example: python get_discogs_url.py artist 'Daft Punk' YOUR_TOKEN")
        sys.exit(1)

    entity_type = sys.argv[1].lower()
    query = sys.argv[2]
    #token = sys.argv[3]

    if entity_type not in ("artist", "release", "label"):
        print("Entity type must be 'artist', 'release', or 'label'.")
        sys.exit(1)

    url = get_discogs_url(entity_type, query)
    if url:
        print(f"Discogs URL: {url}")
#python get_discogs_url.py artist "Daft Punk" YOUR_TOKEN
