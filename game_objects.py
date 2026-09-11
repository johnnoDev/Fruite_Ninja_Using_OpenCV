import pygame
import random
import time
from collections import deque
import physics

# Colores básicos
RED = (255, 50, 50)
GREEN = (50, 255, 50)
WHITE = (255, 255, 255)
ORANGE = (255, 165, 0)

class Blade:
    def __init__(self):
        # Almacena (x, y, marca de tiempo)
        self.points = deque(maxlen=20)
        self.color = (0, 255, 255) # Cian para alto contraste
        self.min_width = 5
        self.max_width = 25
        self.fade_speed = 5 # Qué tan rápido se desvanece la estela

    def update(self, x, y):
        current_time = time.time()
        self.points.append((x, y, current_time))

        # Elimina puntos antiguos (mayores a 0.2s) para mantener la estela corta y ágil
        while self.points:
            if current_time - self.points[0][2] > 0.15:
                self.points.popleft()
            else:
                break
                
    def draw(self, screen):
        if len(self.points) < 2:
            return
            
        # Dibuja líneas conectadas con grosor variable
        # Los puntos más recientes = más gruesos
        points_list = list(self.points)
        for i in range(len(points_list) - 1):
            p1 = points_list[i]
            p2 = points_list[i+1]

            # Proporción: 0 (más antiguo) a 1 (más reciente)
            ratio = i / len(points_list)
            width = int(self.min_width + (self.max_width - self.min_width) * ratio)

            # Dibuja el segmento de línea
            # Nota: las líneas de Pygame con grosor > 1 tienen huecos en las esquinas.
            # Idealmente se dibujarían círculos en las uniones, pero las líneas son rápidas.
            start_pos = (p1[0], p1[1])
            end_pos = (p2[0], p2[1])
            pygame.draw.line(screen, self.color, start_pos, end_pos, width)
            pygame.draw.circle(screen, self.color, end_pos, width // 2)

    def get_segments(self):
        """Devuelve la lista de segmentos de línea ((x1,y1), (x2,y2)) actualmente activos."""
        segments = []
        pts = list(self.points)
        for i in range(len(pts) - 1):
            segments.append(((pts[i][0], pts[i][1]), (pts[i+1][0], pts[i+1][1])))
        return segments

import os

class Fruit(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, fruit_type=None):
        super().__init__()
        
        # Tipos disponibles en los assets
        types = ["apple", "banana", "coconut", "orange", "pineapple", "watermelon"]
        if fruit_type is None:
            self.fruit_type = random.choice(types)
        else:
            self.fruit_type = fruit_type

        # Cargar imagen
        # Intenta cargar la versión pequeña por rendimiento si existe, si no la normal
        try:
            path = f"assets/fruits/{self.fruit_type}_small.png"
            if not os.path.exists(path):
                path = f"assets/fruits/{self.fruit_type}.png"

            raw_image = pygame.image.load(path).convert_alpha()
            # Si las estándar son enormes (pngs de 300KB+ pueden ser grandes), podríamos necesitar escalarlas.
            # Según el tamaño de archivo, las _small son ~10KB, probablemente íconos. Las grandes son ~300KB.

            if "small" not in path:
                # Reduce las imágenes grandes a un tamaño de juego decente
                self.image = pygame.transform.scale(raw_image, (70, 70))
            else:
                self.image = raw_image

        except Exception as e:
            # Alternativa de respaldo
            # print(f"Error loading {self.fruit_type}: {e}")
            self.radius = 35
            self.color = random.choice([RED, ORANGE, GREEN])
            self.image = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
            pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius)

        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.radius = self.rect.width // 2 # Radio aproximado para colisión
        self.screen_h = height

        # Física
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.vel_x = random.uniform(-1.5, 1.5) # Horizontal aún más lento
        self.vel_y = random.uniform(-10, -7.5) # Ajustado para gravedad baja
        self.gravity = 0.08                    # Sensación 40% más lenta (flotante)
        
    def update(self, time_scale=1.0):
        self.vel_y += self.gravity * time_scale
        self.pos_x += self.vel_x * time_scale
        self.pos_y += self.vel_y * time_scale

        self.rect.centerx = int(self.pos_x)
        self.rect.centery = int(self.pos_y)

        if self.rect.top > self.screen_h:
            self.kill()
            
    def check_slice(self, segments):
        """
        Verifica la colisión contra una lista de segmentos de la hoja.
        Usa colisión de círculo barrido (cápsula).
        """
        center = (self.pos_x, self.pos_y)
        for p1, p2 in segments:
            # Tratamos la hoja como si tuviera un grosor
            # Digamos que el radio efectivo de la hoja es 5px
            if physics.check_capsule_circle_collision(p1, p2, 15, center, self.radius): # Radio de hoja aumentado para mayor tolerancia
                return True
        return False

