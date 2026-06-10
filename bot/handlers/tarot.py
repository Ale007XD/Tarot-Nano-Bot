"""Tarot handler — deterministic Card of the Day."""

from __future__ import annotations

import datetime
import hashlib

from aiogram import Router
from aiogram.types import CallbackQuery
from bot.keyboards import paywall_kb, share_kb
from bot.services.payment_service import create_reading_invoice
from bot.services.tarot_engine import draw_spread
from pydantic import BaseModel, Field

from bot.database import decrement_free_spreads, get_user, save_reading
from bot.services.llm_service import generate_reading

try:
    from bot.config import TAROT_SALT as SALT
except ImportError:
    SALT = "NANO_VM_CRYPTO_DETERMINISTIC_SECURE_SALT_2026"

router = Router()

partial_cards: dict[int, str] = {}

TAROT_POOL: list[str] = [
    "The Fool",
    "The Magician",
    "The High Priestess",
    "The Empress",
    "The Emperor",
    "The Hierophant",
    "The Lovers",
    "The Chariot",
    "Strength",
    "The Hermit",
    "Wheel of Fortune",
    "Justice",
    "The Hanged Man",
    "Death",
    "Temperance",
    "The Devil",
    "The Tower",
    "The Star",
    "The Moon",
    "The Sun",
    "Judgement",
    "The World",
] + [f"Minor Arcana Card #{i}" for i in range(22, 78)]


class ProviderResponse(BaseModel):
    card_id: int = Field(..., ge=0, lt=78)
    card_name: str
    interpretation: str
    execution_date: str


def calculate_deterministic_card(user_id: int, current_date: str, salt: str) -> int:
    payload = f"{user_id}:{current_date}:{salt}".encode()
    return int(hashlib.sha256(payload).hexdigest(), 16) % 78


@router.callback_query(lambda c: c.data == "draw")
async def draw(callback: CallbackQuery) -> None:
    if not callback.from_user or not callback.message:
        return

    user_id = callback.from_user.id
    current_date = datetime.date.today().isoformat()

    card_id = calculate_deterministic_card(user_id, current_date, SALT)
    card_name = TAROT_POOL[card_id]
    interpretation = f"Детерминированное состояние {card_name} для сессии {user_id}."

    response = ProviderResponse(
        card_id=card_id,
        card_name=card_name,
        interpretation=interpretation,
        execution_date=current_date,
    )

    partial_cards[user_id] = response.card_name

    await save_reading(
        user_id=user_id,
        spread="card_of_the_day",
        cards=response.card_name,
        interpretation=response.interpretation,
        paid=0,
    )

    text = (
        f"🔮 **Вы вытянули карту дня**\n\n"
        f"**{response.card_name}** (ID: {response.card_id})\n\n"
        f"Это только **часть** послания Вселенной.\n\n"
        f"Чтобы узнать **полную картину** (прошлое • настоящее • будущее"
        f" + глубокая интерпретация) — нажмите кнопку ниже."
    )

    await callback.message.answer(text, reply_markup=paywall_kb())
    await callback.answer()


@router.callback_query(lambda c: c.data == "full_reading")
async def full_reading(callback: CallbackQuery) -> None:
    if not callback.from_user or not callback.message or not callback.bot:
        return

    user_id = callback.from_user.id
    user = await get_user(user_id)

    if user and user[3] > 0:
        await decrement_free_spreads(user_id)
        spread = draw_spread()
        cards_text = "\n".join(f"{pos}: {card}" for pos, card in spread)
        interpretation = await generate_reading(cards_text)

        await save_reading(
            user_id=user_id,
            spread="past_present_future",
            cards=cards_text,
            interpretation=interpretation,
            paid=0,
        )

        await callback.message.answer(
            f"🔮 **Полный расклад (бесплатный)**\n\n{cards_text}\n\n{interpretation}",
            reply_markup=share_kb(),
        )
    else:
        await create_reading_invoice(callback.bot, user_id)

    await callback.answer()
