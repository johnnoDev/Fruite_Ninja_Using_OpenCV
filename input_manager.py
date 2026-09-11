import pygame
import cv2
import math
import time
import threading
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
        # Capturamos a una resolución menor que la ventana: el frame se reescala
        # igual al dibujarlo (smoothscale a WIDTH,HEIGHT), pero una imagen más
        # pequeña hace MUCHO más rápidas tanto la inferencia de MediaPipe como
        # el recorte de fondo (threshold/connectedComponents/morphology/blur),
        # que son las partes más caras de cada frame.
        cam_w, cam_h = 480, 360
        self.webcam = WebcamStream(src=0, width=cam_w, height=cam_h).start()
        self.tracker = HandTracker(detection_con=0.6, track_con=0.6)
        self.bg_remover = BackgroundRemover()

        # La cámara puede no honrar exactamente cam_w/cam_h (usa la resolución
        # soportada más cercana), así que medimos el frame real para el mapeo
        # de coordenadas en vez de asumir el valor pedido.
        first_frame = self.webcam.frame
        if first_frame is not None:
            self.cam_h, self.cam_w = first_frame.shape[:2]
        else:
            self.cam_w, self.cam_h = cam_w, cam_h

        # El seguimiento de mano y la segmentación de fondo son inferencias de
        # IA relativamente lentas (mucho más que un frame a 60 FPS), y la
        # segmentación de fondo es bastante más pesada que el seguimiento de
        # mano. Si ambas corrieran en el mismo hilo/bucle, cada recorte de
        # fondo retrasaría la siguiente lectura del dedo y la detección se
        # sentiría "trabada". Por eso van en DOS hilos independientes, cada
        # uno publicando su propio resultado a su propio ritmo: el dedo se
        # actualiza rápido sin esperar nunca al recorte de fondo (lento).
        self._input_lock = threading.Lock()
        self._latest_input = (None, None, 0, "NONE")
        self._cutout_lock = threading.Lock()
        self._latest_cutout = None

        self._running = True
        self._hand_worker = threading.Thread(target=self._hand_loop, daemon=True)
        self._bg_worker = threading.Thread(target=self._bg_loop, daemon=True)
        self._hand_worker.start()
        self._bg_worker.start()

    def _hand_loop(self):
        while self._running:
            frame = self.webcam.frame
            if frame is None:
                continue
            frame = cv2.flip(frame, 1)  # Efecto espejo

            tx, ty, velocity, gesture = self.tracker.find_position(frame)
            if tx is None:
                result = (None, None, 0, gesture)
            else:
                sx = int((tx / self.cam_w) * self.width)
                sy = int((ty / self.cam_h) * self.height)
                result = (sx, sy, velocity, gesture)

            with self._input_lock:
                self._latest_input = result

    def _bg_loop(self):
        while self._running:
            frame = self.webcam.frame
            if frame is None:
                continue
            frame = cv2.flip(frame, 1)  # Efecto espejo
            cutout = self.bg_remover.cutout(frame)

            with self._cutout_lock:
                self._latest_cutout = cutout

    def get_input(self):
        with self._input_lock:
            return self._latest_input

    def get_frame(self):
        """Devuelve un recorte RGBA solo del jugador, con el fondo eliminado."""
        with self._cutout_lock:
            return self._latest_cutout

    def cleanup(self):
        self._running = False
        self._hand_worker.join(timeout=1.0)
        self._bg_worker.join(timeout=1.0)
        self.webcam.stop()
        self.bg_remover.close()
