"""Program: full_reading

Flow:
  check_balance[tool] → balance_gate[condition]
    → [FREE]  charge_free → draw_spread → llm_interpret → build_save_params [terminal]
    → [other] payment_required [terminal]

Separate tool + condition steps: ProgramValidator sees CONDITION edges (then/otherwise).
TOOL step with condition/then/otherwise is not traversed by validator BFS.
"""

from __future__ import annotations

from nano_vm import OnError, Program, StepType
from nano_vm.models import Step

FULL_READING: Program = Program(
    name="full_reading",
    steps=[
        Step(
            id="check_balance",
            type=StepType.TOOL,
            tool="check_balance",
            args={
                "user_id": "$user_id",
                "free_spreads": "$free_spreads",
            },
            output_key="balance_result",
        ),
        Step(
            id="balance_gate",
            type=StepType.CONDITION,
            condition="$balance_result.output.action == 'FREE'",
            then="charge_free",
            otherwise="payment_required",
        ),
        Step(
            id="charge_free",
            type=StepType.TOOL,
            tool="charge_free_spread",
            args={"user_id": "$user_id"},
            output_key="charge_result",
            next_step="draw_spread",
        ),
        Step(
            id="draw_spread",
            type=StepType.TOOL,
            tool="draw_three_card_spread",
            output_key="spread_result",
        ),
        Step(
            id="llm_interpret",
            type=StepType.LLM,
            prompt=(
                "You are a mystical tarot reader. "
                "Interpret this Past/Present/Future spread:\n\n"
                "$spread_result.output.cards_text\n\n"
                "Write a personal, warm, mysterious interpretation. "
                "Speak directly to the person. "
                "Cover each card position meaningfully. "
                "End your response with exactly: INTERPRETATION_COMPLETE"
            ),
            output_key="interpretation",
            allowed_outputs=["INTERPRETATION_COMPLETE"],
            max_retries=2,
            on_error=OnError.FAIL,
        ),
        Step(
            id="build_save_params",
            type=StepType.TOOL,
            tool="build_full_reading_save_params",
            output_key="save_params",
            is_terminal=True,
        ),
        Step(
            id="payment_required",
            type=StepType.TOOL,
            tool="build_payment_required_params",
            output_key="payment_params",
            is_terminal=True,
        ),
    ],
)
