import pygame
import cv2
import math
import time
from sensors import HandTracker, WebcamStream # Re-using existing robust sensors logic

class InputProvider:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
    def get_input(self):
        """
        Returns (x, y, velocity, is_paused)
        x, y: Screen coordinates (or None)
        velocity: Pixels per second
        is_paused: Boolean (e.g. open palm)
        """
        return None, None, 0, False
        
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
        buttons = pygame.mouse.get_pressed()
        
        # Only track "blade" if left click is held
        if not buttons[0]:
            self.prev_pos = None
            return None, None, 0, False
            
        velocity = 0
        if self.prev_pos:
            dist = math.hypot(mx - self.prev_pos[0], my - self.prev_pos[1])
            velocity = dist / dt
            
        self.prev_pos = (mx, my)
        self.prev_time = cur_time
        return mx, my, velocity, False # Mouse can't really "pause" with gesture

class HandInput(InputProvider):
    def __init__(self, width, height):
        super().__init__(width, height)
        # Initialize Webcam and Tracker
        # We reuse the logic from sensors.py which is already threaded and optimized
        self.webcam = WebcamStream(src=0, width=width, height=height).start()
        self.tracker = HandTracker(detection_con=0.6, track_con=0.6)
        
        # We need to map camera coords to screen
        self.cam_w = width
        self.cam_h = height
        
    def get_input(self):
        frame = self.webcam.read()
        if frame is None:
            return None, None, 0, False
            
        # Flip for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Tracker returns raw frame coords (assuming sensors.py returns pixels)
        # sensors.py find_position signature: (frame) -> cx, cy, velocity, is_palm_open
        tx, ty, velocity, is_palm_open = self.tracker.find_position(frame)
        
        # If sensors.py returns None, tx is None
        if tx is None:
            return None, None, 0, False
            
        # Map logic:
        # sensors.py already returns pixel coordinates relative to the frame passed in.
        # Since we flipped the frame, and passed it to find_position, the x,y are correct for the flipped frame.
        # We just need to scale if window size differs from camera size
        # Assuming 1:1 for now if we init webcam with window size
        
        sx = int((tx / self.cam_w) * self.width)
        sy = int((ty / self.cam_h) * self.height)
        
        return sx, sy, velocity, is_palm_open
        
    def get_frame(self):
        """Optional: Return frame for drawing background"""
        frame = self.webcam.frame # Access last frame directly or via read()
        if frame is not None:
             frame = cv2.flip(frame, 1)
        return frame

    def cleanup(self):
        self.webcam.stop()
