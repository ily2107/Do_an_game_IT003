import pygame
import random
from collections import deque
from setting import *
from high_score import HighScoreManager

class GeometryPlayer:
    def __init__(self):
        self.image = pygame.image.load("assets/ChatGPT Image May 13, 2026, 12_11_43 PM (1).png").convert_alpha()
        self.image.set_colorkey((0, 0, 0))
        self.image = self.crop_to_content(self.image)
        self.image = pygame.transform.scale(self.image, (60, 60))

        self.base_image = self.image.copy()
        self.angle = 0
        self.rotate_speed = -10

        self.rect = self.image.get_rect()
        self.rect.x = 180
        self.rect.bottom = MAP2_FLOOR_Y

        self.velocity_y = 0
        self.gravity = 1.05
        self.jump_force = -17
        self.on_ground = True
        self.jump_buffer = 0
        self.jump_buffer_time = 8

    def crop_to_content(self, image):
        rect = image.get_bounding_rect()

        if rect.width == 0 or rect.height == 0:
            return image

        cropped = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        cropped.blit(image, (0, 0), rect)

        return cropped

    def do_jump(self):
        self.velocity_y = self.jump_force
        self.on_ground = False
        self.jump_buffer = 0


    def request_jump(self):
        self.jump_buffer = self.jump_buffer_time

        if self.on_ground:
            self.do_jump()


    def try_buffered_jump(self):
        if self.on_ground and self.jump_buffer > 0:
            self.do_jump()

    def snap_angle(self):
        self.angle = round(self.angle / 90) * 90
        self.angle %= 360

    def land_on(self, y):
        self.rect.bottom = y
        self.velocity_y = 0
        self.on_ground = True
        self.snap_angle()

    def push_left(self, amount):
        self.rect.x -= amount

    def update(self):
        self.prev_rect = self.rect.copy()

        self.velocity_y += self.gravity
        self.rect.y += self.velocity_y

        if not self.on_ground:
            self.angle += self.rotate_speed
            self.angle %= 360

        self.on_ground = False

        if self.rect.bottom >= MAP2_FLOOR_Y:
            self.land_on(MAP2_FLOOR_Y)
            self.try_buffered_jump()

        if self.jump_buffer > 0:
            self.jump_buffer -= 1

    def draw(self, screen):
        rotated_image = pygame.transform.rotate(self.base_image, self.angle)
        rotated_rect = rotated_image.get_rect(center=self.rect.center)
        screen.blit(rotated_image, rotated_rect)


class GeometryObstacle:
    def __init__(self, obstacle_type, x, y, width=None, height=None):
        self.type = obstacle_type

        if self.type == "spike":
            self.width = width or 42
            self.height = height or 42
            self.rect = pygame.Rect(x, y - self.height, self.width, self.height)

        elif self.type == "mini_spike":
            self.width = width or 32
            self.height = height or 28
            self.rect = pygame.Rect(x, y - self.height, self.width, self.height)

        elif self.type == "block":
            self.width = width or 70
            self.height = height or 70
            self.rect = pygame.Rect(x, y - self.height, self.width, self.height)

        elif self.type == "platform":
            self.width = width or 210
            self.height = height or 45
            self.rect = pygame.Rect(x, y - self.height, self.width, self.height)

        else:
            self.type = "spike"
            self.width = width or 42
            self.height = height or 42
            self.rect = pygame.Rect(x, y - self.height, self.width, self.height)

    def update(self, speed):
        self.rect.x -= speed

    def is_deadly(self):
        return self.type in ["spike", "mini_spike"]

    def is_solid(self):
        return self.type in ["block", "platform"]

    def get_deadly_rects(self):
        if self.type == "spike":
            return [self.rect.inflate(-14, -8)]

        if self.type == "mini_spike":
            return [self.rect.inflate(-10, -6)]

        return []

    def draw_spike(self, screen, rect, pink_width=5, cyan_width=2):
        points = [
            (rect.left, rect.bottom),
            (rect.centerx, rect.top),
            (rect.right, rect.bottom)
        ]

        pygame.draw.polygon(screen, OBJECT_DARK, points)
        pygame.draw.polygon(screen, LASER_PINK, points, pink_width)
        pygame.draw.polygon(screen, LASER_CYAN, points, cyan_width)

    def draw_block(self, screen, rect, main_color):
        pygame.draw.rect(screen, OBJECT_DARK, rect, border_radius=8)

        glow_rect = rect.inflate(8, 8)
        pygame.draw.rect(screen, main_color, glow_rect, 4, border_radius=10)
        pygame.draw.rect(screen, LASER_CYAN, rect, 3, border_radius=8)

        pygame.draw.line(screen, LASER_CYAN, rect.topleft, rect.bottomright, 2)
        pygame.draw.line(screen, LASER_PINK, rect.topright, rect.bottomleft, 2)

    def draw(self, screen):
        if self.type == "spike":
            self.draw_spike(screen, self.rect, 5, 2)

        elif self.type == "mini_spike":
            self.draw_spike(screen, self.rect, 4, 2)

        elif self.type == "platform":
            self.draw_block(screen, self.rect, LASER_CYAN)

        else:
            self.draw_block(screen, self.rect, LASER_PINK)

    def offscreen(self):
        return self.rect.right < 0

