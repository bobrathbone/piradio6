Recording Radio programs
========================

There a number of ways to record a Radio program :
1. Press the 'Record' button on the IR Remote Control
2. Press the 'Record' Button on the radio
3. Run the *record.py* program from the command line (Log in required)

Before you can use the recording facility it is necessary to install the **liquidsoap** software.

1. Run **radio-config** program
2. Select option **8 Install/configure drivers and software components** from the menu
3. Select option **7 Install recording utility (liquidsoap)**
4. Confirm that it is OK to install the **liquidsoap** software
The installation program will then install **liquidsoap**

To record a Radio program
=========================
1. Select the Radio program that you want to record 
2. Use the IR Remote Control to start recording or press the 'Record' button on the Radio
3. To stop record press the 'Record' button  or the 'Record' button on the Radio again 

When you press the 'Record' button the IR remote activity LED it will light up for the duration of the recording process. If you don't have an IR activity LED configured or the IR remote control service isn't running you can still see a recording indicator '*' after the time and date. For example:
```
08:30 06/12/2024*
```

The recordings are stored in the **/home/\<user\>**/Recordings directory where **\<user\>** is the name of the user (usually 'pi') that installed the software. At the end of the recording process the record program creates the /var/lib/mpd/playlists/Recordings.m3u playlist and loads it into the radio's database.

Playing back a recording
========================
1. Press the 'Menu' button from either the remote control or on the radio **twice** to select the **Source** menu
2. Use the Channel UP/DOWN buttons or knob to select the **Recordings** playlist
3. Press the 'Menu' to start playing the recorded stations

**Note:** that all selected radio stations are recorded into the **/home/\<user\>/Recordings** directory where **\<user\>** is noramally 'pi'. However, each radio station is recorded into its own directory using the station name. You can select which **recorded** radio station or track you want to listen to in the search menu.

1. Press the 'Menu' button from either the remote control or on the radio **once** to select the **Search** menu
2. Use the 'Channel' buttons or knob to select each track 
3. Use the 'Volume' buttons or knob to skip through each Radio station 

Setting the recording timer
===========================
1. Press the 'Menu' button from either the remote control or  on the radio **three times** to select the **Options** menu
2. Use the Channel UP/DOWN buttons or knob to select the **Record for** option 
3. Use the Volume UP/DOWN buttons or knob to set the time (Maximum time 12 Hours)  
4. Press the 'Menu' button to save your setting
5. Start the recording

**Note:** Once recording of the current Radio station has started you can selaect a different Radio station to listen to. This is because **liquidsoap** is a completely independant program from ther radio program.

Configuration
=============
Configuration of the recording facility will be found in the **/etc/radiod.conf** configuation file
Record program parameters (See **record_class.py**)
**record_switch=\<GPIO\>** - Record button normally uses GPIO 27 (physical pin 13) or GPIO5 (pin 29)
**record_log=\<loglevel\>** - 0 none, 1 crtitcal , 2 severe (default) , 3 important, 4 info , 5 debug
**record_format=\<format\>** - mp4, flac, opus   , mp3
. . . . . . . . . . . . Also sets codec - aac, flac, libopus, libmp3lame
**record_incomplete** - yes/no Include incomplete tracks when creating the playlist
**cleanup -  yes/no** Remove incomplete tracks from the /home/<user>/Recordings directory
**load_recordings** - yes/no Load new Recordings playlist
```
record_switch=27
record_log=1
record_format=mp3
record_incomplete=yes
record_cleanup=no
load_recordings=no
```

**Logging**
**=======**
Logging output will be found **/var/log/radiod/radio.log**

End of Tutorial
===============
