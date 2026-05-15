"""Applique une décision (OK / SKIP / EDIT) sur un draft.

Déclenché par .github/workflows/apply-draft.yml suite à un dispatch du
Cloudflare Worker (clic sur un bouton inline Telegram).

V1 :
- OK   : marque `status: approved`. AUCUN actuator n'est wiré pour
         exécuter l'action (pas de gmail.send, pas de paiement) — c'est
         volontaire pour la phase de confiance. Sylvain agit à la main.
- SKIP : marque `status: skipped`, append le pattern dans
         core-memory/skip-patterns.md (90j) pour ne plus re-proposer.
- EDIT : marque `status: editing`, demande à Sylvain d'éditer le
         fichier directement (pas de conversation multi-tour pour V1).
"""
from __future__ import annotations

import logging
import os
from datetime import UTC, datetime

from tasks._lib import memory, notify, paths, telegram
from tasks._lib.memory import MarkdownDoc

TASK = "apply_draft"

log = logging.getLogger(TASK)


def _channel_from_chat_id(chat_id: str) -> str:
    if chat_id and chat_id == os.environ.get("TELEGRAM_CHAT_FAMILLE"):
        return "famille"
    return "perso"


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    draft_rel = os.environ["DRAFT_PATH"]
    action = os.environ["ACTION"].upper()
    reason = os.environ.get("REASON", "")
    chat_id = os.environ.get("CHAT_ID", "")
    channel = _channel_from_chat_id(chat_id)

    draft_path = paths.REPO_ROOT / draft_rel
    if not draft_path.exists():
        telegram.send(channel, f"⚠️ draft introuvable : {draft_rel}")
        return 1

    doc = MarkdownDoc.read(draft_path)
    cur_status = doc.front_matter.get("status")
    if cur_status != "pending":
        telegram.send(
            channel, f"⚠️ draft déjà traité (status={cur_status}) : {draft_path.name}"
        )
        return 0

    run_at = datetime.now(UTC)
    type_ = str(doc.front_matter.get("type", "unknown"))
    title = str(doc.front_matter.get("title", "")) or draft_path.stem

    if action == "OK":
        doc.front_matter["status"] = "approved"
        doc.front_matter["approved_at"] = run_at.isoformat()
        doc.write(draft_path)
        telegram.send(
            channel,
            f"✅ approuvé : {title}\n"
            f"⚠️ pas d'actuator wiré pour `{type_}` en V1 — exécution manuelle.",
        )
        summary = f"OK on {draft_path.name} (type={type_})"

    elif action == "SKIP":
        doc.front_matter["status"] = "skipped"
        doc.front_matter["skipped_at"] = run_at.isoformat()
        if reason:
            doc.front_matter["skip_reason"] = reason
        doc.write(draft_path)
        notify.register_skip_pattern(
            type_=type_, subject_match=title, reason=reason
        )
        telegram.send(
            channel,
            f"❌ skip : {title}\npattern enregistré (90j).",
        )
        summary = f"SKIP on {draft_path.name} (type={type_}, reason={reason!r})"

    elif action == "EDIT":
        doc.front_matter["status"] = "editing"
        doc.write(draft_path)
        telegram.send(
            channel,
            f"✏️ édite directement {draft_rel}\n"
            f"puis change `status:` en `approved` ou `skipped` à la main.",
        )
        summary = f"EDIT on {draft_path.name}"

    else:
        telegram.send(channel, f"⚠️ action inconnue : {action!r}")
        return 1

    memory.write_run_log(
        task=TASK,
        run_at=run_at,
        status="completed",
        summary=summary,
        extra={"draft": draft_rel, "action": action, "channel": channel},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
