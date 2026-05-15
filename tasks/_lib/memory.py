"""Mémoire — front matter, working-memory, findings.

Format de référence d'un fichier working-memory (voir SPEC.md) :

    ---
    task: mail_review
    run_at: 2026-05-15T08:00:00+02:00
    model: claude-sonnet-4-6
    tokens_in: 12450
    tokens_out: 1820
    status: completed
    ---

    ## Résumé
    ...
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

from . import paths


@dataclass
class MarkdownDoc:
    """Document markdown avec front matter YAML optionnel."""

    front_matter: dict[str, Any] = field(default_factory=dict)
    body: str = ""

    @classmethod
    def parse(cls, text: str) -> MarkdownDoc:
        if not text.startswith("---\n"):
            return cls(body=text)
        rest = text[4:]
        end = rest.find("\n---\n")
        if end == -1:
            return cls(body=text)
        fm = yaml.safe_load(rest[:end]) or {}
        body = rest[end + len("\n---\n") :]
        return cls(front_matter=fm, body=body)

    @classmethod
    def read(cls, path: Path) -> MarkdownDoc:
        return cls.parse(path.read_text(encoding="utf-8"))

    def render(self) -> str:
        if not self.front_matter:
            return self.body
        fm = yaml.safe_dump(self.front_matter, allow_unicode=True, sort_keys=False)
        return f"---\n{fm}---\n{self.body}"

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render(), encoding="utf-8")


def _parse_dt(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value)
        except ValueError:
            return None
        return dt if dt.tzinfo else dt.replace(tzinfo=UTC)
    return None


def working_memory_path(task: str, run_at: datetime, suffix: str = "") -> Path:
    stamp = run_at.strftime("%Y-%m-%d-%H%M")
    name = f"{stamp}-{task}"
    if suffix:
        name = f"{name}-{suffix}"
    return paths.WORKING_MEMORY / f"{name}.md"


def write_run_log(
    *,
    task: str,
    run_at: datetime,
    status: str,
    model: str | None = None,
    tokens_in: int | None = None,
    tokens_out: int | None = None,
    extra: dict[str, Any] | None = None,
    summary: str = "",
    body: str = "",
    suffix: str = "",
) -> Path:
    """Écrit un log de run standardisé dans working-memory/."""
    fm: dict[str, Any] = {
        "task": task,
        "run_at": run_at.isoformat(),
        "status": status,
    }
    if model:
        fm["model"] = model
    if tokens_in is not None:
        fm["tokens_in"] = tokens_in
    if tokens_out is not None:
        fm["tokens_out"] = tokens_out
    if extra:
        fm.update(extra)

    sections: list[str] = []
    if summary:
        sections.append(f"## Résumé\n{summary.strip()}")
    if body:
        sections.append(body.strip())
    full_body = "\n" + "\n\n".join(sections) + "\n" if sections else "\n"

    path = working_memory_path(task, run_at, suffix=suffix)
    MarkdownDoc(front_matter=fm, body=full_body).write(path)
    return path


def list_working_memory(task: str | None = None) -> list[Path]:
    if not paths.WORKING_MEMORY.exists():
        return []
    files = sorted(paths.WORKING_MEMORY.glob("*.md"))
    if task is None:
        return files
    return [p for p in files if p.stem.endswith(f"-{task}")]


def last_run(task: str) -> datetime | None:
    """Dernier `run_at` avec status=completed pour cette tâche."""
    for path in reversed(list_working_memory(task)):
        try:
            doc = MarkdownDoc.read(path)
        except (OSError, yaml.YAMLError):
            continue
        if doc.front_matter.get("status") != "completed":
            continue
        ts = _parse_dt(doc.front_matter.get("run_at"))
        if ts is not None:
            return ts
    return None


def files_older_than(days: int, now: datetime | None = None) -> list[Path]:
    """working-memory plus vieux que `days`, basé sur le front matter run_at."""
    now = now or datetime.now(UTC)
    cutoff = now - timedelta(days=days)
    out: list[Path] = []
    for path in list_working_memory():
        try:
            doc = MarkdownDoc.read(path)
        except (OSError, yaml.YAMLError):
            continue
        ts = _parse_dt(doc.front_matter.get("run_at"))
        if ts is not None and ts < cutoff:
            out.append(path)
    return out


def read_location() -> dict[str, Any]:
    if not paths.CURRENT_LOCATION.exists():
        return {}
    return MarkdownDoc.read(paths.CURRENT_LOCATION).front_matter


_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def list_pending_drafts(
    now: datetime | None = None, horizon_days: int | None = None
) -> list[dict[str, Any]]:
    """Drafts status=pending, non expirés. Tri par priority.

    `horizon_days`: filtre supplémentaire — ne garde que les drafts dont
    `expires_at` est ≤ now + horizon_days (None = pas de filtre additionnel).
    """
    if not paths.DRAFTS.exists():
        return []
    now = now or datetime.now(UTC)
    today = now.date()
    horizon_date = (now + timedelta(days=horizon_days)).date() if horizon_days else None
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
        exp_date = None
        if expires_raw:
            try:
                exp_date = datetime.fromisoformat(str(expires_raw)).date()
            except ValueError:
                exp_date = None
            if exp_date is not None and exp_date < today:
                continue
        if horizon_date is not None and exp_date is not None and exp_date > horizon_date:
            continue
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
                "path": p.relative_to(paths.REPO_ROOT).as_posix(),
            }
        )
    out.sort(key=lambda d: _PRIORITY_ORDER.get(d["priority"], 1))
    return out


def tail_lines(path: Path, max_chars: int = 2000) -> str:
    """Renvoie la fin d'un fichier texte, plafonnée à `max_chars`. Vide si absent."""
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    if len(text) <= max_chars:
        return text
    return "…\n" + text[-max_chars:]


def append_finding(
    *,
    title: str,
    tags: list[str],
    source: str,
    link: str = "",
    why: str = "",
    followup: str = "",
    fingerprint: str = "",
    when: datetime | None = None,
) -> None:
    """Append une entrée dans digests/findings.md."""
    when = when or datetime.now(UTC)
    fp = f"  `{fingerprint}`" if fingerprint else ""
    lines = [
        "",
        f"### {when.strftime('%Y-%m-%d')} — {title}{fp}",
        f"**Tags** : {', '.join(tags)}",
        f"**Source** : {source}",
    ]
    if link:
        lines.append(f"**Lien** : {link}")
    if why:
        lines.append(f"**Pourquoi ça compte** : {why}")
    if followup:
        lines.append(f"**Suite** : {followup}")
    paths.FINDINGS.parent.mkdir(parents=True, exist_ok=True)
    with paths.FINDINGS.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
