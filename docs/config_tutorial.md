Configuration Tutorial
======================

**Please Note:** Configuration of **/etc/radiod.conf** file, for the most part, is done by
running the **radio-config** utility which in turn calls the configure_radio.sh programs.
NOTE: The configuration in this file uses GPIO numbers and not physical pin numbers.

Further information can be found in the **Raspberry Pi Internet Radio - Technical Reference Manual** available at **https://bobrathbone.com** or **https://github.com/bobrathbone/piradio6/** in the docs directory.

To search this tuturial for a given parameter or string enter a slash '/'.

The RADIOD section
==================
Parameters are grouped together logically along with their default values.

**[RADIOD]**

loglevel is CRITICAL,ERROR,WARNING,INFO,DEBUG or NONE. Set to DEBUG for more information
log_creation mode, either truncate (new log each time) or tail 
**loglevel=INFO**
**log_creation_mode=truncate**

Startup option either RADIO,MEDIA or LAST a playlist name without its m3u extension
**startup=Radio**

 MPD client timeout from 2 to 15 seconds default 10
**client_timeout=10**

Codecs list for media playlist creation (Run 'mpd -V' to display others)
**CODECS="mp3 ogg flac wav wma aac"**

Set date format, US format =  %H:%M %m/%d/%Y
To display timezone use %Z  dateformat=%H:%M %Z %d/%m/%Y
**dateformat=%H:%M %d/%m/%Y**

Volume range 10, 20, 25, 50 or 100. Volume display text or blocks.
**volume_range=20**
**volume_display=blocks**

