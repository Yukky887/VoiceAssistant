import whisper
import sounddevice as sd
import numpy as np

class SpeechRecognizer:
    def __init__(self, model_name="base"):
        self.model = whisper.load_model(model_name)

    def listen(self, duration=5, fs=16000):
        print("🎤 Скажи что-нибудь...")
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
        sd.wait()
        return np.squeeze(audio)

    def transcribe(self, audio, language="ru"):
        result = self.model.transcribe(audio, fp16=False, language=language)
        return result["text"].strip()