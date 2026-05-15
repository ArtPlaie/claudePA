"""Réponse temps-réel à un message libre déposé en inbox/.

Déclenché par .github/workflows/on-webhook.yml suite à un dispatch du
Cloudflare Worker. Lit le message, charge un peu de contexte récent,
appelle Sonnet, répond via Telegram.

Honore le kill switch `.panic` même pour les réponses interactives.
"""
from __future__ import annotations

import logging
import os
from datetime import UTC, datetime

from tasks._lib import llm, memory, paths, schedule, telegram
from tasks._lib.memory import MarkdownDoc

TASK = "respond"

log = logging.getLogger(TASK)


_PROMPT = """\
Tu es l'assistant perso de Sylvain. Tu réponds à un message Telegram qu'il
vient d'envoyer. Style direct, dense, "bro", pas de sycophantie, pas de
signature. Français informel par défaut. "Je sais pas" plutôt que bullshit.

# Message reçu (channel: {channel})
{question}

# Contexte récent (5 derniers logs working-memory)
{recent_context}

Réponds en 1-10 lignes maxi. Si tu as besoin d'une action externe (envoi
mail, réservation, dépense), dis-le et propose un draft à valider — ne
prétends pas avoir agi.
"""


def _recent_context(max_files: int = 5) -> str:
    files = memory.list_working_memory()[-max_files:]
    if not files:
        return "(aucun)"
    chunks: list[str] = []
    for p in files:
        try:
            doc = MarkdownDoc.read(p)
        except Exception:
            continue
        first_line = ""
        for line in doc.body.splitlines():
            if line.strip():
                first_line = line.strip()
                break
        chunks.append(
            f"- {p.stem}: status={doc.front_matter.get('status')} — {first_line[:120]}"
        )
    return "\n".join(chunks) or "(aucun)"


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    if schedule.panic_active():
        log.info("panic active — refusing to respond")
        return 0

    inbox_path = paths.REPO_ROOT / os.environ["INBOX_PATH"]
    chat_id = os.environ["CHAT_ID"]
    channel = os.environ["CHANNEL"]

    if not inbox_path.exists():
        log.error("inbox path missing: %s", inbox_path)
        telegram.send(channel, f"⚠️ message introuvable : {inbox_path.name}")
        return 1

    msg_doc = MarkdownDoc.read(inbox_path)
    question = msg_doc.body.strip()

    if not question:
        telegram.send(channel, "⚠️ message vide reçu")
        return 0

    if question.lower() in ("ping", "/ping"):
        telegram.send(channel, "pong")
        return 0

    run_at = datetime.now(UTC)
    prompt = _PROMPT.format(
        channel=channel,
        question=question,
        recent_context=_recent_context(),
    )

    try:
        resp = llm.call(
            tier="sonnet",
            messages=[{"role": "user", "content": prompt}],
            task=TASK,
            max_tokens=1000,
            temperature=0.7,
        )
    except Exception as e:
        log.exception("LLM call failed")
        telegram.send(channel, f"⚠️ erreur LLM — {type(e).__name__}: {e}")
        memory.write_run_log(
            task=TASK,
            run_at=run_at,
            status="error",
            summary=f"{type(e).__name__}: {e}",
            suffix="error",
        )
        return 1

    reply = resp.text.strip() or "(réponse vide)"
    telegram.send(channel, reply)

    memory.write_run_log(
        task=TASK,
        run_at=run_at,
        status="completed",
        model=resp.model,
        tokens_in=resp.tokens_in,
        tokens_out=resp.tokens_out,
        summary=f"Q: {question[:80]}",
        body=f"## Question\n{question}\n\n## Réponse\n{reply}",
        extra={"chat_id": chat_id, "channel": channel, "inbox": str(inbox_path.relative_to(paths.REPO_ROOT))},
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
