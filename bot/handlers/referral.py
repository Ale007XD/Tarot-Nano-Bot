from aiogram.filters import Command
from aiogram import Router
from aiogram.types import Message

router = Router()


@router.message(Command("invite"))
async def invite(message: Message):

    user_id = message.from_user.id

    link = f"https://t.me/{(await message.bot.get_me()).username}?start=ref_{user_id}"

    await message.answer(f"Invite friends and get free readings:\n\n{link}")
