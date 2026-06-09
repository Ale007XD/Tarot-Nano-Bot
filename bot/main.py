# bot/main.py
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import TELEGRAM_TOKEN
from bot.database import init_db

# Импортируем все хендлеры, включая admin и новый history слой
from bot.handlers import admin, history, payment, referral, start, tarot


async def main():
    # Настройка логирования (поможет видеть ошибки админки в консоли)
    logging.basicConfig(level=logging.INFO)

    # Инициализация бота с поддержкой Markdown/HTML по умолчанию
    bot = Bot(
        token=TELEGRAM_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )

    dp = Dispatcher()

    # Регистрация роутеров
    # Админку лучше ставить выше остальных
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(history.router)  # Подключение History Layer (Sprint-0)
    dp.include_router(tarot.router)
    dp.include_router(payment.router)
    dp.include_router(referral.router)

    # Инициализация базы данных
    await init_db()

    print("Bot started")

    # Запуск поллинга
    await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")
