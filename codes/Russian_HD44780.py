#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# Raspberry Pi Radio Character translation class
# Escaped characters, html and unicode translation to ascii
#
# $Id: Russian_HD44780.py,v 1.5 2020/04/18 19:37:30 bob Exp $
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
codepage = 0x2  # Code page 0x0, 0x1 or 0x2

# Russian Cyrillic characters
# For contrllers with only capital Russian letters
codes = {
        # Three byte special characters, translate first
        '\\xef\\xbb\\xbf' : '',         # '' Remove BOM
        '\\xe2\\x80\\x93' : '-',
        '\\xe2\\x80\\x94' : '-',
        '\\xe2\\x80\\x95' : '-',
	'\\xe3\\xbd\\xb8' : chr(0xb8),  # и ?

        # Russian unicode upper case
	'\\xd0\\x80' : chr(0x45), # Ѐ
        '\\xd0\\x81' : chr(0xa2), # Ё
        '\\xd0\\x85' : chr(0x53), # Ѕ
        '\\xd0\\x86' : chr(0x59), # І
        '\\xd0\\x90' : chr(0x41), # А
        '\\xd0\\x91' : chr(0xa0), # Б
        '\\xd0\\x93' : chr(0xa1), # Г
        '\\xd0\\x94' : chr(0xe0), # Д
        '\\xd0\\x96' : chr(0xa3), # Ж
        '\\xd0\\x97' : chr(0xa4), # З
        '\\xd0\\x98' : chr(0xa5), # И
        '\\xd0\\x99' : chr(0xa6), # Й
        '\\xd0\\x9b' : chr(0xa7), # Л
        '\\xd0\\x9f' : chr(0xa8), # П
        '\\xd0\\xa3' : chr(0xa9), # У
        '\\xd0\\xa4' : chr(0xaa), # Ф
        '\\xd0\\xa6' : chr(0xe1), # Ц
        '\\xd0\\xa7' : chr(0xab), # Ч
        '\\xd0\\xa8' : chr(0xac), # Ш
        '\\xd0\\xa9' : chr(0xe2), # Щ
        '\\xd0\\xaa' : chr(0xad), # Ъ
        '\\xd0\\xab' : chr(0xae), # Ы
        '\\xd0\\xad' : chr(0xaf), # Э
        '\\xd0\\xae' : chr(0xb0), # Ю
        '\\xd0\\xaf' : chr(0xb1), # Я

        # Russian unicode lower case
        '\\xd1\\x91' : chr(0xb5), # ё
        '\\xd0\\xb1' : chr(0xb2), # б
        '\\xd0\\xb2' : chr(0xb3), # в
        '\\xd0\\xb3' : chr(0xb4), # г
        '\\xd0\\xb4' : chr(0xe3), # д
        '\\xd0\\xb6' : chr(0xb6), # ж
        '\\xd0\\xb7' : chr(0xb7), # з
        '\\xd0\\xb8' : chr(0xb8), # и
        '\\xd0\\xb9' : chr(0xb9), # й
        '\\xd0\\xba' : chr(0xba), # к
        '\\xd0\\xbb' : chr(0xbb), # л
        '\\xd0\\xbc' : chr(0xbc), # м
        '\\xd0\\xbd' : chr(0xbd), # н
        '\\xd0\\xbf' : chr(0xbe), # п
        '\\xd1\\x82' : chr(0xbf), # т
        '\\xd1\\x84' : chr(0xe4), # ф
        '\\xd1\\x86' : chr(0xe5), # ц
        '\\xd1\\x87' : chr(0xe6), # ч
        '\\xd1\\x88' : chr(0xc1), # ш
        '\\xd1\\x89' : chr(0xe6), # щ
        '\\xd1\\x8a' : chr(0xc2), # ъ
        '\\xd1\\x8b' : chr(0xc3), # ы
        '\\xd1\\x8c' : chr(0xc4), # ь
        '\\xd1\\x8d' : chr(0xc5), # э
        '\\xd1\\x8e' : chr(0xc6), # ю
        '\\xd1\\x8f' : chr(0xc7), # я

        # UTF-8: C380-C3BF
        '\\xc3\\x81' : chr(0xa0), # Б
        '\\xc3\\x83' : chr(0xa1), # Г
        '\\xc3\\x84' : chr(0xe0), # Д
        '\\xc3\\x86' : chr(0xa3), # Ж
        '\\xc3\\x87' : chr(0xa4), # З
        '\\xc3\\x88' : chr(0xa5), # И
        '\\xc3\\x89' : chr(0xa6), # Й
        '\\xc3\\x8b' : chr(0xa7), # Л
        '\\xc3\\x8f' : chr(0xa8), # П
        '\\xc3\\x93' : chr(0xa9), # У
        '\\xc3\\x94' : chr(0xaa), # Ф
        '\\xc3\\x96' : chr(0xe1), # Ц
        '\\xc3\\x97' : chr(0xab), # Ч
        '\\xc3\\x98' : chr(0xac), # Ш
        '\\xc3\\x99' : chr(0xe2), # Щ
        '\\xc3\\x9a' : chr(0xad), # Ъ
        '\\xc3\\x9b' : chr(0xae), # Ы
        '\\xc3\\x9d' : chr(0xaf), # Э
        '\\xc3\\x9e' : chr(0xb0), # Ю
        '\\xc3\\x9f' : chr(0xb1), # Я

        '\\xc3\\xa1' : chr(0xb2), # б
        '\\xc3\\xa2' : chr(0xb3), # в
        '\\xc3\\xa3' : chr(0xb4), # г
        '\\xc3\\xa4' : chr(0xe3), # д
        '\\xc3\\xa6' : chr(0xb6), # ж
        '\\xc3\\xa7' : chr(0xb7), # з
        '\\xc3\\xa8' : chr(0xb8), # и
        '\\xc3\\xa9' : chr(0xb9), # й
        '\\xc3\\xaa' : chr(0xba), # к
        '\\xc3\\xab' : chr(0xbb), # л
        '\\xc3\\xac' : chr(0xbc), # м
        '\\xc3\\xad' : chr(0xbd), # н
        '\\xc3\\xaf' : chr(0xbe), # п
        '\\xc3\\xb2' : chr(0xbf), # т
        '\\xc3\\xb4' : chr(0xe4), # ф
        '\\xc3\\xb6' : chr(0xe5), # ц
        '\\xc3\\xb7' : chr(0xc0), # ч
        '\\xc3\\xb8' : chr(0xc1), # ш
        '\\xc3\\xb9' : chr(0xe6), # щ
        '\\xc3\\xba' : chr(0xc2), # ъ
        '\\xc3\\xbb' : chr(0xc3), # ы
        '\\xc3\\xbc' : chr(0xc4), # ь
        '\\xc3\\xbd' : chr(0xc5), # э
        '\\xc3\\xbe' : chr(0xc6), # ю
        '\\xc3\\xbf' : chr(0xc7), # я
	'\\xc2\\xab' : '<<',            # «
	'\\xc2\\xbb' : '>>',            # »
	'\\xef\\xbb\\xbf' : '',         # '' (nothing),
}


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

# End of Russian font code tables
