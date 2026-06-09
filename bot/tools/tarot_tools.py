"""Tarot card drawing tools — deterministic and random variants."""

from __future__ import annotations

import hashlib
import random
from datetime import date

# ---------------------------------------------------------------------------
# Deck definition
# ---------------------------------------------------------------------------

MAJOR_ARCANA: list[str] = [
    "The Fool", "The Magician", "The High Priestess", "The Empress",
    "The Emperor", "The Hierophant", "The Lovers", "The Chariot",
    "Strength", "The Hermit", "Wheel of Fortune", "Justice",
    "The Hanged Man", "Death", "Temperance", "The Devil",
    "The Tower", "The Star", "The Moon", "The Sun", "Judgement", "The World",
]

SUITS: list[str] = ["Wands", "Cups", "Swords", "Pentacles"]
RANKS: list[str] = [
    "Ace", "Two", "Three", "Four", "Five", "Six", "Seven",
    "Eight", "Nine", "Ten", "Page", "Knight", "Queen", "King",
]

FULL_DECK: list[str] = MAJOR_ARCANA + [
    f"{rank} of {suit}" for suit in SUITS for rank in RANKS
]

assert len(FULL_DECK) == 78  # noqa: S101


# ---------------------------------------------------------------------------
# Tool functions — sync, **kwargs required (nano-vm constraint)
# ---------------------------------------------------------------------------

def draw_deterministic_card(
    user_id: int,
    execution_date: str | None = None,
    salt: str = "TAROT_GOVERNANCE_SALT_2026",
    **kwargs: object,
) -> dict[str, object]:
    """Deterministic Card of the Day via SHA-256(user_id:date:salt).

    Returns same card for same user on same date — cryptographically provable.
    """
    today = execution_date or date.today().isoformat()
    payload = f"{user_id}:{today}:{salt}".encode("utf-8")
    card_index = int(hashlib.sha256(payload).hexdigest(), 16) % 78
    card_name = FULL_DECK[card_index]
    return {
        "card_index": card_index,
        "card_name": card_name,
        "execution_date": today,
        "algorithm": "SHA-256",
    }


def draw_three_card_spread(**kwargs: object) -> dict[str, object]:
    """Random Past/Present/Future spread.

    Randomness is intentional — interpretation is the governed artifact.
    """
    deck = FULL_DECK.copy()
    random.shuffle(deck)
    drawn = deck[:3]
    reversed_flags = [random.choice([True, False]) for _ in range(3)]
    cards = [
        f"{card} (Reversed)" if rev else card
        for card, rev in zip(drawn, reversed_flags)
    ]
    return {
        "past": cards[0],
        "present": cards[1],
        "future": cards[2],
        "cards_text": f"Past: {cards[0]}\nPresent: {cards[1]}\nFuture: {cards[2]}",
    }
