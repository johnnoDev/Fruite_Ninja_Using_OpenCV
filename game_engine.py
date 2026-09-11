class GameMode:
    def __init__(self):
        self.score = 0
        self.lives = 0
        self.game_over = False
        self.name = "Base"
        
    def on_slice(self, fruit_obj):
        self.score += 1
        return 1 # Points
        
    def on_bomb(self):
        pass
        
    def on_miss(self):
        pass
        
    def get_status(self):
        return f"Score: {self.score}  Lives: {self.lives}"

class ClassicMode(GameMode):
    def __init__(self):
        super().__init__()
        self.lives = 3
        self.name = "Classic"
        
    def on_slice(self, fruit_obj):
        # Bonus for criticals? Simple +1 for now
        self.score += 1
        return 1
        
    def on_bomb(self):
        # Classic: Bomb = -1 Life (or Game Over in arcade, but user said -1 life)
        # Re-reading prompt: "Classic Mode: ... Bombs reduce lives"
        self.lives -= 1
        if self.lives <= 0:
            self.game_over = True
            
    def on_miss(self):
        # Missed fruit = -1 life
        self.lives -= 1
        if self.lives <= 0:
            self.game_over = True

class SurvivalMode(GameMode):
    def __init__(self):
        super().__init__()
        self.lives = 1
        self.name = "Survival"
        
    def on_slice(self, fruit_obj):
        self.score += 1
        return 1
        
    def on_bomb(self):
        # Instant death
        self.lives = 0
        self.game_over = True
        
    def on_miss(self):
        # Instant death
        self.lives = 0
        self.game_over = True
