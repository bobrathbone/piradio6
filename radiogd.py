#!/usr/bin/env python
#
# Graphical Raspberry Pi Radio using pygame 
# Experimental prototype
#
# $Id: radiogd.py,v 1.9 2017/11/11 06:52:30 bob Exp $
#
# Author : Bob Rathbone
# Site   : http://www.bobrathbone.com
#
# License: GNU V3, See https://www.gnu.org/copyleft/gpl.html
#
# Disclaimer: Software is provided as is and absolutly no warranties are implied or given.
#           The authors shall not be liable for any loss or damage however caused.
#
# Acknowlegments: Radio icons from flaticom.com  
#

import time
import pdb

from log_class import Log
from radio_class import Radio
from event_class import Event
from menu_class import Menu
from message_class import Message
from graphic_display import GraphicDisplay

import pygame
from pygame.locals import *
#import sgc

pygame.init()
radio = None
log = Log()
menu = Menu()
display = None
radioEvent = None

size = (600,400)

pygame.font.init()
myfont = pygame.font.SysFont('Comic Sans MS', 30)

BLACK = ( 0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = ( 255, 0, 0)

# handle pygame basic window
# handle event loop
class Window:
	def __init__(self,caption,size,flags=0,depth=0,fps=30):
		self.fps = fps # frames per second

		self.screen = pygame.display.set_mode(size,flags,depth)
		pygame.display.set_caption(caption)

		self.clock = pygame.time.Clock() # use to control framerate
		self.Window_Open = True
		self.Run = True

		self.updatefunc = None
		self.eventfunc = None
		self.setupRadio()

	# Start the radio and MPD
	def setupRadio(self):
		global radio,radioEvent,message,display
		log.init('radio')
		log.message("Starting graphic radio ", log.INFO)

		# Stop the pygame mixer as it conflicts with MPD
		pygame.mixer.quit()

		radioEvent = Event()		# Add radio event handler	
		radio = Radio(menu,radioEvent) 	# Define radio
		radio.start()			# Start it
		radio.loadSource()		# Load sources and playlists

		font = pygame.font.SysFont('Comic Sans MS', 20)
		display = GraphicDisplay(font)
		display.setSize(size)
		message = Message(radio,display)
	  
	def SetPage(self,updatefunc = None,eventfunc = None):
	  self.updatefunc = updatefunc
	  self.eventfunc = eventfunc
	  
	def Flip(self):
	  self.Run = True
	  while self.Run and self.Window_Open:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				self.Window_Open = False
			else:
				if self.eventfunc is not None:
				  self.eventfunc(event)

		if self.updatefunc is not None:
			self.updatefunc(self.screen)

		if radioEvent.detected():
			handleEvent(radio,radioEvent)
		else:
			# Keep the connection to MPD alive
			radio.keepAlive(10)

		# Display the radio details
		displayTimeDate(self.screen,myfont,radio,message)
		displayCurrent(self.screen,myfont,radio,message)
		displayVolume(self.screen,myfont,radio,message)

		# Volume slider
		

		pygame.display.flip()
		self.clock.tick(self.fps)

# Handle radio event
def handleEvent(radio,radioEvent):
	event_type = radioEvent.getType()
	msg = "radioEvent.detected " + str(event_type)
	log.message(msg, log.DEBUG)

	if event_type == radioEvent.CHANNEL_UP:
		radio.channelUp()
	elif event_type == radioEvent.CHANNEL_DOWN:
		radio.channelDown()
	elif event_type == radioEvent.VOLUME_UP:
		radio.increaseVolume()
	elif event_type == radioEvent.VOLUME_DOWN:
		radio.decreaseVolume()
	elif event_type == radioEvent.MUTE_BUTTON_DOWN:
		if radio.muted():
			radio.unmute()
		else:
			radio.mute()
	radioEvent.clear()
	return

# This routine displays the time string
def displayTimeDate(screen,myfont,radio,message):
        timedate = message.get('date_time')

        # If streaming add the streaming indicator
        if radio.getStreaming():
                streaming = ' *'
        else:
                streaming = ''
	rowPos = display.getRowPos(1)
	column = size[0]/4
	color = BLACK
	font = pygame.font.SysFont('Comic Sans MS', 40)
	renderText(timedate,font,screen,rowPos,column,color)
	return

def displayCurrent(screen,font,radio,message):
	color = WHITE
	column = 3

	search_name = radio.getSearchName()
	columnPos = display.getColumnPos(column)
	station_name = radio.getCurrentStationName()
	title = radio.getCurrentTitle()
	bitrate = radio.getBitRate()
	current_id = radio.getCurrentID()
	station_id = "Station " + str(current_id)
	
	if bitrate > 0:
		station_id = station_id + ' ' + str(bitrate) + 'k'

	rowPos = display.getRowPos(4)
	renderText(search_name,font,screen,rowPos,columnPos,color)

	if len(title) > 0:
		station_name = title    # Sometimes title is used

	rowPos = display.getRowPos(6)
	renderText(station_name,font,screen,rowPos,columnPos,color)

	rowPos = display.getRowPos(8)
	renderText(station_id,font,screen,rowPos,columnPos,color)

	return

def displayVolume(screen,font,radio,message):
	color = WHITE
	column = 15
	rowPos = display.getRowPos(11)
	columnPos = display.getColumnPos(column)
	
	if radio.muted():
		sVolume = "Sound muted"
	else:
		sVolume = "Volume " + str(radio.getDisplayVolume())

	textsurface = myfont.render(sVolume, False, (WHITE))
	renderText(sVolume,font,screen,rowPos,columnPos,color)
	return
		

# This routine renders the new text ready to be drawn
def renderText(text,myfont,screen,row,column,color):
	textsurface = myfont.render(text, False, (color))
	screen.blit(textsurface,(column,row))
        return 

# Clickable button class.		 
class Button:
	def __init__(self,text,pos,size=(100,30),color=(0,0,200),hilight=(0,200,200),notification=None):
	  self.notification = notification
	  self.normal = color
	  self.hilight = hilight
	  self.rect = Rect(pos,size)
	  self.mouseover = False
	  self.text = text
	  self.font = pygame.font.Font(None,18)
	  self.text_image = self.font.render(text,1,(255,255,255))
	  w,h = self.font.size(text) # size of font image
	  # center text
	  self.text_pos = (pos[0] + size[0] / 2 - w / 2,pos[1] + size[1] / 2 - h / 2)
	  self.buttondown = False
	  
	def Draw(self,surface):
	  rectout = self.rect.inflate(2,2)
	  rectin = self.rect.inflate(1,1)
	  if self.buttondown:
		 pygame.draw.rect(surface,(0,0,0),rectout)
		 pygame.draw.rect(surface,(255,255,255),rectin)
	  else:
		 pygame.draw.rect(surface,(255,255,255),rectout)
		 pygame.draw.rect(surface,(0,0,0),rectin)
		 
	  if self.mouseover:
		 pygame.draw.rect(surface,self.hilight,self.rect)
	  else:
		 pygame.draw.rect(surface,self.normal,self.rect)

	  surface.blit(self.text_image,self.text_pos)
	  
	def Update(self,event):
	  x,y = event.pos
	  px,py,w,h = self.rect
	  self.mouseover = False
	  if x > px and x < px + w:
		 if y > py and y < py + h:
			self.mouseover = True
	  if not self.mouseover:
		 self.buttondown = False
	
	def MouseDown(self,event):
	  if self.mouseover:
		 self.buttondown = True
			
	def Click(self,event):
		# let you know when mouse is over button and button was push.
		if self.buttondown and self.mouseover:
			self.buttondown = False
			#frame.push = frame.font.render('Click ' + self.text,1,(100,0,200))
			# Despatch the event
			if self.notification != None:
				radioEvent.set(self.notification)

class Main:
	def __init__(self):
		row = 300
		column = 50
		ev = radioEvent.VOLUME_UP
		self.volumeUpButton = Button('Volume Up',(column,row),notification=ev)

		column +=  125
		ev = radioEvent.VOLUME_DOWN
		self.volumeDownButton = Button('Volume Down',(column,row),(100,30),(200,0,0),\
				(200,0,200),notification=ev)

		column +=  125
		ev = radioEvent.CHANNEL_UP
		self.upButton = Button('Channel Up',(column,row),color=(0,200,0),\
				hilight=(200,200,0),notification=ev)

		column +=  130
		ev = radioEvent.CHANNEL_DOWN
		self.downButton = Button('Channel Down',(column,row),color=(0,200,200),\
				hilight=(200,0,200),notification=ev)

		column =  120
		row = 350
		ev = radioEvent.MUTE_BUTTON_DOWN
		self.muteButton = Button('Mute',(column,row),color=(100,100,100),\
				hilight=(200,0,200),notification=ev)

		column =  370
		ev = radioEvent.MENU_BUTTON_DOWN
		self.menuButton = Button('Menu',(column,row),color=(100,100,100),\
				hilight=(200,0,200),notification=ev)

		self.font = pygame.font.Font(None,18)
		self.push = None

	def Update(self,surface):
		surface.fill((150,200,150))
		# draw background here.
		self.volumeUpButton.Draw(surface)
		self.volumeDownButton.Draw(surface)
		self.upButton.Draw(surface)
		self.downButton.Draw(surface)
		self.muteButton.Draw(surface)
		self.menuButton.Draw(surface)
	  
		redColor = pygame.Color(255,0,0)
		blackColor = pygame.Color(0,0,0)

		x = 340
		#pygame.draw.rect(surface,redColor,Rect(x,5,10,200))

		if self.push is not None:
			surface.blit(self.push,(100,100))
	  
	def Event(self,event):
	  if event.type == pygame.MOUSEBUTTONDOWN:
		 self.volumeUpButton.MouseDown(event)
		 self.volumeDownButton.MouseDown(event)
		 self.upButton.MouseDown(event)
		 self.downButton.MouseDown(event)
		 self.muteButton.MouseDown(event)
		 self.menuButton.MouseDown(event)

	  elif event.type == pygame.MOUSEBUTTONUP:
		 self.volumeUpButton.Click(event)
		 self.volumeDownButton.Click(event)
		 self.upButton.Click(event)
		 self.downButton.Click(event)
		 self.muteButton.Click(event)
		 self.menuButton.Click(event)

	  elif event.type == pygame.MOUSEMOTION:
		 self.volumeUpButton.Update(event)
		 self.volumeDownButton.Update(event)
		 self.upButton.Update(event)
		 self.downButton.Update(event)
		 self.muteButton.Update(event)
		 self.menuButton.Update(event)
				
if __name__ == '__main__':
	window = Window('Bob Rathbone Internet Radio',size)
	frame = Main()
	window.SetPage(frame.Update,frame.Event)
	window.Flip()
	pygame.quit()


