import pygame
import sys
import random

# Modules
from audio_manager import AudioManager
from input_manager import MouseInput, HandInput
from ui_manager import SceneManager
from game_engine import ClassicMode, SurvivalMode
from game_objects import Blade, Fruit, Bomb, SlicedFruit, Explosion, SplashEffect

# Colors
WHITE = (255, 255, 255)

# Config
WIDTH, HEIGHT = 800, 600 # Keeping larger window for menu usability
FPS = 60
MIN_CUT_VELOCITY = 150 # Rescaled

# Gesture Power-ups
# Fist -> Shield (blocks the next bomb), Peace sign -> Slow-Mo (fruits/bombs fall slower)
GESTURE_HOLD_FRAMES = 15       # ~0.25s held pose before a power-up triggers (avoids flicker false-positives)
SHIELD_DURATION_FRAMES = 300   # 5s window during which the shield is up, waiting to block a bomb
SHIELD_COOLDOWN_FRAMES = 600   # 10s before Fist can be used again
SLOWMO_DURATION_FRAMES = 180   # 3s of slowed fall speed
SLOWMO_COOLDOWN_FRAMES = 480   # 8s before Peace can be used again
SLOWMO_FACTOR = 0.35           # Fraction of normal fall speed during Slow-Mo


def fresh_powerup_state():
    return {
        "last_gesture": "NONE",
        "gesture_hold_count": 0,
        "shield_timer": 0,
        "shield_cooldown": 0,
        "slowmo_timer": 0,
        "slowmo_cooldown": 0,
    }


