import time


class Analyser:

    def __init__(self):

        self.previous_y = None

        self.descending = False

        self.stroke_start_y = None
        self.stroke_lowest_y = None

        self.last_downbeat_time = None

        self.bars_per_minute = 0.0

        # Prevent multiple detections
        self.cooldown = 1.0

        # Minimum size of a conducting stroke
        self.min_stroke_size = 120

    def update(self, x, y):

        current_time = time.time()

        if self.previous_y is None:
            self.previous_y = y
            return

        # Hand moving down
        if y > self.previous_y:

            if not self.descending:

                self.descending = True
                self.stroke_start_y = self.previous_y
                self.stroke_lowest_y = y

            else:

                self.stroke_lowest_y = max(
                    self.stroke_lowest_y,
                    y
                )

        # Hand now moving upwards
        elif y < self.previous_y:

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
                    and cooldown_finished
                ):

                    if self.last_downbeat_time is not None:

                        interval = (
                            current_time
                            - self.last_downbeat_time
                        )

                        if interval > 0.2:

                            self.bars_per_minute = (
                                60.0 / interval
                            )

                    self.last_downbeat_time = (
                        current_time
                    )

                self.descending = False

        self.previous_y = y

    def get_bars_per_minute(self):

        return round(
            self.bars_per_minute,
            1
        )