# bot/handlers/tarot.py
from aiogram import Router
from aiogram.types import CallbackQuery

from bot.services.tarot_engine import draw_card, draw_spread
from bot.services.llm_service import generate_reading
from bot.services.payment_service import create_reading_invoice
from bot.database import get_user, decrement_free_spreads, save_reading
from bot.keyboards import paywall_kb, share_kb

router = Router()

# Храним частичную карту (для будущего улучшения — сейчас не используется, но оставил)
partial_cards = {}


@router.callback_query(lambda c: c.data == "draw")
async def draw(callback: CallbackQuery):
    """Пользователь нажал «🔮 Draw my card» — показываем одну карту бесплатно"""
    card = draw_card()
    partial_cards[callback.from_user.id] = card

    text = f"""
🔮 Вы вытянули карту:

**{card}**

Это только **часть** послания Вселенной.

Чтобы узнать **полную картину** (прошлое • настоящее • будущее + глубокая интерпретация) — нажмите кнопку ниже.
"""

    await callback.message.answer(text, reply_markup=paywall_kb())


@router.callback_query(lambda c: c.data == "buy")
async def buy(callback: CallbackQuery):
    """Главная точка монетизации"""
    user = await get_user(callback.from_user.id)
    free_spreads = user[3] if user else 0  # free_spreads — 4-й столбец в таблице users

    if free_spreads > 0:
        # Используем бесплатное гадание
        await decrement_free_spreads(callback.from_user.id)
        await process_reading(callback, paid=0)
    else:
        # Предлагаем оплатить через Telegram Stars
        await create_reading_invoice(callback.bot, callback.from_user.id)


async def process_reading(callback: CallbackQuery, paid: int):
    """Единая функция генерации и сохранения полного чтения"""
    spread_data = draw_spread()
    cards_text = "\n".join([f"{pos}: {card}" for pos, card in spread_data])
    
    interpretation = await generate_reading(cards_text)

    # Сохраняем в базу (для аналитики и истории)
    await save_reading(
        user_id=callback.from_user.id,
        spread="Past-Present-Future",
        cards=cards_text,
        interpretation=interpretation,
        paid=paid
    )

    text = f"""
🔮 Ваше полное чтение судьбы

{cards_text}

{interpretation}

Хотите ещё одно гадание? Приглашайте друзей — получите бесплатно! 👇
"""

    await callback.message.answer(text, reply_markup=share_kb())
