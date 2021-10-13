#!/bin/bash
# Change -c 0 to your alsa device number
lxterminal --command="/bin/bash -c 'sudo -H -u mpd alsamixer -c 0 -D equal'"
