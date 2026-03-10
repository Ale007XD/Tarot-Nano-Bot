# bot/services/payment_service.py
from aiogram.types import LabeledPrice


async def create_reading_invoice(bot, user_id: int):
    """Создаём счёт на 69 Telegram Stars (0% комиссии)"""
    prices = [
        LabeledPrice(
            label="🔮 Полное чтение судьбы (3 карты + интерпретация)",
            amount=69
        )
    ]

    await bot.send_invoice(
        chat_id=user_id,
        title="🔮 Полное чтение судьбы",
        description="Прошлое • Настоящее • Будущее + персональная интерпретация от оракула",
        payload=f"reading_{user_id}_{int(__import__('time').time())}",  # уникальный payload
        provider_token="",                    # пусто = Telegram Stars
        currency="XTR",
        prices=prices,
        start_parameter="tarot-reading"
    )
