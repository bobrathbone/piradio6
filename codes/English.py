# -*- coding: latin-1 -*-
#
# Raspberry Pi Radio Character translation class
# Escaped characters, html and unicode translation to ascii
#
# $Id: English.py,v 1.5 2020/04/19 11:14:20 bob Exp $
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

# The following codes are best effort to translate European charachters to their
# English equivelent. The tables are not perfect nor complete so amend if necessay

name = "English"  # Language name, to check against language parameter in /etc/radiod.conf
controller = "HD44780U"	# Used by all controllers as English chart tables are always the same
codepage = 0x0 	# Code page 0x0, 0x1 or 0x2

# Escaped codes (from unicode)
codes = {
	'//' : '/',        # Double /
	'  ' : ' ',     # Double spaces
	'\\n' : ' ',       # Line feed  to space

	# Three byte codes must be checked first
	# German UTF8 codes
	'\\xef\\xbf\\xbd' : chr(246),

	# Currencies and special characters
	'\\xe2\\x82\\xac' : ' Euro ',
	'\\xe2\\x80\\x98' : "'",
	'\\xe2\\x80\\x99' : "'",
	'\\xe2\\x80\\x9c' : '"',
	'\\xe2\\x80\\x9d' : '"',

	# Special characters
	'\\x80\\x99' : "'",     # Single quote
	'\\xc2\\xa1' : '!',     # Inverted exclamation
	'\\xc2\\xa2' : 'c',     # Cent sign
	'\\xc2\\xa3' : '#',     # Pound sign
	'\\xc2\\xa4' : '$',     # Currency sign
	'\\xc2\\xa5' : 'Y',     # Yen sign
	'\\xc2\\xa6' : '|',     # Broken bar
	'\\xc2\\xa7' : '?',     # Section sign
	'\\xc2\\xa8' : ':',     # Diaerisis
	'\\xc2\\xa9' : '(C)',      # Copyright
	'\\xc2\\xaa' : '?',     # Feminal ordinal
	'\\xc2\\xab' : '<<',       # Double left
	'\\xc2\\xac' : '-',     # Not sign
	'\\xc2\\xad' : '',       # Soft hyphen
	'\\xc2\\xae' : '(R)',      # Registered sign
	'\\xc2\\xaf' : '-',     # Macron
	'\\xc2\\xb0' : 'o',     # Degrees sign
	'\\xc2\\xb1' : '+-',       # Plus minus
	'\\xc2\\xb2' : '2',     # Superscript 2
	'\\xc2\\xb3' : '3',     # Superscript 3
	'\\xc2\\xb4' : '',       # Acute accent
	'\\xc2\\xb5' : 'u',     # Micro sign
	'\\xc2\\xb6' : '',       # Pilcrow
	'\\xc2\\xb7' : '.',     # Middle dot
	'\\xc2\\xb8' : '',       # Cedilla
	'\\xc2\\xb9' : '1',     # Superscript 1
	'\\xc2\\xba' : '',       # Masculine indicator
	'\\xc2\\xbb' : '>>',       # Double right
	'\\xc2\\xbc' : '1/4',      # 1/4 fraction
	'\\xc2\\xbd' : '1/2',      # 1/2 Fraction
	'\\xc2\\xbe' : '3/4',      # 3/4 Fraction
	'\\xc2\\xbf' : '?',     # Inverted ?


	# German unicode escape sequences
	'\\xc3\\x83' : chr(223),   # Sharp s es-zett
	'\\xc3\\x9f' : chr(223),   # Sharp s ?
	'\\xc3\\xa4' : chr(228),   # a umlaut
	'\\xc3\\xb6' : chr(246),   # o umlaut
	'\\xc3\\xbc' : chr(252),   # u umlaut
	'\\xc3\\x84' : chr(196),   # A umlaut
	'\\xc3\\x96' : chr(214),   # O umlaut
	'\\xc3\\x9c' : chr(220),   # U umlaut

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

	# Hungarian upper case (not covered elsewhere)
	'\\xc3\\x8d' : 'I',	# Í ?
	'\\xc3\\x90' : 'O',	# Ő
	'\\xc3\\x93' : 'O',	# Ó
	'\\xc3\\x96' : 'O',	# Ö
	'\\xc3\\x9a' : 'U',	# Ú
	'\\xc3\\x9c' : 'U',	# Ü
	'\\xc5\\xb0' : 'U',	# Ű
	'\\xc5\\xbd' : 'Z',	# Ž
	'\\xc5\\x90' : 'O',	# Ő ?

	# Hungarian lower case (not covered elsewhere)
	'\\xc3\\xad' : 'i',	# í
	'\\xc3\\xb3' : 'o',	# ó
	'\\xc3\\xba' : 'u',	# ú
	'\\xc5\\xb1' : 'u',	# ű
	'\\xc5\\x91' : 'o',	# ő

	# Polish unicode escape sequences
	'\\xc4\\x84' : 'A',     # A,
	'\\xc4\\x85' : 'a',     # a,
	'\\xc4\\x86' : 'C',     # C'
	'\\xc4\\x87' : 'c',     # c'
	'\\xc4\\x98' : 'E',     # E,
	'\\xc4\\x99' : 'e',     # e,
	'\\xc5\\x81' : 'L',     # L/
	'\\xc5\\x82' : 'l',     # l/
	'\\xc5\\x83' : 'N',     # N'
	'\\xc5\\x84' : 'n',     # n'
	'\\xc5\\x9a' : 'S',     # S'
	'\\xc5\\x9b' : 's',     # s'
	'\\xc5\\xb9' : 'Z',     # Z'
	'\\xc5\\xba' : 'z',     # z'
	'\\xc5\\xbb' : 'Z',     # Z.
	'\\xc5\\xbc' : 'z',     # z.

       # Greek upper case
	'\\xce\\x91' : 'A',     # Alpha
	'\\xce\\x92' : 'B',     # Beta
	'\\xce\\x93' : 'G',     # Gamma
	'\\xce\\x94' : 'D',     # Delta
	'\\xce\\x95' : 'E',     # Epsilon
	'\\xce\\x96' : 'Z',     # Zeta
	'\\xce\\x97' : 'H',     # Eta
	'\\xce\\x98' : 'TH',       # Theta
	'\\xce\\x99' : 'I',     # Iota
	'\\xce\\x9a' : 'K',     # Kappa
	'\\xce\\x9b' : 'L',     # Lamda
	'\\xce\\x9c' : 'M',     # Mu
	'\\xce\\x9e' : 'N',     # Nu
	'\\xce\\x9f' : 'O',     # Omicron
	'\\xce\\xa0' : 'Pi',       # Pi
	'\\xce '     : 'Pi',       # Pi ?
	'\\xce\\xa1' : 'R',     # Rho
	'\\xce\\xa3' : 'S',     # Sigma
	'\\xce\\xa4' : 'T',     # Tau
	'\\xce\\xa5' : 'Y',     # Upsilon
	'\\xce\\xa6' : 'F',     # Fi
	'\\xce\\xa7' : 'X',     # Chi
	'\\xce\\xa8' : 'PS',       # Psi
	'\\xce\\xa9' : 'O',     # Omega

	# Greek lower case
	'\\xce\\xb1' : 'a',     # Alpha
	'\\xce\\xb2' : 'b',     # Beta
	'\\xce\\xb3' : 'c',     # Gamma
	'\\xce\\xb4' : 'd',     # Delta
	'\\xce\\xb5' : 'e',     # Epsilon
	'\\xce\\xb6' : 'z',     # Zeta
	'\\xce\\xb7' : 'h',     # Eta
	'\\xce\\xb8' : 'th',       # Theta
	'\\xce\\xb9' : 'i',     # Iota
	'\\xce\\xba' : 'k',     # Kappa
	'\\xce\\xbb' : 'l',     # Lamda
	'\\xce\\xbc' : 'm',     # Mu
	'\\xce\\xbd' : 'v',     # Nu
	'\\xce\\xbe' : 'ks',       # Xi
	'\\xce\\xbf' : 'o',     # Omicron
	'\\xce\\xc0' : 'p',     # Pi
	'\\xce\\xc1' : 'r',     # Rho
	'\\xce\\xc3' : 's',     # Sigma
	'\\xce\\xc4' : 't',     # Tau
	'\\xce\\xc5' : 'y',     # Upsilon
	'\\xce\\xc6' : 'f',     # Fi
	'\\xce\\xc7' : 'x',     # Chi
	'\\xce\\xc8' : 'ps',       # Psi
	'\\xce\\xc9' : 'o',     # Omega

	# Icelandic
	'\\xc3\\xbe' : 'p',     # Like a p with up stroke
	'\\xc3\\xbd' : 'y',     # y diaeresis

	# Italian characters
	'\\xc3\\xac' : 'i',     # i reverse circumflex
	'\\xc3\\xb9' : 'u',     # u reverse circumflex

	# Polish (not previously covered)
	'\\xc3\\xa3' : 'a',     # a tilde

	# Romanian
	'\\xc4\\x83' : 'a',     # a circumflex variant
	'\\xc3\\xa2' : 'a',     # a circumflex
	'\\xc3\\xae' : 'i',     # i circumflex
	'\\xc5\\x9f' : 's',     # s cedilla ?
	'\\xc5\\xa3' : 's',     # t cedilla ?
	'\\xc8\\x99' : 's',     # s with down stroke
	'\\xc8\\x9b' : 't',     # t with down stroke

	# Spanish not covered above
	'\\xc3\\xb1' : 'n',     # n tilde

	# Turkish not covered above
	'\\xc3\\xbb' : 'u',     # u circumflex
	'\\xc4\\x9f' : 'g',     # g tilde
	'\\xc4\\xb1' : 'i',     # Looks like an i
	'\\xc4\\xb0' : 'I',     # Looks like an I
	}

# Dummy codes as English is already Romanized
romanized = codes 

# End of English convertion table 
