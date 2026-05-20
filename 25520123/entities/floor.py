import pygame
from setting import *


class Floor:
    def __init__(self, image, y):
        self.image = image
        self.y = y
        self.x = 0
        self.width = self.image.get_width()
        self.height = self.image.get_height()

        # Rect va chạm nên phủ toàn bộ chiều ngang màn hình
        self.rect = pygame.Rect(0, self.y, WIDTH, self.height)

    def update(self):
        self.x -= SCROLL_SPEED

        if self.x <= -self.width:
            self.x = 0

        self.rect.x = 0
        self.rect.y = self.y
        self.rect.width = WIDTH

    def draw(self, screen):
        x = self.x

        while x < WIDTH:
            screen.blit(self.image, (x, self.y))
            x += self.width