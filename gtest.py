#!/usr/bin/env python
# -*- coding: utf-8 -*-
import pygame
from pygame.locals import *
from gcontrols_class import *
size =(400,400)

# Display message popup
def displayPopup(screen,text):
        displayPopup = TextRectangle(pygame)    # Text window
        font = pygame.font.SysFont('freesans', 20, bold=True)
        fx,fy = font.size(text + "A")
        xPos = int((size[0]/2) - (fx/2))
        yPos = size[1]/2
        xSize = fx
        ySize = fy
        color = (50,50,50)
        bcolor = (255,255,255)
        border = 4
        displayPopup.draw(screen,color,bcolor,xPos,yPos,xSize,ySize,border)
        line = 1        # Not used but required
        color = (255,255,255)
        displayPopup.drawText(screen,font,color,line,text)
        return

wallpaper =  "/usr/share/scratch/Media/Backgrounds/Nature/lake.jpg"
pygame.init()
screen=pygame.display.set_mode((500,500),HWSURFACE|DOUBLEBUF|RESIZABLE)
pic=pygame.image.load(wallpaper) #You need an example picture in the same folder as this file!
screen.blit(pygame.transform.scale(pic,(500,500)),(0,0))
pygame.display.flip()
while True:
    pygame.event.pump()
    event=pygame.event.wait()
    if event.type==QUIT: pygame.display.quit()
    elif event.type==VIDEORESIZE:
        screen=pygame.display.set_mode(event.dict['size'],HWSURFACE|DOUBLEBUF|RESIZABLE)
        screen.blit(pygame.transform.scale(pic,event.dict['size']),(0,0))
    text = "Loading Radio Stations"
    text = "Vær så snill"

    displayPopup(screen,text)
    pygame.display.flip()
