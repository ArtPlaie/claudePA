"""Lecture des messages entrants déposés par le Cloudflare Worker dans inbox/.

Format attendu (markdown + front matter, écrit par le Worker) :

    ---
    channel: perso         # perso | famille
    from: Sylvain
    timestamp: 2026-05-15T08:30:00+00:00
    chat_id: 123
    message_id: 456
    ---

    <texte du message>
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from . import paths
from .memory import MarkdownDoc, _parse_dt


@dataclass
class InboxMessage:
    path: Path
    channel: str
    timestamp: datetime
    text: str
    front_matter: dict[str, Any]


def read_recent(days_back: int = 7, now: datetime | None = None) -> list[InboxMessage]:
    if not paths.INBOX.exists():
        return []
    now = now or datetime.now(UTC)
    cutoff = now - timedelta(days=days_back)
    out: list[InboxMessage] = []
    for p in sorted(paths.INBOX.glob("*.md")):
        try:
            doc = MarkdownDoc.read(p)
        except (OSError, yaml.YAMLError):
            continue
        ts = _parse_dt(doc.front_matter.get("timestamp"))
        if ts is None or ts < cutoff:
            continue
        out.append(
            InboxMessage(
                path=p,
                channel=str(doc.front_matter.get("channel", "")),
                timestamp=ts,
                text=doc.body.strip(),
                front_matter=doc.front_matter,
            )
        )
    return out
