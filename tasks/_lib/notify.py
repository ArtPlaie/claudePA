"""Pipeline drafts/validation : skip-patterns, création de drafts, alertes Telegram."""
from __future__ import annotations

import logging
import re
import unicodedata
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from . import paths, telegram
from .memory import MarkdownDoc, _parse_dt

log = logging.getLogger(__name__)

SKIP_DEFAULT_WINDOW_DAYS = 90


def _load_skip_patterns() -> list[dict[str, Any]]:
    """Parse skip-patterns.md : un bloc YAML par entrée, séparés par `---`."""
    if not paths.SKIP_PATTERNS.exists():
        return []
    text = paths.SKIP_PATTERNS.read_text(encoding="utf-8")
    out: list[dict[str, Any]] = []
    for chunk in text.split("\n---\n"):
        try:
            data = yaml.safe_load(chunk)
        except yaml.YAMLError:
            continue
        if isinstance(data, dict) and "type" in data and "subject_match" in data:
            out.append(data)
    return out


def _pattern_active(p: dict[str, Any], now: datetime) -> bool:
    exp = _parse_dt(p.get("expires"))
    if exp is not None:
        return now <= exp
    created = _parse_dt(p.get("created_at"))
    if created is None:
        return True
    return now <= created + timedelta(days=SKIP_DEFAULT_WINDOW_DAYS)


def matches_skip_pattern(
    *, type_: str, subject: str, now: datetime | None = None
) -> dict[str, Any] | None:
    """Renvoie le pattern qui match, ou None."""
    now = now or datetime.now(UTC)
    subj_low = subject.lower()
    for p in _load_skip_patterns():
        if p.get("type") != type_:
            continue
        if not _pattern_active(p, now):
            continue
        m = p.get("subject_match", "")
        if not isinstance(m, str):
            continue
        try:
            if m.lower() in subj_low or re.search(m, subject, re.IGNORECASE):
                return p
        except re.error:
            if m.lower() in subj_low:
                return p
    return None


def register_skip_pattern(
    *,
    type_: str,
    subject_match: str,
    reason: str = "",
    expires_in_days: int = 90,
) -> None:
    """Append une entrée dans skip-patterns.md (appelé par le flow apply-draft SKIP)."""
    now = datetime.now(UTC)
    entry: dict[str, Any] = {
        "type": type_,
        "subject_match": subject_match,
        "created_at": now.date().isoformat(),
        "expires": (now + timedelta(days=expires_in_days)).date().isoformat(),
    }
    if reason:
        entry["reason"] = reason
    block = "\n---\n" + yaml.safe_dump(entry, allow_unicode=True, sort_keys=False)
    paths.SKIP_PATTERNS.parent.mkdir(parents=True, exist_ok=True)
    with paths.SKIP_PATTERNS.open("a", encoding="utf-8") as f:
        f.write(block)


def _slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:60] or "draft"


def create_draft(
    *,
    type_: str,
    title: str,
    body: str,
    priority: str = "medium",
    expires_in_days: int = 7,
    fingerprint: str = "",
    extra_fm: dict[str, Any] | None = None,
    skip_check_subject: str | None = None,
) -> Path | None:
    """Crée drafts/YYYY-MM-DD-<slug>.md. Retourne None si un skip-pattern matche."""
    now = datetime.now(UTC)
    subject = skip_check_subject if skip_check_subject is not None else title
    matched = matches_skip_pattern(type_=type_, subject=subject, now=now)
    if matched is not None:
        log.info("draft annulé via skip-pattern %r: %s", matched.get("subject_match"), title)
        return None

    fm: dict[str, Any] = {
        "created_at": now.isoformat(),
        "type": type_,
        "title": title,
        "priority": priority,
        "expires_at": (now + timedelta(days=expires_in_days)).date().isoformat(),
        "status": "pending",
    }
    if fingerprint:
        fm["fingerprint"] = fingerprint
    if extra_fm:
        fm.update(extra_fm)

    path = paths.DRAFTS / f"{now.strftime('%Y-%m-%d')}-{_slugify(title)}.md"
    MarkdownDoc(front_matter=fm, body="\n" + body.strip() + "\n").write(path)
    return path


def alert(message: str, channel: str = "perso") -> bool:
    """Notification Telegram best-effort. False si non configuré."""
    return telegram.send(channel, message)
