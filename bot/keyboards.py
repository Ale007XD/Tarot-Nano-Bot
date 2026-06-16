from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.i18n import t

_BOT_USERNAME = "tarotnanovmbot"


def _share_url(text: str, bot_username: str = _BOT_USERNAME) -> str:
    """Telegram share URL — works without inline mode enabled."""
    import urllib.parse
    msg = f"{text}\n\nhttps://t.me/{bot_username}"
    return f"https://t.me/share/url?url=https://t.me/{bot_username}&text={urllib.parse.quote(msg)}"


def start_kb(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=t("btn_draw", lang), callback_data="draw")]]
    )


def paywall_kb(lang: str = "en") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t("btn_buy", lang), callback_data="buy")]
        ]
    )


def share_after_payment_kb(lang: str = "en", trace_hash: str = "") -> InlineKeyboardMarkup:
    """Share button after paid reading — rewards user with +1 free spread."""
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
                    url=_share_url(share_text),
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 Поделился → +1 попытка" if lang == "ru" else "🎁 Shared → +1 free reading",
                    callback_data=f"share_done:{trace_hash[:16]}",
                )
            ],
        ]
    )


def share_kb(lang: str = "en") -> InlineKeyboardMarkup:
    """Legacy share keyboard (card_of_the_day flow)."""
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
                    url=_share_url(share_text),
                )
            ]
        ]
    )
