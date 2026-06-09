"""Unit tests for bot/tools/*.py — no async, no DB, no LLM."""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bot.tools.tarot_tools import (
    FULL_DECK,
    draw_deterministic_card,
    draw_three_card_spread,
)
from bot.tools.balance_tools import check_balance, charge_free_spread
from bot.tools.storage_tools import (
    build_card_of_day_save_params,
    build_full_reading_save_params,
    build_payment_required_params,
)


# ---------------------------------------------------------------------------
# tarot_tools
# ---------------------------------------------------------------------------

class TestFullDeck:
    def test_deck_size(self) -> None:
        assert len(FULL_DECK) == 78

    def test_no_duplicates(self) -> None:
        assert len(set(FULL_DECK)) == 78

    def test_major_arcana_present(self) -> None:
        assert "The Fool" in FULL_DECK
        assert "The World" in FULL_DECK

    def test_minor_arcana_present(self) -> None:
        assert "Ace of Wands" in FULL_DECK
        assert "King of Pentacles" in FULL_DECK


class TestDrawDeterministicCard:
    def test_returns_dict_with_required_keys(self) -> None:
        result = draw_deterministic_card(user_id=12345, execution_date="2026-06-09")
        assert "card_index" in result
        assert "card_name" in result
        assert "execution_date" in result

    def test_deterministic_same_input(self) -> None:
        r1 = draw_deterministic_card(user_id=42, execution_date="2026-06-09")
        r2 = draw_deterministic_card(user_id=42, execution_date="2026-06-09")
        assert r1["card_index"] == r2["card_index"]
        assert r1["card_name"] == r2["card_name"]

    def test_different_users_different_cards(self) -> None:
        r1 = draw_deterministic_card(user_id=1, execution_date="2026-06-09")
        r2 = draw_deterministic_card(user_id=2, execution_date="2026-06-09")
        # Statistically near-impossible to collide with different user_ids
        assert r1["card_index"] != r2["card_index"]

    def test_different_dates_different_cards(self) -> None:
        r1 = draw_deterministic_card(user_id=42, execution_date="2026-06-09")
        r2 = draw_deterministic_card(user_id=42, execution_date="2026-06-10")
        assert r1["card_index"] != r2["card_index"]

    def test_card_index_in_range(self) -> None:
        result = draw_deterministic_card(user_id=99999, execution_date="2026-01-01")
        assert 0 <= int(str(result["card_index"])) < 78

    def test_card_name_in_deck(self) -> None:
        result = draw_deterministic_card(user_id=12345, execution_date="2026-06-09")
        assert result["card_name"] in FULL_DECK

    def test_custom_salt_changes_result(self) -> None:
        r1 = draw_deterministic_card(user_id=42, execution_date="2026-06-09", salt="SALT_A")
        r2 = draw_deterministic_card(user_id=42, execution_date="2026-06-09", salt="SALT_B")
        assert r1["card_index"] != r2["card_index"]

    def test_accepts_kwargs(self) -> None:
        result = draw_deterministic_card(
            user_id=1, execution_date="2026-01-01", extra_ignored="x"
        )
        assert result["card_name"] in FULL_DECK


class TestDrawThreeCardSpread:
    def test_returns_three_positions(self) -> None:
        result = draw_three_card_spread()
        assert "past" in result
        assert "present" in result
        assert "future" in result

    def test_cards_text_present(self) -> None:
        result = draw_three_card_spread()
        assert "Past:" in str(result["cards_text"])
        assert "Present:" in str(result["cards_text"])
        assert "Future:" in str(result["cards_text"])

    def test_accepts_kwargs(self) -> None:
        result = draw_three_card_spread(ignored="value")
        assert "past" in result


# ---------------------------------------------------------------------------
# balance_tools
# ---------------------------------------------------------------------------

class TestCheckBalance:
    def test_free_when_spreads_available(self) -> None:
        result = check_balance(free_spreads=3)
        assert result["action"] == "FREE"
        assert result["free_spreads_remaining"] == 3

    def test_requires_action_when_zero(self) -> None:
        result = check_balance(free_spreads=0)
        assert result["action"] == "REQUIRES_ACTION"

    def test_requires_action_default(self) -> None:
        result = check_balance()
        assert result["action"] == "REQUIRES_ACTION"

    def test_accepts_kwargs(self) -> None:
        result = check_balance(free_spreads=1, extra="ignored")
        assert result["action"] == "FREE"


class TestChargeFreeSpread:
    def test_returns_charged_true(self) -> None:
        result = charge_free_spread(user_id=42)
        assert result["charged"] is True
        assert result["user_id"] == 42

    def test_accepts_kwargs(self) -> None:
        result = charge_free_spread(user_id=1, extra="ignored")
        assert result["charged"] is True


# ---------------------------------------------------------------------------
# storage_tools
# ---------------------------------------------------------------------------

class TestBuildCardOfDaySaveParams:
    def test_required_keys(self) -> None:
        result = build_card_of_day_save_params(
            user_id=42, card_name="The Fool", card_index=0,
            execution_date="2026-06-09", trace_id="abc-123",
        )
        assert result["user_id"] == 42
        assert result["spread"] == "card_of_the_day"
        assert result["cards"] == "The Fool"
        assert result["paid"] == 0
        assert result["trace_id"] == "abc-123"

    def test_accepts_kwargs(self) -> None:
        result = build_card_of_day_save_params(user_id=1, extra="ignored")
        assert result["spread"] == "card_of_the_day"


class TestBuildFullReadingSaveParams:
    def test_required_keys(self) -> None:
        result = build_full_reading_save_params(
            user_id=42, cards_text="Past: The Fool\n...",
            interpretation="You stand at a threshold...",
            paid=1, trace_id="def-456",
        )
        assert result["user_id"] == 42
        assert result["spread"] == "past_present_future"
        assert result["paid"] == 1
        assert result["trace_id"] == "def-456"

    def test_default_paid_zero(self) -> None:
        result = build_full_reading_save_params(user_id=1)
        assert result["paid"] == 0


class TestBuildPaymentRequiredParams:
    def test_action_sentinel(self) -> None:
        result = build_payment_required_params(user_id=42)
        assert result["action"] == "REQUIRES_ACTION"
        assert result["user_id"] == 42

    def test_accepts_kwargs(self) -> None:
        result = build_payment_required_params(user_id=1, extra="ignored")
        assert result["action"] == "REQUIRES_ACTION"
