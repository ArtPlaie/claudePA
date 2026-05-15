"""Détection de localisation : voyages + flag vacation_mode.

Sources :
- Google Calendar (next 14j) — voir tasks/_lib/calendar.py
- inbox/ (Telegram déposé par le Worker, 7j) — voir tasks/_lib/inbox.py

Sortie : écrit core-memory/current-location.md uniquement si le LLM
estime que la localisation ou le flag vacances doivent changer.

Tant que GCAL_TOKEN_JSON n'est pas configuré ET que le Worker n'écrit
pas dans inbox/, la tâche est un no-op silencieux (aucun appel LLM).
"""
from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from typing import Any

import yaml

from tasks._lib import calendar, inbox, llm, memory, paths, schedule
from tasks._lib.memory import MarkdownDoc

TASK = "location_context"

log = logging.getLogger(TASK)


def _format_events(events: list[calendar.CalendarEvent]) -> str:
    if not events:
        return "aucun"
    return "\n".join(
        f"- {e.start.strftime('%Y-%m-%d')} → {e.end.strftime('%Y-%m-%d')}: "
        f"{e.summary}" + (f" @ {e.location}" if e.location else "")
        for e in events
    )


def _format_inbox(msgs: list[inbox.InboxMessage]) -> str:
    if not msgs:
        return "aucun"
    return "\n".join(
        f"- {m.timestamp.strftime('%Y-%m-%d %H:%M')} ({m.channel}): {m.text[:200]}"
        for m in msgs
    )


_PROMPT = """\
Tu es un module de détection de localisation pour l'assistant perso de Sylvain.

# État actuel (core-memory/current-location.md)

{current_yaml}

# Signaux

## Calendar (14j à venir)
{events}

## Inbox récente (7j passés)
{messages}

# Tâche
Détermine si Sylvain a changé de localisation, ou est en vacances.

Heuristique :
- mots-clés "vacances", "voyage", "trip", "absence", "off", "vac", "AFK" dans
  agenda ou chats sur plusieurs jours consécutifs → vacation_mode=true
- mention d'une ville/pays ≠ Bois-le-Roi sur plusieurs jours → location change
- sinon, conserve l'état actuel à l'identique

Réponds UNIQUEMENT avec un JSON, pas de prose autour, pas de bloc code :
{{
  "location": "<ville (CP, pays)>",
  "status": "home" | "travel" | "vacation",
  "vacation_mode": true | false,
  "horizon": "<YYYY-MM-DD ou 'indefinite'>",
  "summary": "<2 lignes factuelles>"
}}
"""


def _parse_llm_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            return None
    return None


def _update_location_file(decision: dict[str, Any], run_at: datetime) -> bool:
    """Réécrit current-location.md si la décision diffère. Retourne True ssi modifié."""
    cur_doc = MarkdownDoc.read(paths.CURRENT_LOCATION)
    cur_fm = cur_doc.front_matter

    changed = False
    new_fm = dict(cur_fm)
    for key in ("location", "status", "vacation_mode", "horizon"):
        if key in decision and decision[key] != cur_fm.get(key):
            new_fm[key] = decision[key]
            changed = True

    if not changed:
        return False

    new_fm["since"] = run_at.date().isoformat()
    new_fm["updated_by"] = TASK
    new_fm["updated_at"] = run_at.date().isoformat()

    summary = str(decision.get("summary", "")).strip()
    body = (
        "\n# Current location\n\n"
        + (summary + "\n" if summary else "")
        + "\n> Ce fichier est mis à jour quotidiennement par la tâche\n"
        "> `location_context` qui scanne le calendar et l'inbox pour détecter\n"
        "> voyages et changements temporaires de localisation. Les tâches\n"
        "> sensibles à la localisation (`local_activities`,\n"
        "> `activities_next10days`) lisent ce fichier en priorité.\n"
    )

    MarkdownDoc(front_matter=new_fm, body=body).write(paths.CURRENT_LOCATION)
    return True


def run(cfg: dict[str, Any]) -> None:
    run_at = datetime.now(UTC)
    events = calendar.fetch_upcoming(days_ahead=14, now=run_at)
    messages = inbox.read_recent(days_back=7, now=run_at)

    if not events and not messages:
        log.info("aucun signal — no-op")
        return

    current = memory.read_location()
    current_yaml = yaml.safe_dump(current, allow_unicode=True, sort_keys=False).strip()

    prompt = _PROMPT.format(
        current_yaml=current_yaml,
        events=_format_events(events),
        messages=_format_inbox(messages),
    )

    resp = llm.call(
        tier=cfg.get("model", "haiku"),
        messages=[{"role": "user", "content": prompt}],
        task=TASK,
        max_tokens=400,
        temperature=0.2,
    )

    decision = _parse_llm_json(resp.text)
    if decision is None:
        raise ValueError(f"LLM returned non-JSON: {resp.text[:200]!r}")

    changed = _update_location_file(decision, run_at)
    extra: dict[str, Any] = {"changed": changed}
    if changed:
        extra["new_location"] = decision.get("location")
        extra["vacation_mode"] = decision.get("vacation_mode")

    summary = (
        f"location updated → {decision.get('location')} (vacation_mode={decision.get('vacation_mode')})"
        if changed
        else "no change"
    )

    memory.write_run_log(
        task=TASK,
        run_at=run_at,
        status="completed",
        model=resp.model,
        tokens_in=resp.tokens_in,
        tokens_out=resp.tokens_out,
        summary=summary,
        body="## Décision LLM\n```json\n"
        + json.dumps(decision, indent=2, ensure_ascii=False)
        + "\n```",
        extra=extra,
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    return schedule.run_guarded(TASK, run)


if __name__ == "__main__":
    raise SystemExit(main())
