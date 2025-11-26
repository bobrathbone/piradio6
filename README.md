Radiod - Raspberry Pi Internet Radio 
===== 
**Radiod** is a full feature radio front end for MPD which offers support for a variety of different LCDs, OLEDs and TFTs. There is also a touch-screen version available. User selection of radio streams or music tracks and volume setting, menus etc. can be done using rotary encoders, push buttons or even an IR remote control. Display shows date/time, station/track, artist and volume setting.

Platform
======
Runs on
- Raspberry Pi Zero
- Raspberry Pi 3 B+
- Raspberry Pi 4 B
- Raspberry Pi Zero 2 W
- Raspberry Pi 400 Kit
- Raspberry Pi 5

Pre-requisites
=========
Raspberry Pi Bookworm or Trixie Operating System, 32 or 64-Bit Architecture
Music Player Daemon (**MPD**), python-mpd

Features
======
- Choice of push-button or rotary encoder interface
-  Choice of different displays and audio devices
- Web interface using !OMPD
- Track and Radio artwork display
- Time display and Alarm facility
- Radio station recording facility
- Comprehensive installation manual

Supported Hardware
==============
## Displays
- Any type of **HD44780U LCD** display support two or four lines and six to forty columns
- Àdafruit 2x16 RGB Plate (I2C) 
- Raspberry Pi 7-inch touch screen
- Olimex 128 by 64-pixel OLED
- Adafruit 3.5-inch TFT touch screen
- Pimoroni Pirate Radio 
- Waveshare 1.8/2.3” touchscreen
- Grove I2C 2-line 16-char. LCD
- OLED displays supported by LUMA (SH1106, SSD1306 etc.)
- SH1106 128x64 1.3” OLED (SPI interface) 
- Waveshare 1.5 and 2.42-inch OLED with SPI interface

## Sound cards
- On-board audio output jack
- All devices supporting PCM5102A or PCM5100A DACs
- HDMI audio output (If supported)
- USB DAC via USB interface
- Pimoroni Pirate/pHat with PiVumeter
- HiFiBerry DAC, DAC 4400, Digi, Digi plus/Amp2
- IQaudIO DAC/Zero DAC, Digi/AMP
- JustBoom DAC/Zero/Amp/Digi HAT
- Bluetooth devices
- Adafruit speaker bonnet
- Pimoroni Pirate Audio
- Waveshare WM8960 DAC
- RPi (Raspberry Pi) Audio Cards

## Other
- IR remote control facility using TSOP382xx series sensor or FLIRC dongle

Downloading and creating the radiod package
===========================================
To create the radiod Debian package log into the Raspberry Pi and clone the source tree from GitHub.
```
cd
git clone https://github.com/bobrathbone/piradio6
```
Now change directory to **radio6** and make **setup.sh** executable then run it.
```
cd piradio6
chmod +x setup.sh
./setup.sh
```
This will install all of the necessary packages for the development environment and then run **build.sh**. 
The **setup.sh** script only needs to be run once. Subsequent builds can be done by just running the **./build.sh** script.
*Note:* The control file for the package build is called **piradio**
```
./build.sh
```
Finally install the new package. 
```
sudo dpkg -i radiod_8.1_all.deb
```
This will install the **radiod** package and supporting files in the **/usr/share/radio** directory. 
To configure the **radiod** package further run **radio-config** from the command line.
```
radio-config
```

Licences
=====
**radiod** is released under the
[GNU General Public License version 2](https://www.gnu.org/licenses/gpl-2.0.txt)

See [bobrathbone.com/raspberrypi/pi_internet_radio.html](https://bobrathbone.com/raspberrypi/pi_internet_radio.html) for further information
