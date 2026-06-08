"""Rollup mensuel + purge working-memory > 30j.

Tourne tous les jours à 03:00 UTC. Pour chaque mois M qui sort de la fenêtre
glissante :
1. Lance Haiku sur le bundle des working-memory de M → digest dans `digests/monthly/YYYY-MM.md`.
2. Vérifie que le digest a bien été écrit (non vide) → purge les sources.

Idempotent : un re-run ne re-purge rien (digest déjà présent → on saute).
Si la génération du digest échoue, aucune purge n'a lieu pour ce mois.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tasks._lib import llm, memory, paths, schedule

TASK = "sliding_window"
WINDOW_DAYS = 30

log = logging.getLogger(TASK)


def _month_key(path: Path) -> str | None:
    """Extrait YYYY-MM depuis 'YYYY-MM-DD-HHMM-<task>[-suffix].md'."""
    parts = path.stem.split("-")
    if len(parts) < 2:
        return None
    year, month = parts[0], parts[1]
    if len(year) == 4 and year.isdigit() and len(month) == 2 and month.isdigit():
        return f"{year}-{month}"
    return None


def _digest_path(month: str) -> Path:
    return paths.DIGESTS_MONTHLY / f"{month}.md"


_DIGEST_INSTRUCTION = (
    "Tu reçois ci-dessous tous les working-memory d'un mois (un fichier par run de tâche). "
    "Produis un digest mensuel synthétique, format markdown.\n\n"
    "Sections attendues (skip celles vides) :\n"
    "- **Mails / threads clés** : décisions, follow-ups, oublis évités\n"
    "- **Leads / opportunités** : Sydney, AI, formations, réseau\n"
    "- **Famille / agenda** : sorties faites, jalons\n"
    "- **Drafts** : validés vs skippés, patterns SKIP émergents\n"
    "- **Décisions reportées / en attente**\n"
    "- **Erreurs / tâches dégradées**\n\n"
    "Style : direct, dense, factuel, pas de sycophantie, pas de remplissage. "
    "5-15 lignes max par section."
)


def _produce_digest(month: str, files: list[Path], tier: str) -> tuple[str, int, int]:
    bundle: list[str] = []
    for p in files:
        bundle.append(f"\n\n=== {p.name} ===\n\n{p.read_text(encoding='utf-8')}")
    content = _DIGEST_INSTRUCTION + "\n\n# Working-memory du mois " + month + "\n" + "".join(bundle)
    resp = llm.call(
        tier=tier,
        messages=[{"role": "user", "content": content}],
        task=TASK,
        max_tokens=3000,
    )
    return resp.text, resp.tokens_in, resp.tokens_out


def _write_digest(month: str, text: str, run_at: datetime, n_files: int) -> Path:
    dpath = _digest_path(month)
    dpath.parent.mkdir(parents=True, exist_ok=True)
    fm = (
        f"---\n"
        f"month: {month}\n"
        f"generated_at: {run_at.isoformat()}\n"
        f"source_files: {n_files}\n"
        f"---\n\n"
    )
    dpath.write_text(fm + text.strip() + "\n", encoding="utf-8")
    return dpath


def run(cfg: dict[str, Any]) -> None:
    run_at = datetime.now(UTC)
    old_files = memory.files_older_than(WINDOW_DAYS, now=run_at)

    # Les handovers de session (`*-session-*.md`) sont la seule mémoire
    # inter-session : jamais purgés, ni bundlés dans le digest mensuel.
    old_files = [p for p in old_files if "-session-" not in p.stem]

    if not old_files:
        log.info("nothing older than %sd — no-op", WINDOW_DAYS)
        return

    by_month: dict[str, list[Path]] = defaultdict(list)
    for p in old_files:
        m = _month_key(p)
        if m is None:
            log.warning("ignoring unparseable filename: %s", p.name)
            continue
        by_month[m].append(p)

    tier = cfg.get("model", "haiku")
    digested = 0
    purged = 0
    failures: list[str] = []
    total_in = 0
    total_out = 0

    for month, files in sorted(by_month.items()):
        dpath = _digest_path(month)
        if not dpath.exists():
            try:
                text, ti, to = _produce_digest(month, files, tier)
                _write_digest(month, text, run_at, len(files))
                total_in += ti
                total_out += to
                digested += 1
            except Exception as e:
                log.exception("digest %s failed", month)
                failures.append(f"{month}: {type(e).__name__}: {e}")
                continue

        if dpath.exists() and dpath.stat().st_size > 0:
            for f in files:
                f.unlink()
            purged += len(files)
        else:
            failures.append(f"{month}: digest absent ou vide, purge annulée")

    parts: list[str] = []
    if digested:
        parts.append(f"{digested} digest(s) produit(s)")
    if purged:
        parts.append(f"{purged} fichier(s) purgé(s)")
    if failures:
        parts.append(f"{len(failures)} échec(s)")
    summary = " ; ".join(parts) or "rien à faire"

    body = ""
    if failures:
        body = "## Échecs\n" + "\n".join(f"- {f}" for f in failures)

    memory.write_run_log(
        task=TASK,
        run_at=run_at,
        status="completed",
        model=llm.resolve_model(tier) if digested else None,
        tokens_in=total_in or None,
        tokens_out=total_out or None,
        summary=summary,
        body=body,
        extra={"months_digested": digested, "files_purged": purged},
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    return schedule.run_guarded(TASK, run)


if __name__ == "__main__":
    raise SystemExit(main())
