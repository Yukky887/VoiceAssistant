# voice_processor.py
import webrtcvad
import pvporcupine
import pvcheetah
import pyaudio
import numpy as np
import threading
import time
import queue
from Levenshtein import distance as lev_distance
import speech_recognition as sr


class VoiceProcessor:
    def __init__(self, wake_words=["джарвис", "jarvis"], sensitivity=0.7):
        self.vad = webrtcvad.Vad(2)  # Средний режим
        self.sample_rate = 16000
        self.frame_duration = 30  # ms
        self.frame_size = int(self.sample_rate * self.frame_duration / 1000)

        # Инициализация Porcupine для английского wake word
        try:
            self.porcupine = pvporcupine.create(
                access_key="Uik+LoHMAJvsWvBX+VlvnqdwNzdAdDy3u6buANhykdyT0UZ/AnNnmw==",  # Ваш ключ
                keywords=["jarvis"]  # Английская версия
            )
            self.use_porcupine = True
            print("✅ Porcupine инициализирован для 'jarvis'")
        except Exception as e:
            print(f"⚠️ Porcupine не инициализирован: {e}")
            self.use_porcupine = False

        # Для русского wake word используем распознавание
        self.wake_words = [w.lower() for w in wake_words]
        self.sensitivity = sensitivity
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.callback = None

        # Для русского распознавания
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Настройка аудио потока
        self.audio = pyaudio.PyAudio()
        self.stream = None

        # Буфер для русского распознавания
        self.speech_buffer = b""
        self.speech_timeout = 0

    def start_listening(self, callback):
        """Запускает прослушивание в фоновом режиме"""
        self.callback = callback
        self.is_listening = True

        # Калибруем микрофон для русского распознавания
        print("🔧 Калибрую микрофон для русского распознавания...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

        # Запускаем поток для обработки аудио
        self.process_thread = threading.Thread(target=self._process_audio)
        self.process_thread.daemon = True
        self.process_thread.start()

        # Запускаем поток для записи аудио
        self.record_thread = threading.Thread(target=self._record_audio)
        self.record_thread.daemon = True
        self.record_thread.start()

        print("🎯 Голосовой процессор запущен (русский + английский wake words)")

    def stop_listening(self):
        """Останавливает прослушивание"""
        self.is_listening = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.audio:
            self.audio.terminate()

    def _record_audio(self):
        """Записывает аудио в отдельном потоке"""
        try:
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.frame_size,
                stream_callback=self._audio_callback
            )
            self.stream.start_stream()

            print("🎤 Аудио поток запущен...")

            while self.stream.is_active() and self.is_listening:
                time.sleep(0.1)

        except Exception as e:
            print(f"❌ Ошибка записи аудио: {e}")

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback для аудио потока"""
        self.audio_queue.put(in_data)
        return (in_data, pyaudio.paContinue)

    def _process_audio(self):
        """Обрабатывает аудио данные для wake word detection"""
        consecutive_speech = 0
        audio_chunks = []

        print("🔄 Начинаю обработку аудио...")

        while self.is_listening:
            try:
                # Получаем аудио данные из очереди
                frame = self.audio_queue.get(timeout=0.5)

                # 1. Проверяем английское wake word через Porcupine
                if self.use_porcupine:
                    pcm = np.frombuffer(frame, dtype=np.int16)
                    keyword_index = self.porcupine.process(pcm)
                    if keyword_index >= 0:
                        print("🎯 Английское wake word 'jarvis' обнаружено!")
                        if self.callback:
                            self.callback("wake_word_detected")
                        continue

                # 2. Проверяем VAD для русского распознавания
                is_speech = self.vad.is_speech(frame, self.sample_rate)

                if is_speech:
                    consecutive_speech += 1
                    audio_chunks.append(frame)

                    # Если накопили достаточно речи, пробуем распознать
                    if consecutive_speech >= 10:  # ~300ms речи
                        audio_data = b''.join(audio_chunks)
                        text = self._speech_to_text(audio_data)
                        if text and self._check_russian_wake_word(text):
                            print(f"🎯 Русское wake word обнаружено: {text}")
                            if self.callback:
                                self.callback("wake_word_detected")
                            audio_chunks = []
                            consecutive_speech = 0
                else:
                    # Сброс при тишине
                    if consecutive_speech > 0:
                        consecutive_speech -= 1
                    if consecutive_speech <= 0:
                        audio_chunks = []
                        consecutive_speech = 0

            except queue.Empty:
                continue
            except Exception as e:
                print(f"❌ Ошибка обработки аудио: {e}")
                time.sleep(0.1)

    def _speech_to_text(self, audio_data):
        """Конвертирует аудио в текст для русского wake word"""
        try:
            # Создаем AudioData объект для speech_recognition
            audio = sr.AudioData(audio_data, self.sample_rate, 2)
            text = self.recognizer.recognize_google(audio, language="ru-RU")
            return text.lower().strip()
        except sr.UnknownValueError:
            return None
        except Exception as e:
            return None

    def _check_russian_wake_word(self, text):
        """Проверяет русское wake word с помощью расстояния Левенштейна"""
        if not text:
            return False

        for wake_word in self.wake_words:
            # Простая проверка вхождения
            if wake_word in text:
                return True

            # Проверка расстояния Левенштейна для опечаток
            words = text.split()
            for word in words:
                dist = lev_distance(wake_word, word)
                max_allowed_distance = max(1, len(wake_word) // 3)
                if dist <= max_allowed_distance:
                    print(f"✅ Русское wake word '{wake_word}' обнаружено (расстояние: {dist})")
                    return True

        return False