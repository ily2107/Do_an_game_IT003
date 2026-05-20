#Created by Vu Thi Thu Huong
import pygame
import random
from setting import *
from core.menu import Menu
from entities.bird import Bird
from entities.floor import Floor
from entities.score import Score
from entities.pipe import Pipe
from entities.sound import Sound
from core.stage2 import Map2
from core.stage3 import Map3
from entities.auto_player import AutoPlayer

class Game:
    def __init__(self):
        pygame.init()
        self.clock = pygame.time.Clock()
        
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Flappy_bird")

        icon, self.background, floor_img = load_assets()
        pygame.display.set_icon(icon)
        self.pipe_image = pygame.transform.scale2x(pygame.image.load("assets/pipe-green.png"))

        self.pipes = []
        self.spawn_time = 0
        self.delay = random.randint(90, 140)

        self.bird = Bird()
        self.floor = Floor(floor_img, MAP2_FLOOR_Y)
        self.score = Score()
        self.sound = Sound()
        self.running = True

        self.auto_player = AutoPlayer()
        self.menu = Menu(self.screen)

        self.pipe_count = 0
        self.last_pipe_center_y = HEIGHT // 2
        self.pipe_patterns = ["middle", "high", "low", "wave_up", "wave_down", "random"]

    def run(self):
        while True:
            selected_map = self.menu.run()

            if selected_map == "map1":
                result = self.run_game()

            elif selected_map == "map2":
                map2 = Map2(self.screen)
                result = map2.run()

            elif selected_map == "map3":
                map3 = Map3(self.screen)
                result = map3.run()

            if result == "quit":
                pygame.quit()
                exit()

            if result == "menu":
                continue

    def run_game(self):
        self.running = True

        while self.running:
            self.clock.tick(120)

            action = self.handle_events()

            if action == "quit":
                return "quit"

            if action == "menu":
                return "menu"

            self.update()
            self.check_collision()
            self.draw()

        return self.game_over()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if self.auto_player.handle_event(event):
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"

                if event.key == pygame.K_SPACE and self.running:
                    self.bird.velocity = -5
                    self.sound.jump_sound.play()
                    self.bird.swap = True

        return None
    
    def get_pipe_gap(self):
        base_gap = 250 - self.score.value * 2

        if base_gap < 190:
            base_gap = 190

        min_gap = base_gap - 25
        max_gap = base_gap + 35

        min_gap = max(185, min_gap)
        max_gap = min(290, max_gap)

        return random.randint(min_gap, max_gap)

    def get_next_pipe_center_y(self):
        pattern = random.choice(self.pipe_patterns)

        min_y = 150
        max_y = MAP2_FLOOR_Y - 150

        if pattern == "middle":
            center_y = random.randint(260, 380)

        elif pattern == "high":
            center_y = random.randint(min_y, 260)

        elif pattern == "low":
            center_y = random.randint(380, max_y)

        elif pattern == "wave_up":
            center_y = self.last_pipe_center_y - random.randint(60, 120)

        elif pattern == "wave_down":
            center_y = self.last_pipe_center_y + random.randint(60, 120)

        else:
            center_y = random.randint(min_y, max_y)

        center_y = max(min_y, min(center_y, max_y))

        self.last_pipe_center_y = center_y
        self.pipe_count += 1

        return center_y
    
    def update(self):
        self.auto_player.update(self.bird, self.pipes, MAP2_FLOOR_Y, self.sound)

        self.floor.update()
        self.bird.update()
        self.spawn_time += 1

        if self.spawn_time > self.delay:
            gap = self.get_pipe_gap()

            pipe_type = random.choices(
                ["normal", "bottom_only", "top_only"],
                weights=[75, 12, 13],
                k=1
            )[0]

            MIN_PASS_SPACE = 220

            if pipe_type == "normal":
                center_y = self.get_next_pipe_center_y()

            elif pipe_type == "bottom_only":
                center_y = random.randint(MIN_PASS_SPACE, MAP2_FLOOR_Y - 150)

            elif pipe_type == "top_only":
                max_deep = MAP2_FLOOR_Y - MIN_PASS_SPACE
                center_y = random.randint(240, max_deep)

            self.pipes.append(Pipe(self.pipe_image, center_y, gap, pipe_type))

            self.spawn_time = 0

            min_delay = max(70, 115 - self.score.value)
            max_delay = max(105, 155 - self.score.value)

            self.delay = random.randint(min_delay, max_delay)

        for pipe in self.pipes:
            if not pipe.passed and pipe.top_rect.right<self.bird.rect.left:
                self.sound.point_sound.play()
                self.score.update()
                pipe.passed=True
            pipe.update()

        self.pipes = [pipe for pipe in self.pipes if not pipe.offscreen()]

    def check_collision(self):
        if self.bird.rect.top<=-75: 
            self.running=False
            self.sound.hit_sound.play()
            pygame.time.delay(300)
            self.sound.die_sound.play()

        if self.bird.rect.colliderect(self.floor.rect):
            self.running=False
            self.sound.hit_sound.play()
            pygame.time.delay(300)
            self.sound.die_sound.play()

        for pipe in self.pipes:
            if self.bird.rect.colliderect(pipe.top_rect) or \
            self.bird.rect.colliderect(pipe.bottom_rect):
                self.running = False
                self.sound.hit_sound.play()
                pygame.time.delay(300)
                self.sound.die_sound.play()

    def draw(self):
        self.screen.blit(self.background,(0,0))   
        for pipe in self.pipes:
            pipe.draw(self.screen)
        self.floor.draw(self.screen)

        if self.running:
            self.bird.draw(self.screen)
        self.score.draw(self.screen)

        self.auto_player.draw(self.screen)
        pygame.display.update()

    def reset_map1(self):
        self.bird = Bird()
        self.pipes = []
        self.spawn_time = 0
        self.delay = random.randint(90, 140)
        self.score.value = 0
        self.running = True
        self.auto_player = AutoPlayer()
        self.pipe_count = 0
        self.last_pipe_center_y = HEIGHT // 2

    def restart_map1(self):
        self.bird = Bird()
        self.pipes = []
        self.spawn_time = 0
        self.delay = random.randint(90, 140)
        self.score.value = 0
        self.running = True
        self.auto_player.enabled = False
        self.pipe_count = 0
        self.last_pipe_center_y = HEIGHT // 2

    def game_over(self):
        if self.score.h_value < self.score.value:
            self.score.h_value = self.score.value
            self.sound.victory_sound.play()

        self.screen_end = pygame.image.load("assets/message.png")
        self.screen_end = pygame.transform.scale2x(self.screen_end)

        screen_end_rect = self.screen_end.get_rect(center=(WIDTH // 2, HEIGHT // 2))

        game_over = True

        while game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"

                    if event.key == pygame.K_SPACE or event.key == pygame.K_r:
                        self.restart_map1()
                        return self.run_game()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.restart_map1()
                    return self.run_game()

            self.screen.blit(self.background, (0, 0))

            self.screen.blit(self.screen_end, screen_end_rect)

            self.score.end_draw(self.screen)

            pygame.display.update()

        pygame.quit()

def load_assets():
    icon = pygame.image.load("assets/yellowbird-upflap.png")

    bg = pygame.transform.scale2x(pygame.image.load("assets/background-night.png"))
    floor = pygame.transform.scale2x(pygame.image.load("assets/floor.png"))

    background = pygame.Surface((WIDTH, HEIGHT))
    x = 0
    while x < WIDTH:
        background.blit(bg, (x, 0))
        x += bg.get_width()

    return icon, background, floor