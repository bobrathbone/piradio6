# -*- coding: latin-1 -*-
#
# West European languages character translation table for HD44780U controller
# Do not use for HD44780 controllers
#
# $Id: European.py,v 1.6 2020/04/19 11:14:20 bob Exp $
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
# 	https://en.wikipedia.org/wiki/Western_Latin_character_sets_(computing)

# The following codes are best effort to translate European characters to the
# available LCD fonts. The tables are not perfect nor complete so amend if necessary
# Note that this table is for controller HD44780 character table 0x1 

name = "European"  # Language name, to check against language parameter in /etc/radiod.conf
controller = "HD44780U"      # Used by controllers with A0 and A02 code charts
codepage = 0x1  # Code page 0x0, 0x1 or 0x2

# Escaped codes (from unicode)
codes = {

	# Three byte characters (Must be checked first)
	'\\xe2\\x82\\xac' : 'Euro',	# Euro
	'\\xe2\\x84\\xa2' : ' TM ',	# ™

	# French (Diacritics) unicode escape sequences
	'\\xc3\\x80' : chr(0x98),	# À > A
	'\\xc3\\x81' : chr(0x98),	# Á > A
	'\\xc3\\x82' : chr(0xcb),	# Â
	'\\xc3\\x83' : chr(0x98),	# Ã
	'\\xc3\\x84' : chr(0x99),	# Ä
	'\\xc3\\x88' : chr(0x91),	# È 
	'\\xc3\\x89' : chr(0x92),	# É
	'\\xc3\\x8a' : chr(0x90),	# Ê
	'\\xc3\\x8b' : chr(0x92),	# Ê
	'\\xc3\\xa0' : chr(0x9c),	# Ë
	'\\xc3\\xa1' : chr(0x9d),	# á
	'\\xc3\\xa2' : chr(0x9b),	# â 
	'\\xc3\\xa7' : chr(0xc4),	# ç
	'\\xc3\\xa8' : chr(0x95),	# è
	'\\xc3\\xa9' : chr(0x96),	# é
	'\\xc3\\xaa' : chr(0x94),	# ê
	'\\xc3\\xab' : chr(0x97),	# ë
	'\\xc3\\xae' : chr(0xa4),	# î
	'\\xc3\\xaf' : chr(0xa4),	# ï

        # German unicode escape sequences not previously defined
        '\\xe1\\xba\\x9e' : chr(0xf5),  # ẞ
        '\\xc3\\x9f' : chr(0xf5),	# ẞ
        '\\xc3\\xa4' : chr(0x9e),	# ä
        '\\xc3\\xb6' : chr(0x8e),	# ö
        '\\xc3\\xbc' : chr(0x84),	# ü
        '\\xc3\\x96' : chr(0x8e),	# Ö 
        '\\xc3\\x9c' : chr(0x83),	# Ü 

	# Scandanavian unicode escape sequences
        '\\xc2\\x88' : 'A',   # aelig
        '\\xc2\\xb4' : 'A',   # aelig
        '\\xc3\\x85' : chr(0x98),	# Å
        '\\xc3\\x93' : chr(0x89),	# Ó
        '\\xc3\\x94' : chr(0x87),	# Ô
        '\\xc3\\x95' : 'O',		# Õ
        '\\xc3\\x98' : chr(0xc9),	# Ø
        '\\xc3\\x99' : chr(0x81),	# Ù
        '\\xc3\\x9a' : chr(0x82),	# Ú
        '\\xc3\\x9b' : chr(0x80),	# Û
        '\\xc3\\xa4' : chr(0x9e),	# ä
        '\\xc3\\xa5' : chr(0x9a),	# å
        '\\xc3\\x86' : chr(0xaf),	# Æ
        '\\xc3\\xa6' : 'ae',  		# æ
        '\\xc3\\xb0' : chr(0xcf),	# ð
        '\\xc3\\xb2' : chr(0x8c),	# ò
        '\\xc3\\xb3' : chr(0x8d),	# ó
        '\\xc3\\xb4' : chr(0x8b),   	# ô
        '\\xc3\\xb8' : chr(0xc0),   	# ø

	# Spanish (Not included above)
        '\\xc3\\xb1' : chr(0xa7),   	# ñ
        '\\xc3\\xbf' : chr(0x88),   	# ¿

	# Languages where only a few characters can be translated

	# Hungarian lower case (not covered elsewhere)
	'\\xc3\\xad' : chr(0xa2),	# í
	'\\xc3\\xba' : chr(0x86),	# ú
	
	# Miscellaneous
	'\\xc2\\xa3' : chr(0xb7),   # £
	'\\xc2\\xa9' : chr(0xdd),   # © 
	'\\xc2\\xae' : chr(0xdc),   # ®
}

