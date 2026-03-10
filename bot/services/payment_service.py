# bot/services/payment_service.py
from aiogram.types import LabeledPrice

async def create_reading_invoice(bot, user_id: int):
    prices = [LabeledPrice(label="Полное гадание на 3 карты", amount=69)]
    
    return await bot.send_invoice(
        chat_id=user_id,
        title="🔮 Полное чтение судьбы",
        description="Три карты + глубокая интерпретация от мистического оракула",
        payload=f"reading_{user_id}",
        provider_token="",           # пусто = Telegram Stars
        currency="XTR",
        prices=prices
    )