This is the default listening port for the Music Player Daemon (Don't change)
**mpdport=6600**

These are settings for the IR remote control daemon service (ireventd.service)
Remote control communication host (remote_control_host) and port (remote_control_port)
The host setting is either localhost or the IP address of the remote server
The remote_control_host parameter allows another host to send UDP messages to the UDP server
**remote_control_host=localhost**
**remote_control_port=5100**
**remote_listen_host=localhost**

Audio output device - Must match an audio output using the **aplay -l** command
The **configure_audio.sh** program will set this to headphones(default), HDMI, DAC or USB
depending upon the audio device/card selection. You can override this setting
with your own unique string from the aplay command, for example "HiFiBerry"
In the case of Bluetooth devices it is always "bluetooth" and not the name of the device
**audio_out="headphones"**

Audio config lock stops audio configuration from being dynamically changed 
if HDMI plugged in or out.
**audio_config_locked=no**

Switch to MEDIA if no Internet available for the radio. yes or no(default)
 Needs a USB stick or network drive with media and associated playlist
**no_internet_switch=no**

Output LED for remote control, default GPIO 11 (pin 23) or
GPIO 13 (pin 33) for AdaFruit plate or PiFace CAD (40 pin RPi needed)
Use GPIO 16 (pin 36) for designs using IQAudIO DAC cards etc.
Use GPIO 14 (pin 8) for designs using IQAudIO Cosmic controller
remote_led=0 is no output LED
**remote_led=0**

Display playlist number in brackets yes or no
**display_playlist_number=no**

Background colours (If supported) See Adafruit RGB plate
Adafruit RGB colors: OFF, RED, GREEN, BLUE, YELLOW, TEAL, VIOLET, WHITE
Pimoroni displays RGB colors: Refer to PIL library color chart
**bg_color=WHITE**
**mute_color=PURPLE**
**shutdown_color=TEAL**
**error_color=RED**
**search_color=GREEN**
**news_color=CYAN**
**info_color=BLUE**
**menu_color=YELLOW**
**source_color=TEAL**
**sleep_color=OFF**

Three colour status LED (Typically for the vintage radio) Normally use GPIOs 27,22,23 respectively.
A GPIO setting of '0' disables output
**rgb_red=0**
**rgb_green=0**
**rgb_blue=0**

The i2c_address overides the default i2c address. 0x00 = use default
Some backpacks use other addresses such as 0x2F, then set i2c_address=0x2F
i2c_address=0x00

Menu rotary switch (optional) Normal values are 24,8 and 7 respectively. Value 0 disables output.
**menu_switch_value_1=0**
**menu_switch_value_2=0**
**menu_switch_value_4=0**

I2C addresses for displays using the I2C interface. 
**i2c_address=0x00**
**i2c_rgb_address=0x30**
**i2c_bus=1**   
Some i2c displays such as Grove I2C RGB have a separate interface for colour
The Grove RGB jhd1313_sgm31323 LCD uses address 0x30 and is set in **i2c_rgb_address**. 
The i2c_bus is 1 except for the first RPi models. Do not change 
Use the **i2cdetect -y 1** command to display I2C addresses being used

```
     0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
00:                         -- -- -- -- -- -- -- 0f
10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 1f
20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
30: 30 -- -- -- -- -- -- -- -- -- -- -- 3c -- 3e --
40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
60: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
70: -- -- -- -- -- -- -- --
```

Language and international character sets
-----------------------------------------
**translate_lcd=on**
**language=English**
**controller=HD44780U**
**romanize=on**
**codepage=0**
Set LCD character translation on or off. Graphic and OLED versions unaffected
as they do not need language translation and use system fonts
The language setting decides which translation table is being used  
The **controller** parameter sets the LCD/OLED controller being used. 
HD44780U (default) or HD44780 (Older LCDs)
Romanize characters (eg convert Cyrillic to Latin characters),
Set to on or off. Default is on
The **codepage=0** parameter sets the LCD code page table 0,1,2 or 3. Default 0
Some LCDs have two or three code pages which convert character codes to the actual display character
0 = Use codepage parameter specified in primary font file (Selected by language)
1, 2 or 3 Override codepage setting in the primary font file


Speech for visually impaired or blind listeners, yes or no
Needs espeak package - sudo apt-get install espeak
Speech volume as a percentage of the normal MPD volume
Verbose - yes = each station change is spoken
Speak Info (hostname and IP address)
**speech=no**
**speech_volume=75**
**verbose=no**
**speak_info=no**


User interface type and settings
--------------------------------
Set the user interface to 'buttons' or 'rotary_encoder' or 'graphical'
These can also be used in conjunction with a graphical/touchscreen display
The switch settings are the GPIO settings for each switch nd must match your wiring
**user_interface=rotary_encoder**
**menu_switch=17**
**mute_switch=4**
**up_switch=24**
**down_switch=23**
**left_switch=14**
**right_switch=15**

The Record button normally uses GPIO 27 (physical pin 13) if LCD, TFT or OLED displays
configured. If using Waveshare 2.4" or 1.5" SPI displays set this to GPIO05 (pin 29)
**record_switch=27**

Record program parameters
 --omit_incomplete skip incomplete tracks when creating the playlist
 --cleanup Remove incomplete tracks from the /home/<user>/Recordings directory
 --load Load new Recordings playlist
 --log <loglevel> 1 crtitcal , 2 severe (default) , 3 important, 4 info , 5 debug
**record_params="--omit_incomplete --cleanup"**

Pull GPIO up/down internal resistors. Only set. Only set to up if using first model
Raspberry Pi's and the switches have been wired GPIOx --> Switch --> 0V(GND)
Set to 'none' if external resistors have been wired. Default: up
**pull_up_down=up**

Display types
-------------
**display_type=LCD**
NO_DISPLAY = No display connected
LCD = directly connected LCD via GPIO pins
LCD_I2C_PCF8574 = Arduino (PCF8574) I2C backpack
LCD_I2C_ADAFRUIT = Adafruit I2C backpack
LCD_ADAFRUIT_RGB = LCD I2C RGB plate with buttons
GRAPHICAL = Graphical or touch screen display
OLED_128x64 = 128x64 pixel OLED
PIFACE_CAD = PiFace CAD with six push buttons using the SPI interface
ST7789TFT = Pimoroni Pirate audio with four push buttons using the SPI interface
SSD1306 = Sitronix SSD1306 controller for the 128x64 pixel OLED
SH1106_SPI = Sino Wealth SH1106 controller for the Waveshare 128x64 pixel OLED (SPI)
LUMA = Luma driver for SSD1306, SSD1309, SSD1325, SSD1331, SH1106, SH1106_128x32, WS0010
     For example LUMA.SH1106 for OLEDs using the sh1106 chip
LCD_I2C_JHD1313 = Grove RGB 2x16 LCD (AIP31068L controller)
LCD_I2C_JHD1313_SGM31323 = Grove RGB 2x16 LCD (SGM31323 controller for backlight control)
WS_SPI_SSD1309 = Waveshare SPI Driver for 2.42" and 1.5" OLEDS
      For example WS_SPI_SSD1309.2in42 (2.42" OLED) or WS_SPI_SSD1309.1in5_b (1.5" OLED)
      See drivers in waveshare_OLED/lib directory

Display width, 0 use program default. Usual settings 16 or 20. Number of line 2,4,5 or 6
**display_width=20**
**display_lines=4**

Font size and name (TFT displays only)
**font_size=11**
**font_name="/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"**

LCD GPIO connections for 40 pin version of the radio
**lcd_select=7**
**lcd_enable=8**
**lcd_data4=5**
**lcd_data5=6**
**lcd_data6=12**
**lcd_data7=13**

Scroll oversize messages on the display (default yes). Set to no to prevent 
scrolling except for RSS news feed display which will always be scrolled
**scrolling=yes**

Display Scroll speed 0.001 to 0.02 seconds. 0 = Use default
**scroll_speed=0**

Settings are standard, alternative, rgb_rotary rgb_i2c_rotary
Some rotary switches do not work well with the standard rotary class
Set to "alternative" to use the alternative rotary encoder class
For rotary encoders with RGB LEDs in the shaft set to rgb_rotary
For rotary I2C encoders with RGB LEDs in the shaft set to rgb_i2c_rotary
**rotary_class=standard**

Rotary encoder detection step size 'full' step or 'half' step (default)
Only used in the standard rotary encoder class and NOT the alternative rotary class
 neither does it affect I2C rotary encoders
 ABC encoders seem to work best with 'full' step, KY040 encoders better with 'half' step
**rotary_step_size=half**

KY-040 encoders etc have their own physical 10K pull-up resistors and do not
need the internal gpio pull-up resistors.
In that case set rotary_gpio_pullup=none otherwise set it to "up"
KY040 rotary encoders can have resistor R1 (SW to VCC) yes=fitted (older KY-040 encoders)
**rotary_gpio_pullup=up**
**ky040_r1_fitted=no**

 Station names source, list or stream. Using 'list' will use the names defined in the **/var/lib/radiod/stationlist** file. The 'stream' setting uses the name from the radio stream.
**station_names=list**

Action on exiting radio. Stop radio only, shutdown the system or execute program
1) Shutdown system: exit_action=stop_radio
2) Exit to operating system: exit_action=stop_radio
3) Execute a program: exit_action=<programm name>
   For example: exit_action=/usr/share/radio/weather.py
