from bot.services.tarot_engine import build_deck, draw_card, draw_spread


def run():

    deck = build_deck()

    assert len(deck) == 78, "Deck must contain 78 cards"

    card = draw_card()

    assert isinstance(card, str)

    spread = draw_spread()

    assert len(spread) == 3

    for pos, card in spread:
        assert isinstance(pos, str)
        assert isinstance(card, str)
