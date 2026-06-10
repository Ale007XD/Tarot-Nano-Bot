from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from bot.keyboards import start_kb

from bot.database import add_referral, add_user

router = Router()


@router.message(Command("start"))
async def start(message: Message) -> None:
    if not message.from_user:
        return

    args = message.text.split() if message.text else []
    ref: int | None = None

    if len(args) > 1 and args[1].startswith("ref_"):
        ref = int(args[1].replace("ref_", ""))

    await add_user(message.from_user.id, message.from_user.username, ref)

    if ref:
        await add_referral(ref, message.from_user.id)

    text = """
🔮 Welcome to Destiny Oracle

Draw your tarot card and reveal
what fate prepared for you today.
"""
    await message.answer(text, reply_markup=start_kb())
