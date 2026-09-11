import pygame
import cv2
import math
import time
from sensors import HandTracker, WebcamStream, BackgroundRemover # Reutilizando la lógica robusta existente de sensors

class InputProvider:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
    def get_input(self):
        """
        Devuelve (x, y, velocidad, gesto)
        x, y: Coordenadas de pantalla (o None)
        velocidad: Píxeles por segundo
        gesto: Uno de "OPEN_PALM", "FIST", "PEACE", "NONE"
        """
        return None, None, 0, "NONE"
        
    def cleanup(self):
        pass

class MouseInput(InputProvider):
    def __init__(self, width, height):
        super().__init__(width, height)
        self.prev_pos = None
        self.prev_time = time.time()
        
    def get_input(self):
        cur_time = time.time()
        dt = cur_time - self.prev_time
        if dt == 0: dt = 0.001

        mx, my = pygame.mouse.get_pos()
        buttons = pygame.mouse.get_pressed(num_buttons=3)

        # No hay cámara para leer gestos, así que el modo ratón mapea los dos
        # power-ups a botones extra del ratón: Clic Derecho = Puño
        # (Escudo), Clic Central = Paz (Cámara Lenta).
        gesture = "NONE"
        if buttons[2]:
            gesture = "FIST"
        elif buttons[1]:
            gesture = "PEACE"

        # Solo rastrea la "hoja" si se mantiene presionado el clic izquierdo
        if not buttons[0]:
            self.prev_pos = None
            return None, None, 0, gesture

        velocity = 0
        if self.prev_pos:
            dist = math.hypot(mx - self.prev_pos[0], my - self.prev_pos[1])
            velocity = dist / dt

        self.prev_pos = (mx, my)
        self.prev_time = cur_time
        return mx, my, velocity, gesture

class HandInput(InputProvider):
    def __init__(self, width, height):
        super().__init__(width, height)
        # Inicializa la webcam y el rastreador
        # Reutilizamos la lógica de sensors.py que ya está en hilo aparte y optimizada
        self.webcam = WebcamStream(src=0, width=width, height=height).start()
        self.tracker = HandTracker(detection_con=0.6, track_con=0.6)
        self.bg_remover = BackgroundRemover()

        # Necesitamos mapear las coordenadas de la cámara a la pantalla
        self.cam_w = width
        self.cam_h = height
        
    def get_input(self):
        frame = self.webcam.read()
        if frame is None:
            return None, None, 0, "NONE"

        # Voltear para efecto espejo
        frame = cv2.flip(frame, 1)

        # El rastreador devuelve coordenadas crudas del frame (asumiendo que sensors.py devuelve píxeles)
        # Firma de find_position en sensors.py: (frame) -> cx, cy, velocidad, gesto
        tx, ty, velocity, gesture = self.tracker.find_position(frame)

        # Si sensors.py devuelve None, tx es None
        if tx is None:
            return None, None, 0, gesture

        # Lógica de mapeo:
        # sensors.py ya devuelve coordenadas de píxel relativas al frame que se le pasó.
        # Como volteamos el frame y lo pasamos a find_position, las x,y son correctas para el frame volteado.
        # Solo necesitamos escalar si el tamaño de la ventana difiere del tamaño de la cámara
        # Asumimos 1:1 por ahora si inicializamos la webcam con el tamaño de la ventana

        sx = int((tx / self.cam_w) * self.width)
        sy = int((ty / self.cam_h) * self.height)

        return sx, sy, velocity, gesture
        
    def get_frame(self):
        """Devuelve un recorte RGBA solo del jugador, con el fondo eliminado."""
        frame = self.webcam.frame # Accede al último frame directamente o vía read()
        if frame is None:
            return None
        frame = cv2.flip(frame, 1)
        return self.bg_remover.cutout(frame)

    def cleanup(self):
        self.webcam.stop()
        self.bg_remover.close()
