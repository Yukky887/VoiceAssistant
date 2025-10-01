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
            raise Exception(f"Ошибка получения токена: {resp.text}")

    def get_device_id(self, token):
        try:
            response = requests.get(
                "https://api.spotify.com/v1/me/player/devices",
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code != 200:
                raise Exception(f"Ошибка получения устройств: {response.text}")

            devices_data = response.json()
            device = next((d for d in devices_data.get("devices", []) if d["name"] == self.device_name), None)

            if not device:
                # Попробуем найти любое активное устройство
                active_device = next((d for d in devices_data.get("devices", []) if d["is_active"]), None)

                if active_device:
                    print(f"Устройство '{self.device_name}' не найдено, использую активное: {active_device['name']}")
                    return active_device["id"]
                else:
                    raise Exception(f"Устройство '{self.device_name}' не найдено и нет активных устройств")

            return device["id"]

        except Exception as e:
            raise Exception(f"Ошибка поиска устройства: {e}")

    def get_current_volume(self, token, device_id):
        try:
            response = requests.get(
                f"https://api.spotify.com/v1/me/player",
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code == 200:
                player_data = response.json()

                if player_data and "device" in player_data:
                    return player_data["device"].get("volume_percent", 50)

            return 50

        except:

            return 50

    def set_volume(self, token, device_id, volume_level):
        if volume_level < 0:
            volume_level = 0
        elif volume_level > 100:
            volume_level = 100

        response = requests.put(
            f"https://api.spotify.com/v1/me/player/volume?volume_percent={volume_level}&device_id={device_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        return response.status_code in [200, 204]

    def play_favorites(self, token, device_id, headers):

        try:
            # Получаем список любимых треков
            response = requests.get(
                "https://api.spotify.com/v1/me/tracks?limit=50",
                headers=headers
            )

            if response.status_code == 200:
                tracks_data = response.json()

                if tracks_data["items"]:
                    # Создаем список URI любимых треков
                    uris = [item["track"]["uri"] for item in tracks_data["items"]]

                    play_response = requests.put(
                        f"https://api.spotify.com/v1/me/player/play?device_id={device_id}",
                        headers=headers,
                        data=json.dumps({"uris": uris[:20]})  # ограничиваем первыми 20 треками
                    )

                    print(f"Статус воспроизведения: {play_response.status_code}")

                    if play_response.status_code in [200, 204]:
                        print("Любимые треки включены!")
                        return True
                    else:
                        print(f"Ошибка воспроизведения: {play_response.text}")
                        return False
                else:
                    print("Нет любимых треков")
                    return False
            else:
                print(f"Ошибка получения любимых треков: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"Ошибка воспроизведения любимых треков: {e}")

            return False

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

                print(f"Ищу: {track} - {artist}")

                search_response = requests.get(
                    f"https://api.spotify.com/v1/search?q={search_query}&type=track&limit=1&market=RU",
                    headers=headers
                )

                if search_response.status_code != 200:
                    raise Exception(f"Ошибка поиска: {search_response.text}")

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
                        print(f"Играет: {track_name} - {artist_name}")
                    else:
                        print(f"Ошибка воспроизведения: {play_response.text}")
                else:
                    print("Трек не найден в Spotify")

            elif action == "playlist":
                playlist = query.get('playlist', '')

                search_response = requests.get(
                    f"https://api.spotify.com/v1/search?q={playlist}&type=playlist&limit=1&market=RU",
                    headers=headers
                )

                if search_response.status_code != 200:
                    raise Exception(f"Ошибка поиска плейлиста: {search_response.text}")

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
                        print(f"Плейлист: {playlist_name}")
                    else:
                        print(f"Ошибка воспроизведения плейлиста: {play_response.text}")
                else:
                    print("Плейлист не найден")

            elif action == "favorites":
                print("Включаю любимые треки...")

                if self.play_favorites(token, device_id, headers):
                    print("Любимые треки включены!")
                else:
                    print("Не удалось включить любимые треки")

            elif action == "pause":
                response = requests.put(
                    f"https://api.spotify.com/v1/me/player/pause?device_id={device_id}",
                    headers=headers
                )

                if response.status_code in [200, 204]:
                    print("Пауза")
                else:
                    print(f"Ошибка паузы: {response.text}")

            elif action == "resume":
                response = requests.put(
                    f"https://api.spotify.com/v1/me/player/play?device_id={device_id}",
                    headers=headers
                )

                if response.status_code in [200, 204]:
                    print("Продолжаем воспроизведение")
                else:
                    print(f"Ошибка возобновления: {response.text}")

            elif action == "next":
                response = requests.post(
                    f"https://api.spotify.com/v1/me/player/next?device_id={device_id}",
                    headers=headers
                )

                if response.status_code in [200, 204]:
                    print("Следующий трек")
                else:
                    print(f"Ошибка переключения: {response.text}")

            elif action == "previous":
                response = requests.post(
                    f"https://api.spotify.com/v1/me/player/previous?device_id={device_id}",
                    headers=headers
                )

                if response.status_code in [200, 204]:
                    print("Предыдущий трек")
                else:
                    print(f"Ошибка переключения: {response.text}")

            elif action == "volume":
                volume_level = query.get('level', 50)
                current_volume = self.get_current_volume(token, device_id)

                if volume_level == "up":
                    new_volume = min(current_volume + 20, 100)

                    if self.set_volume(token, device_id, new_volume):
                        print(f"Громкость увеличена до {new_volume}%")
                    else:
                        print("Ошибка изменения громкости")

                elif volume_level == "down":
                    new_volume = max(current_volume - 20, 0)

                    if self.set_volume(token, device_id, new_volume):
                        print(f"Громкость уменьшена до {new_volume}%")
                    else:
                        print("Ошибка изменения громкости")

                elif isinstance(volume_level, int):

                    if self.set_volume(token, device_id, volume_level):
                        print(f"Громкость установлена на {volume_level}%")
                    else:
                        print("Ошибка изменения громкости")
                else:
                    print(f"Неизвестный уровень громкости: {volume_level}")

            elif action == "none":
                print("Это не музыкальная команда")
            else:
                print(f"Неизвестное действие: {action}")

        except Exception as e:
            print(f"Ошибка воспроизведения: {e}")