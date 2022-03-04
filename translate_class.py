#!/usr/bin/env python3
# -*- coding: latin-1 -*-
#
# Raspberry Pi Radio Character translation class
# Escaped characters, html and unicode translation to ascii
#
# $Id: translate_class.py,v 1.8 2021/11/23 10:40:30 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#        The authors shall not be liable for any loss or damage however caused.
#
# Useful Links on character encodings
#   http://www.zytrax.com/tech/web/entities.html
#   http://www.utf8-chartable.de/
#   http://www.codetable.net/
#   http://www.ascii-code.com/
    
import os,sys
import unicodedata
import pdb
import glob
import importlib

from config_class import Configuration
config = Configuration()

class Translate:
    _translate = True
    _romanized = True
    _language = "English"
    _skip_further_translation = False   # Prevent furthur translation
                        # For example after converting Cyrillic
    _codes = None       # Native code table from codes/<language>.py
    _romanized_codes = None # Romanized code table from codes/<language>.py
    _controller = "HD44780" # Controller type

    code_pages = []
    English = None  # English font table set up in _import routine

    def __init__(self):
        # Import font table according to language
        self._language = config.language
        self._controller = config.controller
        self.code_pages = self._import_codes(self._language)
        if len(self.code_pages) < 1:
            print ("No code tables found for controller",self._controller)
            print ("and language",self._language, "Check /etc/radiod.conf")
            sys.exit(1)

    # Import all language font modules in the codes directory
    # Process the <font>.codes for the selected language first
    # Then import romanized codes in the rest and 
    # finally import English romanized codes
    # Returns a list of font tables 
    def _import_codes(self,language):
        translated  = False
        primary = False

        # Get all font tables inn the codes sub-directory
        dir = os.path.dirname(__file__)
        os.chdir(dir)
        font_files = sorted(glob.glob('codes/*.py'))
        code_pages = []     # List of font translation tables
        count = 20
    
        # Process codes
        while not translated and len(font_files) > 0: 
            if count < 0:
                break
            for i in range(0,len(font_files)):

                # Prevent endless loop
                count -= 1

                filepath = os.path.basename(font_files[i])
                font_name,ext = filepath.split('.') 

                # Skip init file 
                if font_name == "__init__":
                    continue

                # Skip HTMLcodes file 
                if font_name == "HTMLcodes":
                    continue

                # Skip if English and set it as primary
                if font_name == "English":
                    if language == "English":
                        primary = True
                    continue

                code_page = importlib.import_module('codes.' + font_name)
                if self._controller != code_page.controller:
                    continue

                #print (i,code_page.name,code_page.controller,font_name)

                if language == 'English' and not translated and not primary:
                    code_pages.append(code_page)
                    continue

                # process primary language
                if code_page.name == language:
                    if not primary:
                        code_pages.append(code_page)
                        primary = True
                    continue

                # If primary language processed
                if primary and font_name != language:
                    code_pages.append(code_page)
                    translated = True

        # Import English table as last one but don't add to array
        code_page = importlib.import_module('codes.' + "English")
        self.English = code_page
        return code_pages

    # Main conversion routine
    def all(self,text):
        if self._translate:
            # Convert escape codes to font ordinals using imported codes
            s = self._convert(text,self.code_pages)

            # Strip quotes
            if len(s) > 0:
                s = s.lstrip('"')
                s = s.rstrip('"')
        else:
            s = text
        return s

    # Translate unicode for RSS feeds
    def rss(self,text):
        s = text
        # Translate HTML codes etc.
        #s = self._translate_unicode(self.HTML_codes.rss_amp_codes,text,delete=False)
        #s = self._translate_unicode(self.HTML_codes.rss_codes,text,delete=False)

        s = self.all(s)
        s = s.lstrip('<')
        return str(s)

    # This routine converts the escape codes for each code table
    # to the font table ordinal of the LCD
    def _convert(self,text,code_pages):
        s = self._convert2escape(text)
        for i in range(0,len(code_pages)):
            code_page = code_pages[i]
            if not self._romanized and i==0:
                s = self._translate_unicode(code_page.codes,s)
            else:
                s = self._translate_unicode(code_page.romanized,s)

            # Finally process English font table
            s = self._translate_unicode(self.English.romanized,s,delete=False)
        return s

    # Convert unicode to escape codes
    def _convert2escape(self,text):
        s = str(text.encode('utf-8')).lstrip('b')
        if s.__len__() > 2: 
            s = s.lstrip('\'')
            s = s.rstrip('\'')
        return s

    # Do translation using supplied translation table
    # and delete the already translated code from code/font table
    def _translate_unicode(self, codes, text, delete=True):
        s = text
        for code in codes:
            l1 =  len(s)
            s = s.replace(code, codes[code])

            if delete:
                # Prevent double conversion
                l2 = len(s)
                if l1 != l2:
                    try:
                        del self.English.codes[code] 
                    except:
                        pass
        return s

    # Translation on off (See translate_lcd in /etc/radiod.conf)
    def setTranslate(self,true_false):
        self._translate = true_false

    # Translation on off (See romanize in /etc/radiod.conf)
    def setRomanize(self,true_false):
        self._romanized = true_false

    # Get the code page from the primary font table 
    def getPrimaryCodePage(self):
        return self.code_pages[0].codepage

    # Get font files
    def getFontFiles(self):
        font_files = []
        for cp in self.code_pages:
            x = str(cp)
            files = x.split(' ')
            font_files.append(files[1])
        x = str(self.English)   
        files = x.split(' ')
        font_files.append(files[1])
        return font_files

        
# End of class

# Test translate class
if __name__ == '__main__':

    translate = Translate() # Test routine object

    if len(sys.argv) > 1:
        text = sys.argv[1]
    else:
        text = 'ABCDEF 012345'
    print (text)

    s = translate._convert2escape(text)
    print()
    print (s)

    # Complete text
    print (translate.all(text))
    print('')
    sys.exit(0)
# End of file
# set tabstop=4 shiftwidth=4 expandtab
# retab
