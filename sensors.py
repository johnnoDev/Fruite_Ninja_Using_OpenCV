import cv2
import os
import time
import math
import urllib.request
import numpy as np
from threading import Thread

import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

# La API clásica `mediapipe.solutions.hands` no viene incluida en los
# wheels de Python 3.13+, así que usamos la API más nueva de MediaPipe Tasks (HandLandmarker).
# Necesita un archivo de modelo que descargamos una vez y guardamos en caché localmente.
MODEL_DIR = os.path.join(os.path.dirname(__file__), "assets", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "hand_landmarker.task")
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)

# Misma API de Tasks, pero para el modelo de segmentación selfie usado para recortar
# al jugador de su fondo real.
SEGMENTER_MODEL_PATH = os.path.join(MODEL_DIR, "selfie_segmenter.tflite")
SEGMENTER_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/image_segmenter/"
    "selfie_segmenter/float16/latest/selfie_segmenter.tflite"
)


def _ensure_model():
    if os.path.exists(MODEL_PATH):
        return
    os.makedirs(MODEL_DIR, exist_ok=True)
    print("Descargando modelo de seguimiento de manos (~7 MB)...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print("Modelo descargado.")


def _ensure_segmenter_model():
    if os.path.exists(SEGMENTER_MODEL_PATH):
        return
    os.makedirs(MODEL_DIR, exist_ok=True)
    print("Descargando modelo de eliminación de fondo (~250 KB)...")
    urllib.request.urlretrieve(SEGMENTER_MODEL_URL, SEGMENTER_MODEL_PATH)
    print("Modelo descargado.")


class BackgroundRemover:
    """
    Usa el modelo de segmentación selfie de MediaPipe para aislar al jugador
    de lo que sea que esté detrás, de modo que solo la persona se muestre sobre el arte del juego.
    """
    def __init__(self):
        _ensure_segmenter_model()

        options = vision.ImageSegmenterOptions(
            base_options=mp_python.BaseOptions(model_asset_path=SEGMENTER_MODEL_PATH),
            running_mode=vision.RunningMode.VIDEO,
            output_confidence_masks=True,
        )
        self.segmenter = vision.ImageSegmenter.create_from_options(options)
        self._start = time.time()

    def cutout(self, frame):
        """
        Devuelve un arreglo RGBA (H, W, 4) uint8: el jugador con opacidad total,
        todo lo demás completamente transparente, listo para convertirse en una superficie de pygame.
        """
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)

        timestamp_ms = int((time.time() - self._start) * 1000)
        result = self.segmenter.segment_for_video(mp_image, timestamp_ms)

        mask = result.confidence_masks[0].numpy_view()  # (H, W), confianza de persona 0..1

        # Umbral duro en lugar de un degradado suave: un desvanecido ancho deja
        # que píxeles de borde con color de fondo se muestren con alfa parcial,
        # produciendo un halo pálido alrededor de la persona. Binarizar estrictamente, descartar
        # cualquier mancha suelta que no sea la silueta principal, cerrar pequeños huecos,
        # y luego erosionar hacia adentro para eliminar el borde contaminado antes de un
        # desenfoque mínimo solo para el anti-aliasing.
        mask_u8 = (mask * 255).astype(np.uint8)
        _, binary = cv2.threshold(mask_u8, 160, 255, cv2.THRESH_BINARY)

        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
        if num_labels > 1:
            largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
            binary = np.where(labels == largest, 255, 0).astype(np.uint8)

        kernel = np.ones((9, 9), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.erode(binary, kernel, iterations=2)

        alpha = cv2.GaussianBlur(binary, (3, 3), 0)

        rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        rgba[:, :, 3] = alpha
        return rgba

    def close(self):
        self.segmenter.close()


class WebcamStream:
    """
    Captura de webcam en un hilo aparte para asegurar que el bucle principal nunca se bloquee por E/S.
    Siempre mantiene el frame más reciente.
    """
    def __init__(self, src=0, width=640, height=480):
        # cv2.CAP_DSHOW es necesario en Windows para evitar errores de MSMF y reducir la latencia de inicialización
        self.stream = cv2.VideoCapture(src, cv2.CAP_DSHOW)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # Leer el primer frame para asegurar que funciona
        (self.grabbed, self.frame) = self.stream.read()
        self.stopped = False

    def start(self):
        Thread(target=self.update, args=()).start()
        return self

    def update(self):
        while True:
            if self.stopped:
                return
            (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.stream.release()


class HandTracker:
    def __init__(self, detection_con=0.6, track_con=0.6):
        _ensure_model()

        options = vision.HandLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=1,                       # Solo rastrear una mano por rendimiento
            min_hand_detection_confidence=detection_con,
            min_hand_presence_confidence=detection_con,
            min_tracking_confidence=track_con,
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)

        # Marca de tiempo monótona en milisegundos para detect_for_video (debe ser creciente)
        self._start = time.time()

        # Estado de seguimiento
        self.prev_x, self.prev_y = 0, 0
        self.prev_time = time.time()

        # Parámetros de suavizado adaptativo
        self.alpha = 0.5

    def classify_gesture(self, lm_list):
        """
        Clasifica la pose de la mano en uno de los gestos a los que el juego reacciona,
        según cuáles de los 4 dedos (sin contar el pulgar: índice, medio, anular, meñique)
        están extendidos (punta más lejos de la muñeca que su articulación PIP):

        - OPEN_PALM: los 4 extendidos      -> Pausa de palma (función existente)
        - FIST:      ninguno extendido     -> Power-up de Escudo
        - PEACE:     solo índice + medio   -> Power-up de Cámara Lenta
        - NONE:      cualquier otro caso
        """
        if not lm_list:
            return "NONE"

        wrist = lm_list[0]
        tips = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]

        extended = []
        for tip_id, pip_id in zip(tips, pips):
            tip = lm_list[tip_id]
            pip = lm_list[pip_id]

            dist_tip = math.hypot(tip[1] - wrist[1], tip[2] - wrist[2])
            dist_pip = math.hypot(pip[1] - wrist[1], pip[2] - wrist[2])

            extended.append(dist_tip > dist_pip)

        index, middle, ring, pinky = extended

        if index and middle and ring and pinky:
            return "OPEN_PALM"
        if not any(extended):
            return "FIST"
        if index and middle and not ring and not pinky:
            return "PEACE"
        return "NONE"

    def find_position(self, frame):
        """
        Procesa el frame y devuelve:
        cx, cy, velocidad, gesto (uno de "OPEN_PALM", "FIST", "PEACE", "NONE")
        """
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)

        timestamp_ms = int((time.time() - self._start) * 1000)
        results = self.landmarker.detect_for_video(mp_image, timestamp_ms)

        timestamp = time.time()
        dt = timestamp - self.prev_time
        if dt == 0:
            dt = 0.001

        gesture = "NONE"
        cx, cy, velocity = None, None, 0.0

        if results.hand_landmarks:
            hand_lms = results.hand_landmarks[0]
            h, w = frame.shape[:2]

            # Convertir a lista de [id, x_px, y_px]
            pixel_lms = [[i, int(lm.x * w), int(lm.y * h)] for i, lm in enumerate(hand_lms)]

            # La punta del dedo índice es el ID 8
            raw_x, raw_y = pixel_lms[8][1], pixel_lms[8][2]

            # Verificar gesto
            gesture = self.classify_gesture(pixel_lms)

            # --- Suavizado adaptativo ---
            dist = math.hypot(raw_x - self.prev_x, raw_y - self.prev_y)
            if dist > 30:
                target_alpha = 0.8
            else:
                target_alpha = 0.2

            self.alpha = target_alpha

            if self.prev_x == 0 and self.prev_y == 0:
                smooth_x, smooth_y = raw_x, raw_y
            else:
                smooth_x = self.alpha * raw_x + (1 - self.alpha) * self.prev_x
                smooth_y = self.alpha * raw_y + (1 - self.alpha) * self.prev_y

            move_dist = math.hypot(smooth_x - self.prev_x, smooth_y - self.prev_y)
            velocity = move_dist / dt

            self.prev_x, self.prev_y = smooth_x, smooth_y

            cx, cy = int(smooth_x), int(smooth_y)

        self.prev_time = timestamp
        return cx, cy, velocity, gesture
