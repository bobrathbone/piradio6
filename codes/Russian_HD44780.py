#!/usr/bin/env python3
# -*- coding: latin-1 -*-
#
# Raspberry Pi Radio Character translation class
# Escaped characters, html and unicode translation to ascii
#
# $Id: Russian_HD44780.py,v 1.3 2021/11/13 15:25:00 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#            The authors shall not be liable for any loss or damage however caused.
#
# Useful Links on character encodings
#       http://www.zytrax.com/tech/web/entities.html
#       http://www.utf8-chartable.de/
#       http://www.codetable.net/
#       http://www.ascii-code.com/

# Russian language OLED/LCD with HD44780 controller
# Do not use for HD44780U controller devices. See Russian.py

name = "Russian"  # Language name, to check against language parameter in /etc/radiod.conf
controller = "HD44780"      # Used by HD44780 controllers using code chart 0x0
codepage = 0x0  # Code page 0x0, 0x1 or 0x2


# Russian Romanize characters
# See https://en.wikipedia.org/wiki/Romanization_of_Russian
romanized = {
    # Three byte special characters, translate first
    '\\xef\\xbb\\xbf' : '',         # '' Remove BOM
    '\\xe2\\x80\\x93' : '-',
    '\\xe2\\x80\\x94' : '-',
    '\\xe2\\x80\\x95' : '-',

    '\\xd0\\x81' : 'E',
    '\\xd0\\x82' : 'D',
    '\\xd0\\x83' : 'G',
    '\\xd0\\x83' : 'D',
    '\\xd0\\x84' : 'E',
    '\\xd0\\x85' : 'Ѕ',
    '\\xd0\\x86' : 'І',
    '\\xd0\\x90' : 'A',
    '\\xd0\\x91' : 'B',
    '\\xd0\\x92' : 'V',
    '\\xd0\\x93' : 'G',
    '\\xd0\\x94' : 'D',
    '\\xd0\\x95' : 'E',
    '\\xd0\\x96' : 'ZH',
    '\\xd0\\x97' : 'Z',
    '\\xd0\\x98' : 'I',
    '\\xd0\\x99' : 'J',
    '\\xd0\\x9a' : 'K',
    '\\xd0\\x9b' : 'L',
    '\\xd0\\x9c' : 'M',
    '\\xd0\\x9d' : 'N',
    '\\xd0\\x9e' : 'O',
    '\\xd0\\x9f' : 'P',
    '\\xd0\\xa0' : 'R',
    '\\xd0\\xa1' : 'S',
    '\\xd0\\xa2' : 'T',
    '\\xd0\\xa3' : 'U',
    '\\xd0\\xa4' : 'F',
    '\\xd0\\xa5' : 'KH',
    '\\xd0\\xa6' : 'TS',
    '\\xd0\\xa7' : 'CH',
    '\\xd0\\xa8' : 'SH',
    '\\xd0\\xa9' : 'SHCH',
    '\\xd0\\xaa' : 'IE',
    '\\xd0\\xab' : 'Y',
    '\\xd0\\xac' : '\'',
    '\\xd0\\xad' : 'E',
    '\\xd0\\xae' : 'IU',
    '\\xd0\\xaf' : 'IA',

    # Small letters
    '\\xd0\\xb0' : 'a',
    '\\xd0\\xb1' : 'b',
    '\\xd0\\xb2' : 'v',
    '\\xd0\\xb3' : 'g',
    '\\xd0\\xb4' : 'd',
    '\\xd0\\xb5' : 'e',
    '\\xd0\\xb6' : 'zh',
    '\\xd0\\xb7' : 'z',
    '\\xd0\\xb8' : 'i',
    '\\xd0\\xb9' : 'j',
    '\\xd0\\xba' : 'k',
    '\\xd0\\xbb' : 'l',
    '\\xd0\\xbc' : 'm',
    '\\xd0\\xbd' : 'n',
    '\\xd0\\xbe' : 'o',
    '\\xd0\\xbf' : 'p',
    '\\xd1\\x80' : 'r',
    '\\xd1\\x81' : 's',
    '\\xd1\\x82' : 't',
    '\\xd1\\x83' : 'u',
    '\\xd1\\x84' : 'f',
    '\\xd1\\x85' : 'h',
    '\\xd1\\x86' : 'c',
    '\\xd1\\x87' : 'ch',
    '\\xd1\\x88' : 'sh',
    '\\xd1\\x89' : 'ssh',
    '\\xd1\\x8a' : 'ie',
    '\\xd1\\x8b' : 'y',
    '\\xd1\\x8c' : '\'',
    '\\xd1\\x8d' : 'je',
    '\\xd1\\x8e' : 'ju',
    '\\xd1\\x8f' : 'ja',
    '\\xd1\\x90' : 'e',
    '\\xd1\\x91' : 'e',
    '\\xd1\\x93' : 'jg',
    '\\xd1\\x94' : 'je',
    '\\xd1\\x95' : 'dz',
    '\\xd1\\x96' : 'i',
    '\\xd1\\x97' : 'i',
    '\\xd1\\x99' : 'j',
    '\\xd1\\xa2' : 'Ye',
    '\\xd1\\xa2' : 'ye',
    '\\xd1\\xb2' : 'Fh',
    '\\xd1\\xb3' : 'fh',
    '\\xd1\\xb4' : 'Yh',
    '\\xd1\\xb5' : 'yh',

    '\\xc3\\xa0' : 'a',  # à 
    '\\xc3\\xa5' : 'e',  # å 
    '\\xc3\\xae' : 'o',  # î
    '\\xc3\\xb0' : 'p',  # ð 
    '\\xc3\\xb1' : 'c',  # ñ 
    '\\xc3\\xb3' : 'y',  # ó 
    '\\xc3\\xb5' : 'x',  # õ 
    '\\xd0\\x86' : 'I',  # Æ 
    '\\xd1\\x96' : 'i',  # Ö
    '\\xd0\\x84' : 'E',  # Ä
    '\\xd0\\x87' : 'I',  # Ç 
    '\\xd1\\x97' : 'i',  # ×
    '\\xd1\\x94' : 'e',  # Ô 
}

# Dummy table The HD44870 cannot support Russian Cyrillic characters
# Use an LCD with HD44870U/MC0100  controller with support 
# for English/European/Japanese and Russian characters
codes = romanized


# End of Russian font code tables
