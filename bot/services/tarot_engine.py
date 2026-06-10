from __future__ import annotations

import random

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


def build_deck() -> list[str]:
    minor = [f"{rank} of {suit}" for suit in SUITS for rank in RANKS]
    return MAJOR_ARCANA + minor


DECK: list[str] = build_deck()


def draw_card() -> str:
    card = random.choice(DECK)
    if random.choice([True, False]):
        card += " (Reversed)"
    return card


def draw_spread() -> list[tuple[str, str]]:
    return [("Past", draw_card()), ("Present", draw_card()), ("Future", draw_card())]
