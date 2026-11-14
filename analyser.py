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

        # store the last 4 intervals, average to make run smoother
        self.intervals = deque(maxlen=4)
        
        # cooldown reduced to 0.25 to allow for 240BPM max
        self.cooldown = 0.25
        # consider adding dynamic cooldown based on recent movements
        

        # Minimum size of a conducting stroke
        self.min_stroke_size = 120
        
        #ignore tiny fluctuations in y position
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
        # Hand moving down
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

        # Hand now moving upwards
        elif delta < 0:

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

                            self.intervals.append(interval)
                            
                            if len(self.intervals) >= 4:
                                average_interval = (
                                    sum(self.intervals)
                                    / len(self.intervals)
                                )

                                self.bars_per_minute = (
                                    60.0 / average_interval
                                )

                    self.last_downbeat_time = (
                        current_time
                    )

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