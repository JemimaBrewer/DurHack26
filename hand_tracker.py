import cv2
import mediapipe as mp
import numpy as np

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

        # shorter trail = faster fade
        self.max_trail_length = 12

        # smoothing
        self.smoothed_x = None
        self.smoothed_y = None
        self.alpha = 0.15

    def catmull_rom_spline(self, points, samples_per_segment=15):

        if len(points) < 4:
            return points

        result = []

        pts = [points[0]] + points + [points[-1]]

        for i in range(1, len(pts) - 2):

            p0 = np.array(pts[i - 1], dtype=float)
            p1 = np.array(pts[i], dtype=float)
            p2 = np.array(pts[i + 1], dtype=float)
            p3 = np.array(pts[i + 2], dtype=float)

            for t in np.linspace(0, 1, samples_per_segment):

                t2 = t * t
                t3 = t2 * t

                point = 0.5 * (
                    (2 * p1)
                    + (-p0 + p2) * t
                    + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                    + (-p0 + 3 * p1 - 3 * p2 + p3) * t3
                )

                result.append(
                    (int(point[0]), int(point[1]))
                )

        return result

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

            # index fingertip
            fingertip = hand[8]

            height, width, _ = frame.shape

            x = int(fingertip.x * width)
            y = int(fingertip.y * height)

            # exponential smoothing
            if self.smoothed_x is None:

                self.smoothed_x = x
                self.smoothed_y = y

            else:

                self.smoothed_x = (
                    self.alpha * x +
                    (1 - self.alpha) * self.smoothed_x
                )

                self.smoothed_y = (
                    self.alpha * y +
                    (1 - self.alpha) * self.smoothed_y
                )

            smooth_point = (
                int(self.smoothed_x),
                int(self.smoothed_y)
            )

            self.trail.append((x,y))

            if len(self.trail) > self.max_trail_length:
                self.trail.pop(0)

            overlay = frame.copy()

            if len(self.trail) >= 4:

                curve = self.catmull_rom_spline(
                    self.trail,
                    samples_per_segment=12
                )

                total = len(curve)

                for i in range(1, total):

                    progress = i / total

                    brightness = int(255 * progress)

                    thickness = max(
                        1,
                        int(7 * progress)
                    )

                    cv2.line(
                        overlay,
                        curve[i - 1],
                        curve[i],
                        (
                            brightness,
                            brightness,
                            brightness
                        ),
                        thickness,
                        cv2.LINE_AA
                    )

            frame = cv2.addWeighted(
                overlay,
                0.9,
                frame,
                0.1,
                0
            )

            cv2.circle(
                frame,
                (x, y),
                8,
                (255, 255, 255),
                -1,
                cv2.LINE_AA
            )

        return frame