import pygame
import os
import random

class AudioManager:
    def __init__(self, asset_dir="assets/audio"):
        self.asset_dir = asset_dir
        self.sounds = {
            "splat": [],
            "combo": [],
            "menu_music": None,
            "game_start": None,
            "game_over": None,
            "bomb": None,
            "game_loop_slow": None,
            "game_loop_fast": None
        }
        self.init_mixer()
        self.load_assets()
        
    def init_mixer(self):
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.set_num_channels(32) # Allow many sounds at once
        
    def load_assets(self):
        if not os.path.exists(self.asset_dir):
            print(f"Warning: Audio dir {self.asset_dir} not found.")
            return

        for filename in os.listdir(self.asset_dir):
            path = os.path.join(self.asset_dir, filename)
            lower_name = filename.lower()
            
            try:
                # Load based on keywords
                if "music menu" in lower_name:
                    self.sounds["menu_music"] = path
                elif "game start" in lower_name: # 37. U I Game Start
                    self.sounds["game_start"] = pygame.mixer.Sound(path)
                elif "game over" in lower_name: # 36. U I Game Over
                    self.sounds["game_over"] = pygame.mixer.Sound(path)
                elif "bomb" in lower_name:
                    self.sounds["bomb"] = pygame.mixer.Sound(path)
                elif "game sound slow" in lower_name:
                    self.sounds["game_loop_slow"] = path
                elif "game sound fast" in lower_name:
                    self.sounds["game_loop_fast"] = path
                elif "splat" in lower_name:
                    self.sounds["splat"].append(pygame.mixer.Sound(path))
                elif "combo" in lower_name:
                    self.sounds["combo"].append(pygame.mixer.Sound(path))
            except Exception as e:
                print(f"Failed to load audio {filename}: {e}")

    def play_music(self, bg_type="menu"):
        """Plays background music looping."""
        try:
            path = None
            if bg_type == "menu":
                path = self.sounds["menu_music"]
            elif bg_type == "game_slow":
                path = self.sounds["game_loop_slow"]
            elif bg_type == "game_fast":
                path = self.sounds["game_loop_fast"]
                
            if path:
                pygame.mixer.music.load(path)
                pygame.mixer.music.play(-1) # Loop
                pygame.mixer.music.set_volume(0.5)
        except Exception as e:
            print(f"Music Error: {e}")

    def stop_music(self):
        pygame.mixer.music.stop()

    def play_sfx(self, sound_type):
        """Plays a one-shot sound effect."""
        try:
            sound = None
            if sound_type == "splat" and self.sounds["splat"]:
                sound = random.choice(self.sounds["splat"])
                sound.set_volume(0.6)
            elif sound_type == "combo" and self.sounds["combo"]:
                sound = random.choice(self.sounds["combo"])
                sound.set_volume(1.0)
            elif sound_type == "bomb":
                sound = self.sounds["bomb"]
                sound.set_volume(1.0)
            elif sound_type == "start":
                sound = self.sounds["game_start"]
            elif sound_type == "over":
                sound = self.sounds["game_over"]
            
            if sound:
                sound.play()
        except Exception as e:
            # print(f"SFX Error: {e}") 
            pass
