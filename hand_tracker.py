import cv2
import mediapipe as mp

from mediapipe.tasks.python import vision
from mediapipe.tasks import python


class HandTracker:
    def __init__(self, model_path="hand_landmarker.task"):
        base_options = python.BaseOptions(
            model_asset_path=model_path
        )

        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=1
        )

        self.detector = vision.HandLandmarker.create_from_options(
            options
        )

        self.trail = []
        self.max_trail_length = 100

    def process_frame(self, frame):
        rgb_frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )

        result = self.detector.detect(mp_image)

        if result.hand_landmarks:

            hand = result.hand_landmarks[0]

            fingertip = hand[8]

            height, width, _ = frame.shape

            x = int(fingertip.x * width)
            y = int(fingertip.y * height)

            self.trail.append((x, y))

            if len(self.trail) > self.max_trail_length:
                self.trail.pop(0)

            cv2.circle(
                frame,
                (x, y),
                10,
                (0, 255, 0),
                -1
            )

            for i in range(1, len(self.trail)):
                cv2.line(
                    frame,
                    self.trail[i - 1],
                    self.trail[i],
                    (255, 0, 255),
                    3
                )

        return frame