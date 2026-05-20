import pygame
import random
import math
from setting import *
from high_score import HighScoreManager

STAGE3_BG = (6, 8, 20)
PLAYER_COLOR = (0, 255, 255)
PLAYER_BULLET_COLOR = (120, 240, 255)
ENEMY_COLOR = (255, 80, 150)
ENEMY_BULLET_COLOR = (255, 80, 80)
WHITE = (255, 255, 255)


class PlayerBullet:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x - 4, y - 16, 8, 18)
        self.speed = 12

    def update(self):
        self.rect.y -= self.speed

    def draw(self, screen):
        pygame.draw.rect(screen, PLAYER_BULLET_COLOR, self.rect, border_radius=4)

    def offscreen(self):
        return self.rect.bottom < 0


class EnemyBullet:
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.radius = 6

    def update(self):
        self.x += self.vx
        self.y += self.vy

    def draw(self, screen):
        pygame.draw.circle(screen, ENEMY_BULLET_COLOR, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius, 1)

    def get_rect(self):
        return pygame.Rect(
            int(self.x - self.radius),
            int(self.y - self.radius),
            self.radius * 2,
            self.radius * 2
        )

    def offscreen(self):
        return self.y > HEIGHT + 30 or self.x < -30 or self.x > WIDTH + 30
    
class EnemyLaser:
    def __init__(self, x1, y1, x2, y2, delay=60, active_time=45):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
        self.delay = delay
        self.active_time = active_time
        self.timer = 0
        self.width = 12

    def update(self):
        self.timer += 1

    def is_active(self):
        return self.timer >= self.delay

    def finished(self):
        return self.timer >= self.delay + self.active_time

    def get_rect(self):
        left = min(self.x1, self.x2) - self.width // 2
        top = min(self.y1, self.y2) - self.width // 2
        width = abs(self.x2 - self.x1) + self.width
        height = abs(self.y2 - self.y1) + self.width

        return pygame.Rect(left, top, max(width, self.width), max(height, self.width))

    def draw(self, screen):
        if not self.is_active():
            color = (255, 60, 60)
            width = 3
        else:
            color = (255, 0, 0)
            width = self.width

        pygame.draw.line(screen, color, (self.x1, self.y1), (self.x2, self.y2), width)

class BossEye:
    def __init__(self, boss, angle):
        self.boss = boss
        self.angle = angle
        self.distance = 95
        self.radius = 18
        self.hp = 5
        self.shoot_timer = random.randint(0, 40)
        self.shoot_delay = 55
        self.rect = pygame.Rect(0, 0, self.radius * 2, self.radius * 2)

    def update(self):
        self.angle += 2.2

        rad = math.radians(self.angle)
        self.rect.centerx = self.boss.rect.centerx + int(math.cos(rad) * self.distance)
        self.rect.centery = self.boss.rect.centery + int(math.sin(rad) * self.distance)

        self.shoot_timer += 1

    def ready_to_shoot(self):
        if self.shoot_timer >= self.shoot_delay:
            self.shoot_timer = 0
            return True
        return False

    def shoot_aimed(self, player):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = max(1, math.sqrt(dx * dx + dy * dy))

        speed = 4
        vx = dx / distance * speed
        vy = dy / distance * speed

        return [EnemyBullet(self.rect.centerx, self.rect.centery, vx, vy)]

    def shoot_spiral(self):
        bullets = []

        for offset in [0, 120, 240]:
            angle = self.angle + offset
            rad = math.radians(angle)
            vx = math.cos(rad) * 3.2
            vy = math.sin(rad) * 3.2
            bullets.append(EnemyBullet(self.rect.centerx, self.rect.centery, vx, vy))

        return bullets

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 80, 255), self.rect.center, self.radius)
        pygame.draw.circle(screen, WHITE, self.rect.center, self.radius, 2)
        pygame.draw.circle(screen, (20, 20, 40), self.rect.center, 7)

