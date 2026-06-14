from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.i18n import t


def start_kb(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t("btn_draw", lang), callback_data="draw")]]
    )


def paywall_kb(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t("btn_buy", lang), callback_data="buy")]]
    )


def share_kb(lang: str = "en") -> InlineKeyboardMarkup:
    share_text = "I just got my tarot reading from Destiny Oracle! 🔮 Try it:"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=t("btn_share", lang),
                    switch_inline_query=share_text,
                )
            ]
        ]
    )
