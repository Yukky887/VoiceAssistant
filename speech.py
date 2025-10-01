import json
import wave
import sounddevice as sd
import numpy as np
from vosk import Model, KaldiRecognizer
import os


class SpeechRecognizer:
    def __init__(self, model_path="models/vosk-model-ru-0.42"):

        # Проверяем существует ли модель
        if not os.path.exists(model_path):
            raise Exception(f"Модель Vosk не найдена по пути: {model_path}")

        self.model = Model(model_path)
        self.sample_rate = 16000

    def listen(self, duration=5):

        print("Слушаю...")

        # Записываем аудио
        audio = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype='int16'
        )
        sd.wait()
        print("Запись завершена")
        return audio.flatten()

    def transcribe(self, audio_data):
        recognizer = KaldiRecognizer(self.model, self.sample_rate)
        recognizer.SetWords(True)

        # Конвертируем в bytes
        audio_bytes = audio_data.tobytes()

        # Процессим аудио chunks
        chunk_size = 4000
        for i in range(0, len(audio_bytes), chunk_size):
            chunk = audio_bytes[i:i + chunk_size]
            if len(chunk) == 0:
                break
            if recognizer.AcceptWaveform(chunk):
                pass

        # Получаем финальный результат
        result = recognizer.FinalResult()
        result_json = json.loads(result)

        return result_json.get("text", "").strip()