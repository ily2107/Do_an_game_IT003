import pygame
from setting import *


class Pipe:
    def __init__(self, image, center_y, gap, pipe_type="normal"):
        self.image = image
        self.image_flipped = pygame.transform.flip(image, False, True)

        self.x = WIDTH
        self.speed = SCROLL_SPEED
        self.GAP = gap
        self.pipe_type = pipe_type

        if self.pipe_type == "bottom_only":
            bottom_y = center_y

            self.top_rect = self.image_flipped.get_rect(
                midbottom=(self.x, -1000)
            )

            self.bottom_rect = self.image.get_rect(
                midtop=(self.x, bottom_y)
            )

            self.gap_top = 0
            self.gap_bottom = bottom_y

        elif self.pipe_type == "top_only":
            top_height = center_y

            self.top_rect = self.image_flipped.get_rect(
                midbottom=(self.x, top_height)
            )

            self.bottom_rect = self.image.get_rect(
                midtop=(self.x, HEIGHT + 1000)
            )

            self.gap_top = top_height
            self.gap_bottom = MAP2_FLOOR_Y

        else:
            top_height = center_y - self.GAP // 2
            bottom_y = center_y + self.GAP // 2

            self.top_rect = self.image_flipped.get_rect(
                midbottom=(self.x, top_height)
            )

            self.bottom_rect = self.image.get_rect(
                midtop=(self.x, bottom_y)
            )

            self.gap_top = top_height
            self.gap_bottom = bottom_y

        self.passed = False

    def update(self):
        self.top_rect.x -= self.speed
        self.bottom_rect.x -= self.speed

    def draw(self, screen):
        screen.blit(self.image, self.top_rect)
        screen.blit(self.image_flipped, self.bottom_rect)

    def offscreen(self):
        return self.top_rect.right < 0 and self.bottom_rect.right < 0