import requests

class SpotifyPlayer:
    def __init__(self, access_token: str):
        self.access_token = access_token

    def play_song(self, song: str, artist: str = None):
        query = f"{song} {artist}" if artist else song
        search_url = f"https://api.spotify.com/v1/search?q={query}&type=track&limit=1"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        r = requests.get(search_url, headers=headers)
        data = r.json()

        if data["tracks"]["items"]:
            track_uri = data["tracks"]["items"][0]["uri"]
            play_url = "https://api.spotify.com/v1/me/player/play"
            requests.put(play_url, headers=headers, json={"uris": [track_uri]})
            print(f"Включаю: {data['tracks']['items'][0]['name']} - {data['tracks']['items'][0]['artists'][0]['name']}")
        else:
            print("Не нашёл трек")