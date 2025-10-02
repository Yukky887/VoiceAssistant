# speech_recognition_alternative.py
import speech_recognition as sr
import threading
import time
import numpy as np
from voice_processor import SimpleVAD


class SpeechRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.vad = SimpleVAD()
        self.is_recording = False

        # Калибруем микрофон
        print("🔧 Калибрую микрофон...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("✅ Микрофон откалиброван!")

    def listen_with_vad(self, timeout=10, phrase_time_limit=7):
        """Слушает с Voice Activity Detection"""
        print("🎤 Слушаю с VAD...")

        start_time = time.time()
        audio_data = None

        def record_callback(recognizer, audio):
            nonlocal audio_data
            audio_data = audio

        # Начинаем слушать в фоне
        stop_listening = self.recognizer.listen_in_background(
            self.microphone,
            record_callback,
            phrase_time_limit=phrase_time_limit
        )

        # Ждем голосовой активности или таймаута
        while time.time() - start_time < timeout:
            if audio_data is not None:
                stop_listening(wait_for_stop=False)
                print("✅ Речь обнаружена!")
                return audio_data
            time.sleep(0.1)

        stop_listening(wait_for_stop=False)
        print("❌ Время ожидания истекло")
        return None

    def listen(self, duration=5):
        """Обычное прослушивание (для обратной совместимости)"""
        print("🎤 Слушаю...")

        try:
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source,
                    timeout=duration,
                    phrase_time_limit=duration
                )
            print("✅ Запись завершена")
            return audio
        except sr.WaitTimeoutError:
            print("❌ Время ожидания истекло")
            return None

    def transcribe(self, audio):
        """Транскрибируем аудио"""
        if audio is None:
            return ""

        try:
            text = self.recognizer.recognize_google(audio, language="ru-RU")
            return text.strip()
        except sr.UnknownValueError:
            print("❌ Не удалось распознать речь")
            return ""
        except sr.RequestError as e:
            print(f"❌ Ошибка сервиса распознавания: {e}")
            return ""