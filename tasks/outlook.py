"""Outlook horizon 3 mois — 1 axe par run.

Cron daily 18h UTC. Lit `core-memory/outlook-axes.yaml`, regarde la date
du jour : si un axe matche `day_of_month`, on l'exécute. Sinon skip silent.

Étalement naturel : 1 axe / semaine (jours 1, 8, 15, 22, 28 par défaut).
Tier configurable par axe → Opus pour les axes "stratégiques" (formuler de
meilleures queries web_search, filtrer le bruit), Sonnet pour le scan factuel.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import yaml

from tasks._lib import llm, memory, paths, schedule, telegram

TASK = "outlook"
log = logging.getLogger(TASK)

AXES_FILE = paths.REPO_ROOT / "core-memory" / "outlook-axes.yaml"
MAX_FINDINGS_CHARS = 3000
MAX_DECISIONS_CHARS = 2000
TELEGRAM_LIMIT = 3800


def _load_axes() -> dict[str, Any]:
    if not AXES_FILE.exists():
        return {}
    return yaml.safe_load(AXES_FILE.read_text(encoding="utf-8")) or {}


def _select_axis_for_today(cfg: dict[str, Any], today_day: int) -> dict[str, Any] | None:
    matched = [a for a in cfg.get("axes", []) if a.get("day_of_month") == today_day]
    if not matched:
        return None
    if len(matched) > 1:
        log.warning(
            "plusieurs axes pour jour %d, prend le premier: %s",
            today_day,
            [a.get("slug") for a in matched],
        )
    return matched[0]


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


def _format_hints(hints: list[str] | None) -> str:
    if not hints:
        return "(aucune)"
    return "\n".join(f"- {h}" for h in hints)


_PROMPT = """\
Tu rédiges l'outlook horizon 3 mois sur l'axe **{title}** pour Sylvain.
Style ton dans profile.md / policies.md (cache).

Date du run : {date_today}
Horizon : maintenant → {date_horizon}
Localisation : {location}

# Focus de l'axe
{focus}

# Findings récents (queue de digests/findings.md)
{findings}

# Décisions récentes (queue de journal/decisions.md)
{decisions}

# Recherche
Fais jusqu'à {ws} web_search pour anticiper les 3 prochains mois sur cet axe.
Formule des queries spécifiques, chaînées si nécessaire (un résultat te
suggère la query suivante). Privilégie sources primaires (site officiel,
job board direct, page programme) sur agrégateurs.

Queries-hints (libre à toi de t'en écarter / les raffiner) :
{queries_hints}

# Output
Format : message Telegram plain text. Première ligne = "{title}".

Pour chaque info pertinente :
- 2-4 lignes factuelles
- Une URL source par item (la plus utile, pas plusieurs)
- Si une deadline est connue, mets-la en évidence

Si rien d'actionnable ce trimestre, dis-le franchement ("RAS sur cet axe").

Termine par "## À planifier" : 2-5 bullets actionnables (verbes infinitif,
dates quand connues). Pas de fluff.

Pas de salutation, pas de signature, pas de markdown lourd.
"""


def _chunk_for_telegram(text: str, limit: int = TELEGRAM_LIMIT) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    remaining = text
    while len(remaining) > limit:
        cut = remaining.rfind("\n\n", 0, limit)
        if cut == -1:
            cut = remaining.rfind("\n", 0, limit)
        if cut == -1:
            cut = limit
        chunks.append(remaining[:cut].rstrip())
        remaining = remaining[cut:].lstrip()
    if remaining:
        chunks.append(remaining)
    return chunks


def run(cfg: dict[str, Any]) -> None:
    run_at = datetime.now(UTC)

    axes_cfg = _load_axes()
    if not axes_cfg:
        memory.write_run_log(
            task=TASK,
            run_at=run_at,
            status="skipped",
            summary="outlook-axes.yaml absent ou vide",
        )
        return

    axis = _select_axis_for_today(axes_cfg, run_at.day)
    if axis is None:
        memory.write_run_log(
            task=TASK,
            run_at=run_at,
            status="skipped",
            summary=f"aucun axe pour le jour {run_at.day}",
        )
        return

    defaults = axes_cfg.get("defaults") or {}
    tier = str(axis.get("tier") or defaults.get("tier") or "sonnet")
    ws_max = int(axis.get("web_search_max") or defaults.get("web_search_max") or 8)
    horizon_days = 30 * int(axes_cfg.get("horizon_months") or 3)
    horizon = run_at + timedelta(days=horizon_days)

    findings = memory.tail_lines(paths.FINDINGS, max_chars=MAX_FINDINGS_CHARS)
    decisions = memory.tail_lines(paths.DECISIONS, max_chars=MAX_DECISIONS_CHARS)
    location = memory.read_location()

    prompt = _PROMPT.format(
        title=axis.get("title") or axis["slug"],
        date_today=run_at.strftime("%d/%m/%Y"),
        date_horizon=horizon.strftime("%d/%m/%Y"),
        location=_format_location(location),
        focus=(axis.get("focus") or "").strip() or "(non précisé)",
        findings=findings or "(vide)",
        decisions=decisions or "(vide)",
        ws=ws_max,
        queries_hints=_format_hints(axis.get("queries_hints")),
    )

    used_llm = False
    llm_error: str | None = None
    model: str | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    title = axis.get("title") or axis["slug"]

    try:
        resp = llm.call(
            tier=tier,
            messages=[{"role": "user", "content": prompt}],
            task=TASK,
            max_tokens=4000,
            temperature=0.5,
            web_search=True,
            web_search_max_uses=ws_max,
        )
        message = resp.text.strip()
        used_llm = True
        model = resp.model
        tokens_in = resp.tokens_in
        tokens_out = resp.tokens_out
    except Exception as e:
        log.warning("LLM outlook failed: %s", e)
        llm_error = f"{type(e).__name__}: {e}"
        message = (
            f"{title} — {run_at.strftime('%d/%m/%Y')}\n"
            f"(LLM indispo — {llm_error[:140]})"
        )

    channel = cfg.get("channel", "perso")
    chunks = _chunk_for_telegram(message)
    sent_count = 0
    for i, chunk in enumerate(chunks, 1):
        prefix = f"[{i}/{len(chunks)}] " if len(chunks) > 1 else ""
        if telegram.send(channel, prefix + chunk, parse_mode=None):
            sent_count += 1

    summary = (
        f"axis={axis['slug']}, tier={tier}, ws={ws_max}, "
        f"chunks={len(chunks)}, sent={sent_count}, "
        f"llm={'yes' if used_llm else 'no'}"
    )
    extra: dict[str, Any] = {
        "axis": axis["slug"],
        "tier": tier,
        "web_search_max": ws_max,
        "chunks": len(chunks),
        "sent": sent_count,
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
        body="## Output\n```\n" + message + "\n```",
        extra=extra,
        suffix=f"-{axis['slug']}",
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    return schedule.run_guarded(TASK, run)


if __name__ == "__main__":
    raise SystemExit(main())
