import json
import random
from pathlib import Path

import pygame
from pygame.math import Vector2


# Find data files beside this script, even when launched from IDLE.
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data"

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 600
FPS = 60

BG_COLOR = (28, 43, 39)
PLAYER_COLOR = (90, 190, 255)
ENEMY_COLOR = (245, 105, 100)
TEXT_COLOR = (245, 245, 235)
PANEL_COLOR = (26, 31, 41)
ACCENT_COLOR = (255, 216, 100)


def load_json(filename):
    """Load a JSON file from the project's data folder."""
    path = DATA_DIR / filename
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


class Creature:
    def __init__(self, data):
        self.name = data["name"]
        self.max_hp = int(data["max_hp"])
        self.hp = self.max_hp
        self.attack_power = int(data["attack"])
        self.defense = int(data["defense"])

    @property
    def fainted(self):
        return self.hp <= 0

    def take_damage(self, attack_power):
        damage = max(1, attack_power + random.randint(-2, 2) - self.defense)
        self.hp = max(0, self.hp - damage)
        return damage


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Aura Pup: Forest Light")

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 20)
        self.small_font = pygame.font.SysFont("Arial", 16)
        self.title_font = pygame.font.SysFont("Arial", 30, bold=True)

        self.creature_data = load_json("creatures.json")
        self.story_data = load_json("story.json")

        self.player = Creature(self.creature_data["player"])
        self.wild_creatures = self.creature_data["wild_creatures"]

        self.pet_pos = Vector2(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.pet_velocity = Vector2(0, 0)
        self.pet_speed = 230

        self.elder_pos = Vector2(180, 170)
        self.elder_radius = 24

        self.state = "roaming"
        self.message = self.story_data["intro"][0]
        self.dialogue_index = 0
        self.enemy = None
        self.encounter_timer = 0

        self.running = True

    def start_battle(self):
        self.enemy = Creature(random.choice(self.wild_creatures))
        self.state = "battle"
        self.message = f"A wild {self.enemy.name} appeared! Press SPACE to attack."

    def attack(self):
        if self.state != "battle" or self.enemy is None:
            return

        damage = self.enemy.take_damage(self.player.attack_power)

        if self.enemy.fainted:
            self.message = f"{self.enemy.name} was defeated! Press SPACE to continue."
            self.state = "battle_won"
            return

        enemy_damage = self.player.take_damage(self.enemy.attack_power)

        if self.player.fainted:
            self.player.hp = self.player.max_hp
            self.state = "roaming"
            self.message = (
                f"Aura Pup got tired and rested. "
                f"Your health was restored. You dealt {damage} damage."
            )
            self.enemy = None
            return

        self.message = (
            f"You dealt {damage} damage. "
            f"{self.enemy.name} hit back for {enemy_damage}. "
            f"Press SPACE to attack again."
        )

    def handle_key(self, key):
        if key == pygame.K_ESCAPE:
            self.running = False
        elif key == pygame.K_SPACE:
            if self.state == "battle":
                self.attack()
            elif self.state == "battle_won":
                self.state = "roaming"
                self.enemy = None
                self.message = "Keep exploring the forest."

    def update_roaming(self, dt):
        mouse_pos = Vector2(pygame.mouse.get_pos())
        direction = mouse_pos - self.pet_pos
        distance = direction.length()

        if distance > 4:
            desired_speed = min(self.pet_speed, distance * 4)
            desired_velocity = direction.normalize() * desired_speed
        else:
            desired_velocity = Vector2(0, 0)

        # Frame-rate-independent easing for smooth movement.
        blend = 1 - pow(0.001, dt)
        self.pet_velocity += (desired_velocity - self.pet_velocity) * blend
        self.pet_pos += self.pet_velocity * dt

        # Keep the pet inside the game window.
        self.pet_pos.x = max(20, min(SCREEN_WIDTH - 20, self.pet_pos.x))
        self.pet_pos.y = max(60, min(SCREEN_HEIGHT - 80, self.pet_pos.y))

        # Talking to the elder.
        elder_distance = self.pet_pos.distance_to(self.elder_pos)
        if elder_distance < 55 and pygame.mouse.get_pressed()[0]:
            dialogue = self.story_data["elder_dialogue"]
            self.message = dialogue[self.dialogue_index % len(dialogue)]
            self.dialogue_index += 1

        # Random encounters happen while the pet is moving.
        if distance > 70:
            self.encounter_timer += dt
            if self.encounter_timer >= 8:
                self.encounter_timer = 0
                if random.random() < 0.35:
                    self.start_battle()
        else:
            self.encounter_timer = 0

    def draw_text(self, text, x, y, color=TEXT_COLOR, font=None):
        font = font or self.font
        image = font.render(text, True, color)
        self.screen.blit(image, (x, y))

    def draw_roaming(self):
        self.screen.fill(BG_COLOR)

        # Simple paths and trees for a forest-like scene.
        pygame.draw.rect(self.screen, (85, 75, 57), (0, 390, SCREEN_WIDTH, 65))
        for x, y in [(60, 100), (760, 110), (700, 350), (100, 500), (830, 490)]:
            pygame.draw.circle(self.screen, (39, 91, 59), (x, y), 36)
            pygame.draw.circle(self.screen, (54, 119, 70), (x - 8, y - 8), 25)

        # Elder Rowan.
        pygame.draw.circle(self.screen, (219, 185, 143), self.elder_pos, self.elder_radius)
        pygame.draw.circle(
            self.screen, (75, 50, 40),
            (int(self.elder_pos.x), int(self.elder_pos.y)), 5
        )
        self.draw_text("Elder Rowan", 125, 205, font=self.small_font)

        # Aura Pup.
        pygame.draw.circle(self.screen, (35, 91, 135), self.pet_pos, 25)
        pygame.draw.circle(self.screen, PLAYER_COLOR, self.pet_pos, 20)
        pygame.draw.circle(
            self.screen, (225, 250, 255),
            (int(self.pet_pos.x - 6), int(self.pet_pos.y - 7)), 5
        )

        # HUD and message box.
        pygame.draw.rect(self.screen, PANEL_COLOR, (0, 0, SCREEN_WIDTH, 48))
        self.draw_text(
            f"{self.player.name}   HP: {self.player.hp}/{self.player
