from gtts import gTTS
import pygame
import io
import threading
import time
import os


class VoiceSynthesizer:
    def __init__(self):
        pygame.mixer.init()
        self.is_speaking = False

    def speak(self, text):
        """Произносит текст с помощью Google TTS"""
        if not text:
            return

        self.is_speaking = True
        print(f"🔊 Озвучиваю: {text}")

        try:
            # Создаем аудио в памяти
            tts = gTTS(text=text, lang='ru', slow=False)
            audio_file = io.BytesIO()
            tts.write_to_fp(audio_file)
            audio_file.seek(0)

            # Воспроизводим
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()

            # Ждем окончания воспроизведения
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)

        except Exception as e:
            print(f"❌ Ошибка синтеза речи: {e}")
        finally:
            self.is_speaking = False

    def speak_async(self, text):
        """Произносит текст в отдельном потоке"""
        if not text:
            return

        def _speak():
            self.speak(text)

        thread = threading.Thread(target=_speak, daemon=True)
        thread.start()

    def stop(self):
        """Останавливает речь"""
        try:
            pygame.mixer.music.stop()
        except:
            pass


# Глобальный экземпляр
tts = VoiceSynthesizer()