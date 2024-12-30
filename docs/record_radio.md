Recording Radio programs
========================

There a number of ways to record a Radio program :
1. Press the 'Record' button on the IR Remote Control
2. Press the 'Record' Button on the radio
3. Run the *record.py* program from the command line (Log in required)

Before you can use the recording facility it is necessary to install the **streamripper** software.

1. Run **radio-config** program
2. Select option **8 Install/configure drivers and software components** from the menu
3. Select option **7 Install recording utility (streamripper)**
4. Confirm that it is OK to install the **streamripper** software
The installation program will then install **streamripper**

To record a Radio program
=========================
1. Select the Radio program that you want to record 
2. Use the IR Remote Control to start recording or press the 'Record' button on the Radio
3. To stop record press the 'Record' button again 

When you press the 'Record' button the IR remote activity LED will flash for about two seconds and after a short pause it will light up for the duration of the recording process. If you don't have an IR activity LED configured you can still see a recording indicator '*' after the date. For example:
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

**Note:** Once recording of the current Radio station has started you can selaect a different Radio station to listen to. This is because **streamripper** is a completely independant program from ther radio program.

Running the record program
========================== 
The actual program that calls **streamripper** software is called **record.py**
1. Log into the Raspberry Pi 
2. Run the following commands
**cd /usr/share/radio**
**sudo ./record.py --help**

The following will be displayed

```
This program can only be run as root user or using sudo

Usage: ./record.py --station_id=<station number> --duration=<duration>
                 --omit_incomplete --playlist_only --directory=<directory>
                 --cleanup

Where <station number> is the number of the radio stream to record
      --station_id if ommited the currently playing station will be recorded
      --omit_incomplete skip incomplete tracks when creating the playlist
      --playlist_only Only create playlist from the recordings directory. No recording
      --cleanup Remove incomplete tracks from the /home/<user>/Recordings directory
      <directory> is the location for recorded files. default /home/<user>/Recordings
      <duration> is the length of time to record in hours:minutes
                 Maximum recording time allowed 12 hours
```
**Examples**
**========**
Record the currently selected Radio station for 5 minutes
**sudo ./record.py --duration=5**

Record the currently selected Radio station for 1 hour and 15 minutes
**sudo ./record.py --duration=1:15**

Record Radio syation 17 for a duration of 15-minutes
**sudo ./record.py --station_id=17 --duration=0:15**

Create a playlist from /home/<usr>/Recordings in /var/lib/mpd/playlists/Recordings.m3u. No recording is carried out.
**sudo ./record.py --playlist_only**

Normally the recording process will omit incomplete tracks when called from the radio software. When using the **record.py** program, this isn't the case. To omit incomplete recordings you need to specify **--omit_incomplete** otherwise all partial tracks will be recorded.
**sudo ./record.py --station_id=17 --duration=0:15 --omit_incomplete**

You can also cleanup the Recordings directory  
**sudo ./record.py --playlist_only --omit_incomplete --cleanup**

**Logging**
**=======**
Logging output will be found **/var/log/radiod/radio.log**

End of Tutorial

