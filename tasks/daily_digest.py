"""Digest matinal Telegram — drafts pending, RDV jour, à préparer 5j, alertes.

Tourne tous les jours à 05:30 UTC (07:30 Paris). `vacation_safe: true` :
continue à tourner pendant les vacances pour garder Sylvain au courant
des drafts pending et des RDV.

Pipeline :
1. Drafts pendants (déterministe, lecture front matter).
2. Events du jour depuis Google Calendar (déterministe).
3. Events J+1..J+5 → Haiku classif "needs_prep ?" + why court.
4. Budget tokens si dépassement de seuil (déterministe).
5. Format + envoi Telegram.

Coût par run : ~$0.001 (un seul appel Haiku, skippé si zéro event 5j).
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import UTC, date, datetime, timedelta
from typing import Any

import yaml

from tasks._lib import calendar, llm, memory, paths, schedule, telegram
from tasks._lib.memory import MarkdownDoc

TASK = "daily_digest"

log = logging.getLogger(TASK)

PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
BUDGET_HEADS_UP_PCT = 0.5

LOOKAHEAD_DAYS = 5
MAX_EVENTS_TO_CLASSIFY = 15


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


def _lookahead_events(
    events: list[calendar.CalendarEvent], today: date
) -> list[calendar.CalendarEvent]:
    """Events strictement après aujourd'hui dans la fenêtre LOOKAHEAD_DAYS."""
    horizon = today + timedelta(days=LOOKAHEAD_DAYS)
    return [e for e in events if today < e.start.date() <= horizon]


def _parse_json_array(text: str) -> list[dict[str, Any]]:
    """Tolère prefix/suffix narratif autour d'un array JSON."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise ValueError("no JSON array found")
    return json.loads(text[start : end + 1])


def _needs_prep_classify(
    events: list[calendar.CalendarEvent], tier: str
) -> list[tuple[calendar.CalendarEvent, str]]:
    """Pour chaque event 5j, retourne (event, why) si needs_prep=True. Sinon vide."""
    if not events:
        return []

    capped = events[:MAX_EVENTS_TO_CLASSIFY]

    def _when(e: calendar.CalendarEvent) -> str:
        if e.all_day:
            return e.start.strftime("%a %d/%m (all-day)")
        return e.start.strftime("%a %d/%m %Hh%M")

    items = [
        {
            "id": e.id or f"idx-{i}",
            "when": _when(e),
            "summary": e.summary[:120],
            "location": e.location[:80],
            "description": (e.description or "")[:300],
        }
        for i, e in enumerate(capped)
    ]

    prompt = (
        "Tu es un assistant qui détermine si un event d'agenda nécessite une "
        "action ou préparation concrète avant qu'il arrive.\n\n"
        "Marque needs_prep=true pour : vols/déplacements (check-in, bagages), "
        "conférences ou talks (slides, prep contenu), RDV médicaux (papiers, "
        "à jeun), RDV pro importants (préparer dossier, lire en amont), "
        "deadlines, anniversaires/cadeaux famille proches, démarches admin.\n\n"
        "Marque needs_prep=false pour : routines (sport, déjeuner régulier), "
        "events récurrents banals, créneaux libres, anniversaires Google de "
        "contacts lointains, all-day events purement informatifs.\n\n"
        "Events à classer :\n"
        f"{json.dumps(items, ensure_ascii=False, indent=2)}\n\n"
        "Réponds UNIQUEMENT avec un array JSON, un objet par event, format :\n"
        '[{"id": "<id>", "needs_prep": true|false, "why": "<1 phrase courte ou \\"\\">"}]'
    )

    resp = llm.call(
        tier=tier,
        messages=[{"role": "user", "content": prompt}],
        task=TASK,
        max_tokens=600,
        temperature=0.2,
    )
    try:
        parsed = _parse_json_array(resp.text)
    except (ValueError, json.JSONDecodeError) as e:
        log.warning("classif LLM non-parsable, skip section À préparer: %s", e)
        return []

    by_id = {item["id"]: item for item in items}
    out: list[tuple[calendar.CalendarEvent, str]] = []
    for entry in parsed:
        if not entry.get("needs_prep"):
            continue
        eid = entry.get("id")
        if eid not in by_id:
            continue
        # retrouve l'event par index ou id
        match = next(
            (e for i, e in enumerate(capped) if (e.id or f"idx-{i}") == eid),
            None,
        )
        if match is None:
            continue
        why = str(entry.get("why", "")).strip()
        out.append((match, why))
    return out


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


def _format_event_when(e: calendar.CalendarEvent) -> str:
    if e.all_day:
        return e.start.strftime("%a %d/%m")
    return e.start.strftime("%a %d/%m %Hh%M")


def _format_digest(
    today: date,
    drafts: list[dict[str, Any]],
    events_today: list[calendar.CalendarEvent],
    prep_events: list[tuple[calendar.CalendarEvent, str]],
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

    if prep_events:
        lines.append(f"À préparer ({LOOKAHEAD_DAYS}j) :")
        for ev, why in prep_events[:6]:
            when = _format_event_when(ev)
            title = ev.summary[:50] or "(sans titre)"
            tail = f" → {why}" if why else ""
            lines.append(f"- {when} : {title}{tail}")

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
    events = calendar.fetch_upcoming(days_ahead=LOOKAHEAD_DAYS, now=run_at)
    events_today = _today_events(events, today)
    events_lookahead = _lookahead_events(events, today)

    tier = cfg.get("model", "haiku")
    try:
        prep_events = _needs_prep_classify(events_lookahead, tier)
    except Exception:
        log.exception("classif needs_prep failed — section omise")
        prep_events = []

    budget = _budget_status()
    location = memory.read_location()

    message = _format_digest(today, drafts, events_today, prep_events, budget, location)

    sent = telegram.send(cfg.get("channel", "perso"), message, parse_mode=None)

    summary = (
        f"{len(drafts)} draft(s), {len(events_today)} évén. jour, "
        f"{len(prep_events)} à préparer — "
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
            "events_lookahead": len(events_lookahead),
            "prep_count": len(prep_events),
            "telegram_sent": sent,
        },
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    return schedule.run_guarded(TASK, run)


if __name__ == "__main__":
    raise SystemExit(main())
