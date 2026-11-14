import time
from collections import deque


class Analyser:

    def __init__(self):
        self.previous_y = None
        self.previous_time = None

        self.previous_velocity = 0.0

        self.last_ictus_time = None

        self.bars_per_minute = 0.0

        self.intervals = deque(maxlen=2)

        self.deadzone = 4
        self.cooldown = 0.12

    def update(self, x, y):

        current_time = time.time()

        if self.previous_y is None:
            self.previous_y = y
            self.previous_time = current_time
            return False

        dt = current_time - self.previous_time

        if dt <= 0:
            return False

        velocity = (
            y - self.previous_y
        ) / dt

        ictus_detected = (
            self.previous_velocity > 0
            and velocity < 0
            and abs(y - self.previous_y) > self.deadzone
        )

        if ictus_detected:

            cooldown_finished = (
                self.last_ictus_time is None
                or (
                    current_time
                    - self.last_ictus_time
                ) > self.cooldown
            )

            if cooldown_finished:

                if self.last_ictus_time is not None:

                    interval = (
                        current_time
                        - self.last_ictus_time
                    )

                    if interval > 0.15:

                        self.intervals.append(
                            interval
                        )

                        average_interval = (
                            sum(self.intervals)
                            / len(self.intervals)
                        )

                        raw_bpm = (
                            60.0
                            / average_interval
                        )

                        # Prevent wild jumps caused
                        # by a single bad detection.
                        if self.bars_per_minute > 0:

                            max_change = 10

                            raw_bpm = max(
                                self.bars_per_minute
                                - max_change,
                                min(
                                    self.bars_per_minute
                                    + max_change,
                                    raw_bpm
                                )
                            )

                        self.bars_per_minute = raw_bpm

                self.last_ictus_time = current_time

        self.previous_velocity = velocity
        self.previous_y = y
        self.previous_time = current_time

        return ictus_detected

    def get_bars_per_minute(self):

        return round(
            self.bars_per_minute,
            1
        )