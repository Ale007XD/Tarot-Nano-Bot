import asyncio

from aiogram import Bot, Dispatcher

from bot.config import TELEGRAM_TOKEN
from bot.database import init_db

from bot.handlers import start, tarot, payment, referral


async def main():

    bot = Bot(TELEGRAM_TOKEN)

    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(tarot.router)
    dp.include_router(payment.router)
    dp.include_router(referral.router)

    await init_db()

    print("Bot started")

    await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":

    asyncio.run(main())
