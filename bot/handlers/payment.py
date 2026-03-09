from aiogram.filters import Command
from aiogram import Router
from aiogram.types import Message, PreCheckoutQuery

router = Router()


@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):

    await pre_checkout_query.answer(ok=True)


@router.message()
async def success(message: Message):

    await message.answer(
        "Payment successful. Your destiny is revealed 🔮"
    )