# Romanized characters (converted to Latin characters)
romanized = {

	# Three byte characters (Must be checked first)
	'\\xe2\\x82\\xac' : 'Euro',	# Euro

        # French (Latin) unicode escape sequences
        '\\xc3\\x80' : 'A',     # A grave
        '\\xc3\\x81' : 'A',     # A acute
        '\\xc3\\x82' : 'A',     # A circumflex
        '\\xc3\\x83' : 'A',     # A tilde
        '\\xc3\\x88' : 'E',     # E grave
        '\\xc3\\x89' : 'E',     # E acute
        '\\xc3\\x8a' : 'E',     # E circumflex
        '\\xc3\\xa0' : 'a',     # a grave
        '\\xc3\\xa1' : 'a',     # a acute
        '\\xc3\\xa2' : 'a',     # a circumflex
        '\\xc3\\xa7' : 'c',     # c cedilla
        '\\xc3\\xa8' : 'e',     # e grave
        '\\xc3\\xa9' : 'e',     # e acute
        '\\xc3\\xaa' : 'e',     # e circumflex
        '\\xc3\\xab' : 'e',     # e diaeresis
        '\\xc3\\xae' : 'i',     # i circumflex
        '\\xc3\\xaf' : 'i',     # i diaeresis
        '\\xc3\\xb7' : "/",     # Division sign
        '\\xc5\\x93' : 'oe',    # oe joined

        # German unicode escape sequences not previously defined
        '\\xe1\\xba\\x9e' : 'ss', # ẞ
        '\\xc3\\x9f' : 'ss',	# ẞ
        '\\xc3\\xa4' : 'a',	# ä
        '\\xc3\\xb6' : 'o',	# ö
        '\\xc3\\xbc' : 'u',	# ü
        '\\xc3\\x96' : 'O',	# Ö 
        '\\xc3\\x9c' : 'U',	# Ü 

        # Scandanavian unicode escape sequences
        '\\xc2\\x88' : 'A',   # aelig
        '\\xc2\\xb4' : 'A',   # aelig
        '\\xc3\\x85' : 'Aa',  # Aring
        '\\xc3\\x93' : 'O',   # O grave
        '\\xc3\\xa4' : 'a',   # a with double dot
        '\\xc3\\xa5' : 'a',   # aring
        '\\xc3\\x86' : 'AE',  # AElig
        '\\xc3\\x98' : '0',   # O crossed
        '\\xc3\\x99' : 'U',   # U grave
        '\\xc3\\xa6' : 'ae',  # aelig
        '\\xc3\\xb0' : 'o',   # o umlaut
        '\\xc3\\xb2' : 'o',   # o tilde
        '\\xc3\\xb3' : 'o',   # o reverse tilde
        '\\xc3\\xb4' : 'o',   # Capital O circumflex
        '\\xc3\\xb8' : 'o',   # oslash

	# Spanish (not included above)
        '\\xc3\\xb1' : 'n',   	# ñ
        '\\xc3\\xbf' : '?',   	# ¿

	# Miscellaneous
	'\\xc2\\xa3' : chr(0x23),   # £
	'\\xc2\\xa9' : '(C)',       # © 
	'\\xc2\\xae' : '(R)',       # ®
}

# End of font tables
