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
        self.current_volume = 150

    def play(self):
        self.player.play()

    def stop(self):
        self.player.stop()

    def set_volume(self, volume):
        self.current_volume = max(1, min(200, int(volume)))
        self.player.audio_set_volume(self.current_volume)

    def get_volume(self):
        return self.current_volume

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

        target_rate = max(
            0.5,
            min(2.5, target_rate)
        )

        max_change = 0.10

        rate_difference = (
            target_rate
            - self.current_rate
        )

        if rate_difference > max_change:
            rate_difference = max_change

        elif rate_difference < -max_change:
            rate_difference = -max_change

        self.current_rate += (
            rate_difference
        )

        self.player.set_rate(
            self.current_rate
        )

        print(
            f"Target={target_rate:.2f} "
            f"Current={self.current_rate:.2f}"
        )

    def get_rate(self):

        return round(
            self.current_rate,
            2
        )