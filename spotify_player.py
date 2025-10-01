import requests
import json
from config import CLIENT_ID, CLIENT_SECRET, REFRESH_TOKEN, DEVICE_NAME


class SpotifyPlayer:
    def __init__(self):
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self.refresh_token = REFRESH_TOKEN
        self.device_name = DEVICE_NAME

    def get_access_token(self):
        url = "https://accounts.spotify.com/api/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        }
        resp = requests.post(url, data=data, auth=(self.client_id, self.client_secret))
        if resp.status_code == 200:
            return resp.json()["access_token"]
        else:
            raise Exception(f"❌ Ошибка получения токена: {resp.text}")

    def get_device_id(self, token):
        try:
            response = requests.get(
                "https://api.spotify.com/v1/me/player/devices",
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code != 200:
                raise Exception(f"❌ Ошибка получения устройств: {response.text}")

            devices_data = response.json()
            device = next((d for d in devices_data.get("devices", []) if d["name"] == self.device_name), None)

            if not device:
                # Попробуем найти любое активное устройство
                active_device = next((d for d in devices_data.get("devices", []) if d["is_active"]), None)
                if active_device:
                    print(f"⚠️ Устройство '{self.device_name}' не найдено, использую активное: {active_device['name']}")
                    return active_device["id"]
                else:
                    raise Exception(f"❌ Устройство '{self.device_name}' не найдено и нет активных устройств")

            return device["id"]
        except Exception as e:
            raise Exception(f"❌ Ошибка поиска устройства: {e}")

    def play(self, query: dict):
        try:
            token = self.get_access_token()
            device_id = self.get_device_id(token)

            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

            action = query.get("action", "none")

            if action == "play":
                track = query.get('track', '')
                artist = query.get('artist', '')

                # Формируем поисковый запрос
                search_query = f"track:{track}"
                if artist:
                    search_query += f" artist:{artist}"

                print(f"🔍 Ищу: {track} - {artist}")

                search_response = requests.get(
                    f"https://api.spotify.com/v1/search?q={search_query}&type=track&limit=1&market=RU",
                    headers=headers
                )

                if search_response.status_code != 200:
                    raise Exception(f"❌ Ошибка поиска: {search_response.text}")

                search_data = search_response.json()

                if search_data["tracks"]["items"]:
                    uri = search_data["tracks"]["items"][0]["uri"]
                    track_name = search_data["tracks"]["items"][0]["name"]
                    artist_name = search_data["tracks"]["items"][0]["artists"][0]["name"]

                    play_response = requests.put(
                        f"https://api.spotify.com/v1/me/player/play?device_id={device_id}",
                        headers=headers,
                        data=json.dumps({"uris": [uri]})
                    )

                    if play_response.status_code in [200, 204]:
                        print(f"🎵 Играет: {track_name} - {artist_name}")
                    else:
                        print(f"❌ Ошибка воспроизведения: {play_response.text}")
                else:
                    print("❌ Трек не найден в Spotify")

            elif action == "playlist":
                playlist = query.get('playlist', '')

                search_response = requests.get(
                    f"https://api.spotify.com/v1/search?q={playlist}&type=playlist&limit=1&market=RU",
                    headers=headers
                )

                if search_response.status_code != 200:
                    raise Exception(f"❌ Ошибка поиска плейлиста: {search_response.text}")

                search_data = search_response.json()

                if search_data["playlists"]["items"]:
                    uri = search_data["playlists"]["items"][0]["uri"]
                    playlist_name = search_data["playlists"]["items"][0]["name"]

                    play_response = requests.put(
                        f"https://api.spotify.com/v1/me/player/play?device_id={device_id}",
                        headers=headers,
                        data=json.dumps({"context_uri": uri})
                    )

                    if play_response.status_code in [200, 204]:
                        print(f"🎵 Плейлист: {playlist_name}")
                    else:
                        print(f"❌ Ошибка воспроизведения плейлиста: {play_response.text}")
                else:
                    print("❌ Плейлист не найден")

            elif action == "pause":
                response = requests.put(
                    f"https://api.spotify.com/v1/me/player/pause?device_id={device_id}",
                    headers=headers
                )
                if response.status_code in [200, 204]:
                    print("⏸️ Пауза")
                else:
                    print(f"❌ Ошибка паузы: {response.text}")

            elif action == "resume":
                response = requests.put(
                    f"https://api.spotify.com/v1/me/player/play?device_id={device_id}",
                    headers=headers
                )
                if response.status_code in [200, 204]:
                    print("▶️ Продолжаем воспроизведение")
                else:
                    print(f"❌ Ошибка возобновления: {response.text}")

            elif action == "next":
                response = requests.post(
                    f"https://api.spotify.com/v1/me/player/next?device_id={device_id}",
                    headers=headers
                )
                if response.status_code in [200, 204]:
                    print("⏭️ Следующий трек")
                else:
                    print(f"❌ Ошибка переключения: {response.text}")

            elif action == "previous":
                response = requests.post(
                    f"https://api.spotify.com/v1/me/player/previous?device_id={device_id}",
                    headers=headers
                )
                if response.status_code in [200, 204]:
                    print("⏮️ Предыдущий трек")
                else:
                    print(f"❌ Ошибка переключения: {response.text}")

            elif action == "none":
                print("🤖 Это не музыкальная команда")
            else:
                print(f"❌ Неизвестное действие: {action}")

        except Exception as e:
            print(f"❌ Ошибка воспроизведения: {e}")