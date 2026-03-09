import random

MAJOR_ARCANA = [
"The Fool","The Magician","The High Priestess","The Empress",
"The Emperor","The Hierophant","The Lovers","The Chariot",
"Strength","The Hermit","Wheel of Fortune","Justice",
"The Hanged Man","Death","Temperance","The Devil",
"The Tower","The Star","The Moon","The Sun",
"Judgement","The World"
]

SUITS = ["Wands","Cups","Swords","Pentacles"]

RANKS = [
"Ace","Two","Three","Four","Five","Six","Seven",
"Eight","Nine","Ten","Page","Knight","Queen","King"
]


def build_deck():

    deck = []

    for card in MAJOR_ARCANA:
        deck.append(card)

    for suit in SUITS:
        for rank in RANKS:
            deck.append(f"{rank} of {suit}")

    return deck


DECK = build_deck()


def draw_card():

    card = random.choice(DECK)

    reversed_card = random.choice([True, False])

    if reversed_card:
        card += " (Reversed)"

    return card


def draw_spread():

    return [
        ("Past", draw_card()),
        ("Present", draw_card()),
        ("Future", draw_card())
    ]
