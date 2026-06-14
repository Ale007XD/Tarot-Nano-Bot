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
        "err_payment_resume": ("🚨 Error resuming reading after payment. Please contact support."),
        "err_payment_incomplete": (
            "⚠️ Payment received, but reading did not complete. Please contact support."
        ),
        # history
        "history_empty": (
            "🔮 *Your reading history is empty.*\n\nDraw your first card to begin your journey!"
        ),
        "history_title": "📜 *Reading History*\n\n",
        "history_paid_marker": "👑 [Paid]",
        "history_free_marker": "🆓 [Free]",
        # referral
        "invite_text": (
            "🔮 Invite friends and get a free reading for each one!\n\nYour invite link:\n{link}"
        ),
        # showcase: /my_traces
        "traces_empty": (
            "\U0001f52e *No readings yet.*\n\n"
            "Draw your first card to create your first governed trace!"
        ),
        "traces_title": "\U0001f517 *Your Governed Traces*\n",
        "traces_no_hash": "_(no hash \u2014 pre-governance reading)_",
        "traces_verify_hint": (
            "\U0001f4a1 Each reading is backed by a deterministic FSM trace.\n"
            "Use /verify `<hash>` to prove any reading is authentic."
        ),
        # showcase: /verify
        "verify_usage": "Usage: `/verify <trace_hash>`\n\nCopy the hash from /my\\_traces.",
        "verify_invalid_hash": "\u2757 Hash too short. Copy the full hash from /my\\_traces.",
        "verify_not_found": (
            "\u274c *Not found.*\n\n"
            "No reading matches this hash. "
            "The hash may be incorrect or the reading was removed."
        ),
        "verify_ok": "\u2705 *Reading verified.*",
        "verify_yours": "\U0001f52e This reading belongs to you.",
        "verify_other": "\U0001f464 This reading belongs to another user.",
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
            "🔮 *Ваша история раскладов пуста.*\n\nВытяните первую карту, чтобы начать!"
        ),
        "history_title": "📜 *История раскладов*\n\n",
        "history_paid_marker": "👑 [Оплачено]",
        "history_free_marker": "🆓 [Бесплатно]",
        # referral
        "invite_text": (
            "🔮 Приглашайте друзей и получайте бесплатный расклад за каждого!\n\n"
            "Ваша реферальная ссылка:\n{link}"
        ),
        # showcase: /my_traces
        "traces_empty": (
            "\U0001f52e *\u0420\u0430\u0441\u043a\u043b\u0430\u0434\u043e\u0432 \u043f\u043e\u043a\u0430 \u043d\u0435\u0442.*\n\n"
            "\u0412\u044b\u0442\u044f\u043d\u0438\u0442\u0435 \u043f\u0435\u0440\u0432\u0443\u044e \u043a\u0430\u0440\u0442\u0443, \u0447\u0442\u043e\u0431\u044b \u0441\u043e\u0437\u0434\u0430\u0442\u044c \u0432\u0430\u0448 \u043f\u0435\u0440\u0432\u044b\u0439 \u0443\u043f\u0440\u0430\u0432\u043b\u044f\u0435\u043c\u044b\u0439 \u0442\u0440\u0435\u0439\u0441!"
        ),
        "traces_title": "\U0001f517 *\u0412\u0430\u0448\u0438 \u0433\u043e\u0432\u0435\u0440\u043d\u0430\u043d\u0441-\u0442\u0440\u0435\u0439\u0441\u044b*\n",
        "traces_no_hash": "_(\u0445\u044d\u0448 \u043e\u0442\u0441\u0443\u0442\u0441\u0442\u0432\u0443\u0435\u0442 \u2014 \u0441\u0442\u0430\u0440\u044b\u0439 \u0440\u0430\u0441\u043a\u043b\u0430\u0434)_",
        "traces_verify_hint": (
            "\U0001f4a1 \u041a\u0430\u0436\u0434\u044b\u0439 \u0440\u0430\u0441\u043a\u043b\u0430\u0434 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0451\u043d \u0434\u0435\u0442\u0435\u0440\u043c\u0438\u043d\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u044b\u043c FSM-\u0442\u0440\u0435\u0439\u0441\u043e\u043c.\n"
            "\u0418\u0441\u043f\u043e\u043b\u044c\u0437\u0443\u0439\u0442\u0435 /verify `<hash>` \u0434\u043b\u044f \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0438 \u043f\u043e\u0434\u043b\u0438\u043d\u043d\u043e\u0441\u0442\u0438."
        ),
        "verify_usage": "\u0424\u043e\u0440\u043c\u0430\u0442: `/verify <trace_hash>`\n\n\u0421\u043a\u043e\u043f\u0438\u0440\u0443\u0439\u0442\u0435 \u0445\u044d\u0448 \u0438\u0437 /my\\_traces.",
        "verify_invalid_hash": "\u2757 \u0425\u044d\u0448 \u0441\u043b\u0438\u0448\u043a\u043e\u043c \u043a\u043e\u0440\u043e\u0442\u043a\u0438\u0439. \u0421\u043a\u043e\u043f\u0438\u0440\u0443\u0439\u0442\u0435 \u043f\u043e\u043b\u043d\u044b\u0439 \u0445\u044d\u0448 \u0438\u0437 /my\\_traces.",
        "verify_not_found": (
            "\u274c *\u041d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u043e.*\n\n"
            "\u041d\u0438 \u043e\u0434\u0438\u043d \u0440\u0430\u0441\u043a\u043b\u0430\u0434 \u043d\u0435 \u0441\u043e\u043e\u0442\u0432\u0435\u0442\u0441\u0442\u0432\u0443\u0435\u0442 \u044d\u0442\u043e\u043c\u0443 \u0445\u044d\u0448\u0443."
        ),
        "verify_ok": "\u2705 *\u0420\u0430\u0441\u043a\u043b\u0430\u0434 \u043f\u043e\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0451\u043d.*",
        "verify_yours": "\U0001f52e \u042d\u0442\u043e \u0432\u0430\u0448 \u0440\u0430\u0441\u043a\u043b\u0430\u0434.",
        "verify_other": "\U0001f464 \u042d\u0442\u043e \u0440\u0430\u0441\u043a\u043b\u0430\u0434 \u0434\u0440\u0443\u0433\u043e\u0433\u043e \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f.",
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
