# bot/handlers/payment.py
from aiogram import Router
from aiogram.types import Message, PreCheckoutQuery

# Импортируем обновлённую функцию из Шага 3+4
from bot.handlers.tarot import process_reading

router = Router()


@router.pre_checkout_query()
async def pre_checkout(pre: PreCheckoutQuery):
    """Подтверждаем, что оплата возможна (Telegram Stars)"""
    await pre.answer(ok=True)


@router.message(lambda m: m.successful_payment is not None)
async def success_payment(message: Message):
    """Пользователь успешно оплатил через Telegram Stars"""
    await message.answer("✅ Оплата прошла успешно! 🔮")

    # Запускаем генерацию полного чтения
    await process_reading(message, paid=1)
