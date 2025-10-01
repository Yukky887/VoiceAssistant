import json
import ollama

class LlamaAssistant:
    def __init__(self, model="llama3.1:8b-instruct-q8_0"):
        self.model = model
        self.system_prompt = """
            Ты голосовой ассистент. Превращай команду про музыку в JSON.
            Примеры:
            - "включи Shape of You Эда Ширана" -> {"action": "play", "track": "Shape of You", "artist": "Ed Sheeran"}
            - "поставь плейлист Chill Vibes" -> {"action": "playlist", "playlist": "Chill Vibes"}
            - "включи кукла калдуна группы король и шут" -> {"action": "play", "track": "кукла колдуна", "artist": "король и шут"}
            - "включи музыку в стиле рок" -> {"action": "playlist", "playlist": "Rock Music"}
            - "включи плейлист который называется этажность" -> {"action": "playlist", "playlist": "этажность"}
            - "пауза" -> {"action": "pause"}
            - "продолжи" -> {"action": "resume"}

            Используй короткие и популярные названия для плейлистов. Если пользователь просит жанр (рок, поп, метал, джаз), 
            добавляй слово "Music" или оставляй только жанр. Когда есть популярная группа название которой на русском языке, 
            не нужно переводить его на другой язык, ты должен сам отслеживать это и понимать какой язык использовать.

            Ответь только JSON без текста.
            """

    def ask(self, query: str) -> str:
        response = ollama.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": query}
            ]
        )

        try:
            content = response["message"]["content"].strip()
            return json.loads(content)

        except json.JSONDecodeError:
            print(f"Не удалось распарсить JSON: {content}")
            return {"action": "none"}