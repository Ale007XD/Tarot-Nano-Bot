# bot/keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def start_kb():
    """Стартовая клавиатура — первая кнопка"""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔮 Вытянуть мою карту", callback_data="draw")]
        ]
    )
    return kb


def paywall_kb():
    """Кнопка после одной карты — главная точка продажи"""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐ Получить полное чтение за 69 Stars", callback_data="buy"
                )
            ]
        ]
    )
    return kb


def share_kb():
    """Кнопка «Поделиться» после полного чтения"""
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔮 Поделиться гаданием",
                    switch_inline_query="Я только что узнал свою судьбу по картам Таро! 🔮 Попробуй и ты:",
                )
            ]
        ]
    )
    return kb
