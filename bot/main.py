# bot/main.py
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode

from bot.config import TELEGRAM_TOKEN
from bot.database import init_db
from bot.handlers import admin, history, payment, referral, showcase, start, tarot


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    session = AiohttpSession(timeout=60)
    bot = Bot(
        token=TELEGRAM_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
        session=session,
    )

    dp = Dispatcher()

    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(history.router)
    dp.include_router(showcase.router)
    dp.include_router(tarot.router)
    dp.include_router(payment.router)
    dp.include_router(referral.router)

    await init_db()
    print("Bot started")
    await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")
