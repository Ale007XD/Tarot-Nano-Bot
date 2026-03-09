from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def start_kb():

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔮 Draw my card", callback_data="draw")]
        ]
    )

    return kb


def paywall_kb():

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Unlock full reading", callback_data="buy")]
        ]
    )

    return kb


def share_kb():

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="🔮 Share",
                switch_inline_query="I just got my tarot reading 🔮"
            )]
        ]
    )

    return kb
