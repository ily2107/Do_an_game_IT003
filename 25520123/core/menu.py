import pygame
from setting import *


class Menu:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()

        self.state = "main"

        self.background = pygame.image.load(
            "assets/Hình nền  _ cây, lá, Chim, Anime, Bầu trời, Đảo nổi, rừng nhiệt đới, Đất ngập nước, đồng cỏ, Ảnh chụp màn hình, 1366x768 px, môi trường sống, môi trường tự nhiên, Hình nền máy tính, Hệ sinh thái, Biome 1366x.jpg"
        ).convert()
        self.background = pygame.transform.scale(self.background, (WIDTH, HEIGHT))

        try:
            self.title_font = pygame.font.Font("04B_19.TTF", 55)
            self.button_font = pygame.font.Font("04B_19.TTF", 38)
            self.card_font = pygame.font.Font("04B_19.TTF", 28)
        except:
            self.title_font = pygame.font.SysFont("arial", 55, bold=True)
            self.button_font = pygame.font.SysFont("arial", 38, bold=True)
            self.card_font = pygame.font.SysFont("arial", 28, bold=True)

        self.play_button = pygame.Rect(0, 0, 180, 70)
        self.play_button.center = (WIDTH // 2, HEIGHT // 2 + 110)

        self.card_width = 280
        self.card_height = 180
        self.card_gap = 50

        total_width = self.card_width * 3 + self.card_gap * 2
        start_x = (WIDTH - total_width) // 2
        card_y = HEIGHT // 2 - 20

        self.map_cards = [
            {
                "id": "map1",
                "name": "MAP 1",
                "rect": pygame.Rect(start_x, card_y, self.card_width, self.card_height),
                "image": self.load_card_image("assets/flappy-bird-wnu7w.png")
            },
            {
                "id": "map2",
                "name": "MAP 2",
                "rect": pygame.Rect(start_x + self.card_width + self.card_gap, card_y, self.card_width, self.card_height),
                "image": self.load_card_image("assets/2023_12_18_638384961936163025_geometry-dash-12.webp")
            },
            {
                "id": "map3",
                "name": "MAP 3",
                "rect": pygame.Rect(start_x + (self.card_width + self.card_gap) * 2, card_y, self.card_width, self.card_height),
                "image": self.load_card_image("assets/35260cee-2edd-4f1d-adf1-f203de512a25_1280x960.jpg")
            }
        ]

        self.running = True

    def load_card_image(self, path):
        image = pygame.image.load(path).convert()
        image = pygame.transform.scale(image, (self.card_width, self.card_height))
        return image

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == "select":
                        self.state = "main"

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.state == "main":
                        if self.play_button.collidepoint(mouse_pos):
                            self.state = "select"

                    elif self.state == "select":
                        for card in self.map_cards:
                            if card["rect"].collidepoint(mouse_pos):
                                return card["id"]

        return None

    def draw_play_button(self):
        mouse_pos = pygame.mouse.get_pos()

        if self.play_button.collidepoint(mouse_pos):
            button_color = (255, 220, 80)
        else:
            button_color = (255, 190, 40)

        pygame.draw.rect(self.screen, button_color, self.play_button, border_radius=18)
        pygame.draw.rect(self.screen, (255, 255, 255), self.play_button, 4, border_radius=18)

        text = self.button_font.render("PLAY", True, (255, 255, 255))
        text_rect = text.get_rect(center=self.play_button.center)
        self.screen.blit(text, text_rect)

    def draw_card(self, card):
        mouse_pos = pygame.mouse.get_pos()
        rect = card["rect"]

        self.screen.blit(card["image"], rect)

        overlay = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 70))
        self.screen.blit(overlay, rect)

        if rect.collidepoint(mouse_pos):
            border_color = (255, 230, 80)
            border_width = 6
            scale_rect = rect.inflate(14, 14)
            pygame.draw.rect(self.screen, border_color, scale_rect, border_width, border_radius=18)
        else:
            border_color = (255, 255, 255)
            border_width = 3
            pygame.draw.rect(self.screen, border_color, rect, border_width, border_radius=14)

        text = self.card_font.render(card["name"], True, (255, 255, 255))
        text_rect = text.get_rect(center=(rect.centerx, rect.bottom + 35))
        self.screen.blit(text, text_rect)

    def draw_main(self):
        title = self.title_font.render("SUPER BIRD", True, (255, 255, 255))
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 90))
        self.screen.blit(title, title_rect)

        self.draw_play_button()

    def draw_select(self):
        title = self.title_font.render("SELECT MAP", True, (255, 255, 255))
        title_rect = title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 180))
        self.screen.blit(title, title_rect)

        for card in self.map_cards:
            self.draw_card(card)

    def draw(self):
        self.screen.blit(self.background, (0, 0))

        if self.state == "main":
            self.draw_main()
        elif self.state == "select":
            self.draw_select()

        pygame.display.update()

    def run(self):
        self.state = "main"

        while self.running:
            self.clock.tick(60)

            action = self.handle_events()

            if action == "quit":
                pygame.quit()
                exit()

            if action in ["map1", "map2", "map3"]:
                return action

            self.draw()