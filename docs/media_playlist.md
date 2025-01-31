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

**/var/lib/mpd/playlists/<name>** Where \<name\> is the name of media playlist such as **USB_Stick.m3u** or **Radio.m3u**

**/var/lib/mpd/music** Actual location of music files pointed to by soft links.
For example **media** points to **/media/pi** which is the mount point for the USB stick

```
$ ls -la
lrwxrwxrwx 1 root root     9 Jan 30 19:46 media -> /media/pi
lrwxrwxrwx 1 root root    19 Jan  8 07:12 recordings -> /home/pi/Recordings
lrwxrwxrwx 1 root root    14 Nov 26 07:40 sdcard -> /home/pi/Music
lrwxrwxrwx 1 root root     6 Jan 30 19:46 share -> /share
lrwxrwxrwx 1 root root    14 Jan 25 09:24 usbdrive -> /home/pi/Music
```
Music on stored on the SD card or a USB SSD drive is usually stored in the **/home/pi/Music** directory.

End of configuration tutorial
=============================