def powerup_status_text(label, timer, cooldown):
    if timer > 0:
        return f"{label}: ACTIVO ({timer // FPS + 1}s)"
    elif cooldown > 0:
        return f"{label}: recarga ({cooldown // FPS + 1}s)"
    else:
        return f"{label}: LISTO"


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Fruit Ninja Final")
    clock = pygame.time.Clock()
    
    # Systems
    audio = AudioManager()
    ui = SceneManager(WIDTH, HEIGHT)
    
    # Load Background
    try:
        bg_raw = pygame.image.load("assets/background/game_background.jpg").convert()
        bg_img = pygame.transform.scale(bg_raw, (WIDTH, HEIGHT))
        # Darken it
        dark = pygame.Surface((WIDTH, HEIGHT))
        dark.set_alpha(80) # 30% dark
        dark.fill((0, 0, 0))
        bg_img.blit(dark, (0,0))
    except Exception as e:
        print(f"Background load error: {e}")
        bg_img = pygame.Surface((WIDTH, HEIGHT))
        bg_img.fill((50, 50, 50))

    # Game State Variables
    input_provider = None
    game_mode = None
    blade = Blade()
    powerups = fresh_powerup_state()

    all_sprites = pygame.sprite.Group()
    fruits = pygame.sprite.Group() # Only active fruits (not slices or bombs)
    
    # VFX State
    shake_timer = 0
    
    # Start Music
    audio.play_music("menu")
    
    running = True
    while running:
        mx, my = pygame.mouse.get_pos()
        click = False
        
        # Shake Logic
        shake_x, shake_y = 0, 0
        if shake_timer > 0:
            shake_timer -= 1
            shake_x = random.randint(-5, 5)
            shake_y = random.randint(-5, 5)

        # Event Loop
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    click = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE and ui.current_scene == "GAME":
                    ui.is_paused = not ui.is_paused
                    
        # --- SCENE LOGIC ---
        
        if ui.current_scene == "MENU":
            screen.blit(bg_img, (0,0))
            action = ui.handle_input("MENU", mx, my, click)
            ui.draw_menu(screen)
            if action == "GOTO_MODE":
                ui.push_scene("MODE_SEL")
                audio.play_sfx("start")

        elif ui.current_scene == "MODE_SEL":
            screen.blit(bg_img, (0,0))
            action = ui.handle_input("MODE_SEL", mx, my, click)
            ui.draw_mode_select(screen)
            
            if action == "MODE_CLASSIC":
                game_mode = ClassicMode()
                ui.push_scene("INPUT_SEL")
                audio.play_sfx("start")
            elif action == "MODE_SURVIVAL":
                game_mode = SurvivalMode()
                ui.push_scene("INPUT_SEL")
                audio.play_sfx("start")
            elif action == "BACK":
                ui.pop_scene()
                audio.play_sfx("start")
                
        elif ui.current_scene == "INPUT_SEL":
            screen.blit(bg_img, (0,0))
            action = ui.handle_input("INPUT_SEL", mx, my, click)
            ui.draw_input_select(screen)
            
            if action:
                if action == "INPUT_MOUSE":
                    input_provider = MouseInput(WIDTH, HEIGHT)
                    ui.push_scene("GAME")
                    audio.play_music("game_slow")
                    all_sprites.empty()
                    fruits.empty()
                    blade = Blade()
                    powerups = fresh_powerup_state()
                elif action == "INPUT_HAND":
                    input_provider = HandInput(WIDTH, HEIGHT)
                    ui.push_scene("GAME")
                    audio.play_music("game_slow")
                    all_sprites.empty()
                    fruits.empty()
                    blade = Blade()
                    powerups = fresh_powerup_state()
                elif action == "BACK":
                    ui.pop_scene()
                    audio.play_sfx("start")

        elif ui.current_scene == "GAME":
            # Check if paused
            if ui.is_paused:
                # Draw game state frozen
                if hasattr(input_provider, 'get_frame'):
                    screen.blit(bg_img, (0,0))
                    frame = input_provider.get_frame()
                    if frame is not None:
                        h, w = frame.shape[:2]
                        surf = pygame.image.frombuffer(frame.tobytes(), (w, h), "RGBA")
                        surf = pygame.transform.smoothscale(surf, (WIDTH, HEIGHT))
                        screen.blit(surf, (0,0))
                else:
                    screen.blit(bg_img, (shake_x, shake_y))
                
                all_sprites.draw(screen)
                blade.draw(screen)
                
                # HUD
                hud = ui.font_small.render(game_mode.get_status(), True, WHITE)
                screen.blit(hud, (20, 20))
                
                # Pause menu (mouse-only input)
                action = ui.handle_input("PAUSE", mx, my, click)
                ui.draw_pause(screen)
                
                if action == "RESUME":
                    ui.is_paused = False
                    audio.play_sfx("start")
                elif action == "BACK":
                    ui.is_paused = False
                    if input_provider:
                        input_provider.cleanup()
                        input_provider = None
                    ui.pop_scene()
                    audio.play_music("menu")
            else:
                # Normal gameplay
                ix, iy, velocity, gesture = input_provider.get_input()
                input_paused = (gesture == "OPEN_PALM")

                # --- Gesture Power-ups: Fist = Shield, Peace = Slow-Mo ---
                if gesture in ("FIST", "PEACE") and gesture == powerups["last_gesture"]:
                    powerups["gesture_hold_count"] += 1
                else:
                    powerups["gesture_hold_count"] = 0
                powerups["last_gesture"] = gesture

                if powerups["gesture_hold_count"] == GESTURE_HOLD_FRAMES:
                    if gesture == "FIST" and powerups["shield_cooldown"] <= 0 and powerups["shield_timer"] <= 0:
                        powerups["shield_timer"] = SHIELD_DURATION_FRAMES
                        audio.play_sfx("start")
                    elif gesture == "PEACE" and powerups["slowmo_cooldown"] <= 0 and powerups["slowmo_timer"] <= 0:
                        powerups["slowmo_timer"] = SLOWMO_DURATION_FRAMES
                        audio.play_sfx("combo")

                if powerups["shield_timer"] > 0:
                    powerups["shield_timer"] -= 1
                    if powerups["shield_timer"] <= 0:
                        powerups["shield_cooldown"] = SHIELD_COOLDOWN_FRAMES
                elif powerups["shield_cooldown"] > 0:
                    powerups["shield_cooldown"] -= 1

                if powerups["slowmo_timer"] > 0:
                    powerups["slowmo_timer"] -= 1
                    if powerups["slowmo_timer"] <= 0:
                        powerups["slowmo_cooldown"] = SLOWMO_COOLDOWN_FRAMES
                elif powerups["slowmo_cooldown"] > 0:
                    powerups["slowmo_cooldown"] -= 1

                time_scale = SLOWMO_FACTOR if powerups["slowmo_timer"] > 0 else 1.0

                # Draw Background
                if hasattr(input_provider, 'get_frame'):
                    screen.blit(bg_img, (0,0))
                    frame = input_provider.get_frame()
                    if frame is not None:
                        h, w = frame.shape[:2]
                        surf = pygame.image.frombuffer(frame.tobytes(), (w, h), "RGBA")
                        surf = pygame.transform.smoothscale(surf, (WIDTH, HEIGHT))
                        screen.blit(surf, (0,0))
                else:
                    screen.blit(bg_img, (shake_x, shake_y))
                
                # Update Logic (only if not palm-paused)
                if not input_paused:
                    if ix is not None:
                        blade.update(ix, iy)
                    
                    # Spawner
                    if random.randint(1, 40) == 1:
                        spawn_x = random.randint(100, WIDTH-100)
                        spawn_y = HEIGHT + 20
                        
                        if random.randint(1, 5) == 1:
                            b = Bomb(spawn_x, spawn_y, WIDTH, HEIGHT)
                            all_sprites.add(b)
                            fruits.add(b)
                        else:
                            f = Fruit(spawn_x, spawn_y, WIDTH, HEIGHT)
                            all_sprites.add(f)
                            fruits.add(f)
                    
                    all_sprites.update(time_scale)

                    # Collisions
                    segments = blade.get_segments()
                    if velocity > MIN_CUT_VELOCITY and segments:
                        hit_count = 0
                        for entity in list(fruits):
                            if entity.check_slice(segments):
                                hit_count += 1

                                if isinstance(entity, Bomb):
                                    boom = Explosion(entity.pos_x, entity.pos_y)
                                    all_sprites.add(boom)
                                    entity.kill()
                                    if powerups["shield_timer"] > 0:
                                        # Shield absorbs the bomb: no life lost, consumed on the spot.
                                        audio.play_sfx("combo")
                                        powerups["shield_timer"] = 0
                                        powerups["shield_cooldown"] = SHIELD_COOLDOWN_FRAMES
                                        shake_timer = 10
                                    else:
                                        audio.play_sfx("bomb")
                                        game_mode.on_bomb()
                                        shake_timer = 20
                                else:
                                    audio.play_sfx("splat")
                                    pts = game_mode.on_slice(entity)
                                    
                                    splash = SplashEffect(entity.pos_x, entity.pos_y, entity.fruit_type, velocity)
                                    all_sprites.add(splash)
                                    
                                    h1 = SlicedFruit(entity.pos_x, entity.pos_y, entity.fruit_type, 1)
                                    h2 = SlicedFruit(entity.pos_x, entity.pos_y, entity.fruit_type, 2)
                                    all_sprites.add(h1)
                                    all_sprites.add(h2)
                                    entity.kill()
                        
                        if hit_count > 1:
                            audio.play_sfx("combo")

                    # Check dropped fruits
                    for entity in list(fruits):
                        if entity.rect.top > HEIGHT:
                            if not isinstance(entity, Bomb):
                                game_mode.on_miss()
                                entity.kill()
                            else:
                                entity.kill()

                    # Check Game Over
                    if game_mode.game_over:
                        ui.current_scene = "OVER"
                        audio.play_sfx("over")
                        audio.stop_music()
                
                # Draw Game
                all_sprites.draw(screen)
                blade.draw(screen)

                # Slow-Mo tint
                if powerups["slowmo_timer"] > 0:
                    tint = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    tint.fill((30, 80, 255, 40))
                    screen.blit(tint, (0, 0))

                # Shield border
                if powerups["shield_timer"] > 0:
                    pygame.draw.rect(screen, (0, 220, 255), screen.get_rect(), 6)

                # Palm pause indicator
                if input_paused:
                    txt = ui.font_big.render("PAUSA (PALMA ABIERTA)", True, (255, 255, 0))
                    screen.blit(txt, (WIDTH//2 - txt.get_width()//2, HEIGHT//2))

                # HUD
                hud = ui.font_small.render(game_mode.get_status(), True, WHITE)
                screen.blit(hud, (20, 20))

                # Power-up HUD
                if isinstance(input_provider, HandInput):
                    shield_label, slowmo_label = "Escudo (Puño)", "Cámara Lenta (Paz)"
                else:
                    shield_label, slowmo_label = "Escudo (Clic Derecho)", "Cámara Lenta (Clic Central)"

                shield_hud = ui.font_small.render(
                    powerup_status_text(shield_label, powerups["shield_timer"], powerups["shield_cooldown"]),
                    True, (0, 220, 255)
                )
                screen.blit(shield_hud, (20, 50))

                slowmo_hud = ui.font_small.render(
                    powerup_status_text(slowmo_label, powerups["slowmo_timer"], powerups["slowmo_cooldown"]),
                    True, (150, 170, 255)
                )
                screen.blit(slowmo_hud, (20, 75))

                # Pause hint
                hint = ui.font_small.render("ESC para Pausar", True, (150, 150, 150))
                screen.blit(hint, (WIDTH - hint.get_width() - 20, 20))

        elif ui.current_scene == "OVER":
            # Keep drawing game in background
            all_sprites.draw(screen)
            action = ui.handle_input("OVER", mx, my, click)
            ui.draw_game_over(screen, game_mode.score)
            
            if action == "GOTO_MENU":
                if input_provider:
                    input_provider.cleanup()
                    input_provider = None
                ui.current_scene = "MENU"
                ui.scene_stack.clear()
                audio.play_music("menu")
            elif action == "RESTART":
                ui.current_scene = "GAME"
                audio.play_music("game_slow")
                
                if isinstance(game_mode, ClassicMode):
                    game_mode = ClassicMode()
                else:
                    game_mode = SurvivalMode()
                    
                all_sprites.empty()
                fruits.empty()
                blade = Blade()
                powerups = fresh_powerup_state()

        pygame.display.flip()
        clock.tick(FPS)
        
    
    # Cleanup logic
    if input_provider:
        input_provider.cleanup()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
