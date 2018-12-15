#!/usr/bin/env python
# -*- coding: latin-1 -*-
#
# Raspberry Pi Radio Character translation class
# Escaped characters, html and unicode translation to ascii
#
# $Id: translate_class.py,v 1.11 2018/11/14 13:15:39 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#	     The authors shall not be liable for any loss or damage however caused.
#
# Useful Links on character encodings
#  	http://www.zytrax.com/tech/web/entities.html
#	http://www.utf8-chartable.de/
#	http://www.codetable.net/
#	http://www.ascii-code.com/
	
import os,sys
import time
import unicodedata
from log_class import Log


log = Log()

class Translate:
	displayUmlauts = True
	_translate = True

	# Escaped codes (from unicode)
	codes = {
		'//' : '/', 	   # Double /
		'  ' : ' ',	# Double spaces
		'\\n' : ' ',       # Line feed  to space

		# German UTF8 codes
		'\\xef\\xbf\\xbd' : chr(246),
	
		# Currencies
		'\\xe2\\x82\\xac' : ' Euro ',

		# Special characters
		'\\x80\\x99' : "'",	# Single quote 
		'\\xc2\\xa1' : '!',	# Inverted exclamation
		'\\xc2\\xa2' : 'c',	# Cent sign
		'\\xc2\\xa3' : '#',	# Pound sign
		'\\xc2\\xa4' : '$',	# Currency sign
		'\\xc2\\xa5' : 'Y',	# Yen sign
		'\\xc2\\xa6' : '|',	# Broken bar
		'\\xc2\\xa7' : '?',	# Section sign
		'\\xc2\\xa8' : ':',	# Diaerisis
		'\\xc2\\xa9' : '(C)',      # Copyright
		'\\xc2\\xaa' : '?',	# Feminal ordinal
		'\\xc2\\xab' : '<<',       # Double left
		'\\xc2\\xac' : '-',	# Not sign
		'\\xc2\\xad' : '',	 # Soft hyphen
		'\\xc2\\xae' : '(R)',      # Registered sign
		'\\xc2\\xaf' : '-',	# Macron
		'\\xc2\\xb0' : 'o',	# Degrees sign
		'\\xc2\\xb1' : '+-',       # Plus minus
		'\\xc2\\xb2' : '2',	# Superscript 2
		'\\xc2\\xb3' : '3',	# Superscript 3
		'\\xc2\\xb4' : '',	 # Acute accent
		'\\xc2\\xb5' : 'u',	# Micro sign
		'\\xc2\\xb6' : '',	 # Pilcrow
		'\\xc2\\xb7' : '.',	# Middle dot
		'\\xc2\\xb8' : '',	 # Cedilla
		'\\xc2\\xb9' : '1',	# Superscript 1
		'\\xc2\\xba' : '',	 # Masculine indicator
		'\\xc2\\xbb' : '>>',       # Double right
		'\\xc2\\xbc' : '1/4',      # 1/4 fraction
		'\\xc2\\xbd' : '1/2',      # 1/2 Fraction
		'\\xc2\\xbe' : '3/4',      # 3/4 Fraction
		'\\xc2\\xbf' : '?',	# Inverted ?

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

		# French (Latin) unicode escape sequences
		'\\xc3\\x80' : 'A',	# A grave
		'\\xc3\\x81' : 'A',	# A acute
		'\\xc3\\x82' : 'A',	# A circumflex
		'\\xc3\\x83' : 'A',	# A tilde
		'\\xc3\\x88' : 'E',	# E grave
		'\\xc3\\x89' : 'E',	# E acute
		'\\xc3\\x8a' : 'E',	# E circumflex
		'\\xc3\\xa0' : 'a',   	   # a grave
		'\\xc3\\xa1' : 'a',   	   # a acute
		'\\xc3\\xa2' : 'a',   	   # a circumflex
		'\\xc3\\xa7' : 'c',	# c cedilla
		'\\xc3\\xa8' : 'e',	# e grave
		'\\xc3\\xa9' : 'e',   	   # e acute
		'\\xc3\\xaa' : 'e',	# e circumflex
		'\\xc3\\xab' : 'e',	# e diaeresis
		'\\xc3\\xae' : 'i',	# i circumflex
		'\\xc3\\xaf' : 'i',	# i diaeresis
		'\\xc3\\xb7' : "/",	# Division sign
		'\\xc5\\x93' : 'oe',       # oe joined

		# Hungarian lower case
		'\\xc3\\xb3' : 'o',	# o circumflex 
		'\\xc3\\xad' : 'i',   	   # i accent
		'\\xc3\\xb5' : 'o',	# o tilde
		'\\xc5\\x91' : 'o',   	   #  o 
		'\\xc5\\xb1' : chr(252),   # 
		'\\xc3\\xba' : 'u',	# u acute

		# Polish unicode escape sequences
		'\\xc4\\x84' : 'A',	# A,
		'\\xc4\\x85' : 'a',	# a,
		'\\xc4\\x86' : 'C',	# C'
		'\\xc4\\x87' : 'c',	# c'
		'\\xc4\\x98' : 'E',	# E,
		'\\xc4\\x99' : 'e',	# e,
		'\\xc5\\x81' : 'L',	# L/
		'\\xc5\\x82' : 'l',	# l/
		'\\xc5\\x83' : 'N',	# N'
		'\\xc5\\x84' : 'n',	# n'
		'\\xc5\\x9a' : 'S',	# S'
		'\\xc5\\x9b' : 's',	# s'
		'\\xc5\\xb9' : 'Z',	# Z'
		'\\xc5\\xba' : 'z',	# z'
		'\\xc5\\xbb' : 'Z',	# Z.
		'\\xc5\\xbc' : 'z',	# z.

		# Greek upper case
		'\\xce\\x91' : 'A',	# Alpha
		'\\xce\\x92' : 'B',	# Beta
		'\\xce\\x93' : 'G',	# Gamma
		'\\xce\\x94' : 'D',	# Delta
		'\\xce\\x95' : 'E',	# Epsilon
		'\\xce\\x96' : 'Z',	# Zeta
		'\\xce\\x97' : 'H',	# Eta
		'\\xce\\x98' : 'TH',       # Theta
		'\\xce\\x99' : 'I',	# Iota
		'\\xce\\x9a' : 'K',	# Kappa
		'\\xce\\x9b' : 'L',	# Lamda
		'\\xce\\x9c' : 'M',	# Mu
		'\\xce\\x9e' : 'N',	# Nu
		'\\xce\\x9f' : 'O',	# Omicron
		'\\xce\\xa0' : 'Pi',       # Pi
		'\\xce '     : 'Pi',       # Pi ?
		'\\xce\\xa1' : 'R',	# Rho
		'\\xce\\xa3' : 'S',	# Sigma
		'\\xce\\xa4' : 'T',	# Tau
		'\\xce\\xa5' : 'Y',	# Upsilon
		'\\xce\\xa6' : 'F',	# Fi
		'\\xce\\xa7' : 'X',	# Chi
		'\\xce\\xa8' : 'PS',       # Psi
		'\\xce\\xa9' : 'O',	# Omega

		# Greek lower case
		'\\xce\\xb1' : 'a',	# Alpha
		'\\xce\\xb2' : 'b',	# Beta
		'\\xce\\xb3' : 'c',	# Gamma
		'\\xce\\xb4' : 'd',	# Delta
		'\\xce\\xb5' : 'e',	# Epsilon
		'\\xce\\xb6' : 'z',	# Zeta
		'\\xce\\xb7' : 'h',	# Eta
		'\\xce\\xb8' : 'th',       # Theta
		'\\xce\\xb9' : 'i',	# Iota
		'\\xce\\xba' : 'k',	# Kappa
		'\\xce\\xbb' : 'l',	# Lamda
		'\\xce\\xbc' : 'm',	# Mu
		'\\xce\\xbd' : 'v',	# Nu
		'\\xce\\xbe' : 'ks',       # Xi
		'\\xce\\xbf' : 'o',	# Omicron
		'\\xce\\xc0' : 'p',	# Pi
		'\\xce\\xc1' : 'r',	# Rho
		'\\xce\\xc3' : 's',	# Sigma
		'\\xce\\xc4' : 't',	# Tau
		'\\xce\\xc5' : 'y',	# Upsilon
		'\\xce\\xc6' : 'f',	# Fi
		'\\xce\\xc7' : 'x',	# Chi
		'\\xce\\xc8' : 'ps',       # Psi
		'\\xce\\xc9' : 'o',	# Omega

		# Icelandic 
		'\\xc3\\xbe' : 'p',	# Like a p with up stroke
		'\\xc3\\xbd' : 'y',	# y diaeresis

		# Italian characters
		'\\xc3\\xac' : 'i',	# i reverse circumflex
		'\\xc3\\xb9' : 'u',	# u reverse circumflex

		# Polish (not previously covered)
		'\\xc3\\xa3' : 'a',	# a tilde

		# Romanian
		'\\xc4\\x83' : 'a',	# a circumflex variant
		'\\xc3\\xa2' : 'a',	# a circumflex 
		'\\xc3\\xae' : 'i',	# i circumflex 
		'\\xc5\\x9f' : 's',	# s cedilla ?
		'\\xc5\\xa3' : 's',	# t cedilla ?
		'\\xc8\\x99' : 's',	# s with down stroke
		'\\xc8\\x9b' : 't',	# t with down stroke

		# Spanish not covered above
		'\\xc3\\xb1' : 'n',	# n tilde

		# Turkish not covered above
		'\\xc3\\xbb' : 'u',	# u circumflex
		'\\xc4\\x9f' : 'g',	# g tilde
		'\\xc4\\xb1' : 'i',	# Looks like an i
		'\\xc4\\xb0' : 'I',	# Looks like an I
	}

	# UTF8 codes (Must be checked after above codes checked)
	short_codes = {
		'\\xa0' : ' ',     # Line feed to space
		'\\xa3' : '#',     # Pound character

		'\\xb4' : "'",    # Apostrophe 
		'\\xc0' : 'A',    # A 
		'\\xc1' : 'A',    # A 
		'\\xc2' : 'A',    # A 
		'\\xc3' : 'A',    # A 
		'\\xc4' : 'A',    # A 
		'\\xc5' : 'A',    # A 
		'\\xc6' : 'Ae',   # AE
		'\\xc7' : 'C',    # C 
		'\\xc8' : 'E',    # E 
		'\\xc9' : 'E',    # E 
		'\\xca' : 'E',    # E 
		'\\xcb' : 'E',    # E 
		'\\xcc' : 'I',    # I 
		'\\xcd' : 'I',    # I 
		'\\xce' : 'I',    # I 
		'\\xcf' : 'I',    # I 
		'\\xd0' : 'D',    # D
		'\\xd1' : 'N',    # N 
		'\\xd2' : 'O',    # O 
		'\\xd3' : 'O',    # O 
		'\\xd4' : 'O',    # O 
		'\\xd5' : 'O',    # O 
		'\\xd6' : 'O',    # O 
		'\\xd7' : 'x',    # Multiply
		'\\xd8' : '0',    # O crossed 
		'\\xd9' : 'U',    # U 
		'\\xda' : 'U',    # U 
		'\\xdb' : 'U',    # U 
		'\\xdc' : 'U',    # U umlaut
		'\\xdd' : 'Y',    # Y
		'\\xdf' : 'S',    # Sharp s es-zett
		'\\xe0' : 'e',    # Small a reverse acute
		'\\xe1' : 'a',    # Small a acute
		'\\xe2' : 'a',    # Small a circumflex
		'\\xe3' : 'a',    # Small a tilde
		'\\xe4' : 'a',    # Small a diaeresis
		'\\xe5' : 'aa',   # Small a ring above
		'\\xe6' : 'ae',   # Joined ae
		'\\xe7' : 'c',    # Small c Cedilla
		'\\xe8' : 'e',    # Small e grave
		'\\xe9' : 'e',    # Small e acute
		'\\xea' : 'e',    # Small e circumflex
		'\\xeb' : 'e',    # Small e diarisis
		'\\xed' : 'i',    # Small i acute
		'\\xee' : 'i',    # Small i circumflex
		'\\xf1' : 'n',    # Small n tilde
		'\\xf3' : 'o',    # Small o acute
		'\\xf4' : 'o',    # Small o circumflex
		'\\xf6' : 'o',    # o umlaut
		'\\xf7' : '/',    # Division sign
		'\\xf8' : 'oe',   # Small o strike through 
		'\\xf9' : 'u',    # Small u circumflex
		'\\xfa' : 'u',    # Small u acute
		'\\xfb' : 'u',    # u circumflex
		'\\xfd' : 'y',    # y circumflex
		'\\xc0' : 'A',    # Small A grave
		'\\xc1' : 'A',    # Capital A acute
		'\\xc7' : 'C',    # Capital C Cedilla
		'\\xc9' : 'E',    # Capital E acute
		'\\xcd' : 'I',    # Capital I acute
		'\\xd3' : 'O',    # Capital O acute
		'\\xda' : 'U',    # Capital U acute
		'\\xfc' : 'u',    # u umlaut
		'\\xbf' : '?',    # Spanish Punctuation

		'\\xb0'  : 'o',	       # Degrees symbol
	}

	# HTML codes (RSS feeds)
	HtmlCodes = {
		# Currency
		chr(156) : '#',       # Pound by hash
		chr(169) : '(c)',     # Copyright

		# Norwegian
		chr(216) : '0',       # Oslash

		# Spanish french
		chr(241) : 'n',       # Small tilde n
		chr(191) : '?',       # Small u acute to u
		chr(224) : 'a',       # Small a grave to a
		chr(225) : 'a',       # Small a acute to a
		chr(226) : 'a',       # Small a circumflex to a
		chr(232) : 'e',       # Small e grave to e
		chr(233) : 'e',       # Small e acute to e
		chr(234) : 'e',       # Small e circumflex to e
		chr(235) : 'e',       # Small e diarisis to e
		chr(237) : 'i',       # Small i acute to i
		chr(238) : 'i',       # Small i circumflex to i
		chr(243) : 'o',       # Small o acute to o
		chr(244) : 'o',       # Small o circumflex to o
		chr(250) : 'u',       # Small u acute to u
		chr(251) : 'u',       # Small u circumflex to u
		chr(192) : 'A',       # Capital A grave to A
		chr(193) : 'A',       # Capital A acute to A
		chr(201) : 'E',       # Capital E acute to E
		chr(205) : 'I',       # Capital I acute to I
		chr(209) : 'N',       # Capital N acute to N
		chr(211) : 'O',       # Capital O acute to O
		chr(218) : 'U',       # Capital U acute to U
		chr(220) : 'U',       # Capital U umlaut to U
		chr(231) : 'c',       # Small c Cedilla
		chr(199) : 'C',       # Capital C Cedilla

		# German
		chr(196) : "Ae",      # A umlaut
		chr(214) : "Oe",      # O umlaut
		chr(220) : "Ue",      # U umlaut
	}


	unicodes = {
		'\\u201e' : '"',       # ORF feed
		'\\u3000' : " ", 
		'\\u201c' : '"', 
		'\\u201d' : '"', 
		'\\u0153' : "oe",      # French oe
		'\\u2009' : ' ',       # Short space to space
		'\\u2013' : '-',       # Long dash to minus sign
		'\\u2018' : "'",       # Left single quote
		'\\u2019' : "'",       # Right single quote

		# Czech
		'\\u010c' : "C",       # C cyrillic
		'\\u010d' : "c",       # c cyrillic
		'\\u010e' : "D",       # D cyrillic
		'\\u010f' : "d",       # d cyrillic
		'\\u011a' : "E",       # E cyrillic
		'\\u011b' : "e",       # e cyrillic
		'\\u013a' : "I",       # I cyrillic
		'\\u013d' : "D",       # D cyrillic
		'\\u013e' : "I",       # I cyrillic
		'\\u0139' : "L",       # L cyrillic
		'\\u0147' : "N",       # N cyrillic
		'\\u0148' : "n",       # n cyrillic
		'\\u0154' : "R",       # R cyrillic
		'\\u0155' : "r",       # r cyrillic
		'\\u0158' : "R",       # R cyrillic
		'\\u0159' : "r",       # r cyrillic
		'\\u0160' : "S",       # S cyrillic
		'\\u0161' : "s",       # s cyrillic
		'\\u0164' : "T",       # T cyrillic
		'\\u0165' : "t",       # t cyrillic
		'\\u016e' : "U",       # U cyrillic
		'\\u016f' : "u",       # u cyrillic
		'\\u017d' : "Z",       # Z cyrillic
		'\\u017e' : "z",       # z cyrillic
		}

	def __init__(self):
		log.init('radio')
		return    

	# Translate all  (Called by rss class)
	def all(self,text):
		if self._translate:
			s = self._convert2escape(text)
			s = self._escape(s)
			s = self._unicode(s)
			s = self._html(s)
		else:
			s = text
		return s   

	# Convert unicode to escape codes
	def _convert2escape(self,text):
		s = repr(text)
		if s.__len__() > 2: 
			s = s.lstrip('\'')
			s = s.rstrip('\'')
		return s

	# Convert escaped characters (umlauts) to normal characters
	def escape(self,text):
		s = ''
		if self._translate:
			if len(text) > 0:
				s = self._convert2escape(text)
				s = self._escape(s)
				s = s.lstrip('"')
				s = s.rstrip('"')
		else:
			s = text
		return s

	def escape_translate(self,text):
		s = text
		if self._translate:
			s = self._convert2escape(text)
			s = self._escape(s)
			s = s.lstrip('"')
			s = s.rstrip('"')
		return s

	# Convert escaped characters (umlauts etc.) to normal characters
	def _escape(self,text):
		s = text
		for code in self.codes:
			s = s.replace(code, self.codes[code])

		for code in self.short_codes:
			s = s.replace(code, self.short_codes[code])

		s = s.replace("'oC",'oC')   # Degrees C fudge
		s = s.replace("'oF",'oF')   # Degrees C fudge
		return s

	# HTML translations (callable)
	def html(self,text):
		s = self._html(s)
		_convert_html(s)
		return s

	# HTML translations
	def _html(self,text):
		s = text
		s = s.replace('&lt;', '<') 
		s = s.replace('&gt;', '>') 
		s = s.replace('&quot;', '"') 
		s = s.replace('&nbsp;', ' ') 
		s = s.replace('&amp;', '&') 
		s = s.replace('&copy;', '(c)') 
		return s

	# Convert &#nn sequences
	def _convert_html(s):
		c = re.findall('&#[0-9][0-9][0-9]', s)
		c += re.findall('&#[0-9][0-9]', s)
		for html in c:
			ch = int(html.replace('&#', ''))
			if ch > 31 and ch < 127:
				s = s.replace(html,chr(ch))
			else:
				s = s.replace(html,'')
		return s

	# Unicodes etc (callable)
	def unicode(self,text):
		s = text
		if self._translate:
			s = self._convert2escape(text)
			s = self._unicode(s)
		return s

	# Unicodes etc
	def _unicode(self,text):
		s = text
		for unicode in self.unicodes:
			s = s.replace(unicode, self.unicodes[unicode])
		return s

	# Decode greek
	def decode_greek(self,text):
		s = text.decode('macgreek')
		return s

	# Display umlats as oe ae etc
	def displayUmlauts(self,value):
		self.displayUmlauts = value
		return

	# Translate special characters (umlautes etc) to LCD values
	# See standard character patterns for LCD display
	def toLCD(self,sp):
		s = sp
		for HtmlCode in self.HtmlCodes:
			s = s.replace(HtmlCode, self.HtmlCodes[HtmlCode])

		if self.displayUmlauts:
			s = s.replace(chr(223), chr(226))       # Sharp s
			s = s.replace(chr(246), chr(239))       # o umlaut (Problem in Hungarian?)
			s = s.replace(chr(228), chr(225))       # a umlaut
			s = s.replace(chr(252), chr(245))       # u umlaut (Problem in Hungarian?)
		else:
			s = s.replace(chr(228), "ae")	   # a umlaut
			s = s.replace(chr(223), "ss")	   # Sharp s
			s = s.replace(chr(246), "oe")	   # o umlaut
			s = s.replace(chr(252), "ue")	   # u umlaut
		return s

	# Translation on off (Used by gradio)
	def setTranslate(self,true_false):
		self._translate = true_false

# End of class

# Test translate class
if __name__ == '__main__':

	translate = Translate()

	if len(sys.argv) > 1:
		text = sys.argv[1]
	else:
		text = 'æ Æ ø Ø å Å'
	print (text)
	s = translate._convert2escape(text)
	print (s)

	# Complete text
	print (translate.all(text))
	print()
	sys.exit(0)
# End of file
