# Tarot Nano Bot

Telegram-бот с таро-раскладами, управляемый через FSM-runtime [llm-nano-vm](https://github.com/Ale007XD/nano_vm).

Каждый расклад — это детерминированное FSM-исполнение с верифицируемым `trace_hash`. Карта дня криптографически привязана к `user_id + date + salt` (SHA-256) — пользователь может убедиться, что карта не подбиралась вручную.

---

## Архитектура

```
Telegram user
     │
     ▼
aiogram handlers (bot/handlers/)
     │
     ▼
vm_runner.py  ←→  llm-nano-vm FSM kernel
     │                    │
     │              LiteLLMAdapter (LLM-интерпретации)
     │
     ▼
bot/database.py  (SQLite WAL)
  ├── readings          — результаты раскладов
  ├── users             — профили пользователей
  └── pending_executions — suspend/resume bridge (Telegram Stars)
```

**Governance layer** (nano-vm-mcp, опционально):
- `execution_traces` — пошаговый лог FSM
- `transition_stats` — агрегированная статистика переходов
- `ExecutionReceipt` — верифицируемый артефакт каждого прогона

---

## Фичи

- **Карта дня** — детерминированный выбор через SHA-256, одна карта на пользователя в день
- **Полный расклад** — Past / Present / Future + LLM-интерпретация, управляемая FSM
- **Оплата через Telegram Stars** — suspend/resume: FSM приостанавливается до подтверждения оплаты, затем продолжается с той же точки
- **`trace_hash`** — криптографическое доказательство честности выбора карт, хранится в `readings`
- **Governance**: каждый прогон производит `ExecutionReceipt = f(Trace)` — детерминированная проекция, не зависящая от LLM

---

## Стек

| Компонент | Версия |
|---|---|
| Python | 3.12+ |
| aiogram | 3.x |
| aiosqlite | — |
| llm-nano-vm | 0.8.5 |
| LiteLLMAdapter | через Vibecode proxy |
| Telegram Stars | XTR (платёжная валюта) |

---

## Установка

```bash
git clone https://github.com/Ale007XD/Tarot-Nano-Bot
cd Tarot-Nano-Bot
pip install -e ".[dev]"
```

Переменные окружения:

```env
BOT_TOKEN=         # Telegram bot token
OPENAI_API_KEY=    # Vibecode proxy key
OPENAI_API_BASE=   # https://api.vibecode-claude.online/v1
LLM_MODEL=         # openai/claude-sonnet-4.6
TAROT_SALT=        # секретная соль для детерминированного выбора карт
```

---

## Запуск

```bash
python -m bot.main
```

---

## Тесты

```bash
pytest                     # все тесты
pytest -v --tb=short       # с деталями
mypy --strict bot/         # проверка типов
```

CI: **90/90 PASS**, mypy 0 errors (26 файлов).

---

## FSM-программы

### `card_of_the_day`

```
draw_card → interpret_card → [done]
```

Карта выбирается детерминированно (`draw_deterministic_card`), интерпретация генерируется LLM под управлением FSM с `allowed_outputs` и `timeout_seconds`.

### `full_reading` (Past / Present / Future)

```
check_balance → [free: draw_spread → interpret → done]
                [paid: SUSPENDED → resume after Stars payment → draw_spread → interpret → done]
```

При `SUSPENDED` FSM сериализует `Trace` в `pending_executions`. После `successful_payment` — `resume_full_reading()` продолжает с той же точки.

---

## Платёжный флоу (Telegram Stars)

```
user → /start → full_reading callback
  → vm_runner.run_full_reading()
  → FSM: check_balance → SUSPENDED
  → save_pending_execution(user_id, execution_id, trace_json)
  → send_invoice (XTR)

user → оплачивает
  → PreCheckoutQuery → validate OrderPayload → ok=True
  → successful_payment
  → get_pending_execution(user_id)
  → Trace.model_validate_json(trace_json)
  → vm_runner.resume_full_reading(trace, charge_id)
  → FSM продолжает → SUCCESS
  → save_reading(paid=1, trace_hash=...)
  → показать расклад
```

`OrderPayload` содержит `execution_id` (FSM `trace_id`) — связывает платёж с конкретным прогоном.

---

## Governance

Бот построен на том же execution runtime, который он демонстрирует:

- FSM-программы в `bot/programs/` — декларативный DSL, верифицируемый `ProgramValidator`
- Каждый прогон производит `Trace` → `ExecutionReceipt`
- `trace_hash` в `readings` — пользователь получает криптографическое доказательство честности выбора карт
- Инфраструктура: [llm-nano-vm](https://github.com/Ale007XD/nano_vm) + [nano-vm-mcp](https://github.com/Ale007XD/nano-vm-mcp)

> nano-vm контролирует **что агент делает** — не что он видит, не что он говорит.
