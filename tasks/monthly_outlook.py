"""Outlook mensuel horizon 3 mois — grosse recherche prospective.

Différent du weekly_briefing :
- weekly_briefing : horizon 10j, actionnable court terme, search léger
- monthly_outlook : horizon 3 mois, anticipation stratégique, search lourd

Sonnet avec web_search server-side intensif (max 10 uses). Le modèle
balaye les axes de profile.md (Australie/visa, AI Safety, Sydney/Suisse,
échéances famille/santé) pour identifier ce qui mérite préparation
maintenant pour ne pas être pris de court dans 1-3 mois.

Output : briefing long (~30-50 lignes) envoyé sur Telegram perso +
sauvegarde working-memory pour relecture.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from tasks._lib import llm, memory, paths, schedule, telegram

TASK = "monthly_outlook"

log = logging.getLogger(TASK)

HORIZON_MONTHS = 3
MAX_FINDINGS_CHARS = 5000
MAX_DECISIONS_CHARS = 3000
WEB_SEARCH_MAX = 10
TELEGRAM_LIMIT = 3800  # marge sous les 4096 chars de l'API


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
Tu rédiges l'outlook mensuel "horizon 3 mois" de Sylvain.
Style ton dans profile.md / policies.md (déjà en cache).

Date : {date_today}
Horizon : maintenant → {date_horizon}
Localisation actuelle : {location}

# Findings récents (digests/findings.md)
{findings}

# Décisions récentes (journal/decisions.md)
{decisions}

# Mission

Pour chaque axe ci-dessous, fais 1-2 recherches web pour identifier ce
qui mérite préparation/anticipation dans les 3 prochains mois.
Budget total : {ws} web_search uses max.

Axes (inspirés de profile.md) :
1. **Australie / visa PR** : actualités immigration AU pour profils
   visa PR / 189, étapes travel facility, deadlines à anticiper.
2. **AI Safety / alignement** : formations qui ouvrent (MATS, ARENA,
   Anthropic Fellows, masters), conférences/ateliers, cohorts à venir
   sur les 3 mois.
3. **Jobs Sydney / Suisse** : postes alignment / AI safety / policy
   avec close date dans les 3 mois, organisations qui recrutent.
4. **Santé / admin** : renouvellements (passeport, ordonnances,
   contrôles annuels), échéances visibles.
5. **Famille / agenda** : vacances scolaires Île-de-France à venir,
   ponts/jours fériés, fenêtres d'organisation.

# Output

Format : briefing structuré, plain text Telegram (pas de markdown lourd,
émojis sobres OK).

Pour chaque axe :
- 1 titre court (ex: "🇦🇺 Australie / visa")
- 3-5 lignes d'analyse factuelle + sources URL quand pertinent
- "RAS sur cet axe ce trimestre" si rien d'actionnable

Termine par une section **"À planifier ce mois"** avec 3-7 bullets
actionnables (verbes à l'infinitif, échéances quand connues).

Pas de salutation, pas de signature. Va à l'essentiel, evidence-based.
"""


def _chunk_for_telegram(text: str, limit: int = TELEGRAM_LIMIT) -> list[str]:
    """Split en morceaux ≤ limit en cassant sur des lignes vides quand possible."""
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
    horizon = run_at + timedelta(days=30 * HORIZON_MONTHS)

    findings = memory.tail_lines(paths.FINDINGS, max_chars=MAX_FINDINGS_CHARS)
    decisions = memory.tail_lines(paths.DECISIONS, max_chars=MAX_DECISIONS_CHARS)
    location = memory.read_location()

    prompt = _PROMPT.format(
        date_today=run_at.strftime("%d/%m/%Y"),
        date_horizon=horizon.strftime("%d/%m/%Y"),
        location=_format_location(location),
        findings=findings or "(vide)",
        decisions=decisions or "(vide)",
        ws=WEB_SEARCH_MAX,
    )

    used_llm = False
    llm_error: str | None = None
    message: str | None = None
    model: str | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None

    try:
        resp = llm.call(
            tier=cfg.get("model", "sonnet"),
            messages=[{"role": "user", "content": prompt}],
            task=TASK,
            max_tokens=4000,
            temperature=0.5,
            web_search=True,
            web_search_max_uses=WEB_SEARCH_MAX,
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
            f"🔭 outlook 3 mois — {run_at.strftime('%d/%m/%Y')}\n"
            f"(LLM indispo — {llm_error[:120]})\n"
            "Aucun outlook généré ce run. Vérifie le budget tokens et l'API key."
        )

    channel = cfg.get("channel", "perso")
    chunks = _chunk_for_telegram(message)
    sent_count = 0
    for i, chunk in enumerate(chunks, 1):
        prefix = f"[{i}/{len(chunks)}] " if len(chunks) > 1 else ""
        if telegram.send(channel, prefix + chunk, parse_mode=None):
            sent_count += 1

    summary = (
        f"chunks={len(chunks)}, sent={sent_count}, "
        f"llm={'yes' if used_llm else 'no'}"
    )
    extra: dict[str, Any] = {
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
        body="## Outlook envoyé\n```\n" + message + "\n```",
        extra=extra,
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    return schedule.run_guarded(TASK, run)


if __name__ == "__main__":
    raise SystemExit(main())