**exit_action=shutdown**

Bluetooth device ID - Replace with the ID of your bluetooth speakers/headphones
Example: bluetooth_device=00:75:58:41:B1:25
Use the following command to display paired devices
bluetoothctl paired-devices
**bluetooth_device=00:00:00:00:00:00**

Action when muting MPD. Options: pause(Stream continues but not processed) or stop(stream is stopped). 'stop' is recommended
**mute_action=stop**

Shoutcast ID needed to access Shoutcast radio streams
**shoutcast_key=anCLSEDQODrElkxl**

Display Pimoroni PHat Beat (pivumeter)
**pivumeter=no**

Internet check URL. This must be a reliable URL and port number
which can be contacted such as google.com
The port number is normally 80 (HTTP).
The internet_timeout in in seconds
Disable by removing the URL from internet_check_url= parameter
internet_check_url=google.com
**internet_check_url=google.com**
**internet_check_port=80**
**internet_timeout=10**


ireventd daemon keytable name. Set by IR remote configuration program
**keytable=myremote.toml**

OLED parameters
Flip display vertically (yes or no) OLED only at present
Path to splash screen
**flip_display_vertically=no**
**splash=bitmaps/raspberry-pi-logo.bmp**

Allow updating of playlists by external clients yes/no (Experimental)
**update_playlists=no**

I2C addresses and interrupt pins for RGB I2C Rotary Encoders
**volume_rgb_i2c=0x0F**
**channel_rgb_i2c=0x1F**
**volume_interrupt_pin=22**
**channel_interrupt_pin=23**

Shutdown command (Default "sudo shutdown -h now")
Replace with required command for example "x735off" for a X735 V2.5 shield
**shutdown_command="sudo shutdown -h now"**

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

The SCREEN Section
==================
Parameters for the Graphical programs **gradio.py** and **vgradio.py**
The parameters are for the most part pretty obvious.
The **switch_programs** parameter allows switchib between **gradio.py** and **vgradio.py**
The **screen_saver** parameter is the screen save time in minutes, 0 is no screen saver

**\[SCREEN\]**
**screen_size=800x480**
**fullscreen=yes**
**screen_saver=0**
**window_title=Bob Rathbone Internet Radio Version %V - %H**
**window_color=turquoise**
**banner_color=white**
**labels_color=white**
**display_window_color=lightblue**
**display_window_labels_color=black**
**slider_color=mediumseagreen**
**display_mouse=yes**
**display_icecast_button=no**
**wallpaper=/usr/share/rpd-wallpaper/aurora.jpg**
**dateformat=%H:%M:%S %A %e %B %Y**
**switch_programs=yes**
**display_shutdown_button=yes**
**scale_labels_color=white**
**stations_per_page=40**
**display_date=yes**
**display_title=yes**

The AIRPLAY Section
===================
**[AIRPLAY]**
Mixer preset volume for radio and media player if using sound card
Set to 0 if using onboard audio or USB sound dongle.
If using a sound card set to 100% initially and adjust as neccessary
**airplay=no**
**mixer_preset=100**

End of configuration tutorial
