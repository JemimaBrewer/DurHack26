import cv2
import mediapipe as mp
import numpy as np
import time

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


MODEL_PATH = "hand_landmarker.task"

# Create hand detector
options = vision.HandLandmarkerOptions(
    base_options=python.BaseOptions(model_asset_path=MODEL_PATH),
    running_mode=vision.RunningMode.VIDEO,
    num_hands=1,
)

cap = cv2.VideoCapture(0)

trail = []
MAX_TRAIL_LENGTH = 150

with vision.HandLandmarker.create_from_options(options) as landmarker:

    previous_time = time.time()

    while True:
        success, frame = cap.read()

        if not success:
            break

        frame = cv2.flip(frame, 1)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )

        timestamp_ms = int(time.time() * 1000)

        result = landmarker.detect_for_video(
            mp_image,
            timestamp_ms
        )

        h, w, _ = frame.shape

        # Transparent overlay for drawing
        overlay = frame.copy()

        if result.hand_landmarks:

            hand = result.hand_landmarks[0]

            # Landmark 8 = index fingertip
            tip = hand[8]

            x = int(tip.x * w)
            y = int(tip.y * h)

            trail.append((x, y))

            if len(trail) > MAX_TRAIL_LENGTH:
                trail.pop(0)

            # Draw fingertip
            cv2.circle(
                overlay,
                (x, y),
                10,
                (0, 255, 255),
                -1
            )

        # Draw conducting trail
        for i in range(1, len(trail)):
            alpha = i / len(trail)

            colour = (
                int(255 * (1 - alpha)),
                int(255 * alpha),
                255
            )

            thickness = max(1, int(6 * alpha))

            cv2.line(
                overlay,
                trail[i - 1],
                trail[i],
                colour,
                thickness
            )

        # Blend overlay onto image
        frame = cv2.addWeighted(
            overlay,
            0.85,
            frame,
            0.15,
            0
        )

        # FPS display
        current_time = time.time()
        fps = 1 / max(current_time - previous_time, 0.001)
        previous_time = current_time

        cv2.putText(
            frame,
            f"FPS: {int(fps)}",
            (10, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            "Conduct using your index finger",
            (10, 75),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        cv2.imshow("Orchestra Practice", frame)

        key = cv2.waitKey(1)

        if key == 27:  # ESC
            break

        if key == ord("c"):
            trail.clear()

cap.release()
cv2.destroyAllWindows()