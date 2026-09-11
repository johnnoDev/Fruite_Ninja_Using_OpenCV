# Fruit Ninja - AI Hand Controlled

A high-performance computer vision game where you play Fruit Ninja using your real hand as the blade! Built with Python, OpenCV, MediaPipe, and Pygame.

## Features

*   **Real-Time Hand Tracking**: Uses MediaPipe to track your index finger with low latency.
*   **Physics-Based Gaming**: Fruits launch and fall with gravity; blade collision uses robust line-segment detection for fast swipes.
*   **Visual Adjustments**: 
    *   **Blade Trail**: Dynamic cyan trail that follows your finger.
    *   **Slicing Effects**: Fruits split into two halves when sliced.
    *   **Assets**: Uses real fruit graphics (Apple, Banana, Watermelon, etc.).
*   **Gameplay Mechanics**:
    *   **Bombs**: Avoid slicing the dark bombs with red fuses! (-5 points).
    *   **Palm Pause**: Show an **Open Palm** to the camera to Pause/Shield the blade (safety mechanism).
    *   **Gesture Power-ups**: Hold a pose for about a quarter second to activate it (then it goes on cooldown):
        *   **Fist -> Shield**: Absorbs the next bomb you hit, no life lost.
        *   **Peace Sign (index + middle finger) -> Slow-Mo**: Fruits and bombs fall in slow motion for a few seconds.
    *   **Score System**: Track your slicing performance.

## Prerequisites

*   Python 3.9 - 3.14
*   Webcam

## Installation

1.  Clone the repository (or download files).
2.  Create a virtual environment and install dependencies:
    ```bash
    python -m venv venv
    venv\Scripts\activate        # Windows  (use: source venv/bin/activate on Linux/Mac)
    pip install -r requirements.txt
    ```

> On the first run the game downloads the MediaPipe hand-tracking model
> (~7 MB) into `assets/models/`. This needs an internet connection once.

### Note on Python 3.13 / 3.14

The classic `mediapipe.solutions` API has no wheels for Python 3.13+, so hand
tracking uses the newer **MediaPipe Tasks API** (`HandLandmarker`). The game also
uses `pygame-ce` (a drop-in fork of `pygame` that ships 3.14 wheels).

## How to Play

1.  Run the game:
    ```bash
    python main.py
    ```
2.  **Controls**:
    *   **Slice**: Move your index finger across the screen to slice fruits. You must move fast enough to create a "cut".
    *   **Pause**: Open your hand (extend all 5 fingers) to pause the blade. This is useful if a bomb is in the way and you want to move your hand safely.
    *   **Shield**: Make a fist to arm a shield that absorbs your next bomb hit.
    *   **Slow-Mo**: Hold up a peace sign (index + middle finger) to slow down falling fruits/bombs for a few seconds.
    *   **Quit**: Close the window or press `Alt+F4`.
    *   **Playing with Mouse**: the power-ups above need a hand gesture, so mouse mode maps them to extra buttons instead — hold **Right-Click** for Shield, hold **Middle-Click** for Slow-Mo.

## Troubleshooting

*   **Lag?** ensure you have good lighting for the camera.
*   **Camera Error?** The code uses `cv2.CAP_DSHOW` for Windows compatibility. If on Linux/Mac, you might need to remove that flag in `sensors.py`.

## Credits

Built with:
*   [MediaPipe](https://developers.google.com/mediapipe)
*   [Pygame](https://www.pygame.org/)
*   [OpenCV](https://opencv.org/)

