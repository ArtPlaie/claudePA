"""Briefing hebdo horizon 10 jours.

Pipeline :
1. Python collecte : drafts pendants (10j), events calendar 10j, findings
   récents, décisions récentes, localisation actuelle.
2. Sonnet synthétise (cache profile+policies hérité) avec accès web_search
   léger (max 3 uses) pour les activités/événements à venir.
3. Envoi Telegram direct (whitelist policies — notif informative).

Fallback : si Sonnet échoue, on envoie un résumé déterministe Python.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from tasks._lib import calendar, llm, memory, paths, schedule, telegram

TASK = "weekly_briefing"

log = logging.getLogger(TASK)

HORIZON_DAYS = 10
MAX_FINDINGS_CHARS = 2500
MAX_DECISIONS_CHARS = 2000
WEB_SEARCH_MAX = 3


def _format_drafts(drafts: list[dict[str, Any]]) -> str:
    if not drafts:
        return "aucun"
    lines = []
    for d in drafts:
        age = f", {d['age_days']}j" if d.get("age_days") is not None else ""
        lines.append(f"- [{d['priority']}] {d['title']} (type: {d['type']}{age})")
    return "\n".join(lines)


def _format_events(events: list[calendar.CalendarEvent]) -> str:
    if not events:
        return "aucun (ou Google Calendar pas encore wiré)"
    lines = []
    for e in events:
        when = e.start.strftime("%a %d/%m %H:%M")
        loc = f" @ {e.location}" if e.location else ""
        lines.append(f"- {when} — {e.summary}{loc}")
    return "\n".join(lines)


def _format_location(loc: dict[str, Any]) -> str:
    if not loc:
        return "inconnue"
    parts = [str(loc.get("location") or "")]
    status = loc.get("status")
    if status and status != "home":
        parts.append(f"({status})")
    if loc.get("vacation_mode"):
        parts.append("[mode vacances]")
    return " ".join(p for p in parts if p) or "inconnue"


_PROMPT = """\
Tu rédiges le briefing hebdomadaire "horizon 10 jours" de Sylvain.
Style ton dans profile.md / policies.md (déjà en cache).

Période couverte : {date_from} → {date_to}.
Localisation actuelle : {location}

# Drafts pendants pertinents ({n_drafts})
{drafts}

# RDV calendrier 10 jours ({n_events})
{events}

# Findings récents (queue de digests/findings.md)
{findings}

# Décisions récentes (queue de journal/decisions.md)
{decisions}

# Consignes

Format : message Telegram plain text, 10-20 lignes max.

Structure suggérée (omets toute section vide) :
1. Première ligne : "🗓️ horizon 10j — {date_from}"
2. **À traiter / décider** — drafts high-prio, échéances visibles dans les RDV, deadlines.
3. **Semaine qui vient** — RDV saillants (pas un dump exhaustif, ce qui mérite attention).
4. **Activités / sorties proposées** — utilise web_search (max {ws} uses) pour trouver des événements près de {location} ce week-end ou la semaine prochaine (sorties culturelles, famille, intello). Donne le nom + jour + 1 ligne de pourquoi.
5. **À garder en tête** — 1 fil stratégique issu des findings/decisions si pertinent.

Règles :
- Pas de salutation, pas de signature, pas de question rhétorique.
- Pas de markdown lourd (pas de #, *, `). Tirets et émojis sobres OK.
- Si une section est vide ou non saillante, omets-la franchement.
- Évite le ton corporate / coaching. Direct, evidence-based.

Sors uniquement le briefing, rien d'autre.
"""


def _fallback_message(
    now: datetime,
    drafts: list[dict[str, Any]],
    events: list[calendar.CalendarEvent],
) -> str:
    date_str = now.strftime("%d/%m")
    lines = [f"🗓️ horizon 10j — {date_str}", "(LLM indispo, dump brut)"]
    if drafts:
        lines.append(f"\n{len(drafts)} draft(s) pendants :")
        for d in drafts[:5]:
            lines.append(f"- [{d['priority']}] {d['title']}")
        if len(drafts) > 5:
            lines.append(f"… +{len(drafts) - 5}")
    if events:
        lines.append(f"\n{len(events)} RDV :")
        for e in events[:5]:
            lines.append(f"- {e.start.strftime('%a %d %H:%M')} {e.summary}")
        if len(events) > 5:
            lines.append(f"… +{len(events) - 5}")
    if not drafts and not events:
        lines.append("Pas de draft pendant, pas de RDV connu.")
    return "\n".join(lines)


def run(cfg: dict[str, Any]) -> None:
    run_at = datetime.now(UTC)
    date_to = run_at + timedelta(days=HORIZON_DAYS)

    drafts = memory.list_pending_drafts(now=run_at, horizon_days=HORIZON_DAYS)
    events = calendar.fetch_upcoming(days_ahead=HORIZON_DAYS, now=run_at)
    findings = memory.tail_lines(paths.FINDINGS, max_chars=MAX_FINDINGS_CHARS)
    decisions = memory.tail_lines(paths.DECISIONS, max_chars=MAX_DECISIONS_CHARS)
    location = memory.read_location()

    used_llm = False
    llm_error: str | None = None
    model: str | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None

    prompt = _PROMPT.format(
        date_from=run_at.strftime("%d/%m"),
        date_to=date_to.strftime("%d/%m"),
        location=_format_location(location),
        n_drafts=len(drafts),
        drafts=_format_drafts(drafts),
        n_events=len(events),
        events=_format_events(events),
        findings=findings or "(vide)",
        decisions=decisions or "(vide)",
        ws=WEB_SEARCH_MAX,
    )

    try:
        resp = llm.call(
            tier=cfg.get("model", "sonnet"),
            messages=[{"role": "user", "content": prompt}],
            task=TASK,
            max_tokens=2000,
            temperature=0.6,
            web_search=True,
            web_search_max_uses=WEB_SEARCH_MAX,
        )
        message = resp.text.strip()
        used_llm = True
        model = resp.model
        tokens_in = resp.tokens_in
        tokens_out = resp.tokens_out
    except Exception as e:
        log.warning("LLM briefing failed, fallback déterministe: %s", e)
        llm_error = f"{type(e).__name__}: {e}"
        message = _fallback_message(run_at, drafts, events)

    channel = cfg.get("channel", "perso")
    sent = telegram.send(channel, message, parse_mode=None)

    summary = (
        f"{len(drafts)} draft(s), {len(events)} event(s), "
        f"llm={'yes' if used_llm else 'no'}, sent={sent}"
    )
    extra: dict[str, Any] = {
        "sent": sent,
        "drafts_count": len(drafts),
        "events_count": len(events),
        "used_llm": used_llm,
    }
    if llm_error:
        extra["llm_error"] = llm_error[:200]

    memory.write_run_log(
        task=TASK,
        run_at=run_at,
        status="completed",
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        summary=summary,
        body="## Briefing envoyé\n```\n" + message + "\n```",
        extra=extra,
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    return schedule.run_guarded(TASK, run)


if __name__ == "__main__":
    raise SystemExit(main())
