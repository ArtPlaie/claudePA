"""Wrapper Anthropic : tiers haiku/sonnet/opus, prompt caching profile+policies, budget gate.

Compteur usage dans `core-memory/usage.json` (reset le 1er du mois UTC).
Alerte Telegram quand on dépasse 80% du budget, refus d'appel au-delà de 100%.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from . import paths

log = logging.getLogger(__name__)

MODELS: dict[str, str] = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-7",
}

# Pricing approximatif USD / M tokens (input, output). Worst-case — sert au gate budget,
# pas à de la facturation précise. Cache read/write tarifés comme input.
_PRICING: dict[str, tuple[float, float]] = {
    "haiku": (1.0, 5.0),
    "sonnet": (3.0, 15.0),
    "opus": (15.0, 75.0),
}

DEFAULT_BUDGET_USD = 30.0
ALERT_PCT = 0.8


class BudgetExceeded(RuntimeError):
    """Levée quand le budget mensuel est atteint — refus d'appel."""


@dataclass
class LLMResponse:
    text: str
    tokens_in: int
    tokens_out: int
    model: str


def resolve_model(tier: str) -> str:
    if tier in MODELS:
        return MODELS[tier]
    if tier in MODELS.values():
        return tier
    raise ValueError(f"Unknown model tier: {tier!r}")


def _budget() -> float:
    raw = os.environ.get("TOKEN_BUDGET_USD")
    if raw:
        try:
            return float(raw)
        except ValueError:
            pass
    return DEFAULT_BUDGET_USD


def _current_month() -> str:
    return datetime.now(UTC).strftime("%Y-%m")


def _load_usage() -> dict[str, Any]:
    if not paths.USAGE_JSON.exists():
        return {"month": _current_month(), "cost_usd": 0.0, "by_task": {}}
    try:
        data = json.loads(paths.USAGE_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"month": _current_month(), "cost_usd": 0.0, "by_task": {}}
    if data.get("month") != _current_month():
        return {"month": _current_month(), "cost_usd": 0.0, "by_task": {}}
    data.setdefault("cost_usd", 0.0)
    data.setdefault("by_task", {})
    return data


def _save_usage(usage: dict[str, Any]) -> None:
    paths.USAGE_JSON.parent.mkdir(parents=True, exist_ok=True)
    paths.USAGE_JSON.write_text(json.dumps(usage, indent=2), encoding="utf-8")


def _cost(tier: str, tokens_in: int, tokens_out: int) -> float:
    in_rate, out_rate = _PRICING[tier]
    return (tokens_in * in_rate + tokens_out * out_rate) / 1_000_000


def _system_blocks(extra: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """profile.md + policies.md → blocs system avec cache_control sur policies."""
    blocks: list[dict[str, Any]] = []
    if paths.PROFILE.exists():
        blocks.append(
            {"type": "text", "text": f"# profile.md\n\n{paths.PROFILE.read_text(encoding='utf-8')}"}
        )
    if paths.POLICIES.exists():
        blocks.append(
            {
                "type": "text",
                "text": f"# policies.md\n\n{paths.POLICIES.read_text(encoding='utf-8')}",
                "cache_control": {"type": "ephemeral"},
            }
        )
    if extra:
        blocks.extend(extra)
    return blocks


def call(
    *,
    tier: str,
    messages: list[dict[str, Any]],
    task: str,
    system_extra: list[dict[str, Any]] | None = None,
    max_tokens: int = 2048,
    temperature: float = 1.0,
) -> LLMResponse:
    """Appel Anthropic. Lève BudgetExceeded si budget atteint."""
    import anthropic

    usage = _load_usage()
    budget = _budget()
    if usage["cost_usd"] >= budget:
        raise BudgetExceeded(
            f"budget mensuel atteint : ${usage['cost_usd']:.2f} >= ${budget:.2f}"
        )

    model = resolve_model(tier)
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=_system_blocks(system_extra),
        messages=messages,
    )

    u = resp.usage
    tokens_in = (
        (u.input_tokens or 0)
        + (getattr(u, "cache_creation_input_tokens", 0) or 0)
        + (getattr(u, "cache_read_input_tokens", 0) or 0)
    )
    tokens_out = u.output_tokens or 0
    cost = _cost(tier, tokens_in, tokens_out)

    prev_cost = float(usage["cost_usd"])
    new_cost = round(prev_cost + cost, 6)
    usage["cost_usd"] = new_cost
    usage["by_task"][task] = round(float(usage["by_task"].get(task, 0.0)) + cost, 6)
    _save_usage(usage)

    threshold = budget * ALERT_PCT
    if prev_cost < threshold <= new_cost:
        try:
            from . import notify

            notify.alert(
                f"⚠️ budget tokens à {new_cost / budget:.0%} "
                f"(${new_cost:.2f} / ${budget:.2f})"
            )
        except Exception:
            log.exception("budget alert send failed")

    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
    return LLMResponse(text=text, tokens_in=tokens_in, tokens_out=tokens_out, model=model)
