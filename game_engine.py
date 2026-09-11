class GameMode:
    def __init__(self):
        self.score = 0
        self.lives = 0
        self.game_over = False
        self.name = "Base"
        
    def on_slice(self, fruit_obj):
        self.score += 1
        return 1 # Puntos
        
    def on_bomb(self):
        pass
        
    def on_miss(self):
        pass
        
    def get_status(self):
        return f"Puntos: {self.score}  Vidas: {self.lives}"

class ClassicMode(GameMode):
    def __init__(self):
        super().__init__()
        self.lives = 3
        self.name = "Classic"
        
    def on_slice(self, fruit_obj):
        # ¿Bono por críticos? Simple +1 por ahora
        self.score += 1
        return 1

    def on_bomb(self):
        # Clásico: Bomba = -1 Vida (o Fin del Juego en arcade, pero se pidió -1 vida)
        # Releyendo el prompt: "Modo Clásico: ... Las bombas reducen vidas"
        self.lives -= 1
        if self.lives <= 0:
            self.game_over = True

    def on_miss(self):
        # Fruta perdida = -1 vida
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
        # Muerte instantánea
        self.lives = 0
        self.game_over = True

    def on_miss(self):
        # Muerte instantánea
        self.lives = 0
        self.game_over = True
