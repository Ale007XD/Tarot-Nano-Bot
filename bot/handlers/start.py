from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.database import add_referral, add_user
from bot.i18n import lang_from_user, t
from bot.keyboards import start_kb

router = Router()


@router.message(Command("start"))
async def start(message: Message) -> None:
    if not message.from_user:
        return

    lang = lang_from_user(message.from_user)
    args = message.text.split() if message.text else []
    ref: int | None = None

    if len(args) > 1 and args[1].startswith("ref_"):
        ref = int(args[1].replace("ref_", ""))

    await add_user(message.from_user.id, message.from_user.username, ref)

    if ref:
        await add_referral(ref, message.from_user.id)

    await message.answer(t("welcome", lang), reply_markup=start_kb(lang))
