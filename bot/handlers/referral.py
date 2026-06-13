from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.i18n import lang_from_user, t

router = Router()


@router.message(Command("invite"))
async def invite(message: Message) -> None:
    if not message.from_user or not message.bot:
        return

    lang = lang_from_user(message.from_user)
    user_id = message.from_user.id
    bot_info = await message.bot.get_me()
    link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    await message.answer(t("invite_text", lang, link=link))
