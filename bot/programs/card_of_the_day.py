"""Program: card_of_the_day

Flow:
  draw_card → llm_interpret → build_save_params [terminal: SUCCESS]

FSM failure (LLM on_error=FAIL) → Trace.status=FAILED, no separate terminal step needed.
build_save_params id contains no failure keyword → PV-13 WARNING expected (acceptable).
"""

from __future__ import annotations

from nano_vm import OnError, Program, StepType
from nano_vm.models import Step

CARD_OF_THE_DAY: Program = Program(
    name="card_of_the_day",
    steps=[
        Step(
            id="draw_card",
            type=StepType.TOOL,
            tool="draw_deterministic_card",
            args={
                "user_id": "$user_id",
                "execution_date": "$execution_date",
                "salt": "$salt",
            },
            output_key="card_result",
        ),
        Step(
            id="llm_interpret",
            type=StepType.LLM,
            prompt=(
                "You are a mystical tarot reader. "
                "The user has drawn their Card of the Day: $card_result.output.card_name "
                "on $card_result.output.execution_date.\n\n"
                "Write a personal, warm, mysterious interpretation in 2-3 paragraphs. "
                "Speak directly to the person. "
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
            tool="build_card_of_day_save_params",
            output_key="save_params",
            is_terminal=True,
        ),
    ],
)