class BossEnemy:
    def __init__(self, wave):
        self.type = "boss"
        self.wave = wave
        self.rect = pygame.Rect(0, 0, 130, 90)
        self.rect.center = (WIDTH // 2, -80)

        self.target_y = 120
        self.entered = False
        self.vulnerable = False

        self.hp = 120 + wave * 18
        self.max_hp = self.hp

        self.move_timer = 0
        self.shoot_timer = 0
        self.form = 1

        self.eyes = []
        self.eye_spawned = False

        self.laser_timer = 0

    def update_form(self):
        hp_ratio = self.hp / self.max_hp

        if hp_ratio > 0.66:
            self.form = 1
        elif hp_ratio > 0.33:
            self.form = 2
        else:
            self.form = 3

    def update(self):
        self.move_timer += 1
        self.update_form()

        if not self.entered:
            self.rect.y += 2

            if self.rect.y >= self.target_y:
                self.rect.y = self.target_y
                self.entered = True
                self.vulnerable = True

            return [], [], []

        self.rect.centerx = WIDTH // 2 + int(math.sin(self.move_timer * 0.025) * 220)
        self.rect.centery = self.target_y + int(math.sin(self.move_timer * 0.04) * 35)

        new_bullets = []
        new_lasers = []
        new_eyes = []

        self.shoot_timer += 1
        self.laser_timer += 1

        if self.form == 1:
            if self.shoot_timer >= 45:
                self.shoot_timer = 0
                new_bullets.extend(self.shoot_spread(7, 3.6))

        elif self.form == 2:
            if not self.eye_spawned:
                self.eye_spawned = True
                new_eyes.extend([
                    BossEye(self, 0),
                    BossEye(self, 120),
                    BossEye(self, 240)
                ])

            if self.shoot_timer >= 70:
                self.shoot_timer = 0
                new_bullets.extend(self.shoot_circle(20, 3.0))

        else:
            if self.shoot_timer >= 25:
                self.shoot_timer = 0
                new_bullets.extend(self.shoot_spiral(3.6))

            if self.laser_timer >= 150:
                self.laser_timer = 0
                new_lasers.append(
                    EnemyLaser(
                        self.rect.centerx,
                        self.rect.bottom,
                        self.rect.centerx,
                        HEIGHT,
                        delay=60,
                        active_time=45
                    )
                )

        return new_bullets, new_lasers, new_eyes

    def shoot_spread(self, count, speed):
        bullets = []
        start_angle = 45
        end_angle = 135
        step = (end_angle - start_angle) / max(1, count - 1)

        for i in range(count):
            angle = start_angle + step * i
            rad = math.radians(angle)
            vx = math.cos(rad) * speed
            vy = math.sin(rad) * speed
            bullets.append(EnemyBullet(self.rect.centerx, self.rect.bottom, vx, vy))

        return bullets

    def shoot_circle(self, count, speed):
        bullets = []

        for i in range(count):
            angle = 360 / count * i
            rad = math.radians(angle)
            vx = math.cos(rad) * speed
            vy = math.sin(rad) * speed
            bullets.append(EnemyBullet(self.rect.centerx, self.rect.centery, vx, vy))

        return bullets

    def shoot_spiral(self, speed):
        bullets = []

        base_angle = self.move_timer * 7

        for offset in [0, 90, 180, 270]:
            angle = base_angle + offset
            rad = math.radians(angle)
            vx = math.cos(rad) * speed
            vy = math.sin(rad) * speed
            bullets.append(EnemyBullet(self.rect.centerx, self.rect.centery, vx, vy))

        return bullets

    def can_be_hit(self):
        return self.vulnerable

    def draw_hp_bar(self, screen):
        bar_width = 420
        bar_height = 16
        x = WIDTH // 2 - bar_width // 2
        y = 20

        pygame.draw.rect(screen, (60, 60, 60), (x, y, bar_width, bar_height), border_radius=8)

        hp_width = int(bar_width * self.hp / self.max_hp)
        pygame.draw.rect(screen, (255, 60, 100), (x, y, hp_width, bar_height), border_radius=8)

        pygame.draw.rect(screen, WHITE, (x, y, bar_width, bar_height), 2, border_radius=8)

    def draw(self, screen):
        pygame.draw.rect(screen, (255, 40, 100), self.rect, border_radius=22)
        pygame.draw.rect(screen, WHITE, self.rect, 3, border_radius=22)

        eye1 = (self.rect.centerx - 30, self.rect.centery - 10)
        eye2 = (self.rect.centerx + 30, self.rect.centery - 10)

        pygame.draw.circle(screen, WHITE, eye1, 10)
        pygame.draw.circle(screen, WHITE, eye2, 10)
        pygame.draw.circle(screen, (20, 20, 20), eye1, 4)
        pygame.draw.circle(screen, (20, 20, 20), eye2, 4)

        self.draw_hp_bar(screen)

class TouhouPlayer:
    def __init__(self):
        self.image = pygame.image.load("assets/ChatGPT Image May 12, 2026, 05_43_05 PM.png").convert_alpha()
        self.image.set_colorkey((0, 0, 0))
        self.image = pygame.transform.scale(self.image, (72, 72))

        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH // 2, HEIGHT - 100)

        self.speed = 6
        self.slow_speed = 3

        self.shoot_cooldown = 0
        self.hitbox_radius = 10

    def update(self):
        keys = pygame.key.get_pressed()

        speed = self.slow_speed if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT] else self.speed

        dx = 0
        dy = 0

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += speed
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += speed

        self.rect.x += dx
        self.rect.y += dy

        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(WIDTH, self.rect.right)
        self.rect.top = max(0, self.rect.top)
        self.rect.bottom = min(HEIGHT, self.rect.bottom)

        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def can_shoot(self):
        keys = pygame.key.get_pressed()
        return (keys[pygame.K_SPACE] or keys[pygame.K_j]) and self.shoot_cooldown == 0

    def shoot(self):
        self.shoot_cooldown = 4

        return [
            PlayerBullet(self.rect.centerx - 10, self.rect.top),
            PlayerBullet(self.rect.centerx + 10, self.rect.top)
        ]

    def get_hitbox(self):
        return pygame.Rect(
            self.rect.centerx - self.hitbox_radius,
            self.rect.centery - self.hitbox_radius,
            self.hitbox_radius * 2,
            self.hitbox_radius * 2
        )

    def draw(self, screen):
        screen.blit(self.image, self.rect)

        pygame.draw.circle(screen, (255, 60, 60), self.rect.center, self.hitbox_radius, 2)


