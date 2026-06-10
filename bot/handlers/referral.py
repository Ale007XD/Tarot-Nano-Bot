from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("invite"))
async def invite(message: Message) -> None:
    if not message.from_user or not message.bot:
        return
    user_id = message.from_user.id
    bot_info = await message.bot.get_me()
    link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    await message.answer(f"Invite friends and get free readings:\n\n{link}")
