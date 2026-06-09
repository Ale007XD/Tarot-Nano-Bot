"""Balance management tools — check free spreads, charge or gate to payment."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Tool functions — sync, **kwargs required (nano-vm constraint)
# ---------------------------------------------------------------------------

def check_balance(free_spreads: int = 0, **kwargs: object) -> dict[str, object]:
    """Check if user has free spreads available.

    Returns action sentinel:
    - FREE        — has free spreads, will be consumed
    - REQUIRES_ACTION — no free spreads, payment required
    """
    if free_spreads > 0:
        return {"action": "FREE", "free_spreads_remaining": free_spreads}
    return {"action": "REQUIRES_ACTION", "free_spreads_remaining": 0}


def charge_free_spread(user_id: int, **kwargs: object) -> dict[str, object]:
    """Mark that a free spread will be consumed.

    Actual DB decrement happens in storage_tools.save_reading_tool
    after successful execution to avoid charging on LLM failure.
    """
    return {"charged": True, "user_id": user_id}
