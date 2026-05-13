import pygame
from setting import *


class AutoPlayer:
    def __init__(self):
        self.enabled = False
        self.button_rect = pygame.Rect(WIDTH - 118, 16, 100, 40)
        self.font = pygame.font.SysFont("arial", 20, bold=True)
        self.cooldown = 0
        self.safe_margin = 35

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.button_rect.collidepoint(event.pos):
                self.enabled = not self.enabled
                return True
        return False

    def get_next_pipe(self, bird, pipes):
        front_pipes = []

        for pipe in pipes:
            if pipe.top_rect.right > bird.rect.left - 35:
                front_pipes.append(pipe)

        if len(front_pipes) == 0:
            return None

        return min(front_pipes, key=lambda pipe: pipe.top_rect.x)

    def flap(self, bird, sound=None):
        bird.velocity = -5
        bird.swap = True

        if sound is not None:
            sound.jump_sound.play()

        self.cooldown = 4

    def predict_y(self, y, velocity, frames):
        pos = y
        v = velocity

        for i in range(frames):
            v += P
            pos += v

        return pos


    def flap_is_safe(self, bird, gap_top):
        if gap_top <= 5:
            return True

        for frame in range(1, 32):
            future_top = self.predict_y(bird.rect.top, -5, frame)

            if future_top < gap_top + 35:
                return False

        return True


    def will_touch_bottom(self, bird, gap_bottom, frames, buffer):
        for frame in range(1, frames + 1):
            future_bottom = self.predict_y(bird.rect.bottom, bird.velocity, frame)

            if future_bottom > gap_bottom - buffer:
                return True

        return False

    def get_pipe_bounds(self, pipe):
        if hasattr(pipe, "gap_top") and hasattr(pipe, "gap_bottom"):
            gap_top = pipe.gap_top + self.safe_margin
            gap_bottom = pipe.gap_bottom - self.safe_margin
        else:
            gap_top = pipe.top_rect.bottom + self.safe_margin
            gap_bottom = pipe.bottom_rect.top - self.safe_margin

        return gap_top, gap_bottom


    def get_pipes_ahead(self, bird, pipes):
        front_pipes = []

        for pipe in pipes:
            if pipe.top_rect.right > bird.rect.left - 35:
                front_pipes.append(pipe)

        front_pipes.sort(key=lambda pipe: pipe.top_rect.x)
        return front_pipes

    def update(self, bird, pipes, floor_y, sound=None):
        if not self.enabled:
            return

        if self.cooldown > 0:
            self.cooldown -= 1

        front_pipes = self.get_pipes_ahead(bird, pipes)

        current_pipe = front_pipes[0] if len(front_pipes) > 0 else None
        next_pipe = front_pipes[1] if len(front_pipes) > 1 else None

        inside_pipe_zone = False
        just_exiting_pipe = False

        if current_pipe is None:
            gap_top = 80
            gap_bottom = floor_y - 80
            active_pipe = None
        else:
            current_top, current_bottom = self.get_pipe_bounds(current_pipe)
            current_target = (current_top + current_bottom) // 2

            active_pipe = current_pipe
            gap_top = current_top
            gap_bottom = current_bottom

            inside_current_pipe = (
                current_pipe.top_rect.left - 30 < bird.rect.right
                and bird.rect.left < current_pipe.top_rect.right + 70
            )

            already_passed_current = bird.rect.left > current_pipe.top_rect.right + 20

            if next_pipe is not None and not inside_current_pipe and already_passed_current:
                next_top, next_bottom = self.get_pipe_bounds(next_pipe)
                next_target = (next_top + next_bottom) // 2

                need_climb_next = next_target < current_target - 55

                if need_climb_next:
                    active_pipe = next_pipe
                    gap_top = next_top
                    gap_bottom = next_bottom

            inside_pipe_zone = (
                active_pipe.top_rect.left - 30 < bird.rect.right
                and bird.rect.left < active_pipe.top_rect.right + 70
            )

            just_exiting_pipe = (
                bird.rect.left >= active_pipe.top_rect.right
                and bird.rect.left < active_pipe.top_rect.right + 70
            )

        target_y = (gap_top + gap_bottom) // 2
        middle_zone = 35

        bottom_buffer = 48 + max(0, bird.velocity) * 8

        bottom_now = bird.rect.bottom > gap_bottom - 35
        bottom_soon = self.will_touch_bottom(bird, gap_bottom, 14, bottom_buffer)
        near_floor = bird.rect.bottom > floor_y - 75

        below_middle = bird.rect.centery > target_y + middle_zone
        slightly_below_middle = bird.rect.centery > target_y - 8

        too_high = bird.rect.centery < target_y - middle_zone
        too_close_to_top = gap_top > 5 and bird.rect.top < gap_top + 35
        going_up_fast = bird.velocity < -0.4

        need_climb = bird.rect.centery > target_y + 20

        if self.cooldown > 0:
            return

        if too_close_to_top:
            return

        if near_floor:
            if self.flap_is_safe(bird, gap_top):
                self.flap(bird, sound)
            return

        if not self.flap_is_safe(bird, gap_top):
            return

        if need_climb and bird.velocity >= -0.2:
            self.flap(bird, sound)
            return

        if bottom_now:
            if bird.velocity >= -0.2:
                self.flap(bird, sound)
            return

        if bottom_soon:
            if slightly_below_middle and bird.velocity >= -0.2:
                self.flap(bird, sound)
            return

        if just_exiting_pipe:
            if bird.rect.centery > target_y and bird.velocity >= -0.2:
                self.flap(bird, sound)
            return

        if inside_pipe_zone:
            return

        if too_high:
            return

        if going_up_fast:
            return

        if below_middle and bird.velocity >= 0:
            self.flap(bird, sound)

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