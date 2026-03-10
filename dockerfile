FROM python:3.12-slim

# Отключаем буферизацию логов, чтобы сразу видеть их в консоли
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Устанавливаем системные зависимости (если в будущем добавишь библиотеки для графиков или БД)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Создаем пустые файлы, чтобы монтирование Volume прошло корректно
RUN touch tarot.db bot.log

# Запуск бота через модуль
CMD ["python", "-m", "bot.main"]

