import json
import os
import random
import sys
import time

import pygame

APP_ID = "org.evans.SpaceDodge"
WINDOW_FLAGS = pygame.RESIZABLE

pygame.init()
pygame.font.init()

# ----- SETTINGS -----
if getattr(sys, "frozen", False):
    BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

GAME_PATH = BASE_DIR

if os.environ.get("FLATPAK_ID") == APP_ID:
    SCORE_DIR = os.path.join(os.path.expanduser("~"), ".var", "app", APP_ID)
else:
    XDG_DATA_HOME = os.environ.get(
        "XDG_DATA_HOME",
        os.path.join(os.path.expanduser("~"), ".local", "share"),
    )
    SCORE_DIR = os.path.join(XDG_DATA_HOME, "SpaceDodge")

SCORES_FILE = os.path.join(SCORE_DIR, "scores.txt")

WIDTH, HEIGHT = 1364, 698
WIN = pygame.display.set_mode((WIDTH, HEIGHT), WINDOW_FLAGS)
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
AUDIO_ENABLED = False
UI_FPS = 60
BUTTON_BG = (18, 28, 50)
BUTTON_HOVER = (36, 58, 98)
BUTTON_BORDER = (120, 190, 255)
BUTTON_TEXT = "white"


def asset_path(filename, subdir=None):
    """Resolve assets from either the project root or packaged asset folders."""
    candidates = [os.path.join(GAME_PATH, filename)]
    if subdir:
        candidates.append(os.path.join(GAME_PATH, "assets", subdir, filename))

    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]


def initialize_audio():
    """Initialize the mixer and start the menu music when available."""
    global AUDIO_ENABLED

    try:
        pygame.mixer.init()
    except pygame.error:
        return

    menu_track = asset_path("pulsar.mp3", "music")
    if not os.path.exists(menu_track):
        return

    try:
        pygame.mixer.music.load(menu_track)
        pygame.mixer.music.set_volume(0.6)
        pygame.mixer.music.play(-1)
        AUDIO_ENABLED = True
    except pygame.error:
        AUDIO_ENABLED = False

# ----- HELPER FUNCTIONS -----
def load_scores():
    """Load high scores from file."""
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_scores(scores):
    """Save updated scores to file."""
    os.makedirs(SCORE_DIR, exist_ok=True)
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f)

def draw_text_center(text, size, color, y):
    """Draw centered text."""
    font_obj = pygame.font.SysFont(None, size)
    text_surf = font_obj.render(text, True, color)
    WIN.blit(text_surf, (WIDTH / 2 - text_surf.get_width() / 2, y))


def draw_text_left(text, size, color, x, y):
    """Draw text aligned from the left edge."""
    font_obj = pygame.font.SysFont(None, size)
    text_surf = font_obj.render(text, True, color)
    WIN.blit(text_surf, (x, y))


