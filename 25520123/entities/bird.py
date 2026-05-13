import pygame
from setting import *

class Bird:
    def __init__(self):
        self.frames=[
            pygame.transform.scale2x(pygame.image.load("assets/yellowbird-upflap.png")),
            pygame.transform.scale2x(pygame.image.load("assets/yellowbird-midflap.png")),
            pygame.transform.scale2x(pygame.image.load("assets/yellowbird-downflap.png")),
        ]
        self.frame_index=0
        self.image=self.frames[self.frame_index]

        self.rect = self.image.get_rect(center=(220, 300))  

        self.velocity=0
        self.animation_time=0

    def update(self):
        self.velocity+=P
        self.rect.y+=self.velocity
        self.animation_time+=1

        if self.animation_time>8:
            self.frame_index+=1
            if self.frame_index>=len(self.frames):
                self.frame_index=0
            self.image=self.frames[self.frame_index]
            self.animation_time=0
    
    def draw(self,screen):
        rotated=pygame.transform.rotate(self.image,-self.velocity*3)
        rect=rotated.get_rect(center=self.rect.center)
        screen.blit(rotated,rect)