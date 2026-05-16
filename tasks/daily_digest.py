"""Digest matinal Telegram : 3-5 lignes — drafts pending, RDV du jour, alertes.

Tourne tous les jours à 05:30 UTC (07:30 Paris). `vacation_safe: true` :
continue à tourner pendant les vacances pour garder Sylvain au courant
des drafts pending et des RDV.

Pas d'appel LLM en V1 : formatting déterministe sur des sources déjà
structurées (front matter drafts, events calendar, usage.json). Budget
$0/run. Le tier `model: haiku` dans schedule.yaml est conservé pour une
V2 éventuelle (synthèse contextuelle d'alertes).
"""
from __future__ import annotations

import json
import logging
import os
from datetime import UTC, date, datetime
from typing import Any

import yaml

from tasks._lib import calendar, llm, memory, paths, schedule, telegram
from tasks._lib.memory import MarkdownDoc

TASK = "daily_digest"

log = logging.getLogger(TASK)

PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
BUDGET_HEADS_UP_PCT = 0.5


def _list_pending_drafts(today: date) -> list[dict[str, Any]]:
    """Drafts avec status: pending et expires_at >= today, triés par priorité."""
    if not paths.DRAFTS.exists():
        return []
    out: list[dict[str, Any]] = []
    for p in sorted(paths.DRAFTS.glob("*.md")):
        try:
            doc = MarkdownDoc.read(p)
        except (OSError, yaml.YAMLError):
            continue
        fm = doc.front_matter
        if fm.get("status") != "pending":
            continue
        exp = fm.get("expires_at")
        if isinstance(exp, str):
            try:
                if date.fromisoformat(exp) < today:
                    continue
            except ValueError:
                pass
        elif isinstance(exp, date) and exp < today:
            continue
        out.append(
            {
                "title": str(fm.get("title", p.stem)),
                "priority": str(fm.get("priority", "medium")),
                "type": str(fm.get("type", "")),
            }
        )
    out.sort(key=lambda d: (PRIORITY_RANK.get(d["priority"], 9), d["title"]))
    return out


def _today_events(
    events: list[calendar.CalendarEvent], today: date
) -> list[calendar.CalendarEvent]:
    return [e for e in events if e.start.date() <= today <= e.end.date()]


def _budget_status() -> tuple[float, float, float] | None:
    """(pct, cost, budget) si pct >= BUDGET_HEADS_UP_PCT, sinon None."""
    if not paths.USAGE_JSON.exists():
        return None
    try:
        data = json.loads(paths.USAGE_JSON.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if data.get("month") != datetime.now(UTC).strftime("%Y-%m"):
        return None
    cost = float(data.get("cost_usd", 0.0))
    raw_budget = os.environ.get("TOKEN_BUDGET_USD")
    try:
        budget = float(raw_budget) if raw_budget else llm.DEFAULT_BUDGET_USD
    except ValueError:
        budget = llm.DEFAULT_BUDGET_USD
    if budget <= 0:
        return None
    pct = cost / budget
    if pct < BUDGET_HEADS_UP_PCT:
        return None
    return pct, cost, budget


def _format_digest(
    today: date,
    drafts: list[dict[str, Any]],
    events_today: list[calendar.CalendarEvent],
    budget: tuple[float, float, float] | None,
    location: dict[str, Any],
) -> str:
    lines: list[str] = [f"Digest {today.strftime('%d/%m')}"]

    if drafts:
        shown = drafts[:5]
        titles = ", ".join(d["title"][:40] for d in shown)
        suffix = f" (+{len(drafts) - len(shown)})" if len(drafts) > len(shown) else ""
        lines.append(f"drafts pending ({len(drafts)}) : {titles}{suffix}")

    if events_today:
        evs = "; ".join(
            f"{e.start.strftime('%Hh%M')} {e.summary[:30]}" for e in events_today[:4]
        )
        more = f" +{len(events_today) - 4}" if len(events_today) > 4 else ""
        lines.append(f"RDV : {evs}{more}")

    if budget:
        pct, cost, b = budget
        lines.append(f"budget tokens {pct:.0%} (${cost:.2f}/${b:.0f})")

    if location.get("vacation_mode"):
        loc = str(location.get("location", "?"))
        lines.append(f"vacances ({loc}) — tâches non vacation_safe en pause")

    if len(lines) == 1:
        lines.append("RAS — aucun draft pending, pas de RDV connu")

    return "\n".join(lines)


def run(cfg: dict[str, Any]) -> None:
    run_at = datetime.now(UTC)
    today = run_at.date()

    drafts = _list_pending_drafts(today)
    events = calendar.fetch_upcoming(days_ahead=2, now=run_at)
    events_today = _today_events(events, today)
    budget = _budget_status()
    location = memory.read_location()

    message = _format_digest(today, drafts, events_today, budget, location)

    sent = telegram.send(cfg.get("channel", "perso"), message, parse_mode=None)

    summary = (
        f"{len(drafts)} draft(s), {len(events_today)} évén. — "
        + ("envoyé Telegram" if sent else "Telegram off, log only")
    )

    memory.write_run_log(
        task=TASK,
        run_at=run_at,
        status="completed",
        summary=summary,
        body="## Message\n```\n" + message + "\n```",
        extra={
            "drafts_count": len(drafts),
            "events_today": len(events_today),
            "telegram_sent": sent,
        },
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    return schedule.run_guarded(TASK, run)


if __name__ == "__main__":
    raise SystemExit(main())
