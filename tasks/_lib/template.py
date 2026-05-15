"""Template d'une nouvelle tâche. Copier vers `tasks/<nom>.py` et adapter.

Étapes pour ajouter une tâche (cf. CLAUDE.md > "Pour ajouter une nouvelle tâche") :

1. cp tasks/_lib/template.py tasks/<nom>.py
2. Remplacer TASK ci-dessous, ajuster `run()`.
3. Déclarer la tâche dans schedule.yaml (cron, channel, model tier).
4. Créer .github/workflows/task-<nom>.yml.
5. Local : `python -m tasks.<nom>` (skip tant que enabled: false).

Invariants assurés par `schedule.run_guarded` :
- exit immédiat si `.panic` existe à la racine
- exit immédiat si la tâche n'est pas dans schedule.yaml ou est `enabled: false`
- exit immédiat si `vacation_mode: true` dans current-location.md et tâche non vacation_safe
- exit immédiat si `cadence_days` non écoulé depuis le dernier run completed
- toute exception non gérée → log d'erreur en working-memory + alerte Telegram
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from tasks._lib import memory, schedule

TASK = "template"

log = logging.getLogger(TASK)


def run(cfg: dict[str, Any]) -> None:
    run_at = datetime.now(UTC)

    # 1. Charger contexte (inbox, calendar, mails, web search…).
    # 2. llm.call(tier=cfg["model"], messages=[...], task=TASK) si besoin.
    # 3. notify.create_draft(...) pour toute action externe (passe par skip-patterns).
    # 4. memory.append_finding(...) pour les pépites cross-task.

    memory.write_run_log(
        task=TASK,
        run_at=run_at,
        status="completed",
        model=cfg.get("model"),
        summary="<résumé du run>",
        body="## Détails\n<...>",
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    return schedule.run_guarded(TASK, run)


if __name__ == "__main__":
    raise SystemExit(main())
