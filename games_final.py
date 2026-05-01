import pygame
import time
import random
import os
import sys
import json

pygame.init()
pygame.font.init()
pygame.mixer.init()

# ----- SETTINGS -----
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

GAME_PATH = BASE_DIR
SCORES_FILE = os.path.join(
    os.path.expanduser("~"),
    ".var/app/org.evans.SpaceDodge/scores.txt"
)
#GAME_PATH = r"/home/evans/Documents/Space Dodge"
#SCORES_FILE = os.path.join(GAME_PATH, "scores.txt")

WIDTH, HEIGHT = 1364, 698
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Dodge")

PLAYER_WIDTH = 40
PLAYER_HEIGHT = 60
PLAYER_VEL = 10
STAR_WIDTH = 10
STAR_HEIGHT = 20
BULLET_WIDTH = 5
BULLET_HEIGHT = 10
BULLET_VEL = 8

FONT = pygame.font.SysFont("comicsans", 30)

pygame.mixer.music.load(os.path.join(GAME_PATH, "pulsar.mp3"))
pygame.mixer.music.set_volume(0.6)
pygame.mixer.music.play(-1)

# ----- HELPER FUNCTIONS -----
def load_scores():
    """Load high scores from file."""
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_scores(scores):
    """Save updated scores to file."""
    with open(SCORES_FILE, "w") as f:
        json.dump(scores, f)

def draw_text_center(text, size, color, y):
    """Draw centered text."""
    font_obj = pygame.font.SysFont(None, size)
    text_surf = font_obj.render(text, True, color)
    WIN.blit(text_surf, (WIDTH / 2 - text_surf.get_width() / 2, y))

def load_background(level):
    """Load background for the current level."""
    bg_file = os.path.join(GAME_PATH, f"bg_level{level}.jpg")
    if os.path.exists(bg_file):
        return pygame.transform.scale(pygame.image.load(bg_file), (WIDTH, HEIGHT))
    return pygame.Surface((WIDTH, HEIGHT))  # fallback

def play_level_music(level):
    """Play music for the current level."""
    music_file = os.path.join(GAME_PATH, f"music_level{level}.mp3")
    if os.path.exists(music_file):
        pygame.mixer.music.load(music_file)
        pygame.mixer.music.play(-1)

