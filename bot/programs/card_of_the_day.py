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
                "The user has drawn their Card of the Day. "
                "Write a personal, warm, mysterious interpretation in 2-3 paragraphs. "
                "Speak directly to the person."
            ),
            output_key="interpretation",
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