def build_button_rect(center_y, width=280, height=56):
    """Create a centered button rectangle."""
    return pygame.Rect(WIDTH // 2 - width // 2, center_y - height // 2, width, height)


def draw_button(rect, label, hovered=False):
    """Render a menu button."""
    fill = BUTTON_HOVER if hovered else BUTTON_BG
    pygame.draw.rect(WIN, fill, rect, border_radius=14)
    pygame.draw.rect(WIN, BUTTON_BORDER, rect, width=2, border_radius=14)

    font_obj = pygame.font.SysFont(None, 38)
    text_surf = font_obj.render(label, True, BUTTON_TEXT)
    WIN.blit(
        text_surf,
        (
            rect.centerx - text_surf.get_width() / 2,
            rect.centery - text_surf.get_height() / 2,
        ),
    )

def load_background(level):
    """Load background for the current level."""
    bg_file = asset_path(f"bg_level{level}.jpg", "backgrounds")
    if os.path.exists(bg_file):
        return pygame.transform.scale(pygame.image.load(bg_file), (WIDTH, HEIGHT))

    fallback = pygame.Surface((WIDTH, HEIGHT))
    fallback.fill((4, 8, 18))
    return fallback


def load_menu_background():
    """Load the main menu background if available."""
    bg_file = asset_path("main.png")
    if os.path.exists(bg_file):
        return pygame.transform.scale(pygame.image.load(bg_file), (WIDTH, HEIGHT))

    fallback = pygame.Surface((WIDTH, HEIGHT))
    fallback.fill((8, 10, 24))
    return fallback

def play_level_music(level):
    """Play music for the current level."""
    if not AUDIO_ENABLED:
        return

    music_file = asset_path(f"music_level{level}.mp3", "music")
    if os.path.exists(music_file):
        try:
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.play(-1)
        except pygame.error:
            return


def shift_active_effect_timers(duration, effect_ends):
    """Keep active power-up timers from expiring while the game is paused."""
    for effect_name, end_time in effect_ends.items():
        if end_time > 0:
            effect_ends[effect_name] = end_time + duration


def get_powerup_timers(now, effect_ends):
    """Return display labels for active power-up timers."""
    labels = {
        "shield": "Shield",
        "slow": "Slow",
        "freeze": "Freeze",
        "double": "Double",
    }
    active_effects = []
    for key, label in labels.items():
        remaining = max(0.0, effect_ends[key] - now)
        if remaining > 0:
            active_effects.append(f"{label}: {remaining:0.1f}s")
    return active_effects


def pause_music():
    """Pause background music when supported."""
    if AUDIO_ENABLED:
        pygame.mixer.music.pause()


def resume_music():
    """Resume background music when supported."""
    if AUDIO_ENABLED:
        pygame.mixer.music.unpause()


def pause_menu(frame, elapsed_time, high_score, level, powerup_timers):
    """Show the pause menu and return the selected action."""
    options = ["Resume", "Main Menu", "Quit"]
    selected = 0
    clock = pygame.time.Clock()

    while True:
        clock.tick(UI_FPS)
        mouse_pos = pygame.mouse.get_pos()
        WIN.blit(frame, (0, 0))

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        WIN.blit(overlay, (0, 0))

        draw_text_center("Paused", 64, "white", HEIGHT // 5)
        draw_text_center("Use Up/Down and Enter", 32, "lightgray", HEIGHT // 5 + 55)
        draw_text_center(f"Time: {int(elapsed_time) // 60:02d}m {int(elapsed_time) % 60:02d}s", 30, "white", HEIGHT // 5 + 95)

        menu_top = HEIGHT // 2 - 20
        for index, option in enumerate(options):
            button_rect = build_button_rect(menu_top + index * 72)
            is_hovered = button_rect.collidepoint(mouse_pos)
            if is_hovered:
                selected = index
            draw_button(button_rect, option, hovered=(selected == index or is_hovered))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.VIDEORESIZE:
                resize_window(event.w, event.h)
                frame = pygame.transform.scale(frame, (WIDTH, HEIGHT))
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_p):
                    return "resume"
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    return options[selected].lower().replace(" ", "_")
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for index, option in enumerate(options):
                    button_rect = build_button_rect(menu_top + index * 72)
                    if button_rect.collidepoint(event.pos):
                        return option.lower().replace(" ", "_")


def resize_window(width, height):
    """Resize the game window while keeping a sensible minimum size."""
    global WIDTH, HEIGHT, WIN

    WIDTH = max(800, width)
    HEIGHT = max(500, height)
    WIN = pygame.display.set_mode((WIDTH, HEIGHT), WINDOW_FLAGS)

def main_menu():
    """Display main menu with top 5 leaderboard."""
    scores = load_scores()
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
    bg = load_menu_background()
    options = ["Start", "Quit"]
    selected = 0
    clock = pygame.time.Clock()

    waiting = True
    while waiting:
        clock.tick(UI_FPS)
        mouse_pos = pygame.mouse.get_pos()
        WIN.blit(bg, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 110))
        WIN.blit(overlay, (0, 0))
        draw_text_center("SPACE DODGE", 70, "yellow", HEIGHT // 6)
        draw_text_center("Dodge. Survive. Shoot back.", 36, "white", HEIGHT // 3)

        menu_top = HEIGHT // 2 - 20
        for index, option in enumerate(options):
            button_rect = build_button_rect(menu_top + index * 72)
            is_hovered = button_rect.collidepoint(mouse_pos)
            if is_hovered:
                selected = index
            draw_button(button_rect, option, hovered=(selected == index or is_hovered))

        y_offset = HEIGHT // 2 + 110
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
            if event.type == pygame.VIDEORESIZE:
                resize_window(event.w, event.h)
                bg = load_menu_background()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if options[selected] == "Start":
                        return
                    pygame.quit()
                    quit()
                elif event.key == pygame.K_s:
                    return
                elif event.key == pygame.K_q:
                    pygame.quit()
                    quit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for index, option in enumerate(options):
                    button_rect = build_button_rect(menu_top + index * 72)
                    if button_rect.collidepoint(event.pos):
                        if option == "Start":
                            return
                        pygame.quit()
                        quit()

def input_player_name():
    """Ask the player to enter their name."""
    name = ""
    active = True
    bg = load_menu_background()
    clock = pygame.time.Clock()
    while active:
        clock.tick(UI_FPS)
        WIN.blit(bg, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 130))
        WIN.blit(overlay, (0, 0))
        draw_text_center("Enter Your Name:", 50, "white", HEIGHT // 3)
        draw_text_center(name + "_", 50, "yellow", HEIGHT // 2)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.VIDEORESIZE:
                resize_window(event.w, event.h)
                bg = load_menu_background()
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
    bg = load_menu_background()
    options = ["Retry", "Quit"]
    selected = 0
    clock = pygame.time.Clock()
    waiting = True
    while waiting:
        clock.tick(UI_FPS)
        mouse_pos = pygame.mouse.get_pos()
        WIN.blit(bg, (0, 0))
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 125))
        WIN.blit(overlay, (0, 0))

        draw_text_center("GAME OVER", 60, "white", HEIGHT // 3)
        minutes = int(elapsed_time) // 60
        seconds = int(elapsed_time) % 60
        draw_text_center(f"Your Time: {minutes:02d}m {seconds:02d}s", 40, "white", HEIGHT // 2 - 40)
        hs_minutes = int(high_score) // 60
        hs_seconds = int(high_score) % 60
        draw_text_center(f"Best ({player_name}): {hs_minutes:02d}m {hs_seconds:02d}s", 35, "yellow", HEIGHT // 2)

        menu_top = HEIGHT // 2 + 90
        for index, option in enumerate(options):
            button_rect = build_button_rect(menu_top + index * 72)
            is_hovered = button_rect.collidepoint(mouse_pos)
            if is_hovered:
                selected = index
            draw_button(button_rect, option, hovered=(selected == index or is_hovered))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.VIDEORESIZE:
                resize_window(event.w, event.h)
                bg = load_menu_background()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return options[selected] == "Retry"
                elif event.key == pygame.K_r:
                    return True
                elif event.key == pygame.K_q:
                    return False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for index, option in enumerate(options):
                    button_rect = build_button_rect(menu_top + index * 72)
                    if button_rect.collidepoint(event.pos):
                        return option == "Retry"

def draw(player, elapsed_time, stars, high_score, level, powerups, shield_active, bg, boss, boss_hp, boss_max_hp, bullets, powerup_timers=None):
    WIN.blit(bg, (0, 0))

    minutes = int(elapsed_time) // 60
    seconds = int(elapsed_time) % 60
    WIN.blit(FONT.render(f"Time: {minutes:02d}m {seconds:02d}s", 1, "white"), (10, 10))
    hs_minutes = int(high_score) // 60
    hs_seconds = int(high_score) % 60
    WIN.blit(FONT.render(f"Best: {hs_minutes:02d}m {hs_seconds:02d}s", 1, "yellow"), (10, 40))
    WIN.blit(FONT.render(f"Level: {level}", 1, "cyan"), (10, 70))

    if player is not None:
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

    draw_text_left("P / ESC: Pause", 28, "white", 10, HEIGHT - 40)
    if powerup_timers:
        timer_y = 100
        for timer_text in powerup_timers:
            draw_text_left(timer_text, 28, "gold", 10, timer_y)
            timer_y += 28

    pygame.display.update()

# ------------------- MAIN GAME LOOP -------------------
def main():
    initialize_audio()
    while True:
        main_menu()
        player_name = input_player_name()

        scores = load_scores()
        high_score = scores.get(player_name, 0)

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
        freeze_active = False
        double_points_active = False
        effect_ends = {
            "shield": 0,
            "slow": 0,
            "freeze": 0,
            "double": 0,
        }

        boss = None
        boss_timer = 0
        boss_vel = 0
        boss_hp = 0
        boss_max_hp = 0
        boss_spawned_for_level = False

        bullets = []

        while run:
            dt = clock.tick(60)
            star_count += dt
            powerup_timer += dt
            boss_timer += dt
            now = time.time()
            elapsed_time = now - start_time
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
                boss_spawned_for_level = False

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
            if level % 5 == 0 and boss is None and not boss_spawned_for_level and boss_timer > 8000:
                boss = pygame.Rect(random.randint(0, WIDTH - 100), 0, 100, 100)
                boss_vel = star_vel * 1.5
                boss_max_hp = 10 * level
                boss_hp = boss_max_hp
                boss_timer = 0
                boss_spawned_for_level = True

            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
                if event.type == pygame.VIDEORESIZE:
                    resize_window(event.w, event.h)
                    bg = load_background(level)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        bullet = pygame.Rect(player.x + player.width // 2 - BULLET_WIDTH // 2, player.y, BULLET_WIDTH, BULLET_HEIGHT)
                        bullets.append(bullet)
                    elif event.key in (pygame.K_p, pygame.K_ESCAPE):
                        frame_powerups = get_powerup_timers(now, effect_ends)
                        draw(
                            player,
                            effective_time,
                            stars,
                            high_score,
                            level,
                            powerups,
                            shield_active,
                            bg,
                            boss,
                            boss_hp,
                            boss_max_hp,
                            bullets,
                            frame_powerups,
                        )
                        pause_frame = WIN.copy()
                        pause_music()
                        pause_started = time.time()
                        action = pause_menu(
                            pause_frame,
                            effective_time,
                            high_score,
                            level,
                            frame_powerups,
                        )
                        pause_duration = time.time() - pause_started
                        start_time += pause_duration
                        shift_active_effect_timers(pause_duration, effect_ends)
                        if action == "quit":
                            pygame.quit()
                            return
                        if action == "main_menu":
                            resume_music()
                            run = False
                            break
                        resume_music()
                        bg = load_background(level)

            if not run:
                continue

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
                        effect_ends["shield"] = now + 30
                    elif p["type"] == "slow":
                        slow_motion_active = True
                        effect_ends["slow"] = now + 5
                    elif p["type"] == "freeze":
                        freeze_active = True
                        effect_ends["freeze"] = now + 3
                    elif p["type"] == "double":
                        double_points_active = True
                        effect_ends["double"] = now + 10
                    powerups.remove(p)

            # Bullets movement & collisions
            for b in bullets[:]:
                b.y -= BULLET_VEL
                if b.y < 0:
                    bullets.remove(b)
                else:
                    bullet_consumed = False
                    for star in stars[:]:
                        if b.colliderect(star):
                            stars.remove(star)
                            bullets.remove(b)
                            bullet_consumed = True
                            break
                    if bullet_consumed:
                        continue
                    if boss and b.colliderect(boss):
                        bullets.remove(b)
                        boss_hp -= 1
                        if boss_hp <= 0:
                            boss = None

            # Power-up timers
            if shield_active and now > effect_ends["shield"]:
                shield_active = False
                effect_ends["shield"] = 0
            if slow_motion_active and now > effect_ends["slow"]:
                slow_motion_active = False
                effect_ends["slow"] = 0
            if freeze_active and now > effect_ends["freeze"]:
                freeze_active = False
                effect_ends["freeze"] = 0
            if double_points_active and now > effect_ends["double"]:
                double_points_active = False
                effect_ends["double"] = 0

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

            draw(
                player,
                effective_time,
                stars,
                high_score,
                level,
                powerups,
                shield_active,
                bg,
                boss,
                boss_hp,
                boss_max_hp,
                bullets,
                get_powerup_timers(now, effect_ends),
            )

if __name__ == "__main__":
    main()
