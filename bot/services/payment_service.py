from __future__ import annotations

import json

from aiogram import Bot
from aiogram.types import LabeledPrice

_READING_AMOUNT = 69  # Telegram Stars


async def create_reading_invoice(
    bot: Bot,
    user_id: int,
    execution_id: str,
) -> None:
    """Send Telegram Stars invoice. payload = OrderPayload JSON."""
    payload = json.dumps(
        {"user_id": user_id, "execution_id": execution_id, "amount": _READING_AMOUNT}
    )
    prices = [LabeledPrice(label="🔮 Полное чтение судьбы (3 карты + интерпретация)", amount=_READING_AMOUNT)]
    await bot.send_invoice(
        chat_id=user_id,
        title="🔮 Полное чтение судьбы",
        description="Прошлое • Настоящее • Будущее + персональная интерпретация от оракула",
        payload=payload,
        provider_token="",
        currency="XTR",
        prices=prices,
        start_parameter="tarot-reading",
    )
