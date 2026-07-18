"""Chemins canoniques du repo — single source of truth."""
from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

CORE_MEMORY = REPO_ROOT / "core-memory"
WORKING_MEMORY = REPO_ROOT / "working-memory"
DIGESTS = REPO_ROOT / "digests"
DIGESTS_MONTHLY = DIGESTS / "monthly"
DRAFTS = REPO_ROOT / "drafts"
INBOX = REPO_ROOT / "inbox"
FEEDBACK = REPO_ROOT / "feedback"   # legacy (ancienne boucle prompt-only)
REPLIES = REPO_ROOT / "replies"     # réponses brutes de Sylvain (inbox de la routine)
CALENDAR = REPO_ROOT / "calendar"   # cycle de vie des events (requested → created)
JOURNAL = REPO_ROOT / "journal"

SCHEDULE_YAML = REPO_ROOT / "schedule.yaml"
PANIC_SENTINEL = REPO_ROOT / ".panic"

PROFILE = CORE_MEMORY / "profile.md"
POLICIES = CORE_MEMORY / "policies.md"
CURRENT_LOCATION = CORE_MEMORY / "current-location.md"
SKIP_PATTERNS = CORE_MEMORY / "skip-patterns.md"
USAGE_JSON = CORE_MEMORY / "usage.json"

FINDINGS = DIGESTS / "findings.md"
DECISIONS = JOURNAL / "decisions.md"
