"""Tests for Program DSL correctness — ProgramValidator (llm-nano-vm 0.8.5)."""

from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from nano_vm.validator import ProgramValidator, IssueSeverity

from bot.programs.card_of_the_day import CARD_OF_THE_DAY
from bot.programs.full_reading import FULL_READING


class TestCardOfTheDayProgram:
    def test_program_name(self) -> None:
        assert CARD_OF_THE_DAY.name == "card_of_the_day"

    def test_step_count(self) -> None:
        assert len(CARD_OF_THE_DAY.steps) == 3

    def test_has_terminal_step(self) -> None:
        terminals = [s for s in CARD_OF_THE_DAY.steps if s.is_terminal]
        assert len(terminals) == 1

    def test_terminal_is_last(self) -> None:
        assert CARD_OF_THE_DAY.steps[-1].is_terminal is True

    def test_llm_step_has_allowed_outputs(self) -> None:
        step = next(s for s in CARD_OF_THE_DAY.steps if s.id == "llm_interpret")
        assert step.allowed_outputs == ["INTERPRETATION_COMPLETE"]

    def test_all_step_ids_unique(self) -> None:
        ids = [s.id for s in CARD_OF_THE_DAY.steps]
        assert len(ids) == len(set(ids))

    def test_no_pending_sentinel(self) -> None:
        for step in CARD_OF_THE_DAY.steps:
            if step.allowed_outputs:
                assert "PENDING" not in step.allowed_outputs

    def test_draw_card_uses_deterministic_tool(self) -> None:
        step = next(s for s in CARD_OF_THE_DAY.steps if s.id == "draw_card")
        assert step.tool == "draw_deterministic_card"

    def test_validator_no_errors(self) -> None:
        result = ProgramValidator(CARD_OF_THE_DAY).validate()
        errors = [i for i in result.issues if i.severity == IssueSeverity.ERROR]
        assert errors == [], f"Validation errors: {errors}"

    def test_validator_is_valid(self) -> None:
        assert ProgramValidator(CARD_OF_THE_DAY).validate().is_valid()


class TestFullReadingProgram:
    def test_program_name(self) -> None:
        assert FULL_READING.name == "full_reading"

    def test_has_condition_step(self) -> None:
        assert "balance_gate" in [s.id for s in FULL_READING.steps]

    def test_balance_gate_is_condition_type(self) -> None:
        step = next(s for s in FULL_READING.steps if s.id == "balance_gate")
        assert step.type == "condition"

    def test_payment_required_terminal_exists(self) -> None:
        step = next(s for s in FULL_READING.steps if s.id == "payment_required")
        assert step.is_terminal is True

    def test_balance_gate_branches(self) -> None:
        step = next(s for s in FULL_READING.steps if s.id == "balance_gate")
        assert step.then == "charge_free"
        assert step.otherwise == "payment_required"

    def test_no_pending_sentinel_anywhere(self) -> None:
        for step in FULL_READING.steps:
            if step.allowed_outputs:
                assert "PENDING" not in step.allowed_outputs

    def test_llm_step_has_allowed_outputs(self) -> None:
        step = next(s for s in FULL_READING.steps if s.id == "llm_interpret")
        assert step.allowed_outputs == ["INTERPRETATION_COMPLETE"]

    def test_all_step_ids_unique(self) -> None:
        ids = [s.id for s in FULL_READING.steps]
        assert len(ids) == len(set(ids))

    def test_condition_uses_balance_result(self) -> None:
        step = next(s for s in FULL_READING.steps if s.id == "balance_gate")
        assert "balance_result" in str(step.condition)
        assert "FREE" in str(step.condition)

    def test_validator_no_errors(self) -> None:
        result = ProgramValidator(FULL_READING).validate()
        errors = [i for i in result.issues if i.severity == IssueSeverity.ERROR]
        assert errors == [], f"Validation errors: {errors}"

    def test_validator_is_valid(self) -> None:
        assert ProgramValidator(FULL_READING).validate().is_valid()
