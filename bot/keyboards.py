from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def start_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔮 Вытянуть мою карту", callback_data="draw")]
        ]
    )


def paywall_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐ Получить полное чтение за 69 Stars",
                    callback_data="buy",
                )
            ]
        ]
    )


def share_kb() -> InlineKeyboardMarkup:
    share_text = "Я только что узнал свою судьбу по картам Таро! 🔮 Попробуй и ты:"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔮 Поделиться гаданием",
                    switch_inline_query=share_text,
                )
            ]
        ]
    )
