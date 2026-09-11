import cv2
import mediapipe as mp
import time

import math

class HandTracker:
    def __init__(self, mode=False, max_hands=1, detection_con=0.5, track_con=0.5):
        self.mode = mode
        self.max_hands = max_hands
        self.detection_con = detection_con
        self.track_con = track_con

        # Estado de suavizado
        self.prev_x, self.prev_y = 0, 0
        self.alpha = 0.5  # Factor de suavizado (0 < alpha < 1). Menor = más suave pero más retraso.

        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.max_hands,
            model_complexity=0,  # Optimizado para velocidad
            min_detection_confidence=self.detection_con,
            min_tracking_confidence=self.track_con
        )
        self.mp_draw = mp.solutions.drawing_utils

    def find_hands(self, img, draw=True):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)

        if self.results.multi_hand_landmarks:
            for hand_lms in self.results.multi_hand_landmarks:
                if draw:
                    self.mp_draw.draw_landmarks(img, hand_lms, self.mp_hands.HAND_CONNECTIONS)
        return img

    def find_position(self, img, hand_no=0):
        lm_list = []
        if self.results.multi_hand_landmarks:
            if hand_no < len(self.results.multi_hand_landmarks):
                my_hand = self.results.multi_hand_landmarks[hand_no]
                for id, lm in enumerate(my_hand.landmark):
                    h, w, c = img.shape
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lm_list.append([id, cx, cy])
        return lm_list

    def get_tracked_data(self, img):
        """
        Devuelve (x, y, velocidad) para la punta del dedo índice.
        Aplica suavizado EMA.
        """
        # Procesar la imagen primero para obtener los landmarks
        self.find_hands(img, draw=False)

        lm_list = self.find_position(img)
        if len(lm_list) != 0:
            # La punta del dedo índice es el ID 8
            raw_x, raw_y = lm_list[8][1], lm_list[8][2]

            # Suavizado EMA
            # Si este es el primer frame (prev 0,0), saltar directo a él para evitar que llegue volando desde la esquina
            if self.prev_x == 0 and self.prev_y == 0:
                self.prev_x, self.prev_y = raw_x, raw_y

            curr_x = self.alpha * raw_x + (1 - self.alpha) * self.prev_x
            curr_y = self.alpha * raw_y + (1 - self.alpha) * self.prev_y

            # Cálculo de velocidad (distancia euclidiana por frame)
            velocity = math.hypot(curr_x - self.prev_x, curr_y - self.prev_y)
            
            self.prev_x, self.prev_y = curr_x, curr_y
            
            return int(curr_x), int(curr_y), velocity
        return None, None, 0