class GeometryAutoPlayer:
    def __init__(self):
        self.enabled = False
        self.button_rect = pygame.Rect(WIDTH - 118, 66, 100, 40)
        self.font = pygame.font.SysFont("arial", 20, bold=True)
        self.cooldown = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.button_rect.collidepoint(event.pos):
                self.enabled = not self.enabled
                return True
        return False

    def request_jump(self, player):
        if hasattr(player, "request_jump"):
            player.request_jump()
        else:
            player.jump()

        self.cooldown = 8

    def get_next_obstacles(self, player, obstacles):
        front = []

        for obstacle in obstacles:
            if obstacle.rect.right > player.rect.left:
                front.append(obstacle)

        front.sort(key=lambda obstacle: obstacle.rect.left)
        return front

    def get_support_block(self, player, obstacles):
        for obstacle in obstacles:
            if obstacle.is_solid():
                standing_on = (
                    abs(player.rect.bottom - obstacle.rect.top) <= 6
                    and player.rect.right > obstacle.rect.left + 8
                    and player.rect.left < obstacle.rect.right - 8
                )

                if standing_on:
                    return obstacle

        return None

    def update(self, player, obstacles, game_speed):
        if not self.enabled:
            return

        if self.cooldown > 0:
            self.cooldown -= 1
            return

        front = self.get_next_obstacles(player, obstacles)
        support_block = self.get_support_block(player, obstacles)

        if support_block is not None:
            distance_to_edge = support_block.rect.right - player.rect.right

            if 0 < distance_to_edge < 32 and player.on_ground:
                self.request_jump(player)
                return

        for obstacle in front:
            distance = obstacle.rect.left - player.rect.right

            if distance < 0:
                continue

            if obstacle.is_solid():
                elevated = obstacle.rect.top < player.rect.bottom - 20
                player_will_hit_side = player.rect.bottom > obstacle.rect.top + 18

                if elevated:
                    min_jump_distance = 45
                    max_jump_distance = 105 + game_speed * 3.2
                else:
                    min_jump_distance = 25
                    max_jump_distance = 62 + game_speed * 1.5

                if player_will_hit_side:
                    if min_jump_distance <= distance <= max_jump_distance and player.on_ground:
                        self.request_jump(player)
                        return

            if obstacle.is_deadly():
                same_level_spike = obstacle.rect.bottom >= player.rect.bottom - 15

                if not same_level_spike:
                    continue

                if obstacle.type == "mini_spike":
                    min_jump_distance = 20
                    max_jump_distance = 48 + game_speed * 1.3
                else:
                    min_jump_distance = 25
                    max_jump_distance = 58 + game_speed * 1.3

                if min_jump_distance <= distance <= max_jump_distance and player.on_ground:
                    self.request_jump(player)
                    return

    def draw(self, screen):
        if self.enabled:
            bg_color = (40, 180, 80)
            text = "AUTO ON"
        else:
            bg_color = (80, 80, 80)
            text = "AUTO"

        pygame.draw.rect(screen, bg_color, self.button_rect, border_radius=10)
        pygame.draw.rect(screen, (255, 255, 255), self.button_rect, 2, border_radius=10)

        label = self.font.render(text, True, (255, 255, 255))
        label_rect = label.get_rect(center=self.button_rect.center)
        screen.blit(label, label_rect)

