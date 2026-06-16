# bot/main.py
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats

from bot.config import TELEGRAM_TOKEN
from bot.database import init_db
from bot.handlers import admin, history, payment, referral, share, showcase, start, tarot


_USER_COMMANDS_RU = [
    BotCommand(command="start", description="Главное меню"),
    BotCommand(command="draw", description="🃏 Карта дня"),
    BotCommand(command="full_reading", description="🔮 Полный расклад"),
    BotCommand(command="history", description="📜 История раскладов"),
    BotCommand(command="my_traces", description="🔗 Мои трейсы (nano-vm)"),
    BotCommand(command="verify", description="✅ Проверить расклад по хэшу"),
    BotCommand(command="trace", description="🔬 Посмотреть FSM-трейс расклада"),
    BotCommand(command="invite", description="🎁 Пригласить друга"),
]

_USER_COMMANDS_EN = [
    BotCommand(command="start", description="Main menu"),
    BotCommand(command="draw", description="🃏 Card of the day"),
    BotCommand(command="full_reading", description="🔮 Full reading"),
    BotCommand(command="history", description="📜 Reading history"),
    BotCommand(command="my_traces", description="🔗 My traces (nano-vm)"),
    BotCommand(command="verify", description="✅ Verify reading by hash"),
    BotCommand(command="trace", description="🔬 View FSM trace for a reading"),
    BotCommand(command="invite", description="🎁 Invite a friend"),
]


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
    dp.include_router(share.router)
    dp.include_router(tarot.router)
    dp.include_router(payment.router)
    dp.include_router(referral.router)

    await init_db()

    # Register slash commands in Telegram menu
    await bot.set_my_commands(_USER_COMMANDS_RU, scope=BotCommandScopeAllPrivateChats(), language_code="ru")
    await bot.set_my_commands(_USER_COMMANDS_EN, scope=BotCommandScopeAllPrivateChats())

    print("Bot started")
    await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped")
