import pygame
from setting import *

class Sound:
    def __init__(self):
        self.jump_sound=pygame.mixer.Sound("sound/sfx_wing.wav")
        self.die_sound=pygame.mixer.Sound("sound/sfx_die.wav")
        self.hit_sound=pygame.mixer.Sound("sound/sfx_hit.wav")
        self.point_sound=pygame.mixer.Sound("sound/sfx_point.wav")
        self.fall_sound=pygame.mixer.Sound("sound/sfx_swooshing.wav")
        self.victory_sound=pygame.mixer.Sound("sound/sfx_end.mp3")