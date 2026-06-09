"""vm_runner.py — ExecutionVM factory and run/resume helpers.

Single place where all tools are registered and VM is configured.
Handlers import run_card_of_day() / run_full_reading() / resume_full_reading().
"""

from __future__ import annotations

from typing import Any, Callable

from nano_vm import ExecutionVM, WebhookEvent
from nano_vm.adapters import LiteLLMAdapter
from nano_vm.analyzer import TraceAnalyzer
from nano_vm.models import Trace

from bot.programs.card_of_the_day import CARD_OF_THE_DAY
from bot.programs.full_reading import FULL_READING
from bot.tools.balance_tools import charge_free_spread, check_balance
from bot.tools.storage_tools import (
    build_card_of_day_save_params,
    build_full_reading_save_params,
    build_payment_required_params,
)
from bot.tools.tarot_tools import draw_deterministic_card, draw_three_card_spread


def _build_vm(model: str) -> ExecutionVM:
    """Construct ExecutionVM with full tool registry."""
    llm = LiteLLMAdapter(model)
    tools: dict[str, Callable[..., Any]] = {
        "draw_deterministic_card": draw_deterministic_card,
        "draw_three_card_spread": draw_three_card_spread,
        "check_balance": check_balance,
        "charge_free_spread": charge_free_spread,
        "build_card_of_day_save_params": build_card_of_day_save_params,
        "build_full_reading_save_params": build_full_reading_save_params,
        "build_payment_required_params": build_payment_required_params,
    }
    return ExecutionVM(llm=llm, tools=tools)


def get_trace_hash(trace: Trace) -> str | None:
    """Extract trace_hash from ExecutionReceipt. Returns None on any error."""
    try:
        receipt = TraceAnalyzer(trace).receipt()
        return receipt.trace_hash
    except Exception:
        return None


async def run_card_of_day(
    user_id: int,
    execution_date: str,
    salt: str,
    model: str,
) -> Trace:
    vm = _build_vm(model)
    context: dict[str, object] = {
        "user_id": user_id,
        "execution_date": execution_date,
        "salt": salt,
    }
    return await vm.run(CARD_OF_THE_DAY, context=context)


async def run_full_reading(
    user_id: int,
    free_spreads: int,
    model: str,
) -> Trace:
    vm = _build_vm(model)
    context: dict[str, object] = {
        "user_id": user_id,
        "free_spreads": free_spreads,
        "paid": 0,
    }
    return await vm.run(FULL_READING, context=context)


async def resume_full_reading(
    trace: Trace,
    charge_id: str,
    model: str,
) -> Trace:
    """Resume suspended full_reading after Telegram Stars payment confirmed."""
    vm = _build_vm(model)
    event = WebhookEvent(
        trace_id=trace.trace_id,
        payload={"charge_id": charge_id, "paid": 1},
        source="WEBHOOK",
    )
    return await vm.resume_with_program(event, FULL_READING)
