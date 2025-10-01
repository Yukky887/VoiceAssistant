from speech_to_text import SpeechRecognizer
from llama_assistant import LlamaAssistant
from spotify_player import SpotifyPlayer


def main():
    # Инициализация компонентов
    recognizer = SpeechRecognizer()
    assistant = LlamaAssistant()
    player = SpotifyPlayer()

    try:
        # Запись аудио
        audio = recognizer.listen()

        # Транскрибация
        query = recognizer.transcribe(audio)
        print("Ты сказал:", query)

        if not query or len(query.strip()) < 3:
            print("Не удалось распознать речь")
            return

        # Обработка команд через LLM
        intent = assistant.ask(query)
        print("Ассистент понял:", intent)

        # Выполнение команды в Spotify
        player.play(intent)

    except Exception as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    main()