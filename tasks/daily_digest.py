"""Digest matinal Telegram : drafts pendants, RDV du jour, 1 alerte.

V1 pur Python — aucun appel LLM. Les données sont déjà structurées, un
format déterministe est plus robuste (et gratuit). Le tier `haiku` dans
schedule.yaml est gardé pour un futur ajout de synthèse.

Whitelist policies : notification Telegram informative → envoi direct,
pas de draft.

Alerte (1 max, priorité descendante) :
1. dernière working-memory en `status: error` dans les 24h
2. budget tokens >= 80% du plafond mensuel
3. sinon aucune
"""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import yaml

from tasks._lib import calendar, llm, memory, paths, schedule, telegram
from tasks._lib.memory import MarkdownDoc, _parse_dt

TASK = "daily_digest"

log = logging.getLogger(TASK)

MAX_DRAFTS = 5
MAX_EVENTS = 5
ERROR_LOOKBACK_HOURS = 24
BUDGET_ALERT_PCT = 0.8
PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _load_pending_drafts(now: datetime) -> list[dict[str, Any]]:
    """Drafts avec status=pending et non expirés. Tri high>medium>low."""
    if not paths.DRAFTS.exists():
        return []
    today = now.date()
    out: list[dict[str, Any]] = []
    for p in sorted(paths.DRAFTS.glob("*.md")):
        try:
            doc = MarkdownDoc.read(p)
        except (OSError, yaml.YAMLError):
            continue
        fm = doc.front_matter
        if fm.get("status") != "pending":
            continue
        expires_raw = fm.get("expires_at")
        if expires_raw:
            try:
                exp_date = datetime.fromisoformat(str(expires_raw)).date()
                if exp_date < today:
                    continue
            except ValueError:
                pass
        out.append(
            {
                "title": str(fm.get("title") or p.stem),
                "priority": str(fm.get("priority") or "medium"),
                "type": str(fm.get("type") or "unknown"),
            }
        )
    out.sort(key=lambda d: PRIORITY_ORDER.get(d["priority"], 1))
    return out


def _today_events(now: datetime) -> list[calendar.CalendarEvent]:
    """Events qui démarrent d'ici minuit (calendrier perso, stub renvoie []
    sans GCAL_TOKEN_JSON)."""
    events = calendar.fetch_upcoming(days_ahead=1, now=now)
    end_of_day = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return [e for e in events if e.start <= end_of_day]


def _recent_errors(now: datetime) -> list[dict[str, Any]]:
    cutoff = now - timedelta(hours=ERROR_LOOKBACK_HOURS)
    out: list[dict[str, Any]] = []
    for path in memory.list_working_memory():
        try:
            doc = MarkdownDoc.read(path)
        except (OSError, yaml.YAMLError):
            continue
        if doc.front_matter.get("status") != "error":
            continue
        ts = _parse_dt(doc.front_matter.get("run_at"))
        if ts is None or ts < cutoff:
            continue
        out.append(
            {
                "task": doc.front_matter.get("task"),
                "summary": str(doc.front_matter.get("summary") or "")[:120],
                "at": ts,
            }
        )
    out.sort(key=lambda d: d["at"], reverse=True)
    return out


def _budget_ratio() -> tuple[float, float] | None:
    """(cost_usd, budget_usd) ou None si pas de données."""
    if not paths.USAGE_JSON.exists():
        return None
    try:
        data = json.loads(paths.USAGE_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    cost = float(data.get("cost_usd", 0.0))
    budget = llm._budget()
    return cost, budget


def _pick_alert(now: datetime) -> str | None:
    errors = _recent_errors(now)
    if errors:
        e = errors[0]
        when = e["at"].strftime("%H:%M UTC")
        summary = e["summary"] or "(pas de détail)"
        return f"⚠️ erreur {e['task']} à {when} — {summary}"
    budget = _budget_ratio()
    if budget:
        cost, cap = budget
        if cap > 0 and cost / cap >= BUDGET_ALERT_PCT:
            return f"⚠️ budget tokens à {cost / cap:.0%} (${cost:.2f} / ${cap:.2f})"
    return None


def _format_digest(
    now: datetime,
    drafts: list[dict[str, Any]],
    events: list[calendar.CalendarEvent],
    alert: str | None,
) -> str:
    date_str = now.strftime("%d/%m")
    lines = [f"☀️ digest {date_str}"]

    if drafts:
        shown = drafts[:MAX_DRAFTS]
        extra = len(drafts) - len(shown)
        lines.append("")
        lines.append(f"📋 drafts pendants ({len(drafts)})")
        for d in shown:
            prio = (d["priority"] or "medium")[0].upper()  # H/M/L
            lines.append(f"• [{prio}] {d['title']}")
        if extra > 0:
            lines.append(f"… +{extra} autre(s)")

    if events:
        lines.append("")
        lines.append("📅 aujourd'hui")
        for e in events[:MAX_EVENTS]:
            t = e.start.strftime("%H:%M")
            loc = f" @ {e.location}" if e.location else ""
            lines.append(f"• {t} — {e.summary}{loc}")

    if alert:
        lines.append("")
        lines.append(alert)

    if not drafts and not events and not alert:
        lines.append("RAS — 0 draft, pas de RDV connu, no incident.")

    return "\n".join(lines)


def run(cfg: dict[str, Any]) -> None:
    run_at = datetime.now(UTC)

    drafts = _load_pending_drafts(run_at)
    events = _today_events(run_at)
    alert = _pick_alert(run_at)

    message = _format_digest(run_at, drafts, events, alert)
    channel = cfg.get("channel", "perso")
    sent = telegram.send(channel, message, parse_mode=None)

    summary = (
        f"{len(drafts)} draft(s), {len(events)} event(s), "
        f"alert={'yes' if alert else 'no'}, sent={sent}"
    )

    memory.write_run_log(
        task=TASK,
        run_at=run_at,
        status="completed",
        summary=summary,
        body="## Message envoyé\n```\n" + message + "\n```",
        extra={
            "sent": sent,
            "drafts_count": len(drafts),
            "events_count": len(events),
            "alert": bool(alert),
        },
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    return schedule.run_guarded(TASK, run)


if __name__ == "__main__":
    raise SystemExit(main())
