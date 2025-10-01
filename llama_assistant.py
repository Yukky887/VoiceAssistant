import json
import ollama
import re


class LlamaAssistant:
    def __init__(self, model="qwen2.5:7b-instruct"):
        self.model = model
        self.music_system_prompt = """
Ты — классификатор команд для голосового ассистента. Твоя задача — определить тип запроса пользователя и вернуть ТОЛЬКО JSON.

Доступные действия:
- "play" - включить конкретный трек (пример: "включи трек Shape of You")
- "playlist" - включить плейлист/жанр (пример: "включи рок музыку")  
- "favorites" - включить любимые треки (пример: "включи мои любимые треки")
- "pause" - пауза (пример: "пауза")
- "resume" - продолжить (пример: "продолжи")
- "next" - следующий трек (пример: "следующий трек")
- "previous" - предыдущий трек (пример: "предыдущий")
- "volume" - изменить громкость (пример: "громче")
- "question" - общий вопрос НЕ о музыке (пример: "сколько будет 2+2", "расскажи о космосе")
- "none" - непонятная команда

ВОЗВРАЩАЙ ТОЛЬКО JSON БЕЗ ЛЮБОГО ДРУГОГО ТЕКСТА!

Формат JSON:
{"action": "тип_действия", "track": "название_трека", "artist": "исполнитель", "playlist": "название_плейлиста", "level": "уровень_громкости", "query": "оригинальный_вопрос"}

Примеры:
"включи shape of you эда ширана" -> {"action": "play", "track": "Shape of You", "artist": "Ed Sheeran"}
"поставь рок музыку" -> {"action": "playlist", "playlist": "Rock"}
"сколько времени" -> {"action": "question", "query": "сколько времени"}
"пауза" -> {"action": "pause"}
"громче" -> {"action": "volume", "level": "up"}
"включи мои треки" -> {"action": "favorites"}

Запрос пользователя: "{query}"
"""

        self.qa_system_prompt = """
Ты — полезный голосовой ассистент Джа́рвис. Отвечай на вопросы пользователя КРАТКО и ПОНЯТНО на РУССКОМ ЯЗЫКЕ.

ОЧЕНЬ ВАЖНЫЕ ПРАВИЛА:
1. Отвечай ТОЛЬКО на РУССКОМ языке
2. НИКОГДА не используй китайские, английские или другие иностранные языки в ответе
3. Будь максимально кратким (1-2 предложения)
4. Говори естественно, как в разговоре
5. Если не знаешь точного ответа, честно скажи об этом на русском

Примеры хороших ответов:
Вопрос: "Сколько будет 2+2?"
Ответ: "Два плюс два будет четыре"

Вопрос: "Какая сегодня погода?"
Ответ: "К сожалению, я не могу узнать текущую погоду, но вы можете проверить это в погодном приложении"

Вопрос: "Расскажи о космосе"
Ответ: "Космос — это бескрайнее пространство со звездами, планетами и галактиками. Наша Солнечная система находится в галактике Млечный Путь"

Вопрос: "Сколько весит слон?"
Ответ: "Взрослый африканский слон весит от 4 до 7 тонн, а индийский слон — от 3 до 5 тонн"

Теперь ответь на вопрос: "{query}"
"""

    def clean_transcription(self, text):
        """Очистка и улучшение транскрипции"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def extract_json_from_response(self, content):
        """Извлекает JSON из ответа модели"""
        try:
            # Пробуем найти JSON в ответе
            json_match = re.search(r'\{[^{}]*\}', content)
            if json_match:
                json_str = json_match.group()
                return json.loads(json_str)
            else:
                # Если JSON не найден, пробуем распарсить весь ответ как JSON
                return json.loads(content)
        except json.JSONDecodeError:
            # Если это не JSON, анализируем текст чтобы определить действие
            content_lower = content.lower()

            # Проверяем, похоже ли на вопрос
            question_indicators = ['сколько', 'что', 'кто', 'как', 'почему', 'зачем', 'расскажи', 'объясни']
            if any(indicator in content_lower for indicator in question_indicators):
                return {"action": "question", "query": content}

            # Проверяем музыкальные команды
            music_commands = {
                'пауза': 'pause',
                'стоп': 'pause',
                'продолжи': 'resume',
                'дальше': 'next',
                'следующий': 'next',
                'предыдущий': 'previous',
                'назад': 'previous',
                'громче': 'volume',
                'тише': 'volume',
                'любимые': 'favorites',
                'мои треки': 'favorites'
            }

            for ru_command, action in music_commands.items():
                if ru_command in content_lower:
                    if action == 'volume':
                        level = 'up' if 'громче' in content_lower else 'down'
                        return {"action": "volume", "level": level}
                    return {"action": action}

            # Если содержит слова про включение музыки
            if any(word in content_lower for word in ['включи', 'поставь', 'запусти']):
                if 'плейлист' in content_lower or 'музык' in content_lower:
                    return {"action": "playlist", "playlist": "Popular"}
                else:
                    return {"action": "play", "track": "Unknown", "artist": ""}

            return {"action": "none"}

    def classify_intent(self, query: str) -> dict:
        """Классифицирует намерение пользователя"""
        try:
            formatted_prompt = self.music_system_prompt.replace("{query}", query)

            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": formatted_prompt},
                    {"role": "user", "content": query}
                ],
                options={
                    'temperature': 0.1
                }
            )

            content = response["message"]["content"].strip()
            print(f"📨 Сырой ответ классификации: {content}")

            return self.extract_json_from_response(content)

        except Exception as e:
            print(f"❌ Ошибка классификации: {e}")
            return {"action": "none"}

    def clean_russian_response(self, text: str) -> str:
        """Очищает ответ, оставляя только русский текст"""
        # Удаляем китайские символы
        text = re.sub(r'[\u4e00-\u9fff]+', '', text)
        # Удаляем английские инструкции
        text = re.sub(r'Note:.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Example:.*', '', text, flags=re.IGNORECASE)
        text = re.sub(r'Answer:.*', '', text, flags=re.IGNORECASE)
        # Удаляем код и форматирование
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        text = re.sub(r'`.*?`', '', text)
        # Удаляем номерованные списки на английском
        text = re.sub(r'\d+\.\s*[A-Za-z].*', '', text)
        # Удаляем лишние пробелы
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def answer_question(self, query: str) -> str:
        """Отвечает на общие вопросы ТОЛЬКО на русском"""
        try:
            # Добавляем строгое ограничение по языку
            strict_prompt = f"""
