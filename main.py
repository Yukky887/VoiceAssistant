# main.py
from llama_assistant import LlamaAssistant
from spotify_player import SpotifyPlayer
from voice_synthesizer_gtts import tts
from voice_processor import VoiceProcessor
import time
import sys
import random

# Импортируем распознаватель речи
try:
    from speech_recognition_alternative import SpeechRecognizer

    print("✅ Использую SpeechRecognition с VAD")
except ImportError:
    try:
        from speech import SpeechRecognizer

        print("✅ Использую Vosk")
    except ImportError:
        print("❌ Не найден ни один модуль распознавания речи")
        sys.exit(1)


class AdvancedVoiceActivator:
    def __init__(self, activation_phrases=["джарвис", "jarvis"], deactivation_phrase="спать"):
        self.activation_phrases = [p.lower() for p in activation_phrases]
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

        # Инициализируем голосовой процессор
        self.voice_processor = VoiceProcessor(wake_words=activation_phrases)

    def wake_word_callback(self, event):
        """Callback при обнаружении wake word"""
        if event == "wake_word_detected" and not self.is_active:
            self.activate()

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
        """Проверяет текст на наличие команд активации/деактивации с учетом Левенштейна"""
        if not text:
            return False

        text_lower = text.lower()

        # Проверка активации с учетом опечаток
        for phrase in self.activation_phrases:
            if self._fuzzy_match(phrase, text_lower):
                return self.activate()

        # Проверка деактивации
        if self.deactivation_phrase in text_lower:
            return self.deactivate()

        return False

    def _fuzzy_match(self, target, text, max_distance_ratio=0.3):
        """Проверяет совпадение с учетом расстояния Левенштейна"""
        from Levenshtein import distance as lev_distance

        words = text.split()
        for word in words:
            dist = lev_distance(target, word)
            max_allowed = int(len(target) * max_distance_ratio)
            if dist <= max_allowed:
                return True
        return False

    def start_wake_word_detection(self):
        """Запускает обнаружение wake word"""
        self.voice_processor.start_listening(self.wake_word_callback)

    def stop_wake_word_detection(self):
        """Останавливает обнаружение wake word"""
        self.voice_processor.stop_listening()


def main():
    try:
        # Инициализация компонентов
        print("🚀 Загружаю компоненты...")

        # Инициализируем улучшенный активатор
        activator = AdvancedVoiceActivator(
            activation_phrases=["джарвис", "джаврис", "джарвиз", "jarvis"],
            deactivation_phrase="спать"
        )

        # Инициализируем распознаватель
        recognizer = SpeechRecognizer()
        assistant = LlamaAssistant()
        player = SpotifyPlayer()

        print("✅ Все компоненты загружены!")

        # Приветствие при запуске
        tts.speak("Голосовой ассистент Джа́рвис запущен. Используйте кодовое слово для активации")

        # Запускаем обнаружение wake word
        activator.start_wake_word_detection()

        print(f"\n🎯 Голосовой ассистент запущен!")
        print(f"🔊 Wake word detection активен")
        print(f"🎯 Скажите '{activator.activation_phrases[0]}' для активации")
        print(f"💤 Скажите '{activator.deactivation_phrase}' для деактивации")
        print(f"❓ Можете задавать любые вопросы!")
        print(f"🎵 Или управлять музыкой\n")

        while True:
            try:
                # В режиме ожидания показываем статус
                if not activator.is_active:
                    print("⏳ ОЖИДАНИЕ - скажите 'джарвис' для активации...", end='\r')
                    time.sleep(1)
                    continue

                # Активный режим
                print("\n🎤 АКТИВНЫЙ РЕЖИМ - слушаю команду или вопрос...")

                # Используем улучшенное прослушивание с VAD
                audio = recognizer.listen_with_vad(timeout=10, phrase_time_limit=7)

                # Транскрибация
                query = recognizer.transcribe(audio) if audio else ""

                if query:
                    print(f"📝 Распознано: {query}")

                # Проверяем команды активации/деактивации
                if activator.check_activation(query):
                    continue

                # Если активен, но команда пустая
                if not query or len(query.strip()) < 2:
                    print("❌ Не удалось распознать речь")
                    continue

                # Обработка через LLM
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

                    # Выполнение музыкальной команды
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
                    tts.speak("Извините, я не понял команду")
                    print("❓ Неизвестная команда")

                print("\n" + "=" * 50)
                if activator.is_active:
                    print("🎯 АКТИВНЫЙ РЕЖИМ - жду следующую команду")
                    print("💤 Скажите 'спать' для выхода из активного режима")
                print("=" * 50 + "\n")

            except KeyboardInterrupt:
                print("\n👋 Выключаю колонку...")
                activator.stop_wake_word_detection()
                tts.speak("Выключаюсь, до свидания!")
                break
            except Exception as e:
                print(f"❌ Ошибка в основном цикле: {e}")
                time.sleep(1)

    except Exception as e:
        print(f"❌ Критическая ошибка инициализации: {e}")


if __name__ == "__main__":
    main()