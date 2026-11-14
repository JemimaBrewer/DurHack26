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

        self.max_trail_length = 15

        self.frames_without_hand = 0
        self.fade_delay = 10

    def catmull_rom_spline(
        self,
        points,
        samples_per_segment=12
    ):

        if len(points) < 4:
            return points

        result = []

        pts = [points[0]] + points + [points[-1]]

        for i in range(1, len(pts) - 2):

            p0 = np.array(pts[i - 1], dtype=float)
            p1 = np.array(pts[i], dtype=float)
            p2 = np.array(pts[i + 1], dtype=float)
            p3 = np.array(pts[i + 2], dtype=float)

            for t in np.linspace(
                0,
                1,
                samples_per_segment,
                endpoint=False
            ):

                t2 = t * t
                t3 = t2 * t

                point = 0.5 * (
                    (2 * p1)
                    + (-p0 + p2) * t
                    + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                    + (-p0 + 3 * p1 - 3 * p2 + p3) * t3
                )

                result.append(
                    (
                        int(point[0]),
                        int(point[1])
                    )
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

        fingertip_position = None

        if result.hand_landmarks:

            self.frames_without_hand = 0

            hand = result.hand_landmarks[0]

            fingertip = hand[8]

            height, width, _ = frame.shape

            x = int(fingertip.x * width)
            y = int(fingertip.y * height)

            fingertip_position = (x, y)

            self.trail.append(fingertip_position)

            if len(self.trail) > self.max_trail_length:
                self.trail.pop(0)

        else:

            self.frames_without_hand += 1

            if (
                self.frames_without_hand > self.fade_delay
                and len(self.trail) > 0
            ):
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

                brightness = int(
                    255 * progress
                )

                thickness = max(
                    1,
                    int(6 * progress)
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

        if fingertip_position is not None:

            cv2.circle(
                frame,
                fingertip_position,
                8,
                (255, 255, 255),
                -1,
                cv2.LINE_AA
            )

        return frame