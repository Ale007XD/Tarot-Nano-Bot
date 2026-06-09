"""Storage tools — produce save parameters for post-execution DB write.

Design: FSM tools are sync and must not do async I/O.
These tools return structured save_params; the async DB write
happens in vm_runner.py after trace completes.
"""

from __future__ import annotations


def build_card_of_day_save_params(
    user_id: int,
    card_name: str = "",
    card_index: int = 0,
    execution_date: str = "",
    trace_id: str = "",
    **kwargs: object,
) -> dict[str, object]:
    """Build parameters for saving Card of the Day reading."""
    return {
        "user_id": user_id,
        "spread": "card_of_the_day",
        "cards": card_name,
        "interpretation": f"Deterministic card for {execution_date} (index={card_index})",
        "paid": 0,
        "trace_id": trace_id,
    }


def build_full_reading_save_params(
    user_id: int,
    cards_text: str = "",
    interpretation: str = "",
    paid: int = 0,
    trace_id: str = "",
    **kwargs: object,
) -> dict[str, object]:
    """Build parameters for saving full Past/Present/Future reading."""
    return {
        "user_id": user_id,
        "spread": "past_present_future",
        "cards": cards_text,
        "interpretation": interpretation,
        "paid": paid,
        "trace_id": trace_id,
    }


def build_payment_required_params(
    user_id: int,
    **kwargs: object,
) -> dict[str, object]:
    """Signal that payment is required — no reading saved yet."""
    return {
        "action": "REQUIRES_ACTION",
        "user_id": user_id,
    }
