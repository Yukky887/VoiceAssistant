import speech_recognition as sr
import threading
import time

class VoiceActivator:
    def __init__(self, activation_phrase="джарвис", deactivation_phrase="спать"):
        self.activation_phrase = activation_phrase.lower()
        self.deactivation_phrase = deactivation_phrase.lower()
        self.is_active = False
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.listening = False

        # Калибруем микрофон
        print("Калибрую микрофон для активации...")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        print("Микрофон откалиброван!")

    def listen_for_activation(self):
        self.listening = True
        print(f"Ожидаю кодовое слово '{self.activation_phrase}'...")

        while self.listening:
            try:
                with self.microphone as source:
                    # Слушаем короткие фразы для активации
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=3)

                text = self.recognizer.recognize_google(audio, language="ru-RU").lower()
                print(f"Услышано: {text}")

                if self.activation_phrase in text and not self.is_active:
                    self.is_active = True
                    print(f"АКТИВИРОВАН! Кодовое слово '{self.activation_phrase}' распознано")
                    return True

                elif self.deactivation_phrase in text and self.is_active:
                    self.is_active = False
                    print(f"ДЕАКТИВИРОВАН! Команда '{self.deactivation_phrase}' распознана")

            except sr.WaitTimeoutError:
                # Таймаут - это нормально, продолжаем слушать
                continue
            except sr.UnknownValueError:
                # Не распознано - продолжаем
                continue
            except Exception as e:
                print(f"Ошибка в активаторе: {e}")
                time.sleep(0.1)

        return False

    def start_listening(self):
        """Запускает фоновое прослушивание для активации"""
        thread = threading.Thread(target=self.listen_for_activation, daemon=True)
        thread.start()

    def stop_listening(self):
        """Останавливает прослушивание"""
        self.listening = False

    def wait_for_activation(self):
        """Блокирующее ожидание активации"""
        return self.listen_for_activation()