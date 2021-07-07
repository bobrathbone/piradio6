#!/usr/bin/env python3
# Raspberry Pi Internet Radio Class
# $Id: test_alsa.py,v 1.1 2021/05/17 05:29:32 bob Exp $
#
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# This program uses python3-alsaaudio package
# Use "apt-get install python3-alsaaudio" to install the library
# See: https://pypi.org/project/python-mpd2/
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#         The authors shall not be liable for any loss or damage however caused.
#
# See https://www.programcreek.com/python/example/91453/alsaaudio.PCM
#     https://larsimmisch.github.io/pyalsaaudio/libalsaaudio.html

import pdb
import alsaaudio
pcms = alsaaudio.pcms()
for pcm in pcms:
    print(pcm)
print('')
cards =alsaaudio.cards()
for card in cards:
    print(card)
