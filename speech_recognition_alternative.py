import speech_recognition as sr


class SpeechRecognizer:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()

        # Калибруем микрофон для уменьшения шума
        print("Калибрую микрофон...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        print("Микрофон откалиброван!")

    def listen(self, duration=5):
        print("Слушаю...")

        try:
            with self.microphone as source:
                # Записываем аудио
                audio = self.recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
            print("Запись завершена")
            return audio
        except sr.WaitTimeoutError:
            print("Время ожидания истекло")
            return None

    def transcribe(self, audio):
        """Транскрибируем аудио с помощью Google Speech Recognition"""
        if audio is None:
            return ""

        try:
            text = self.recognizer.recognize_google(audio, language="ru-RU")
            return text.strip()
        except sr.UnknownValueError:
            print("Не удалось распознать речь")
            return ""
        except sr.RequestError as e:
            print(f"Ошибка сервиса распознавания: {e}")
            return ""