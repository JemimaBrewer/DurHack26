import math
import time

import vlc


class AudioPlayer:

    def __init__(
        self,
        audio_file,
        reference_bars_per_minute
    ):

        self.reference_bpm = (
            reference_bars_per_minute
        )

        self.instance = vlc.Instance()

        self.player = (
            self.instance.media_player_new()
        )

        media = (
            self.instance.media_new(
                audio_file
            )
        )

        self.player.set_media(
            media
        )

        self.current_rate = 1.0
        self.target_rate = 1.0
        self.last_rate_update = time.monotonic()
        self.current_volume = 150

    def play(self):
        self.player.play()

    def stop(self):
        self.player.stop()

    def set_volume(self, volume):
        self.current_volume = max(1, min(400, int(volume)))
        self.player.audio_set_volume(self.current_volume)

    def get_volume(self):
        return self.current_volume

    def update_tempo(
        self,
        live_bpm
    ):

        if live_bpm <= 0:
            return

        self.target_rate = (
            live_bpm
            / self.reference_bpm
        )

        self.target_rate = max(
            0.5,
            min(2.5, self.target_rate)
        )

        now = time.monotonic()
        elapsed = max(0.0, now - self.last_rate_update)
        self.last_rate_update = now
        smoothing = 1.0 - math.exp(-elapsed / 0.18)
        self.current_rate += (
            self.target_rate - self.current_rate
        ) * smoothing

        if abs(self.target_rate - self.current_rate) > 0.001:
            self.player.set_rate(self.current_rate)

    def get_rate(self):

        return round(
            self.current_rate,
            2
        )