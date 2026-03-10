from aiogram import Router
from aiogram.types import Message, PreCheckoutQuery, SuccessfulPayment
from bot.handlers.tarot import process_reading  # импортируем

router = Router()

@router.pre_checkout_query()
async def pre_checkout(pre: PreCheckoutQuery):
    await pre.answer(ok=True)

@router.message(lambda m: m.successful_payment)
async def success_payment(message: Message):
    await message.answer("✅ Оплата прошла! Готовы узнать судьбу?")
    await process_reading(message, paid=1)  # paid=1
