"""Look-forward hebdo 20j — gros événements à anticiper.

Tourne tous les dimanches à 18:00 UTC (20:00 Paris). Pas vacation_safe :
en vacances on n'a pas besoin de préparer la semaine pro.

Pipeline :
1. Fetch tous les calendars sur 20j.
2. Haiku classifie en buckets `major` (vol, deadline, conf, rdv médical,
   famille important) / `prepare` (prep mais pas critique) / `routine`.
3. Formate les `major` + `prepare` groupés par semaine ISO, envoie Telegram.
4. Skip silencieux si aucun event qualifiant.

Coût par run : ~$0.003 (un appel Haiku sur 20j).
"""
from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime, timedelta
from typing import Any

from tasks._lib import calendar, llm, memory, schedule, telegram

TASK = "weekly_lookahead"

log = logging.getLogger(TASK)

LOOKAHEAD_DAYS = 20
MAX_EVENTS_TO_CLASSIFY = 60
BUCKETS = ("major", "prepare", "routine")


def _parse_json_array(text: str) -> list[dict[str, Any]]:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise ValueError("no JSON array found")
    return json.loads(text[start : end + 1])


def _format_event_when(e: calendar.CalendarEvent) -> str:
    if e.all_day:
        return e.start.strftime("%a %d/%m")
    return e.start.strftime("%a %d/%m %Hh%M")


def _classify(
    events: list[calendar.CalendarEvent], tier: str
) -> list[tuple[calendar.CalendarEvent, str, str]]:
    """Retourne [(event, bucket, why)] pour les events bucket=major|prepare."""
    if not events:
        return []
    capped = events[:MAX_EVENTS_TO_CLASSIFY]

    def _when(e: calendar.CalendarEvent) -> str:
        if e.all_day:
            return e.start.strftime("%a %Y-%m-%d (all-day)")
        return e.start.strftime("%a %Y-%m-%d %Hh%M")

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
        "Tu classes les events agenda de Sylvain sur les 20 prochains jours "
        "en 3 buckets, pour un briefing hebdo du dimanche soir.\n\n"
        "- `major` : événement important à anticiper. Vols/déplacements, "
        "conférences ou talks, deadlines, RDV médicaux importants, "
        "anniversaires/événements famille proche (Isa, enfants, parents), "
        "RDV pro stratégiques.\n"
        "- `prepare` : nécessite une préparation concrète mais moins "
        "critique. RDV pro normal nécessitant lecture amont, démarche admin, "
        "cadeau à acheter, etc.\n"
        "- `routine` : à ignorer. Sport hebdo, déjeuners récurrents, "
        "anniversaires Google de contacts lointains, créneaux libres, "
        "all-day informatifs sans action.\n\n"
        "Events à classer :\n"
        f"{json.dumps(items, ensure_ascii=False, indent=2)}\n\n"
        "Réponds UNIQUEMENT avec un array JSON, format :\n"
        '[{"id": "<id>", "bucket": "major|prepare|routine", "why": "<1 phrase courte>"}]'
    )

    resp = llm.call(
        tier=tier,
        messages=[{"role": "user", "content": prompt}],
        task=TASK,
        max_tokens=1500,
        temperature=0.2,
    )

    parsed = _parse_json_array(resp.text)
    out: list[tuple[calendar.CalendarEvent, str, str]] = []
    for entry in parsed:
        bucket = str(entry.get("bucket", "")).lower()
        if bucket not in ("major", "prepare"):
            continue
        eid = entry.get("id")
        match = next(
            (e for i, e in enumerate(capped) if (e.id or f"idx-{i}") == eid),
            None,
        )
        if match is None:
            continue
        why = str(entry.get("why", "")).strip()
        out.append((match, bucket, why))
    out.sort(key=lambda t: (t[0].start, 0 if t[1] == "major" else 1))
    return out


def _format_message(
    classified: list[tuple[calendar.CalendarEvent, str, str]],
    now: datetime,
) -> str:
    """Groupe par semaine ISO, sépare major (★) et prepare (•)."""
    if not classified:
        return ""

    by_week: dict[tuple[int, int], list[tuple[calendar.CalendarEvent, str, str]]] = {}
    for ev, bucket, why in classified:
        key = ev.start.isocalendar()[:2]
        by_week.setdefault(key, []).append((ev, bucket, why))

    today = now.date()
    lines: list[str] = [f"Look-forward 20j ({today.strftime('%d/%m')})"]
    for week_key in sorted(by_week):
        year, week_num = week_key
        # En-tête semaine : "Sem. 21 (18→24/05)" — bornes lundi/dimanche
        monday = datetime.fromisocalendar(year, week_num, 1).date()
        sunday = monday + timedelta(days=6)
        lines.append(f"\nSem. {week_num} ({monday.strftime('%d/%m')}→{sunday.strftime('%d/%m')})")
        for ev, bucket, why in by_week[week_key]:
            mark = "★" if bucket == "major" else "•"
            when = _format_event_when(ev)
            title = ev.summary[:55] or "(sans titre)"
            tail = f" → {why}" if why else ""
            lines.append(f"{mark} {when} : {title}{tail}")
    return "\n".join(lines)


def run(cfg: dict[str, Any]) -> None:
    run_at = datetime.now(UTC)

    events = calendar.fetch_upcoming(days_ahead=LOOKAHEAD_DAYS, now=run_at)
    if not events:
        log.info("aucun event sur %sj — skip silencieux", LOOKAHEAD_DAYS)
        memory.write_run_log(
            task=TASK,
            run_at=run_at,
            status="completed",
            summary="no events in 20d window — nothing to surface",
            extra={"events_total": 0, "major_prepare": 0, "telegram_sent": False},
        )
        return

    tier = cfg.get("model", "haiku")
    classified = _classify(events, tier)

    if not classified:
        log.info("aucun event major/prepare détecté — skip silencieux")
        memory.write_run_log(
            task=TASK,
            run_at=run_at,
            status="completed",
            summary=f"{len(events)} events scannés, aucun major/prepare",
            extra={
                "events_total": len(events),
                "major_prepare": 0,
                "telegram_sent": False,
            },
        )
        return

    message = _format_message(classified, run_at)
    sent = telegram.send(cfg.get("channel", "perso"), message, parse_mode=None)

    major_count = sum(1 for _, b, _ in classified if b == "major")
    prepare_count = len(classified) - major_count
    summary = (
        f"{major_count} major + {prepare_count} prepare sur {len(events)} events — "
        + ("envoyé Telegram" if sent else "Telegram off, log only")
    )

    memory.write_run_log(
        task=TASK,
        run_at=run_at,
        status="completed",
        summary=summary,
        body="## Message\n```\n" + message + "\n```",
        extra={
            "events_total": len(events),
            "major_prepare": len(classified),
            "major_count": major_count,
            "prepare_count": prepare_count,
            "telegram_sent": sent,
        },
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    return schedule.run_guarded(TASK, run)


if __name__ == "__main__":
    raise SystemExit(main())
