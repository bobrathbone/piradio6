#!/usr/bin/env python3
import pygame
import requests
import sys
from io import BytesIO

# To run
# DISPLAY=:0.0 ./test_graphic_url.py
size = (800,600) 
pygame.init()
screen = pygame.display.set_mode(size)
 
response = requests.get('https://www.denofgeek.com/wp-content/uploads/2022/05/Leged-of-Zelda-Link.jpg')
 
img = pygame.image.load(BytesIO(response.content))
img = pygame.transform.scale(img,(500,300))
 
while True:   # Game Loop
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    screen.blit(img, (60, 60))
    pygame.display.update()

