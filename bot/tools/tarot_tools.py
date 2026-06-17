"""Tarot card drawing tools — deterministic and random variants."""

from __future__ import annotations

import hashlib
import random
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Deck definition
# ---------------------------------------------------------------------------

MAJOR_ARCANA: list[str] = [
    "The Fool",
    "The Magician",
    "The High Priestess",
    "The Empress",
    "The Emperor",
    "The Hierophant",
    "The Lovers",
    "The Chariot",
    "Strength",
    "The Hermit",
    "Wheel of Fortune",
    "Justice",
    "The Hanged Man",
    "Death",
    "Temperance",
    "The Devil",
    "The Tower",
    "The Star",
    "The Moon",
    "The Sun",
    "Judgement",
    "The World",
]

SUITS: list[str] = ["Wands", "Cups", "Swords", "Pentacles"]
RANKS: list[str] = [
    "Ace",
    "Two",
    "Three",
    "Four",
    "Five",
    "Six",
    "Seven",
    "Eight",
    "Nine",
    "Ten",
    "Page",
    "Knight",
    "Queen",
    "King",
]

FULL_DECK: list[str] = MAJOR_ARCANA + [f"{rank} of {suit}" for suit in SUITS for rank in RANKS]

assert len(FULL_DECK) == 78  # noqa: S101

# ---------------------------------------------------------------------------
# Card image filenames — index-aligned with FULL_DECK, derived from
# rider_waite.json (deck_id=rider_waite_v1). Static to avoid runtime JSON
# parsing as a tool-function dependency.
# ---------------------------------------------------------------------------

_MAJOR_FILES: list[str] = [
    "the_fool.jpg",
    "the_magician.jpg",
    "the_high_priestess.jpg",
    "the_empress.jpg",
    "the_emperor.jpg",
    "the_hierophant.jpg",
    "the_lovers.jpg",
    "the_chariot.jpg",
    "strength.jpg",
    "the_hermit.jpg",
    "wheel_of_fortune.jpg",
    "justice.jpg",
    "the_hanged_man.jpg",
    "death.jpg",
    "temperance.jpg",
    "the_devil.jpg",
    "the_tower.jpg",
    "the_star.jpg",
    "the_moon.jpg",
    "the_sun.jpg",
    "judgement.jpg",
    "the_world.jpg",
]

_SUIT_FILE_PREFIX: dict[str, str] = {
    "Wands": "wands",
    "Cups": "cups",
    "Swords": "swords",
    "Pentacles": "pentacles",
}

CARD_FILES: list[str] = _MAJOR_FILES + [
    f"{_SUIT_FILE_PREFIX[suit]}{rank_idx + 1:02d}.jpg"
    for suit in SUITS
    for rank_idx in range(len(RANKS))
]

assert len(CARD_FILES) == 78  # noqa: S101

CARDS_DIR: Path = Path("assets/cards")


def get_card_image_path(card_index: int) -> Path:
    """Resolve card_index → image file path under assets/cards/.

    Reversed cards reuse the same artwork as upright (no separate asset).
    """
    return CARDS_DIR / CARD_FILES[card_index % 78]


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
    payload = f"{user_id}:{today}:{salt}".encode()
    card_index = int(hashlib.sha256(payload).hexdigest(), 16) % 78
    card_name = FULL_DECK[card_index]
    return {
        "card_index": card_index,
        "card_name": card_name,
        "card_file": CARD_FILES[card_index],
        "execution_date": today,
        "algorithm": "SHA-256",
    }


def draw_three_card_spread(**kwargs: object) -> dict[str, object]:
    """Random Past/Present/Future spread.

    Randomness is intentional — interpretation is the governed artifact.
    """
    indices = list(range(78))
    random.shuffle(indices)
    drawn_indices = indices[:3]
    reversed_flags = [random.choice([True, False]) for _ in range(3)]
    cards = [
        f"{FULL_DECK[idx]} (Reversed)" if rev else FULL_DECK[idx]
        for idx, rev in zip(drawn_indices, reversed_flags)
    ]
    card_files = [CARD_FILES[idx] for idx in drawn_indices]
    return {
        "past": cards[0],
        "present": cards[1],
        "future": cards[2],
        "cards_text": f"Past: {cards[0]}\nPresent: {cards[1]}\nFuture: {cards[2]}",
        "card_indices": drawn_indices,
        "card_files": card_files,
    }
