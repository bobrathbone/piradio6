#!/usr/bin/python
# -*- coding: latin-1 -*-
#
# $Id: rss_class.py,v 1.20 2020/05/09 12:48:01 bob Exp $
# Raspberry Pi RSS feed class
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#	     The authors shall not be liable for any loss or damage however caused.
#


import os
import time
import urllib2
import importlib
import pdb 

from xml.dom.minidom import parseString
from log_class import Log

log = Log()
url = "/var/lib/radiod/rss"
DELAY = 5

class Rss:
	rss = []	# Array for the RSS feed

	HTMLcodes = None	# HTML entities

	# Fields for scrolling routine
	rss_delay1 = 0
	rss_delay2 = 0
	rss_line1 = ''
	rss_line2 = ''

	translate = None	# Translate class setup in __init__
	_translate = True


	length = 0	# Number of RSS news items
	feed_available = False
	rss_error = False # RSS Error (prevents repetitive error logging)

	def __init__(self,translate):
		self.translate = translate
		log.init('radio')
		if os.path.isfile(url):
			self.feed_available = True

		# Import HTML codes from codes sub-directory
                self.HTMLcodes = importlib.import_module('codes.' + "HTMLcodes")
		return    

	# Gets the next RSS entry from the rss array
	def getFeed(self):
		self.feed_available = False
		line = "No RSS feed"
		#pdb.set_trace()
		if self.length < 1:
			self.rss = self.get_new_feed(url)    
			self.length = self.rss.__len__()

		if self.length > 0:
			self.feed_available = True
			feed = self.rss.pop()
			self.length -= 1
			
			feed = self._remove_content(feed)	# Do before strip entities
			feed = self._strip_entities(feed)

			# Translate into language LCD codes
			feed = self.translate.rss(feed)
		return feed

	# Strip out quotes etc
	def _strip_entities(self,text):
		s = text
		for entity in self.HTMLcodes.rss_amp_codes:
			s = s.replace(entity,'')
		for entity in self.HTMLcodes.html_entities:
			s = s.replace(entity,'')
		return s

	# Is an RSS news feed available
	def isAvailable(self):
		return self.feed_available

	# Get a new feed and put it into the rss array
	def get_new_feed(self,url):
		rss = []
		if os.path.isfile(url):
			rss_feed = self.execCommand("cat " + url)
			try:
				file = urllib2.urlopen(rss_feed)
				data = file.read()
				file.close()
				dom = parseString(data)
				dom.normalize()
				rss = self.parse_feed(dom)
				self.rss_error = False # Clear RSS Error
				log.message("Getting RSS feed: " + rss_feed,log.INFO)
			except:
				if not self.rss_error:
					log.message("Invalid RSS feed: " + rss_feed,log.ERROR)
					self.rss_error = True  # Set RSS error
				rss.append("No RSS feed found")
		return rss
		
	# Parse XML line
	def parse_feed(self,dom):	
		rss = []
		for news in dom.getElementsByTagName('*'):
			display = False
			line = news.toxml()
			line = line.replace("&lt;", "<")	# Replace special string
			line = line.replace("&gt;", ">")
			
			msg =  "LINE:" + line
			line = line.lstrip(' ')
			if (line.find("VIDEO:") != -1):
				continue
			if (line.find("AUDIO:") != -1):
				continue
			if (line.find("<rss") != -1):
				continue
			if (line.find("<item") != -1):
				continue
			if (line.find("<image") == 0):
				continue
			if (line.find("<title>") >= 0):
				display= True
			if (line.find("<description>") >= 0):
				display= True

			if display:
				title = ''
				description = ''
				line = line.rstrip(' ')
				line = line.replace("![CDATA[", "")
				line = line.replace("]]>", "")

				if (line.find("<description>") == 0):
					description = line.split("</description>", 2)[0]
					description = self._strip_string(description,"<img","</img>")
					description = self._strip_string(description,"<a href","</a>")
					description = self._strip_string(description,"<br ","</br>")

				if (line.find("<title>") >= 0):
					title = line.split("</title>", 2)[0]

				if len(title) > 0:
					for tag in self.HTMLcodes.tags:	# Strip out HTML tags
						title = title.replace(tag, "")
					rss.append(title)

				if len(description) > 0:
					for tag in self.HTMLcodes.tags:	# Strip out HTML tags
						description = description.replace(tag, "")
					rss.append(description)

				self.feed_available = True
		rss.reverse()
		return rss

	# Sometimes descriptions contain embedded content.
	def _remove_content(self,text):
		s = text
		#pdb.set_trace()
		for i in range(0,len(self.HTMLcodes.deletion_tags)):
			if i % 2 != 0:
				continue
			start_tag = self.HTMLcodes.deletion_tags[i]
			end_tag = self.HTMLcodes.deletion_tags[i+1]

			# Were tags found?
			if start_tag in s and  end_tag in s:
				s = self._strip_string(s, start_tag, end_tag)	
			i += 1
		return s	

	# Execute system command
	def execCommand(self,cmd):
		p = os.popen(cmd)
		result = p.readline().rstrip('\n')
		return result

	# Strip string (between tags)
	def _strip_string(self, text, s_start, s_end):
		new_text = text
		
		try:
			while new_text.find(s_start) > 0:
				idx_start = new_text.find(s_start)
				replace_str = new_text[idx_start:]
				idx_end = replace_str.find(s_end)
				if idx_end < 0:
					idx_end = replace_str.find("/>")
					len2 = 2	
				else:
					len2 = len(s_end)
				replace_str = replace_str[0:idx_end + len2]
				new_text =  new_text.replace(replace_str,'')
		except:
			new_text = text
		return new_text


	# Scroll RSS feed (Used by gradio.py)
	def scrollRssFeed(self,display):
		startColumn = display.getStartColumn()
		max_columns = int(display.getColumns() - startColumn*2)

		leng = len(self.rss_line1)
		if leng < 1:
			self.rss_line1 = self.getFeed()
			self.rss_line2 = self.rss_line1
			self.rss_delay2 = 0
			if leng > max_columns:
				self.rss_delay1 = 1
			else: 
				self.rss_delay1 = DELAY

		if self.rss_delay1 > 0:
			self.rss_line2 = self.rss_line1[:max_columns]
			self.rss_delay1 -= 1

		if leng > max_columns:
			self.rss_line2 = display.scroll(self.rss_line1,4,max_columns)
			self.rss_delay1 = DELAY

			# This is the end of scrolling
			if self.rss_line2 == self.rss_line1[leng-max_columns:]:
				self.rss_delay1 = 0
				if self.rss_delay2 == 0:
					self.rss_delay2 = DELAY
		else:
			self.rss_line2 = self.rss_line1[:max_columns]

		if self.rss_delay2 > 0 and self.rss_delay1 < 1:
			self.rss_line2 = self.rss_line1[leng-max_columns:]
			self.rss_delay2 -= 1

		if  self.rss_delay2 < 1 and self.rss_delay1 < 1:
			self.rss_line1 = ''

		return self.rss_line2

# End of class