class Map2:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True

        self.bg_offset = 0

        self.player = GeometryPlayer()
        self.auto_player = GeometryAutoPlayer()

        self.obstacles = []
        self.spawn_timer = 0
        self.spawn_delay = 90

        self.score = 0
        self.font = pygame.font.SysFont("arial", 36, bold=True)

        self.high_score_manager = HighScoreManager()
        self.high_score = self.high_score_manager.get("stage2")

        self.base_speed = 7
        self.game_speed = self.base_speed
        self.max_speed = 12

        self.pattern_queue = deque([
            "single_spike",
            "mini_carpet",
            "one_column",
            "two_columns",
            "three_columns",
            "low_platform_spikes"
        ])

    def reset(self):
        self.player = GeometryPlayer()
        self.auto_player = GeometryAutoPlayer()

        self.obstacles = []
        self.spawn_timer = 0
        self.spawn_delay = 90
        self.score = 0
        self.running = True

        self.base_speed = 7
        self.game_speed = self.base_speed
        self.max_speed = 12

        self.pattern_queue = deque([
            "single_spike",
            "mini_carpet",
            "one_column",
            "two_columns",
            "three_columns",
            "low_platform_spikes"
        ])

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if self.auto_player.handle_event(event):
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"

                if event.key == pygame.K_SPACE:
                    if hasattr(self.player, "request_jump"):
                        self.player.request_jump()
                    else:
                        self.player.jump()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if hasattr(self.player, "request_jump"):
                        self.player.request_jump()
                    else:
                        self.player.jump()

        return None

    def spawn_obstacle(self):
        if len(self.pattern_queue) == 0:
            new_pattern = random.choice([
                ["single_spike", "one_column"],
                ["mini_carpet", "two_columns"],
                ["two_columns"],
                ["three_columns"],
                ["low_platform_spikes"],
                ["single_spike", "mini_carpet"],
                ["one_column", "three_columns"]
            ])

            for item in new_pattern:
                self.pattern_queue.append(item)

        pattern = self.pattern_queue.popleft()
        base_x = WIDTH + 20

        if pattern == "single_spike":
            self.obstacles.append(
                GeometryObstacle("spike", base_x, MAP2_FLOOR_Y)
            )

        elif pattern == "mini_carpet":
            for i in range(3):
                self.obstacles.append(
                    GeometryObstacle("mini_spike", base_x + i * 30, MAP2_FLOOR_Y)
                )

        elif pattern == "one_column":
            self.obstacles.append(
                GeometryObstacle("block", base_x, MAP2_FLOOR_Y, 90, 75)
            )

            for i in range(2):
                self.obstacles.append(
                    GeometryObstacle("mini_spike", base_x + 125 + i * 30, MAP2_FLOOR_Y)
                )

        elif pattern == "two_columns":
            column_width = 90
            jump_gap = 135

            first_x = base_x
            second_x = first_x + column_width + jump_gap

            self.obstacles.append(
                GeometryObstacle("block", first_x, MAP2_FLOOR_Y, column_width, 75)
            )

            self.obstacles.append(
                GeometryObstacle("block", second_x, MAP2_FLOOR_Y, column_width, 90)
            )

            spike_start_x = first_x + column_width + 25

            for i in range(3):
                self.obstacles.append(
                    GeometryObstacle("mini_spike", spike_start_x + i * 30, MAP2_FLOOR_Y)
                )

        elif pattern == "three_columns":
            column_width = 90
            first_gap = 130
            second_gap = 165

            first_x = base_x
            second_x = first_x + column_width + first_gap
            third_x = second_x + column_width + second_gap

            self.obstacles.append(
                GeometryObstacle("block", first_x, MAP2_FLOOR_Y, column_width, 75)
            )

            self.obstacles.append(
                GeometryObstacle("block", second_x, MAP2_FLOOR_Y, column_width, 85)
            )

            self.obstacles.append(
                GeometryObstacle("block", third_x, MAP2_FLOOR_Y, column_width, 75)
            )

            first_spike_x = first_x + column_width + 25
            second_spike_x = second_x + column_width + 25

            for i in range(3):
                self.obstacles.append(
                    GeometryObstacle("mini_spike", first_spike_x + i * 30, MAP2_FLOOR_Y)
                )

            for i in range(3):
                self.obstacles.append(
                    GeometryObstacle("mini_spike", second_spike_x + i * 30, MAP2_FLOOR_Y)
                )

        elif pattern == "low_platform_spikes":
            for i in range(3):
                self.obstacles.append(
                    GeometryObstacle("mini_spike", base_x + i * 30, MAP2_FLOOR_Y)
                )

            self.obstacles.append(
                GeometryObstacle("platform", base_x + 115, MAP2_FLOOR_Y - 45, 230, 45)
            )

        self.spawn_delay = random.randint(115, 165)

    def update(self):
        self.game_speed = min(
            self.max_speed,
            self.base_speed + self.score // 900 * 0.35
        )

        self.auto_player.update(self.player, self.obstacles, self.game_speed)

        self.player.update()

        self.spawn_timer += 1

        if self.spawn_timer >= self.spawn_delay:
            self.spawn_obstacle()
            self.spawn_timer = 0

        self.game_speed = min(
            self.max_speed,
            self.base_speed + self.score // 900 * 0.35
        )

        for obstacle in self.obstacles:
            obstacle.update(self.game_speed)

        self.obstacles = [
            obstacle for obstacle in self.obstacles
            if not obstacle.offscreen()
        ]

        for obstacle in self.obstacles:
            if obstacle.is_solid():
                if self.player.rect.colliderect(obstacle.rect):
                    landed_on_top = (
                        self.player.velocity_y >= 0
                        and self.player.prev_rect.bottom <= obstacle.rect.top + 10
                        and self.player.rect.bottom <= obstacle.rect.top + 35
                    )

                    if landed_on_top:
                        self.player.land_on(obstacle.rect.top)
                        self.player.try_buffered_jump()
                    else:
                        self.player.rect.right = obstacle.rect.left
                        self.player.push_left(self.game_speed)

            if obstacle.is_deadly():
                for hitbox in obstacle.get_deadly_rects():
                    if self.player.rect.colliderect(hitbox):
                        self.running = False

        if self.player.rect.right < 0:
            self.running = False

        self.score += 1

    def draw_tech_background(self):
        self.screen.fill(BACKGROUND_DARK)

        self.bg_offset = (self.bg_offset + 2) % 40

        for x in range(-40, WIDTH + 40, 40):
            draw_x = x - self.bg_offset
            pygame.draw.line(self.screen, GRID_BLUE, (draw_x, 0), (draw_x, MAP2_FLOOR_Y), 1)

        for y in range(0, MAP2_FLOOR_Y, 40):
            pygame.draw.line(self.screen, GRID_BLUE, (0, y), (WIDTH, y), 1)

        for x in range(-100, WIDTH, 180):
            pygame.draw.line(
                self.screen,
                (0, 120, 160),
                (x - self.bg_offset, MAP2_FLOOR_Y - 120),
                (x + 90 - self.bg_offset, MAP2_FLOOR_Y),
                1
            )

    def draw_ground(self):
        ground_rect = pygame.Rect(0, MAP2_FLOOR_Y, WIDTH, HEIGHT - MAP2_FLOOR_Y)
        pygame.draw.rect(self.screen, GROUND_DARK, ground_rect)

        for x in range(0, WIDTH, 50):
            pygame.draw.line(self.screen, LASER_CYAN, (x, MAP2_FLOOR_Y), (x + 25, MAP2_FLOOR_Y + 25), 2)

        pygame.draw.line(self.screen, LASER_CYAN, (0, MAP2_FLOOR_Y), (WIDTH, MAP2_FLOOR_Y), 4)
        pygame.draw.line(self.screen, LASER_PINK, (0, MAP2_FLOOR_Y + 6), (WIDTH, MAP2_FLOOR_Y + 6), 2)

    def draw_score(self):
        score_text = self.font.render(f"SCORE: {self.score // 10}", True, LASER_CYAN)
        self.screen.blit(score_text, (30, 30))

        high_text = self.font.render(f"BEST: {self.high_score}", True, LASER_PINK)
        self.screen.blit(high_text, (30, 70))

    def draw(self):
        self.draw_tech_background()
        self.draw_ground()

        for obstacle in self.obstacles:
            obstacle.draw(self.screen)

        self.player.draw(self.screen)
        self.draw_score()
        self.auto_player.draw(self.screen)

        pygame.display.update()

    def game_over(self):
        final_score = self.score // 10

        if self.high_score_manager.update("stage2", final_score):
            self.high_score = final_score

        title_font = pygame.font.SysFont("arial", 60, bold=True)
        small_font = pygame.font.SysFont("arial", 32, bold=True)

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"

                    if event.key == pygame.K_SPACE or event.key == pygame.K_r:
                        self.reset()
                        return self.run()

                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.reset()
                    return self.run()

            self.draw_tech_background()
            self.draw_ground()

            game_over_text = title_font.render("GAME OVER", True, (255, 255, 255))
            game_over_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
            self.screen.blit(game_over_text, game_over_rect)

            score_text = small_font.render(f"SCORE: {self.score // 10}", True, (255, 255, 255))
            score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            self.screen.blit(score_text, score_rect)

            best_text = small_font.render(f"BEST: {self.high_score}", True, WHITE)
            best_rect = best_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
            self.screen.blit(best_text, best_rect)

            help_text = small_font.render("SPACE / R / CLICK: RESTART    ESC: MENU", True, (255, 255, 255))
            help_rect = help_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 75))
            self.screen.blit(help_text, help_rect)

            pygame.display.update()

    def run(self):
        self.reset()

        while self.running:
            self.clock.tick(60)

            action = self.handle_events()

            if action == "quit":
                return "quit"

            if action == "menu":
                return "menu"

            self.update()
            self.draw()

        return self.game_over()