from __future__ import annotations

from aiogram import Bot
from aiogram.types import LabeledPrice


async def create_reading_invoice(bot: Bot, user_id: int) -> None:
    import time
    prices = [LabeledPrice(label="🔮 Полное чтение судьбы (3 карты + интерпретация)", amount=69)]
    await bot.send_invoice(
        chat_id=user_id,
        title="🔮 Полное чтение судьбы",
        description="Прошлое • Настоящее • Будущее + персональная интерпретация от оракула",
        payload=f"reading_{user_id}_{int(time.time())}",
        provider_token="",
        currency="XTR",
        prices=prices,
        start_parameter="tarot-reading",
    )
