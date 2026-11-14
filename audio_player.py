import vlc


class AudioPlayer:
    def __init__(
        self,
        audio_file,
        reference_bars_per_minute,
        smoothing=0.15
    ):
        self.reference_bpm = (
            reference_bars_per_minute
        )

        self.smoothing = smoothing

        self.instance = vlc.Instance()
        self.player = (
            self.instance.media_player_new()
        )

        media = self.instance.media_new(
            audio_file
        )

        self.player.set_media(media)

        self.current_rate = 1.0
        self.target_rate = 1.0

    def play(self):
        self.player.play()

    def stop(self):
        self.player.stop()

    def update_tempo(
        self,
        live_bars_per_minute
    ):
        if live_bars_per_minute <= 0:
            return

        self.target_rate = (
            live_bars_per_minute
            / self.reference_bpm
        )

        # Prevent ridiculous values
        self.target_rate = max(
            0.5,
            min(2.0, self.target_rate)
        )

        self.current_rate += (
            self.target_rate
            - self.current_rate
        ) * self.smoothing

        self.player.set_rate(
            self.current_rate
        )

    def get_rate(self):
        return round(
            self.current_rate,
            2
        )