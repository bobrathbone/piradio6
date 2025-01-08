Creating Media playlists
========================

To create a Media Playlist select option **4 Create media playlists** from the **radio-config** menu. This will give you five options.

```
Create playlist
1 From USB stick 
2 From network share
3 From SD card
4 From USB Disk Drive
5 Recordings 
```

Files
=====
**/var/lib/mpd/playlists** Location of MPD playlists

**/var/lib/mpd/playlists/<name>** Where <name>of media playlist such as **USB_Stick.m3u**

Running the create_playlist program from the command line
=========================================================
Usually you will call the create_stations program from radio-config

**radio-config --> Update radio stations playlist**

However there may be occasions that you want to run the **create_playlist.sh** program from the command line or in a script. First populate the media with music files and then run **create_playlist.sh** 


```
cd /usr/share/radio
./create_stations.py
```

End of configuration tutorial