def main_menu():
    """Display main menu with top 5 leaderboard."""
    scores = load_scores()
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]

    waiting = True
    while waiting:
        WIN.fill((0, 0, 0))
        draw_text_center("SPACE DODGE", 70, "yellow", HEIGHT // 6)
        draw_text_center("Press S to Start or Q to Quit", 40, "white", HEIGHT // 3)

        y_offset = HEIGHT // 2
        draw_text_center("🏆 Top 5 Players", 45, "cyan", y_offset)
        y_offset += 50

        for name, score in sorted_scores:
            minutes = int(score) // 60
            seconds = int(score) % 60
            draw_text_center(f"{name}: {minutes:02d}m {seconds:02d}s", 35, "white", y_offset)
            y_offset += 40

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_s:
                    return
                elif event.key == pygame.K_q:
                    pygame.quit()
                    quit()

def input_player_name():
    """Ask the player to enter their name."""
    name = ""
    active = True
    while active:
        WIN.fill((0, 0, 0))
        draw_text_center("Enter Your Name:", 50, "white", HEIGHT // 3)
        draw_text_center(name + "_", 50, "yellow", HEIGHT // 2)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and name.strip() != "":
                    active = False
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                else:
                    if len(name) < 12 and event.unicode.isalnum():
                        name += event.unicode
    return name

def game_over_screen(elapsed_time, high_score, player_name):
    """Show Game Over screen."""
    WIN.fill((0, 0, 0))
    draw_text_center("GAME OVER", 60, "white", HEIGHT // 3)
    minutes = int(elapsed_time) // 60
    seconds = int(elapsed_time) % 60
    draw_text_center(f"Your Time: {minutes:02d}m {seconds:02d}s", 40, "white", HEIGHT // 2 - 40)
    hs_minutes = int(high_score) // 60
    hs_seconds = int(high_score) % 60
    draw_text_center(f"Best ({player_name}): {hs_minutes:02d}m {hs_seconds:02d}s", 35, "yellow", HEIGHT // 2)
    draw_text_center("Press R to Retry or Q to Quit", 35, "white", HEIGHT // 2 + 60)
    pygame.display.update()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True
                elif event.key == pygame.K_q:
                    return False

def draw(player, elapsed_time, stars, high_score, level, powerups, shield_active, bg, boss, boss_hp, boss_max_hp, bullets):
    WIN.blit(bg, (0, 0))

    minutes = int(elapsed_time) // 60
    seconds = int(elapsed_time) % 60
    WIN.blit(FONT.render(f"Time: {minutes:02d}m {seconds:02d}s", 1, "white"), (10, 10))
    hs_minutes = int(high_score) // 60
    hs_seconds = int(high_score) % 60
    WIN.blit(FONT.render(f"Best: {hs_minutes:02d}m {hs_seconds:02d}s", 1, "yellow"), (10, 40))
    WIN.blit(FONT.render(f"Level: {level}", 1, "cyan"), (10, 70))

    color = "blue" if shield_active else "red"
    pygame.draw.rect(WIN, color, player)

    for star in stars:
        pygame.draw.rect(WIN, "white", star)
    for p in powerups:
        pygame.draw.rect(WIN, p["color"], p["rect"])
    for b in bullets:
        pygame.draw.rect(WIN, "yellow", b)

    if boss:
        pygame.draw.rect(WIN, "orange", boss)
        bar_width = 200
        bar_height = 15
        bar_x = WIDTH // 2 - bar_width // 2
        bar_y = 20
        pygame.draw.rect(WIN, "red", (bar_x, bar_y, bar_width, bar_height))
        health_ratio = boss_hp / boss_max_hp
        current_width = int(bar_width * health_ratio)
        pygame.draw.rect(WIN, "green", (bar_x, bar_y, current_width, bar_height))
        #pygame.draw.rect(WIN, "green", (bar_x, bar_y, int(bar_width * (boss_hp / boss_max_hp) * bar_width), bar_height))

    pygame.display.update()

# ------------------- MAIN GAME LOOP -------------------
def main():
    main_menu()
    player_name = input_player_name()

    scores = load_scores()
    high_score = scores.get(player_name, 0)

    while True:
        run = True
        player = pygame.Rect(200, HEIGHT - PLAYER_HEIGHT, PLAYER_WIDTH, PLAYER_HEIGHT)
        clock = pygame.time.Clock()
        start_time = time.time()
        elapsed_time = 0

        star_add_increment = 678
        star_count = 0
        stars = []
        hit = False

        level = 1
        star_vel = 2.3
        bg = load_background(level)
        play_level_music(level)

        powerups = []
        powerup_timer = 0
        shield_active = False
        shield_end = 0
        slow_motion_active = False
        slow_end = 0
        freeze_active = False
        freeze_end = 0
        double_points_active = False
        double_points_end = 0

        boss = None
        boss_timer = 0
        boss_vel = 0
        boss_hp = 0
        boss_max_hp = 0

        bullets = []

        while run:
            dt = clock.tick(60)
            star_count += dt
            powerup_timer += dt
            boss_timer += dt
            elapsed_time = time.time() - start_time
            effective_time = elapsed_time * (2 if double_points_active else 1)

            # Level progression
            new_level = int(effective_time // 90) + 1
            if new_level > level:
                level = new_level
                star_vel += 0.5
                if star_add_increment > 200:
                    star_add_increment -= 30
                bg = load_background(level)
                play_level_music(level)
                boss = None

            # Star spawning
            if star_count > star_add_increment:
                for _ in range(level):
                    star_x = random.randint(0, WIDTH - STAR_WIDTH)
                    stars.append(pygame.Rect(star_x, STAR_HEIGHT, STAR_WIDTH, STAR_HEIGHT))
                star_count = 0

            # Power-up spawning
            if powerup_timer > random.randint(10000, 15000):
                kind = random.choice(["shield", "slow", "freeze", "double"])
                color_map = {"shield": "blue", "slow": "green", "freeze": "cyan", "double": "gold"}
                rect = pygame.Rect(random.randint(0, WIDTH - 30), 0, 30, 30)
                powerups.append({"type": kind, "color": color_map[kind], "rect": rect})
                powerup_timer = 0

            # Boss spawning
            if level % 5 == 0 and boss is None and boss_timer > 8000:
                boss = pygame.Rect(random.randint(0, WIDTH - 100), 0, 100, 100)
                boss_vel = star_vel * 1.5
                boss_max_hp = 10 * level
                boss_hp = boss_max_hp
                boss_timer = 0

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        bullet = pygame.Rect(player.x + player.width // 2 - BULLET_WIDTH // 2, player.y, BULLET_WIDTH, BULLET_HEIGHT)
                        bullets.append(bullet)

            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] and player.x - PLAYER_VEL >= 0:
                player.x -= PLAYER_VEL
            if keys[pygame.K_RIGHT] and player.x + PLAYER_VEL + player.width <= WIDTH:
                player.x += PLAYER_VEL

            # Update stars
            for star in stars[:]:
                if not freeze_active:
                    vel = star_vel * (0.5 if slow_motion_active else 1)
                    star.y += vel
                if star.y > HEIGHT:
                    stars.remove(star)
                elif star.colliderect(player) and not shield_active:
                    hit = True
                    break

            # Power-ups collision
            for p in powerups[:]:
                p["rect"].y += 3
                if p["rect"].y > HEIGHT:
                    powerups.remove(p)
                elif p["rect"].colliderect(player):
                    if p["type"] == "shield":
                        shield_active = True
                        shield_end = time.time() + 30
                    elif p["type"] == "slow":
                        slow_motion_active = True
                        slow_end = time.time() + 5
                    elif p["type"] == "freeze":
                        freeze_active = True
                        freeze_end = time.time() + 3
                    elif p["type"] == "double":
                        double_points_active = True
                        double_points_end = time.time() + 10
                    powerups.remove(p)

            # Bullets movement & collisions
            for b in bullets[:]:
                b.y -= BULLET_VEL
                if b.y < 0:
                    bullets.remove(b)
                else:
                    for star in stars[:]:
                        if b.colliderect(star):
                            stars.remove(star)
                            bullets.remove(b)
                            break
                    if boss and b.colliderect(boss):
                        bullets.remove(b)
                        boss_hp -= 1
                        if boss_hp <= 0:
                            boss = None

            # Power-up timers
            if shield_active and time.time() > shield_end:
                shield_active = False
            if slow_motion_active and time.time() > slow_end:
                slow_motion_active = False
            if freeze_active and time.time() > freeze_end:
                freeze_active = False
            if double_points_active and time.time() > double_points_end:
                double_points_active = False

            # Boss update
            if boss:
                boss.y += boss_vel
                if boss.y > HEIGHT:
                    boss = None
                elif boss.colliderect(player) and not shield_active:
                    hit = True

            # Check loss
            if hit:
                if elapsed_time > high_score:
                    high_score = elapsed_time
                    scores[player_name] = high_score
                    save_scores(scores)
                retry = game_over_screen(elapsed_time, high_score, player_name)
                if retry:
                    break
                else:
                    pygame.quit()
                    return

            draw(player, effective_time, stars, high_score, level, powerups, shield_active, bg, boss, boss_hp, boss_max_hp, bullets)

if __name__ == "__main__":
    main()