class Enemy:
    def __init__(self, x, enemy_type="normal", wave=1, move_type="hover"):
        self.type = enemy_type
        self.wave = wave
        self.move_type = move_type

        self.entered = False
        self.vulnerable = False

        self.base_x = x
        self.target_y = random.randint(90, int(HEIGHT * 0.38))
        self.move_timer = 0
        self.entered = False

        if self.type == "normal":
            self.rect = pygame.Rect(x, -50, 46, 46)
            self.hp = 3 + wave // 3
            self.speed = 3
            self.shoot_delay = max(35, 80 - wave * 3)
            self.color = (255, 80, 150)

        elif self.type == "spread":
            self.rect = pygame.Rect(x, -55, 52, 52)
            self.hp = 4 + wave // 3
            self.speed = 2.7
            self.shoot_delay = max(40, 90 - wave * 3)
            self.color = (255, 170, 60)

        elif self.type == "circle":
            self.rect = pygame.Rect(x, -65, 62, 62)
            self.hp = 6 + wave // 2
            self.speed = 2.2
            self.shoot_delay = max(65, 120 - wave * 3)
            self.color = (160, 100, 255)

        elif self.type == "spiral":
            self.rect = pygame.Rect(x, -65, 62, 62)
            self.hp = 7 + wave // 2
            self.speed = 2.0
            self.shoot_delay = max(14, 28 - wave)
            self.color = (80, 220, 255)
            self.spiral_angle = random.randint(0, 360)

        elif self.type == "dasher":
            self.rect = pygame.Rect(x, -50, 50, 50)
            self.hp = 4 + wave // 3
            self.speed = 4
            self.shoot_delay = 55
            self.color = (80, 255, 120)
            self.dash_timer = 0
            self.dash_vx = random.choice([-1, 1]) * 7

        elif self.type == "laser":
            self.rect = pygame.Rect(x, -58, 58, 58)
            self.hp = 6 + wave // 2
            self.speed = 2.2
            self.shoot_delay = 130
            self.color = (255, 40, 40)

        else:
            self.type = "big"
            self.rect = pygame.Rect(x, -80, 76, 76)
            self.hp = 12 + wave
            self.speed = 1.8
            self.shoot_delay = max(45, 75 - wave * 2)
            self.color = (255, 60, 90)

        self.shoot_timer = random.randint(0, self.shoot_delay)
        self.vx = random.choice([-1, 1]) * random.uniform(1.4, 2.4)

    def can_be_hit(self):
        return self.vulnerable

    def update(self):
        self.move_timer += 1

        if not self.entered:
            self.rect.y += self.speed

            if self.rect.y >= self.target_y:
                self.rect.y = self.target_y
                self.entered = True
                self.vulnerable = True

            return
        
        if self.type == "dasher":
            self.dash_timer += 1

            if self.dash_timer > 70:
                self.rect.x += self.dash_vx

                if self.rect.left < 40 or self.rect.right > WIDTH - 40:
                    self.dash_vx *= -1

            self.rect.y = self.target_y + int(math.sin(self.move_timer * 0.05) * 25)
            self.shoot_timer += 1
            return

        if self.move_type == "hover":
            self.rect.centerx = self.base_x + int(math.sin(self.move_timer * 0.045) * 70)
            self.rect.centery = self.target_y + int(math.sin(self.move_timer * 0.035) * 20)

        elif self.move_type == "patrol":
            self.rect.x += self.vx

            if self.rect.left < 50 or self.rect.right > WIDTH - 50:
                self.vx *= -1

            self.rect.y = self.target_y + int(math.sin(self.move_timer * 0.05) * 18)

        elif self.move_type == "circle_move":
            self.rect.centerx = self.base_x + int(math.cos(self.move_timer * 0.04) * 80)
            self.rect.centery = self.target_y + int(math.sin(self.move_timer * 0.04) * 35)

        else:
            self.rect.centerx = self.base_x + int(math.sin(self.move_timer * 0.07) * 100)
            self.rect.centery = self.target_y + int(math.sin(self.move_timer * 0.043) * 45)

        self.rect.top = max(40, self.rect.top)
        self.rect.bottom = min(int(HEIGHT * 0.48), self.rect.bottom)

        self.shoot_timer += 1

    def ready_to_shoot(self):
        if not self.entered:
            return False

        if self.shoot_timer >= self.shoot_delay:
            self.shoot_timer = 0
            return True

        return False

    def shoot_aimed(self, player, speed=4):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = max(1, math.sqrt(dx * dx + dy * dy))

        vx = dx / distance * speed
        vy = dy / distance * speed

        return [EnemyBullet(self.rect.centerx, self.rect.centery, vx, vy)]

    def shoot_spread(self, count=5, speed=4):
        bullets = []
        start_angle = 55
        end_angle = 125

        step = (end_angle - start_angle) / max(1, count - 1)

        for i in range(count):
            angle = start_angle + step * i
            rad = math.radians(angle)
            vx = math.cos(rad) * speed
            vy = math.sin(rad) * speed
            bullets.append(EnemyBullet(self.rect.centerx, self.rect.centery, vx, vy))

        return bullets

    def shoot_circle(self, count=16, speed=3):
        bullets = []

        for i in range(count):
            angle = 360 / count * i
            rad = math.radians(angle)
            vx = math.cos(rad) * speed
            vy = math.sin(rad) * speed
            bullets.append(EnemyBullet(self.rect.centerx, self.rect.centery, vx, vy))

        return bullets

    def shoot_spiral(self, speed=3.4):
        bullets = []

        for offset in [0, 180]:
            angle = self.spiral_angle + offset
            rad = math.radians(angle)
            vx = math.cos(rad) * speed
            vy = math.sin(rad) * speed
            bullets.append(EnemyBullet(self.rect.centerx, self.rect.centery, vx, vy))

        self.spiral_angle += 16 + self.wave
        self.spiral_angle %= 360

        return bullets

    def shoot_big_mix(self, player):
        bullets = []
        bullets.extend(self.shoot_aimed(player, 4.2))
        bullets.extend(self.shoot_spread(6, 3.4))
        return bullets

    def shoot(self, player):
        if self.type == "dasher":
            return self.shoot_spread(6, 4.2)

        if self.type == "laser":
            return []

        if self.type == "normal":
            return self.shoot_aimed(player, 4 + self.wave * 0.08)

        if self.type == "spread":
            count = min(7, 5 + self.wave // 4)
            return self.shoot_spread(count, 3.8 + self.wave * 0.05)

        if self.type == "circle":
            count = min(24, 14 + self.wave)
            return self.shoot_circle(count, 2.7 + self.wave * 0.04)

        if self.type == "spiral":
            return self.shoot_spiral(3.2 + self.wave * 0.04)

        return self.shoot_big_mix(player)

    def draw(self, screen):
        if self.type == "normal":
            pygame.draw.circle(screen, self.color, self.rect.center, self.rect.width // 2)
            pygame.draw.circle(screen, WHITE, self.rect.center, self.rect.width // 2, 2)

        elif self.type == "spread":
            pygame.draw.polygon(
                screen,
                self.color,
                [
                    (self.rect.centerx, self.rect.top),
                    (self.rect.left, self.rect.centery),
                    (self.rect.centerx, self.rect.bottom),
                    (self.rect.right, self.rect.centery)
                ]
            )
            pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=8)
            if not self.vulnerable:
                pygame.draw.rect(screen, (120, 120, 120), self.rect, 2, border_radius=10)

        elif self.type == "circle":
            pygame.draw.rect(screen, self.color, self.rect, border_radius=18)
            pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=18)

        elif self.type == "spiral":
            pygame.draw.circle(screen, self.color, self.rect.center, self.rect.width // 2)
            pygame.draw.circle(screen, WHITE, self.rect.center, self.rect.width // 2, 2)
            pygame.draw.circle(screen, WHITE, self.rect.center, 10, 2)

        else:
            pygame.draw.rect(screen, self.color, self.rect, border_radius=16)
            pygame.draw.rect(screen, WHITE, self.rect, 2, border_radius=16)

class TouhouAutoPlayer:
    def __init__(self):
        self.enabled = False
        self.button_rect = pygame.Rect(WIDTH - 118, 16, 100, 40)
        self.font = pygame.font.SysFont("arial", 20, bold=True)

        self.float_x = None
        self.float_y = None

        self.acceleration = 0.22
        self.friction = 0.88

        self.target_history = {}
        self.lead_frames = 16

        self.max_speed = 10
        self.normal_smooth = 0.55
        self.panic_smooth = 0.9

        self.safe_y = HEIGHT - 95
        self.attack_y = HEIGHT - 105
        self.min_y = HEIGHT - 220
        
        self.idle_x = WIDTH // 2
        self.idle_y = HEIGHT - 90

        self.fire_delay = 0
        self.fire_interval = 3
        self.aim_tolerance = 90

    def is_idle_state(self, enemies, boss_eyes, enemy_bullets, enemy_lasers):
        return (
            len(enemies) == 0
            and len(boss_eyes) == 0
            and len(enemy_bullets) == 0
            and len(enemy_lasers) == 0
        )

    def move_to_idle_position(self, player):
        target_x = self.idle_x
        target_y = self.idle_y

        dx = target_x - player.rect.centerx
        dy = target_y - player.rect.centery

        if abs(dx) > 4:
            player.rect.x += 4 if dx > 0 else -4

        if abs(dy) > 4:
            player.rect.y += 4 if dy > 0 else -4

        self.vx *= 0.6
        self.vy *= 0.6

        self.clamp_player(player)

    def attack_single_target(self, player, enemies, boss_eyes, enemy_bullets, enemy_lasers):
        target = self.get_best_target(player, enemies, boss_eyes)

        if target is None:
            return None
        
        if self.boss_is_alive(enemies):
            return None

        danger = self.get_survival_danger(
            player,
            player.rect.center,
            enemy_bullets,
            enemy_lasers,
            enemies
        )

        if danger > 35000:
            return None

        aim_x = self.get_shoot_aim_x(player, target)

        dx = aim_x - player.rect.centerx
        dy = self.attack_y - player.rect.centery

        move_speed = 7

        self.sync_float_position(player)

        target_vx = max(-7, min(7, dx * 0.08))
        target_vy = max(-4, min(4, dy * 0.05))

        self.vx += (target_vx - self.vx) * 0.18
        self.vy += (target_vy - self.vy) * 0.18

        self.apply_smooth_movement(player)

        tolerance = 75

        if hasattr(target, "type") and target.type == "boss":
            tolerance = 120

        if isinstance(target, BossEye):
            tolerance = 90

        if player.shoot_cooldown > 0:
            player.shoot_cooldown -= 1

        if self.fire_delay > 0:
            self.fire_delay -= 1

        if abs(player.rect.centerx - aim_x) <= tolerance:
            if player.shoot_cooldown == 0 and self.fire_delay == 0:
                self.fire_delay = self.fire_interval
                return player.shoot()

        return []

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.button_rect.collidepoint(event.pos):
                self.enabled = not self.enabled
                self.vx = 0
                self.vy = 0
                return True

        return False

    def clamp_player(self, player):
        player.rect.left = max(0, player.rect.left)
        player.rect.right = min(WIDTH, player.rect.right)

        player.rect.top = max(self.min_y, player.rect.top)
        player.rect.bottom = min(HEIGHT, player.rect.bottom)

    def sync_float_position(self, player):
        if self.float_x is None or self.float_y is None:
            self.float_x = float(player.rect.centerx)
            self.float_y = float(player.rect.centery)


    def apply_smooth_movement(self, player):
        self.sync_float_position(player)

        self.float_x += self.vx
        self.float_y += self.vy

        player.rect.centerx = int(self.float_x)
        player.rect.centery = int(self.float_y)

        self.clamp_player(player)

        self.float_x = float(player.rect.centerx)
        self.float_y = float(player.rect.centery)

    def make_hitbox(self, center, radius):
        return pygame.Rect(
            int(center[0] - radius),
            int(center[1] - radius),
            radius * 2,
            radius * 2
        )

    def get_targets(self, enemies, boss_eyes):
        targets = []

        for enemy in enemies:
            if hasattr(enemy, "can_be_hit"):
                if enemy.can_be_hit():
                    targets.append(enemy)
            else:
                targets.append(enemy)

        for eye in boss_eyes:
            targets.append(eye)

        return targets
    
    def boss_is_alive(self, enemies):
        for enemy in enemies:
            if isinstance(enemy, BossEnemy):
                return True
        return False
    
    def update_target_history(self, enemies, boss_eyes):
        targets = self.get_targets(enemies, boss_eyes)
        alive_ids = set()

        for target in targets:
            target_id = id(target)
            alive_ids.add(target_id)

            old_data = self.target_history.get(target_id)

            if old_data is None:
                self.target_history[target_id] = {
                    "x": target.rect.centerx,
                    "y": target.rect.centery,
                    "vx": 0,
                    "vy": 0
                }
            else:
                old_x = old_data["x"]
                old_y = old_data["y"]

                vx = target.rect.centerx - old_x
                vy = target.rect.centery - old_y

                self.target_history[target_id] = {
                    "x": target.rect.centerx,
                    "y": target.rect.centery,
                    "vx": vx,
                    "vy": vy
                }

        dead_ids = []

        for target_id in self.target_history:
            if target_id not in alive_ids:
                dead_ids.append(target_id)

        for target_id in dead_ids:
            del self.target_history[target_id]


    def predict_target_x(self, target, frames=None):
        if frames is None:
            frames = self.lead_frames

        data = self.target_history.get(id(target))

        if data is None:
            return target.rect.centerx

        predicted_x = target.rect.centerx + data["vx"] * frames
        predicted_x = max(30, min(WIDTH - 30, predicted_x))

        return predicted_x


    def get_shoot_aim_x(self, player, target):
        bullet_speed = 12
        distance_y = player.rect.top - target.rect.centery

        frames = distance_y / bullet_speed
        frames = max(8, min(45, frames))

        return self.predict_target_x(target, frames)

    def get_best_target(self, player, enemies, boss_eyes):
        targets = self.get_targets(enemies, boss_eyes)

        if len(targets) == 0:
            return None

        def target_score(target):
            predicted_x = self.predict_target_x(target, 14)
            x_error = abs(predicted_x - player.rect.centerx)

            y_priority = target.rect.centery * 0.25

            hp_priority = 0
            if hasattr(target, "hp"):
                hp_priority = target.hp * 0.8

            return x_error + y_priority + hp_priority

        return min(targets, key=target_score)

    def bullet_danger(self, hitbox, bullet):
        danger = 0

        for frame in [0, 6, 12, 18, 24, 30]:
            future_x = bullet.x + bullet.vx * frame
            future_y = bullet.y + bullet.vy * frame

            dx = hitbox.centerx - future_x
            dy = hitbox.centery - future_y
            dist_sq = dx * dx + dy * dy

            if dist_sq < 24 * 24:
                danger += 100000
            elif dist_sq < 95 * 95:
                danger += 9000 / max(1, dist_sq)

        return danger

    def laser_danger(self, hitbox, laser):
        laser_rect = laser.get_rect()

        if laser.is_active():
            if hitbox.colliderect(laser_rect):
                return 100000
            return 0

        warning_rect = laser_rect.inflate(75, 75)

        if hitbox.colliderect(warning_rect):
            return 12000

        return 0

    def enemy_danger(self, hitbox, enemy):
        if hitbox.colliderect(enemy.rect):
            return 100000

        dx = hitbox.centerx - enemy.rect.centerx
        dy = hitbox.centery - enemy.rect.centery
        dist_sq = dx * dx + dy * dy

        if dist_sq < 180 * 180:
            return 30000 / max(1, dist_sq)

        return 0

    def get_survival_danger(self, player, center, enemy_bullets, enemy_lasers, enemies):
        hitbox = self.make_hitbox(center, player.hitbox_radius)
        danger = 0

        for bullet in enemy_bullets:
            danger += self.bullet_danger(hitbox, bullet)

        for laser in enemy_lasers:
            danger += self.laser_danger(hitbox, laser)

        for enemy in enemies:
            danger += self.enemy_danger(hitbox, enemy)

        return danger

    def score_position(self, player, center, enemy_bullets, enemy_lasers, enemies, boss_eyes):
        danger = self.get_survival_danger(
            player,
            center,
            enemy_bullets,
            enemy_lasers,
            enemies
        )

        score = -danger

        if center[0] < 25 or center[0] > WIDTH - 25:
            score -= 2500

        if center[1] < 60 or center[1] > HEIGHT - 35:
            score -= 2500

        if center[1] < self.min_y:
            score -= 50000

        target = self.get_best_target(player, enemies, boss_eyes)

        if target is not None:
            aim_x = self.get_shoot_aim_x(player, target)
            x_error = abs(center[0] - aim_x)

            if danger < 30000:
                score -= x_error * 4.5
                score -= abs(center[1] - self.attack_y) * 0.8
            else:
                score -= x_error * 0.4
                score -= abs(center[1] - self.safe_y) * 0.6
        else:
            score -= abs(center[0] - self.idle_x) * 0.35
            score -= abs(center[1] - self.idle_y) * 0.45

        return score

    def move_player(self, player, enemy_bullets, enemy_lasers, enemies, boss_eyes):
        directions = [
            (0, 0),
            (-1, 0),
            (1, 0),
            (0, 1),
            (-1, 1),
            (1, 1),
            (0, -1),
            (-1, -1),
            (1, -1)
        ]

        current_center = player.rect.center

        current_danger = self.get_survival_danger(
            player,
            current_center,
            enemy_bullets,
            enemy_lasers,
            enemies
        )

        best_score = None
        best_dir = (0, 0)

        for dx, dy in directions:
            length = max(1, (dx * dx + dy * dy) ** 0.5)

            step_x = dx / length * self.max_speed
            step_y = dy / length * self.max_speed

            next_center = (
                current_center[0] + step_x,
                current_center[1] + step_y
            )

            second_center = (
                current_center[0] + step_x * 2,
                current_center[1] + step_y * 2
            )

            score_1 = self.score_position(
                player,
                next_center,
                enemy_bullets,
                enemy_lasers,
                enemies,
                boss_eyes
            )

            score_2 = self.score_position(
                player,
                second_center,
                enemy_bullets,
                enemy_lasers,
                enemies,
                boss_eyes
            )

            score = score_1 * 0.65 + score_2 * 0.35
            score -= abs(step_x - self.vx) * 2
            score -= abs(step_y - self.vy) * 2

            if best_score is None or score > best_score:
                best_score = score
                best_dir = (dx, dy)

        length = max(1, (best_dir[0] * best_dir[0] + best_dir[1] * best_dir[1]) ** 0.5)

        target_vx = best_dir[0] / length * self.max_speed
        target_vy = best_dir[1] / length * self.max_speed

        if current_danger > 60000:
            smooth = 0.85
        elif current_danger > 25000:
            smooth = 0.55
        else:
            smooth = 0.18

        self.vx += (target_vx - self.vx) * smooth
        self.vy += (target_vy - self.vy) * smooth

        if best_dir == (0, 0):
            self.vx *= 0.7
            self.vy *= 0.7

        self.apply_smooth_movement(player)

    def should_shoot(self, player, enemies, boss_eyes, enemy_bullets, enemy_lasers):
        if player.shoot_cooldown > 0:
            return False

        if self.fire_delay > 0:
            return False

        target = self.get_best_target(player, enemies, boss_eyes)

        if target is None:
            return False

        current_danger = self.get_survival_danger(
            player,
            player.rect.center,
            enemy_bullets,
            enemy_lasers,
            enemies
        )

        if current_danger > 120000:
            return False

        aim_x = self.get_shoot_aim_x(player, target)
        x_error = abs(player.rect.centerx - aim_x)

        target_count = len(self.get_targets(enemies, boss_eyes))

        tolerance = self.aim_tolerance

        if target_count <= 2:
            tolerance = 75

        if isinstance(target, BossEye):
            tolerance = max(tolerance, 90)

        if hasattr(target, "type") and target.type == "boss":
            tolerance = max(tolerance, 120)

        if x_error <= tolerance:
            return True

        return False

    def update(self, player, enemy_bullets, enemy_lasers, enemies, boss_eyes):
        if not self.enabled:
            return []
        
        if self.is_idle_state(enemies, boss_eyes, enemy_bullets, enemy_lasers):
            if player.shoot_cooldown > 0:
                player.shoot_cooldown -= 1

            if self.fire_delay > 0:
                self.fire_delay -= 1

            self.move_to_idle_position(player)
            return []

        self.update_target_history(enemies, boss_eyes)

        targets = self.get_targets(enemies, boss_eyes)
        boss_alive = self.boss_is_alive(enemies)

        if 0 < len(targets) <= 2 and not boss_alive and len(enemy_lasers) == 0:
            bullets = self.attack_single_target(
                player,
                enemies,
                boss_eyes,
                enemy_bullets,
                enemy_lasers
            )

            if bullets is not None:
                return bullets

        if player.shoot_cooldown > 0:
            player.shoot_cooldown -= 1

        if self.fire_delay > 0:
            self.fire_delay -= 1

        self.move_player(player, enemy_bullets, enemy_lasers, enemies, boss_eyes)

        if self.should_shoot(player, enemies, boss_eyes, enemy_bullets, enemy_lasers):
            self.fire_delay = self.fire_interval
            return player.shoot()

        return []

    def draw(self, screen):
        if self.enabled:
            bg_color = (40, 180, 80)
            text = "AUTO ON"
        else:
            bg_color = (80, 80, 80)
            text = "AUTO"

        pygame.draw.rect(screen, bg_color, self.button_rect, border_radius=10)
        pygame.draw.rect(screen, WHITE, self.button_rect, 2, border_radius=10)

        label = self.font.render(text, True, WHITE)
        label_rect = label.get_rect(center=self.button_rect.center)
        screen.blit(label, label_rect)

class Map3:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 32, bold=True)
        self.big_font = pygame.font.SysFont("arial", 60, bold=True)

        self.high_score_manager = HighScoreManager()
        self.high_score = self.high_score_manager.get("stage3")

        self.reset()

    def reset(self):
        self.running = True

        self.player = TouhouPlayer()
        self.auto_player = TouhouAutoPlayer()

        self.player_bullets = []
        self.enemy_bullets = []
        self.enemies = []
        self.enemy_lasers = []
        self.boss_eyes = []

        self.score = 0
        self.wave = 0
        self.wave_cooldown = 60
        self.spawn_events = []

        self.stars = []
        for _ in range(80):
            self.stars.append([
                random.randint(0, WIDTH),
                random.randint(0, HEIGHT),
                random.randint(1, 3)
            ])

    def create_wave(self):
        self.wave += 1
        events = []

        if self.wave % 5 == 0:
            events = [
                [0, "boss", WIDTH // 2, "hover"]
            ]

            self.spawn_events = events
            return

        enemy_count = min(10, 3 + self.wave // 2)

        for i in range(enemy_count):
            delay = 25 if i > 0 else 0

            if self.wave < 3:
                enemy_type = random.choice(["normal", "spread"])

            elif self.wave < 6:
                enemy_type = random.choices(
                    ["normal", "spread", "circle", "laser"],
                    weights=[35, 30, 20, 15],
                    k=1
                )[0]

            elif self.wave < 10:
                enemy_type = random.choices(
                    ["normal", "spread", "circle", "spiral", "dasher", "laser"],
                    weights=[25, 25, 18, 14, 10, 8],
                    k=1
                )[0]

            else:
                enemy_type = random.choices(
                    ["normal", "spread", "circle", "spiral", "dasher", "laser", "big"],
                    weights=[18, 22, 18, 16, 12, 10, 4],
                    k=1
                )[0]

            x = random.randint(90, WIDTH - 140)
            move_type = random.choice(["hover", "patrol", "circle_move", "chaos"])

            events.append([delay, enemy_type, x, move_type])

        self.spawn_events = events

    def spawn_enemy_from_event(self, enemy_type, x, move_type):
        if enemy_type == "boss":
            self.enemies.append(BossEnemy(self.wave))
        else:
            self.enemies.append(
                Enemy(x, enemy_type, self.wave, move_type)
            )


    def update_waves(self):
        if len(self.spawn_events) == 0:
            if len(self.enemies) == 0 and len(self.boss_eyes) == 0:
                self.wave_cooldown -= 1

                if self.wave_cooldown <= 0:
                    self.create_wave()
                    self.wave_cooldown = max(45, 95 - self.wave * 3)

            return

        self.spawn_events[0][0] -= 1

        if self.spawn_events[0][0] <= 0:
            delay, enemy_type, x, move_type = self.spawn_events.pop(0)
            self.spawn_enemy_from_event(enemy_type, x, move_type)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if self.auto_player.handle_event(event):
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"

        return None

    def update_background(self):
        for star in self.stars:
            star[1] += star[2]

            if star[1] > HEIGHT:
                star[0] = random.randint(0, WIDTH)
                star[1] = 0
                star[2] = random.randint(1, 3)

    def bullet_hits_player(self, bullet):
        dx = bullet.x - self.player.rect.centerx
        dy = bullet.y - self.player.rect.centery

        radius = bullet.radius + self.player.hitbox_radius

        return dx * dx + dy * dy <= radius * radius

    def get_enemy_score(self, enemy):
        base_scores = {
            "normal": 100,
            "spread": 140,
            "circle": 180,
            "laser": 220,
            "spiral": 260,
            "dasher": 300,
            "big": 420,
            "boss": 2500
        }

        base_score = base_scores.get(enemy.type, 100)
        enemy_wave = getattr(enemy, "wave", self.wave)
        difficulty_bonus = 1 + max(0, enemy_wave - 1) * 0.15

        return int(base_score * difficulty_bonus)

    def get_boss_eye_score(self, eye):
        boss_wave = getattr(eye.boss, "wave", self.wave)
        difficulty_bonus = 1 + max(0, boss_wave - 1) * 0.15

        return int(180 * difficulty_bonus)

    def update(self):
        self.update_background()

        if self.auto_player.enabled:
            self.player_bullets.extend(
                self.auto_player.update(
                    self.player,
                    self.enemy_bullets,
                    self.enemy_lasers,
                    self.enemies,
                    self.boss_eyes
                )
            )
        else:
            self.player.update()

            if self.player.can_shoot():
                self.player_bullets.extend(self.player.shoot())

        self.update_waves()

        for bullet in self.player_bullets:
            bullet.update()

        for bullet in self.enemy_bullets:
            bullet.update()

        for laser in self.enemy_lasers:
            laser.update()

        for eye in self.boss_eyes:
            eye.update()

            if eye.ready_to_shoot():
                if random.random() < 0.5:
                    self.enemy_bullets.extend(eye.shoot_aimed(self.player))
                else:
                    self.enemy_bullets.extend(eye.shoot_spiral())

        for enemy in self.enemies:
            if isinstance(enemy, BossEnemy):
                new_bullets, new_lasers, new_eyes = enemy.update()

                self.enemy_bullets.extend(new_bullets)
                self.enemy_lasers.extend(new_lasers)
                self.boss_eyes.extend(new_eyes)

            else:
                enemy.update()

                if enemy.ready_to_shoot():
                    if enemy.type == "laser":
                        self.enemy_lasers.append(
                            EnemyLaser(
                                enemy.rect.centerx,
                                enemy.rect.bottom,
                                enemy.rect.centerx,
                                HEIGHT,
                                delay=60,
                                active_time=45
                            )
                        )
                    else:
                        self.enemy_bullets.extend(enemy.shoot(self.player))

        self.player_bullets = [
            bullet for bullet in self.player_bullets
            if not bullet.offscreen()
        ]

        self.enemy_bullets = [
            bullet for bullet in self.enemy_bullets
            if not bullet.offscreen()
        ]

        self.enemy_lasers = [
            laser for laser in self.enemy_lasers
            if not laser.finished()
        ]

        self.check_collisions()

    def check_collisions(self):
        for enemy in self.enemies[:]:
            if hasattr(enemy, "can_be_hit") and not enemy.can_be_hit():
                continue

            for bullet in self.player_bullets[:]:
                if enemy.rect.colliderect(bullet.rect):
                    enemy.hp -= 1

                    if bullet in self.player_bullets:
                        self.player_bullets.remove(bullet)

                    if enemy.hp <= 0:
                        self.score += self.get_enemy_score(enemy)

                        if isinstance(enemy, BossEnemy):
                            self.boss_eyes.clear()

                        if enemy in self.enemies:
                            self.enemies.remove(enemy)

                    break

        for eye in self.boss_eyes[:]:
            for bullet in self.player_bullets[:]:
                if eye.rect.colliderect(bullet.rect):
                    eye.hp -= 1

                    if bullet in self.player_bullets:
                        self.player_bullets.remove(bullet)

                    if eye.hp <= 0:
                        self.score += self.get_boss_eye_score(eye)

                        if eye in self.boss_eyes:
                            self.boss_eyes.remove(eye)

                    break

        player_hitbox = self.player.get_hitbox()

        for bullet in self.enemy_bullets:
            if self.bullet_hits_player(bullet):
                self.running = False

        for enemy in self.enemies:
            if player_hitbox.colliderect(enemy.rect):
                self.running = False

    def draw_background(self):
        self.screen.fill(STAGE3_BG)

        for star in self.stars:
            pygame.draw.circle(
                self.screen,
                (80, 120, 180),
                (star[0], star[1]),
                star[2]
            )

    def draw_score(self):
        text = self.font.render(f"SCORE: {self.score}", True, WHITE)
        self.screen.blit(text, (30, 30))

        wave_text = self.font.render(f"WAVE: {self.wave}", True, WHITE)
        self.screen.blit(wave_text, (30, 65))

        best_text = self.font.render(f"BEST: {self.high_score}", True, WHITE)
        self.screen.blit(best_text, (30, 100))

        help_text = pygame.font.SysFont("arial", 22, bold=True).render(
            "WASD/ARROW: MOVE   SHIFT: SLOW   SPACE/J: SHOOT   ESC: MENU",
            True,
            (180, 220, 255)
        )
        self.screen.blit(help_text, (30, HEIGHT - 35))

    def draw(self):
        self.draw_background()

        for bullet in self.player_bullets:
            bullet.draw(self.screen)

        for enemy in self.enemies:
            enemy.draw(self.screen)

        for eye in self.boss_eyes:
            eye.draw(self.screen)

        for bullet in self.enemy_bullets:
            bullet.draw(self.screen)

        for laser in self.enemy_lasers:
            laser.draw(self.screen)

        self.player.draw(self.screen)
        self.draw_score()
        self.auto_player.draw(self.screen)
        
        pygame.display.update()

    def game_over(self):
        final_score = self.score

        if self.high_score_manager.update("stage3", final_score):
            self.high_score = final_score

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

            self.draw_background()

            game_over_text = self.big_font.render("GAME OVER", True, WHITE)
            game_over_rect = game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 70))
            self.screen.blit(game_over_text, game_over_rect)

            score_text = self.font.render(f"SCORE: {self.score}", True, WHITE)
            score_rect = score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            self.screen.blit(score_text, score_rect)

            best_text = self.font.render(f"BEST: {self.high_score}", True, WHITE)
            best_rect = best_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 40))
            self.screen.blit(best_text, best_rect)

            help_text = self.font.render("SPACE / R / CLICK: RESTART    ESC: MENU", True, WHITE)
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