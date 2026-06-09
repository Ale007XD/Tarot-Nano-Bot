import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Основные токены
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

# ID администратора для доступа к админ-панели
# Если переменная не задана в .env, устанавливаем 0, чтобы админ-функции не сработали
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Ключи для LLM
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Настройки LLM
USE_OPENROUTER = os.getenv("USE_OPENROUTER", "true").lower() == "true"

# Путь к БД
DB_PATH = "tarot.db"

# Валидация критических переменных (опционально, но полезно для отладки)
if not TELEGRAM_TOKEN:
    raise ValueError("❌ Ошибка: TELEGRAM_TOKEN не найден в .env файле!")