class SlicedFruit(pygame.sprite.Sprite):
    def __init__(self, x, y, fruit_type, half_id):
        super().__init__()
        # Intenta cargar la mitad específica
        try:
            # ej. assets/fruits/apple_half_1_small.png
            base = f"assets/fruits/{fruit_type}_half_{half_id}"
            path_small = f"{base}_small.png"
            path_large = f"{base}.png"

            path = path_small if os.path.exists(path_small) else path_large

            if os.path.exists(path):
                 raw = pygame.image.load(path).convert_alpha()
                 if "small" not in path:
                     self.image = pygame.transform.scale(raw, (35, 70)) # tamaño genérico de mitad
                 else:
                     self.image = raw
            else:
                 raise FileNotFoundError(f"Half image not found: {path}")
        except Exception as e:
            print(f"SlicedFruit load error for {fruit_type} half {half_id}: {e}")
            # Alternativa de respaldo
            self.image = pygame.Surface((35, 35), pygame.SRCALPHA)
            pygame.draw.arc(self.image, GREEN, (0,0,35,35), 0, 3.14, 20)
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        # Física para salir despedidas
        self.pos_x = float(x)
        self.pos_y = float(y)
        self.gravity = 0.12 # Caída lenta

        # Separación según el ID
        if half_id == 1:
            self.vel_x = random.uniform(-4, -1)
            self.angle_speed = 2
        else:
            self.vel_x = random.uniform(1, 4)
            self.angle_speed = -2

        self.vel_y = random.uniform(-3, -1) # Pequeño salto hacia arriba

        # Lógica de rotación
        self.original_image = self.image
        self.angle = 0
        self.alpha = 255 # Para desvanecimiento si se desea (opcional)

    def update(self, time_scale=1.0):
        self.vel_y += self.gravity * time_scale
        self.pos_x += self.vel_x * time_scale
        self.pos_y += self.vel_y * time_scale

        # Rotar
        self.angle += self.angle_speed * time_scale
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect = self.image.get_rect(center=(self.pos_x, self.pos_y))

        if self.rect.top > 800: # Limpieza
            self.kill()

class Bomb(Fruit):
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "bomb")
        try:
            path = "assets/fruits/bomb_small.png"
            if not os.path.exists(path):
                 path = "assets/fruits/bomb.png"
            
            self.image = pygame.image.load(path).convert_alpha()
            if "small" not in path:
                 self.image = pygame.transform.scale(self.image, (80, 80))
            
            self.radius = self.image.get_width() // 2
        except Exception as e:
            print(f"Bomb load error: {e}")
            self.radius = 40
            self.image = pygame.Surface((80, 80), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (50, 50, 50), (40, 40), 40)
            pygame.draw.circle(self.image, RED, (40, 40), 10) # Mecha
        
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.radius = self.rect.width // 2

class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            # Usa el asset específico de explosión
            path = "assets/vfx/explosion_small.png"
            if not os.path.exists(path):
                 path = "assets/vfx/explosion.png"

            self.image = pygame.image.load(path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (150, 150)) # explosión grande
        except:
            self.image = pygame.Surface((100, 100))
            self.image.fill(RED)

        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.timer = 30 # frames (0.5 seg a 60fps)
        self.original_image = self.image

    def update(self, time_scale=1.0):
        # Efecto cosmético: siempre se reproduce a velocidad normal, incluso durante el Slow-Mo.
        self.timer -= 1
        # Desvanecimiento simple
        alpha = int((self.timer / 30) * 255)
        self.image.set_alpha(alpha)

        if self.timer <= 0:
            self.kill()

class SplashEffect(pygame.sprite.Sprite):
    # Mapeo de fruta a color de salpicadura
    FRUIT_SPLASH_MAP = {
        "apple": "red",
        "watermelon": "red",
        "banana": "yellow",
        "pineapple": "yellow",
        "orange": "orange",
        "coconut": "transparent"
    }
    
    def __init__(self, x, y, fruit_type, velocity=0):
        super().__init__()

        # Determinar el color de la salpicadura
        splash_color = self.FRUIT_SPLASH_MAP.get(fruit_type, "transparent")

        # Elegir la variante de tamaño según la velocidad
        # Velocidad alta (corte rápido) = salpicadura más grande
        if velocity > 400:
            size_variant = ""  # Usa salpicadura grande
            scale_size = (180, 180)
        else:
            size_variant = "_small"
            scale_size = (120, 120)

        # Cargar imagen de salpicadura
        try:
            path = f"assets/vfx/splash_{splash_color}{size_variant}.png"
            if not os.path.exists(path):
                # Alternativa pequeña si no existe la grande
                path = f"assets/vfx/splash_{splash_color}_small.png"
                scale_size = (120, 120)

            raw_image = pygame.image.load(path).convert_alpha()
            self.image = pygame.transform.scale(raw_image, scale_size)
            self.original_image = self.image.copy()

        except Exception as e:
            # Alternativa: círculo de color
            self.image = pygame.Surface((100, 100), pygame.SRCALPHA)
            color_map = {
                "red": (255, 50, 50),
                "yellow": (255, 255, 50),
                "orange": (255, 165, 0)
            }
            color = color_map.get(splash_color, (200, 200, 200))
            pygame.draw.circle(self.image, (*color, 150), (50, 50), 50)
            self.original_image = self.image.copy()
        
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

        # Propiedades de la animación
        self.lifetime = 20  # frames (~0.33 seg a 60fps)
        self.age = 0

        # Ligera rotación aleatoria para variedad
        angle = random.randint(-15, 15)
        self.image = pygame.transform.rotate(self.original_image, angle)
        self.rect = self.image.get_rect(center=(x, y))

    def update(self, time_scale=1.0):
        # Efecto cosmético: siempre se reproduce a velocidad normal, incluso durante el Slow-Mo.
        self.age += 1

        # Desvanecimiento
        alpha = int(255 * (1 - self.age / self.lifetime))
        if alpha < 0:
            alpha = 0

        # Crear versión desvanecida
        self.image = self.original_image.copy()
        self.image.set_alpha(alpha)
        
        if self.age >= self.lifetime:
            self.kill()
