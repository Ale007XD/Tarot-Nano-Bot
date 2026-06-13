"""Internationalization — static UI texts.

Default language: English (en).
LLM interpretations use prompt-level language injection (see programs/).
"""
from __future__ import annotations

_TEXTS: dict[str, dict[str, str]] = {
    "en": {
        # start
        "welcome": (
            "🔮 Welcome to Destiny Oracle\n\n"
            "Draw your tarot card and reveal\n"
            "what fate prepared for you today."
        ),
        "btn_draw": "🔮 Draw My Card",
        "btn_buy": "⭐ Get Full Reading for 69 Stars",
        "btn_share": "🔮 Share My Reading",
        # card of the day
        "card_of_day_title": "🔮 **Your Card of the Day**",
        "card_of_day_upsell": (
            "This is only **part** of the Universe's message.\n\n"
            "To reveal the **full picture** (past • present • future"
            " + deep interpretation) — tap the button below."
        ),
        # full reading
        "full_reading_title": "🔮 **Full Reading**",
        "full_reading_paid_title": "🔮 **Payment confirmed! Full Reading**",
        # errors
        "err_card_unavailable": "⚠️ Card of the Day is unavailable. Please try again later.",
        "err_card_extract": "⚠️ Could not extract card from trace.",
        "err_card_failed": "⚠️ Failed to draw card. Please try again later.",
        "err_reading_unavailable": "⚠️ Reading unavailable. Please try again later.",
        "err_reading_extract": "⚠️ Could not extract reading from trace.",
        "err_reading_failed": "⚠️ Failed to start reading. Please try again later.",
        "err_payment_parse": "🚨 Payment parsing error. Please contact support.",
        "err_payment_no_pending": (
            "⚠️ Payment received, but no active reading found. Please contact support."
        ),
        "err_payment_resume": (
            "🚨 Error resuming reading after payment. Please contact support."
        ),
        "err_payment_incomplete": (
            "⚠️ Payment received, but reading did not complete. Please contact support."
        ),
        # history
        "history_empty": (
            "🔮 *Your reading history is empty.*\n\n"
            "Draw your first card to begin your journey!"
        ),
        "history_title": "📜 *Reading History*\n\n",
        "history_paid_marker": "👑 [Paid]",
        "history_free_marker": "🆓 [Free]",
        # referral
        "invite_text": (
            "🔮 Invite friends and get a free reading for each one!\n\n"
            "Your invite link:\n{link}"
        ),
    },
    "ru": {
        # start
        "welcome": (
            "🔮 Добро пожаловать в Destiny Oracle\n\n"
            "Вытяните карту таро и узнайте,\n"
            "что судьба приготовила вам сегодня."
        ),
        "btn_draw": "🔮 Вытянуть мою карту",
        "btn_buy": "⭐ Получить полный расклад за 69 Stars",
        "btn_share": "🔮 Поделиться гаданием",
        # card of the day
        "card_of_day_title": "🔮 **Ваша карта дня**",
        "card_of_day_upsell": (
            "Это только **часть** послания Вселенной.\n\n"
            "Чтобы узнать **полную картину** (прошлое • настоящее • будущее"
            " + глубокая интерпретация) — нажмите кнопку ниже."
        ),
        # full reading
        "full_reading_title": "🔮 **Полный расклад**",
        "full_reading_paid_title": "🔮 **Оплата подтверждена! Полный расклад**",
        # errors
        "err_card_unavailable": "⚠️ Карта дня недоступна. Попробуйте позже.",
        "err_card_extract": "⚠️ Не удалось извлечь карту из трейса.",
        "err_card_failed": "⚠️ Ошибка при вытягивании карты. Попробуйте позже.",
        "err_reading_unavailable": "⚠️ Расклад недоступен. Попробуйте позже.",
        "err_reading_extract": "⚠️ Не удалось извлечь расклад из трейса.",
        "err_reading_failed": "⚠️ Ошибка при запуске расклада. Попробуйте позже.",
        "err_payment_parse": "🚨 Ошибка разбора платежа. Обратитесь в поддержку.",
        "err_payment_no_pending": (
            "⚠️ Оплата получена, но активный расклад не найден. Обратитесь в поддержку."
        ),
        "err_payment_resume": (
            "🚨 Ошибка при продолжении расклада после оплаты. Обратитесь в поддержку."
        ),
        "err_payment_incomplete": (
            "⚠️ Оплата получена, но расклад не завершился корректно. Обратитесь в поддержку."
        ),
        # history
        "history_empty": (
            "🔮 *Ваша история раскладов пуста.*\n\n"
            "Вытяните первую карту, чтобы начать!"
        ),
        "history_title": "📜 *История раскладов*\n\n",
        "history_paid_marker": "👑 [Оплачено]",
        "history_free_marker": "🆓 [Бесплатно]",
        # referral
        "invite_text": (
            "🔮 Приглашайте друзей и получайте бесплатный расклад за каждого!\n\n"
            "Ваша реферальная ссылка:\n{link}"
        ),
    },
}

_DEFAULT_LANG = "en"
_SUPPORTED = set(_TEXTS.keys())


def t(key: str, lang: str | None = None, **kwargs: str) -> str:
    """Return localised text for key. Falls back to English."""
    code = (lang or _DEFAULT_LANG)[:2].lower()
    if code not in _SUPPORTED:
        code = _DEFAULT_LANG
    text = _TEXTS[code].get(key) or _TEXTS[_DEFAULT_LANG].get(key, key)
    return text.format(**kwargs) if kwargs else text


def lang_from_user(user: object) -> str:
    """Extract language code from aiogram User object."""
    code = getattr(user, "language_code", None) or _DEFAULT_LANG
    return code[:2].lower()
