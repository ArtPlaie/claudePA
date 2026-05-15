"""Digest matinal Telegram : drafts pendants, RDV du jour, 1 alerte.

Pipeline :
1. Python collecte les data brutes (drafts, events, errors, budget).
2. Haiku synthétise en 3-5 lignes (ton Sylvain hérité du cache
   profile+policies, déjà chargé dans `_lib/llm.py`).
3. Envoi Telegram direct (whitelist policies — notif informative).

Court-circuits :
- Tout vide (0 draft, 0 event, 0 alerte) → message "RAS" hardcodé,
  pas d'appel LLM (économie de tokens).
- Appel LLM raté → fallback déterministe Python (mieux que rien).
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
        created_raw = fm.get("created_at")
        age_days: int | None = None
        if created_raw:
            ts = _parse_dt(created_raw)
            if ts is not None:
                age_days = (now - ts).days
        out.append(
            {
                "title": str(fm.get("title") or p.stem),
                "priority": str(fm.get("priority") or "medium"),
                "type": str(fm.get("type") or "unknown"),
                "age_days": age_days,
            }
        )
    out.sort(key=lambda d: PRIORITY_ORDER.get(d["priority"], 1))
    return out


def _today_events(now: datetime) -> list[calendar.CalendarEvent]:
    """Events qui démarrent d'ici minuit (stub renvoie [] sans GCAL)."""
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
        return f"erreur {e['task']} à {when} — {summary}"
    budget = _budget_ratio()
    if budget:
        cost, cap = budget
        if cap > 0 and cost / cap >= BUDGET_ALERT_PCT:
            return f"budget tokens à {cost / cap:.0%} (${cost:.2f} / ${cap:.2f})"
    return None


def _format_drafts_block(drafts: list[dict[str, Any]]) -> str:
    if not drafts:
        return "aucun"
    shown = drafts[:MAX_DRAFTS]
    lines = []
    for d in shown:
        age = f", {d['age_days']}j" if d.get("age_days") is not None else ""
        lines.append(
            f"- [{d['priority']}] {d['title']} (type: {d['type']}{age})"
        )
    extra = len(drafts) - len(shown)
    if extra > 0:
        lines.append(f"- … +{extra} autre(s) non détaillé(s)")
    return "\n".join(lines)


def _format_events_block(events: list[calendar.CalendarEvent]) -> str:
    if not events:
        return "aucun (ou Google Calendar pas encore wiré)"
    lines = []
    for e in events[:MAX_EVENTS]:
        t = e.start.strftime("%H:%M")
        loc = f" @ {e.location}" if e.location else ""
        lines.append(f"- {t} — {e.summary}{loc}")
    return "\n".join(lines)


_PROMPT = """\
Tu rédiges le digest matinal Telegram de Sylvain. Style ton dans profile/policies (déjà en cache).

Date : {date}

# Drafts pendants ({n_drafts})
{drafts}

# RDV aujourd'hui ({n_events})
{events}

# Alerte candidate
{alert}

# Consignes
- 3 à 5 lignes max, format Telegram plain text (pas de Markdown, pas de listes à puces).
- Démarre par "☀️ {date}" sur la 1ère ligne.
- Mentionne uniquement ce qui mérite attention : drafts high-prio, RDV serrés ou inhabituels, l'alerte si pertinente.
- Si rien de saillant, dis-le franchement en 1-2 lignes.
- Ne sors pas un dump exhaustif — c'est un digest, pas un listing. Si 5 drafts, mentionne le nombre + le plus urgent.
- Pas de salutation, pas de signature, pas de question rhétorique.

Sors uniquement le texte à envoyer, rien d'autre.
"""


def _fallback_message(
    now: datetime,
    drafts: list[dict[str, Any]],
    events: list[calendar.CalendarEvent],
    alert: str | None,
) -> str:
    """Format déterministe si LLM indisponible. Pas joli mais informatif."""
    date_str = now.strftime("%d/%m")
    lines = [f"☀️ {date_str}"]
    if drafts:
        top = drafts[0]
        lines.append(
            f"drafts pendants: {len(drafts)} (top: [{top['priority']}] {top['title']})"
        )
    if events:
        first = events[0]
        lines.append(f"RDV: {first.start.strftime('%H:%M')} {first.summary}"
                     + (f" +{len(events) - 1}" if len(events) > 1 else ""))
    if alert:
        lines.append(f"⚠️ {alert}")
    if not drafts and not events and not alert:
        lines.append("RAS.")
    return "\n".join(lines)


def _llm_digest(
    *,
    now: datetime,
    drafts: list[dict[str, Any]],
    events: list[calendar.CalendarEvent],
    alert: str | None,
    cfg: dict[str, Any],
) -> tuple[str, llm.LLMResponse]:
    prompt = _PROMPT.format(
        date=now.strftime("%d/%m"),
        n_drafts=len(drafts),
        drafts=_format_drafts_block(drafts),
        n_events=len(events),
        events=_format_events_block(events),
        alert=alert or "rien à signaler",
    )
    resp = llm.call(
        tier=cfg.get("model", "haiku"),
        messages=[{"role": "user", "content": prompt}],
        task=TASK,
        max_tokens=300,
        temperature=0.5,
    )
    return resp.text.strip(), resp


def run(cfg: dict[str, Any]) -> None:
    run_at = datetime.now(UTC)

    drafts = _load_pending_drafts(run_at)
    events = _today_events(run_at)
    alert = _pick_alert(run_at)

    used_llm = False
    llm_error: str | None = None
    model: str | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None

    if not drafts and not events and not alert:
        message = f"☀️ {run_at.strftime('%d/%m')}\nRAS."
    else:
        try:
            message, resp = _llm_digest(
                now=run_at, drafts=drafts, events=events, alert=alert, cfg=cfg
            )
            used_llm = True
            model = resp.model
            tokens_in = resp.tokens_in
            tokens_out = resp.tokens_out
        except Exception as e:
            log.warning("LLM digest failed, fallback déterministe: %s", e)
            llm_error = f"{type(e).__name__}: {e}"
            message = _fallback_message(run_at, drafts, events, alert)

    channel = cfg.get("channel", "perso")
    sent = telegram.send(channel, message, parse_mode=None)

    extra: dict[str, Any] = {
        "sent": sent,
        "drafts_count": len(drafts),
        "events_count": len(events),
        "alert": bool(alert),
        "used_llm": used_llm,
    }
    if llm_error:
        extra["llm_error"] = llm_error

    summary = (
        f"{len(drafts)} draft(s), {len(events)} event(s), "
        f"alert={'yes' if alert else 'no'}, "
        f"llm={'yes' if used_llm else 'no'}, sent={sent}"
    )

    memory.write_run_log(
        task=TASK,
        run_at=run_at,
        status="completed",
        model=model,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        summary=summary,
        body="## Message envoyé\n```\n" + message + "\n```",
        extra=extra,
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    return schedule.run_guarded(TASK, run)


if __name__ == "__main__":
    raise SystemExit(main())
