import time
from collections import deque


class Analyser:
    def __init__(self):
        self.previous_y = None

        self.descending = False
        self.stroke_start_y = None
        self.stroke_lowest_y = None

        self.last_downbeat_time = None

        self.bars_per_minute = 0.0

        # Faster response
        self.intervals = deque(maxlen=2)

        # Initial cooldown
        self.cooldown = 0.25

        # Smaller gestures accepted
        self.min_stroke_size = 80

        # Ignore tiny fluctuations
        self.deadzone = 6

    def update(self, x, y):
        current_time = time.time()

        if self.previous_y is None:
            self.previous_y = y
            return False

        delta = y - self.previous_y

        if abs(delta) <= self.deadzone:
            self.previous_y = y
            return False

        # Moving down
        if delta > 0:
            if not self.descending:
                self.descending = True
                self.stroke_start_y = self.previous_y
                self.stroke_lowest_y = y
            else:
                self.stroke_lowest_y = max(
                    self.stroke_lowest_y,
                    y
                )

        # Moving up
        else:
            if self.descending:

                stroke_size = (
                    self.stroke_lowest_y
                    - self.stroke_start_y
                )

                sufficiently_large = (
                    stroke_size >
                    self.min_stroke_size
                )

                cooldown_finished = (
                    self.last_downbeat_time is None
                    or
                    current_time
                    - self.last_downbeat_time
                    > self.cooldown
                )

                if (
                    sufficiently_large
                    and
                    cooldown_finished
                ):
                    if self.last_downbeat_time is not None:

                        interval = (
                            current_time
                            - self.last_downbeat_time
                        )

                        if interval > 0.2:

                            self.intervals.append(
                                interval
                            )

                            average_interval = (
                                sum(self.intervals)
                                / len(self.intervals)
                            )

                            self.bars_per_minute = (
                                60.0
                                / average_interval
                            )

                            # Dynamic cooldown
                            self.cooldown = max(
                                0.12,
                                average_interval * 0.3
                            )

                    self.last_downbeat_time = current_time

                self.descending = False

                self.previous_y = y
                return True

        self.previous_y = y
        return False

    def get_bars_per_minute(self):
        return round(
            self.bars_per_minute,
            1
        )