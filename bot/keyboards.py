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


def share_after_payment_kb(lang: str = "en", trace_hash: str = "") -> InlineKeyboardMarkup:
    """Share button after paid reading — rewards user with +1 free spread."""
    share_text = (
        "Я только что получил таро-расклад от TarotNanoVMBot! 🔮 Попробуй:"
        if lang == "ru"
        else "I just got my tarot reading from TarotNanoVMBot! 🔮 Try it:"
    )
    btn_label = t("btn_share", lang)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=btn_label,
                    switch_inline_query=share_text,
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 Поделился → +1 попытка"
                    if lang == "ru"
                    else "🎁 Shared → +1 free reading",
                    callback_data=f"share_done:{trace_hash[:16]}",
                )
            ],
        ]
    )
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


def share_kb(lang: str = "en") -> InlineKeyboardMarkup:
    """Legacy share keyboard (used in card_of_the_day flow)."""
    share_text = (
        "Я только что получил таро-расклад от TarotNanoVMBot! 🔮 Попробуй:"
        if lang == "ru"
        else "I just got my tarot reading from TarotNanoVMBot! 🔮 Try it:"
    )
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
