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

    def play(self):
        self.player.play()

    def stop(self):
        self.player.stop()

    def update_tempo(
        self,
        live_bpm
    ):

        if live_bpm <= 0:
            return

        target_rate = (
            live_bpm
            / self.reference_bpm
        )

        # Wider range
        target_rate = max(
            0.4,
            min(3.0, target_rate)
        )

        # Gentle adjustment
        self.current_rate += (
            target_rate
            - self.current_rate
        ) * 0.35

        self.player.set_rate(
            self.current_rate
        )

    def get_rate(self):

        return round(
            self.current_rate,
            2
        )