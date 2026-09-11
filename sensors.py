import cv2
import os
import time
import math
import urllib.request
from threading import Thread

import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

# The classic `mediapipe.solutions.hands` API is not shipped in the Python 3.13+
# wheels, so we use the newer MediaPipe Tasks API (HandLandmarker) instead.
# It needs a model file that we download once and cache locally.
MODEL_DIR = os.path.join(os.path.dirname(__file__), "assets", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "hand_landmarker.task")
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)


def _ensure_model():
    if os.path.exists(MODEL_PATH):
        return
    os.makedirs(MODEL_DIR, exist_ok=True)
    print("Downloading hand tracking model (~7 MB)...")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print("Model downloaded.")


class WebcamStream:
    """
    Threaded webcam capture to ensure the main loop never blocks on I/O.
    Always holds the most recent frame.
    """
    def __init__(self, src=0, width=640, height=480):
        # cv2.CAP_DSHOW is required on Windows to avoid MSMF errors and reduce initialization latency
        self.stream = cv2.VideoCapture(src, cv2.CAP_DSHOW)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # Read first frame to ensure it's working
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
            num_hands=1,                       # Only track one hand for performance
            min_hand_detection_confidence=detection_con,
            min_hand_presence_confidence=detection_con,
            min_tracking_confidence=track_con,
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)

        # Monotonic millisecond timestamp for detect_for_video (must be increasing)
        self._start = time.time()

        # Tracking State
        self.prev_x, self.prev_y = 0, 0
        self.prev_time = time.time()

        # Adaptive Smoothing params
        self.alpha = 0.5

    def is_palm_open(self, lm_list):
        """
        Heuristic to check if hand is open.
        Checks if tips of fingers (8, 12, 16, 20) are further from the wrist (0)
        than the corresponding PIP joints.
        """
        if not lm_list:
            return False

        wrist = lm_list[0]
        tips = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]

        open_fingers = 0
        for i in range(4):
            tip = lm_list[tips[i]]
            pip = lm_list[pips[i]]

            dist_tip = math.hypot(tip[1] - wrist[1], tip[2] - wrist[2])
            dist_pip = math.hypot(pip[1] - wrist[1], pip[2] - wrist[2])

            if dist_tip > dist_pip:
                open_fingers += 1

        return open_fingers == 4  # Thumb is tricky, ignoring for "Palm"

    def find_position(self, frame):
        """
        Processes frame and returns:
        cx, cy, velocity, is_palm_open
        """
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)

        timestamp_ms = int((time.time() - self._start) * 1000)
        results = self.landmarker.detect_for_video(mp_image, timestamp_ms)

        timestamp = time.time()
        dt = timestamp - self.prev_time
        if dt == 0:
            dt = 0.001

        is_open = False
        cx, cy, velocity = None, None, 0.0

        if results.hand_landmarks:
            hand_lms = results.hand_landmarks[0]
            h, w = frame.shape[:2]

            # Convert to list of [id, x_px, y_px]
            pixel_lms = [[i, int(lm.x * w), int(lm.y * h)] for i, lm in enumerate(hand_lms)]

            # Index Finger Tip is ID 8
            raw_x, raw_y = pixel_lms[8][1], pixel_lms[8][2]

            # Check Gesture
            is_open = self.is_palm_open(pixel_lms)

            # --- Adaptive Smoothing ---
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
        return cx, cy, velocity, is_open
