"""Lecture de schedule.yaml + gates de démarrage (panic, vacances, cadence)."""
from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import yaml

from . import paths
from .memory import last_run, read_location, write_run_log

log = logging.getLogger(__name__)


class Skip(Exception):
    """Levée quand une tâche doit skip son run. Catch par run_guarded."""


def load_schedule() -> dict[str, Any]:
    with paths.SCHEDULE_YAML.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def task_config(task: str) -> dict[str, Any]:
    sched = load_schedule()
    defaults = sched.get("defaults") or {}
    tasks = sched.get("tasks") or {}
    if task not in tasks:
        raise KeyError(f"Task {task!r} not declared in schedule.yaml")
    return {**defaults, **(tasks[task] or {})}


def panic_active() -> bool:
    return paths.PANIC_SENTINEL.exists()


def vacation_active() -> bool:
    return bool(read_location().get("vacation_mode"))


def cadence_satisfied(task: str, cadence_days: int, now: datetime | None = None) -> bool:
    now = now or datetime.now(UTC)
    prev = last_run(task)
    if prev is None:
        return True
    return (now - prev) >= timedelta(days=cadence_days)


def preflight(task: str) -> dict[str, Any]:
    """Run tous les gates de démarrage. Lève Skip avec raison sinon retourne la config."""
    if panic_active():
        raise Skip("panic sentinel active")

    cfg = task_config(task)

    if not cfg.get("enabled", False):
        raise Skip("task disabled in schedule.yaml")

    if vacation_active() and not cfg.get("vacation_safe", False):
        raise Skip("vacation_mode active and task not vacation_safe")

    cadence = cfg.get("cadence_days")
    if cadence and not cadence_satisfied(task, int(cadence)):
        raise Skip(f"cadence_days={cadence} not elapsed since last completed run")

    return cfg


def run_guarded(task: str, fn: Callable[[dict[str, Any]], None]) -> int:
    """Exécute fn(cfg) après preflight. Log skip/error en working-memory, retourne exit code."""
    run_at = datetime.now(UTC)
    try:
        cfg = preflight(task)
    except Skip as s:
        log.info("skip %s: %s", task, s)
        write_run_log(
            task=task,
            run_at=run_at,
            status="skipped",
            summary=str(s),
            suffix="skip",
        )
        return 0

    try:
        fn(cfg)
        return 0
    except Exception as e:
        log.exception("task %s failed", task)
        write_run_log(
            task=task,
            run_at=run_at,
            status="error",
            summary=f"{type(e).__name__}: {e}",
            suffix="error",
        )
        try:
            from . import notify

            notify.alert(f"[{task}] erreur — {type(e).__name__}: {e}")
        except Exception:
            log.exception("alert send failed")
        return 1
