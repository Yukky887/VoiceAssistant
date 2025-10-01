from llama_assistant import LlamaAssistant
from spotify_player import SpotifyPlayer
from voice_synthesizer_gtts import tts
import time
import sys

# Попробуем импортировать распознаватель речи
try:
    from speech_recognition_alternative import SpeechRecognizer

    print("✅ Использую SpeechRecognition")
except ImportError:
    try:
        from speech import SpeechRecognizer

        print("✅ Использую Vosk")
    except ImportError:
        print("❌ Не найден ни один модуль распознавания речи")
        sys.exit(1)


class VoiceActivator:
    def __init__(self, activation_phrase="джарвис", deactivation_phrase="спать"):
        self.activation_phrase = activation_phrase.lower()
        self.deactivation_phrase = deactivation_phrase.lower()
        self.is_active = False

        self.greetings = [
            "Слушаю вас",
            "Да, я здесь",
            "Чем могу помочь?",
            "Готов к работе",
            "Слушаю ваши команды"
        ]

        self.goodbyes = [
            "Хорошего дня!",
            "До скорой встречи!",
            "Отдыхаю до вашего возвращения",
            "Выключаюсь",
            "До свидания!"
        ]

    def activate(self):
        """Активация с голосовым приветствием"""
        if not self.is_active:
            self.is_active = True
            greeting = random.choice(self.greetings)
            print(f"✅ АКТИВИРОВАН! {greeting}")
            tts.speak_async(greeting)
            return True
        return False

    def deactivate(self):
        """Деактивация с голосовым прощанием"""
        if self.is_active:
            self.is_active = False
            goodbye = random.choice(self.goodbyes)
            print(f"💤 ДЕАКТИВИРОВАН! {goodbye}")
            tts.speak_async(goodbye)
            return True
        return False

    def check_activation(self, text):
        """Проверяет текст на наличие команд активации/деактивации"""
        if not text:
            return False

        text_lower = text.lower()

        if self.activation_phrase in text_lower:
            return self.activate()

        elif self.deactivation_phrase in text_lower:
            return self.deactivate()

        return False


import random  # Добавляем импорт random


def main():
    try:
        # Инициализация компонентов
        print("🚀 Загружаю компоненты...")

        # Инициализируем активатор
        activator = VoiceActivator(activation_phrase="джарвис", deactivation_phrase="спать")

        # Инициализируем распознаватель
        recognizer = SpeechRecognizer()
        assistant = LlamaAssistant()
        player = SpotifyPlayer()

        print("✅ Все компоненты загружены!")

        # Приветствие при запуске
        tts.speak("Голосовой ассистент Джа́рвис запущен. Готов отвечать на вопросы и управлять музыкой")

        print(f"\n🎵 Голосовой ассистент запущен!")
        print(f"🎯 Скажите '{activator.activation_phrase}' для активации")
        print(f"💤 Скажите '{activator.deactivation_phrase}' для деактивации")
        print(f"❓ Можете задавать любые вопросы!")
        print(f"🎵 Или управлять музыкой: 'включи трек', 'пауза', 'громче' и т.д.\n")

        while True:
            try:
                # Всегда слушаем, но обрабатываем команды только в активном режиме
                if activator.is_active:
                    print("🎤 АКТИВНЫЙ РЕЖИМ - слушаю команду или вопрос...")
                else:
                    print("⏳ ОЖИДАНИЕ - скажите 'джарвис' для активации...")

                # Запись аудио
                audio = recognizer.listen(duration=7)

                # Транскрибация
                query = recognizer.transcribe(audio)

                if query:
                    print(f"📝 Распознано: {query}")

                # Проверяем команды активации/деактивации
                if activator.check_activation(query):
                    continue

                # Если не активен - игнорируем команды
                if not activator.is_active:
                    if query and len(query.strip()) > 2:
                        print("❌ Неактивный режим - игнорирую команду")
                    continue

                # Если активен, но команда пустая
                if not query or len(query.strip()) < 2:
                    print("❌ Не удалось распознать речь")
                    continue

                # Обработка через LLM для классификации и ответа
                intent = assistant.ask(query)
                print(f"🤖 LLM классифицировал как: {intent}")

                action = intent.get('action', 'none')

                # Обработка музыкальных команд
                if action in ['play', 'playlist', 'favorites', 'pause', 'resume', 'next', 'previous', 'volume']:
                    # Голосовое подтверждение музыкальных команд
                    if action == 'play':
                        track = intent.get('track', '')
                        if track:
                            tts.speak_async(f"Включаю {track}")
                    elif action == 'playlist':
                        playlist = intent.get('playlist', '')
                        if playlist:
                            tts.speak_async(f"Включаю плейлист {playlist}")
                    elif action == 'favorites':
                        tts.speak_async("Включаю ваши любимые треки")
                    elif action == 'pause':
                        tts.speak_async("Ставлю на паузу")
                    elif action == 'resume':
                        tts.speak_async("Продолжаю воспроизведение")
                    elif action == 'next':
                        tts.speak_async("Переключаю на следующий трек")
                    elif action == 'previous':
                        tts.speak_async("Возвращаю предыдущий трек")
                    elif action == 'volume':
                        level = intent.get('level', '')
                        if level == 'up':
                            tts.speak_async("Увеличиваю громкость")
                        elif level == 'down':
                            tts.speak_async("Уменьшаю громкость")
                        elif isinstance(level, int):
                            tts.speak_async(f"Устанавливаю громкость на {level} процентов")

                    # Выполнение музыкальной команды в Spotify
                    player.play(intent)

                # Обработка вопросов
                elif action == 'question':
                    answer = intent.get('answer', '')
                    if answer:
                        print(f"💭 Ответ на вопрос: {answer}")
                        tts.speak(answer)
                    else:
                        tts.speak("Извините, я не смог обработать ваш вопрос")

                # Неизвестная команда
                elif action == 'none':
                    tts.speak("Извините, я не понял команду. Вы можете управлять музыкой или задать вопрос")
                    print("❓ Неизвестная команда")

                print("\n" + "=" * 50)
                if activator.is_active:
                    print("🎯 АКТИВНЫЙ РЕЖИМ - жду следующую команду или вопрос")
                    print("💤 Скажите 'спать' для выхода из активного режима")
                print("=" * 50 + "\n")

            except KeyboardInterrupt:
                print("\n👋 Выключаю колонку...")
                tts.speak("Выключаюсь, до свидания!")
                break
            except Exception as e:
                print(f"❌ Ошибка в основном цикле: {e}")
                time.sleep(1)

    except Exception as e:
        print(f"❌ Критическая ошибка инициализации: {e}")


if __name__ == "__main__":
    main()