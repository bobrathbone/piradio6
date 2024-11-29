Station list - Source list for radio stations streams
=====================================================

File: /var/lib/radiod/stationlist (Don't use station.urls - distribution only)

To display document use **radio-config**

Information, Documents and Diagnostics --> Update radio stations playlist**

Format of the stationlist file
==============================

To use this file add the URL that points to either an asx or pls file
The format is:


```
  (<playlist>)
  [<title>] http://<url>
```

The (<playlist>) parameter groups the following station definitions into one playlist
For example (BBC Stations) creates a playlist called BBC_Stations.m3u

**Note:** Play lists are terminated with a blank line

The title paramter is the name you want to display on the screen when you select a station 

Some sites that you can use are:
```
  http://www.radiomap.eu
  http://www.internet-radio.com
  http://www.radio-locator.com
  http://bbcstreams.com/
```

Then run create_playlists.py in the /home/pi/radio directory to create M3U files

Example playlist entries
========================

```
# UK stations
(Radio)
[Caroline Pirate] http://sc3.radiocaroline.net:8030/listen.m3u8
[Thornbury Radio] https://s42.myradiostream.com/29400/listen.mp3

# Dutch stations
[NPO Radio 1] http://icecast.omroep.nl/radio1-bb-mp3
[NPO Radio 2] http://icecast.omroep.nl/radio2-bb-mp3
[NPO Radio 3fm] http://icecast.omroep.nl/3fm-bb-mp3
[NPO Radio 4] http://icecast.omroep.nl/radio4-bb-mp3.m3u

```

Instructions  to create playlists
=================================

- Edit the /var/lib/radiod/stationlist file 
- Run the create_stations.py script (or select from menu) to create the MPD playlist
- Restart radiod with the following instruction or reboot
```
sudo systemctl restart radiod 
```

The **create_stations.py** script creates the **/var/lib/mpd/playlists/Radio.m3u** playlist file

Files
=====

**/var/lib/radiod/stationlist** The file containing the users list of radio stations 

**/usr/share/radio/station.urls** Initial distribution Radio playlist. This is copied to /var/lib/radiod/stationlist directory during program installation.

**/var/lib/mpd/playlists** Location of MPD playlists

**/var/lib/mpd/music** Location of media files for either a USB stick or a Network share

Running the create_stations.py program from the command line 
=========================================================
Usually you will call the create_stations program from **radio-config**. 
Select option 3 **Update radio stations playlist**

**radio-config --> Update radio stations playlist**

However there may be occasions that you want to run the create_stations.py program from the command line or in a script. First change to the **/usr/share/radio** directory and then run **create_stations.py**

```
cd /usr/share/radio/
./create_stations.py

This program can only be run as root user or using sudo
Usage: sudo ./create_stations.py [--delete_old] [--no_delete] [--input_file=<input file>] [--help]
        Where: --delete_old   Delete old playlists
               --force        Force update of MPD playlists
               --no_delete    Don't delete old playlists
               --input_file=<input_file>  Use alternative input file
               --help     Display help message
```

