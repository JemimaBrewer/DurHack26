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

        media = self.instance.media_new(
            audio_file
        )

        self.player.set_media(media)

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

        self.current_rate = max(
            0.5,
            min(
                2.0,
                live_bpm
                / self.reference_bpm
            )
        )

        self.player.set_rate(
            self.current_rate
        )

    def get_rate(self):

        return round(
            self.current_rate,
            2
        )