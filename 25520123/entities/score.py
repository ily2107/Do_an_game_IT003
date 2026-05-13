import pygame
from setting import *

class Score:
    def __init__(self):
        self.value=0
        self.h_value=0
        self.font=pygame.font.Font("04B_19.TTF",40)
        self.h_font=pygame.font.Font("04B_19.TTF",50)

    def update(self):
        self.value+=1

    def draw(self,screen):
        surface=self.font.render(f'Score: {(self.value)}',True,(255,255,255))
        rect=surface.get_rect(center=(WIDTH//2,100))
        screen.blit(surface,rect)

    def end_draw(self,screen):
        surface=self.font.render(f'Score: {(self.value)}',True,(255,255,255))
        h_surface=self.h_font.render(f'High score: {(self.h_value)}',True,(255,0,0))
        rect=surface.get_rect(center=(WIDTH//2,60))
        h_rect=h_surface.get_rect(center=(WIDTH//2,125))
        screen.blit(surface,rect)
        screen.blit(h_surface,h_rect)