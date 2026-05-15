"""De-dup cross-task : fingerprint (type, titre, org) + fenêtre 90j sur les drafts."""
from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import UTC, datetime, timedelta

import yaml

from . import paths
from .memory import MarkdownDoc, _parse_dt

DEDUP_WINDOW_DAYS = 90


def _canon(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s


def fingerprint(type_: str, title: str, org: str = "") -> str:
    key = "|".join(_canon(x) for x in (type_, title, org))
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def _draft_fingerprints(now: datetime) -> set[str]:
    if not paths.DRAFTS.exists():
        return set()
    cutoff = now - timedelta(days=DEDUP_WINDOW_DAYS)
    out: set[str] = set()
    for path in paths.DRAFTS.glob("*.md"):
        try:
            doc = MarkdownDoc.read(path)
        except (OSError, yaml.YAMLError):
            continue
        fp = doc.front_matter.get("fingerprint")
        ts = _parse_dt(doc.front_matter.get("created_at"))
        if fp and ts is not None and ts >= cutoff:
            out.add(str(fp))
    return out


def seen_recently(fp: str, now: datetime | None = None) -> bool:
    now = now or datetime.now(UTC)
    return fp in _draft_fingerprints(now)
