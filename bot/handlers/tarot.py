from aiogram.filters import Command
from aiogram import Router
from aiogram.types import CallbackQuery
from bot.services.tarot_engine import draw_card, draw_spread
from bot.services.llm_service import generate_reading
from bot.keyboards import paywall_kb, share_kb

router = Router()

partial_cards = {}


@router.callback_query(lambda c: c.data == "draw")
async def draw(callback: CallbackQuery):

    card = draw_card()

    partial_cards[callback.from_user.id] = card

    text = f"""
You drew:

🔮 {card}

This card reveals only part of the message.

Two more cards complete the destiny spread.
"""

    await callback.message.answer(text, reply_markup=paywall_kb())


@router.callback_query(lambda c: c.data == "buy")
async def buy(callback: CallbackQuery):

    spread = draw_spread()

    cards = "\n".join(
        [f"{pos}: {card}" for pos, card in spread]
    )

    interpretation = await generate_reading(cards)

    text = f"""
🔮 Your Destiny Reading

{cards}

{interpretation}
"""

    await callback.message.answer(text, reply_markup=share_kb())
