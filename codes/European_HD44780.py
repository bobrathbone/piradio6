# -*- coding: latin-1 -*-
#
# OLED/LCD Western European languages character translation table
# Escaped characters, html and unicode translation to ascii
#
# $Id: European_HD44780.py,v 1.5 2023/01/24 09:52:05 bob Exp $
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

# The following codes are best effort to translate European characters to the
# available LCD fonts. The tables are not perfect nor complete so amend if necessary
# Note that this table is for controller HD44780 character character table A02 
# Do not use for HD44780U controller devices. See Russian.py

name = "European"  # Language name, to check against language statement in /etc/radiod.conf
controller = "HD44780"      # Used by HD44780 controllers using code chart 0x1
codepage = 0x0  # Code page 0x0, 0x1 or 0x2

# Romanized characters (converted to Latin characters)
romanized = {
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
}

# Dummy table The HD44870 cannot support Russian Western European
# Use an LCD with HD44870U/MC0100  controller and support
# for English/European/Japanese and Russian
codes = romanized
# End of European font code tables