ТЫ ДОЛЖЕН ОТВЕЧАТЬ ТОЛЬКО НА РУССКОМ ЯЗЫКЕ!
НЕ ИСПОЛЬЗУЙ КИТАЙСКИЙ, АНГЛИЙСКИЙ ИЛИ ДРУГИЕ ЯЗЫКИ!
ОТВЕТ ДОЛЖЕН БЫТЬ КРАТКИМ (1-2 предложения) И ПОНЯТНЫМ.

Вопрос: {query}

Русский ответ:"""

            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Ты — русскоязычный ассистент. ВСЕГДА отвечай только на русском языке. НИКОГДА не используй другие языки."
                    },
                    {"role": "user", "content": strict_prompt}
                ],
                options={
                    'temperature': 0.3,
                    'top_p': 0.9
                }
            )

            answer = response["message"]["content"].strip()

            # Очищаем ответ от любых не-русских вкраплений
            answer = self.clean_russian_response(answer)

            # Если ответ пустой после очистки, возвращаем стандартный ответ
            if not answer:
                answer = "Извините, я не могу ответить на этот вопрос прямо сейчас."

            print(f"🤖 Ответ на вопрос: {answer}")
            return answer

        except Exception as e:
            print(f"❌ Ошибка генерации ответа: {e}")
            return "Извините, произошла ошибка при обработке вашего вопроса"

    def ask(self, query: str) -> dict:
        cleaned_query = self.clean_transcription(query)
        print(f"🧹 Очищенный запрос: {cleaned_query}")

        if not cleaned_query:
            return {"action": "none"}

        # Сначала классифицируем намерение
        intent = self.classify_intent(cleaned_query)

        # Если это вопрос, получаем ответ
        if intent.get("action") == "question":
            question_text = intent.get("query", cleaned_query)
            answer = self.answer_question(question_text)
            intent["answer"] = answer

        return intent