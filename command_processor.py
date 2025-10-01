from spotify_player import SpotifyPlayer

class CommandProcessor:
    def __init__(self, spotify: SpotifyPlayer):
        self.spotify = spotify

    def handle(self, command: dict):
        action = command.get("action")

        if action == "play":
            self.spotify.play_song(command.get("song"), command.get("artist"))
        else:
            print("Не понял команду:", command)
