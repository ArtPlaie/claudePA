"""Wrapper Google Calendar — un seul compte (perso), scope read + write.

Le contrat OPSEC (cf. policies.md) :
- Lecture : tous les calendars visibles côté Google (primary + partagés
  Isa/famille auxquels Sylvain est abonné, filtre `selected: true`).
- Écriture : autorisée pour des events `tentative` + `private` (cf.
  whitelist policies.md ligne 23). Toute autre écriture passe par drafts.

Secret attendu (env var) :
- `GCAL_TOKEN_JSON` — refresh token user info JSON.

Format : sortie standard de google-auth-oauthlib (`Credentials.to_json()`),
généré par `scripts/setup_calendar_oauth.py`.

Si la var est absente, `fetch_upcoming()` retourne [] et logue en INFO
(les tâches consommatrices continuent à tourner). `service_for()` lève
RuntimeError si appelée sans token — `is_configured()` pour les chemins
gracieux.
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

log = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/calendar"]

_ENV_VAR = "GCAL_TOKEN_JSON"

# Plafond par calendar pour borner le coût/latence. 250 events sur 20j
# couvre largement les cas normaux ; au-delà on tronque silencieusement.
_MAX_EVENTS_PER_CALENDAR = 250


@dataclass
class CalendarEvent:
    """Vue normalisée d'un event Calendar."""

    id: str
    calendar_id: str
    summary: str
    start: datetime
    end: datetime
    location: str = ""
    description: str = ""
    all_day: bool = False


def is_configured() -> bool:
    return bool(os.environ.get(_ENV_VAR))


def service_for() -> Any:
    """Construit un service Calendar authentifié. Lève RuntimeError si absent."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    raw = os.environ.get(_ENV_VAR)
    if not raw:
        raise RuntimeError(
            f"{_ENV_VAR} absent — lance scripts/setup_calendar_oauth.py"
        )
    info = json.loads(raw)
    creds = Credentials.from_authorized_user_info(info, scopes=SCOPES)
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def _parse_event_time(node: dict[str, Any]) -> tuple[datetime, bool]:
    """Parse un bloc start/end Calendar. Retourne (datetime UTC, all_day)."""
    if "dateTime" in node:
        dt = datetime.fromisoformat(node["dateTime"].replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC), False
    if "date" in node:
        dt = datetime.fromisoformat(node["date"]).replace(tzinfo=UTC)
        return dt, True
    raise ValueError(f"event time node has neither dateTime nor date: {node!r}")


def _normalize_event(raw: dict[str, Any], calendar_id: str) -> CalendarEvent | None:
    start_node = raw.get("start") or {}
    end_node = raw.get("end") or {}
    if not start_node or not end_node:
        return None
    try:
        start, start_all_day = _parse_event_time(start_node)
        end, _ = _parse_event_time(end_node)
    except ValueError:
        return None
    return CalendarEvent(
        id=raw.get("id", ""),
        calendar_id=calendar_id,
        summary=raw.get("summary", "") or "",
        start=start,
        end=end,
        location=raw.get("location", "") or "",
        description=raw.get("description", "") or "",
        all_day=start_all_day,
    )


def _selected_calendar_ids(service: Any) -> list[str]:
    """IDs des calendars marqués selected=True côté UI Google (visibles)."""
    out: list[str] = []
    page_token: str | None = None
    while True:
        resp = service.calendarList().list(pageToken=page_token).execute()
        for cal in resp.get("items", []):
            if cal.get("hidden"):
                continue
            if not cal.get("selected", False):
                continue
            cid = cal.get("id")
            if cid:
                out.append(cid)
        page_token = resp.get("nextPageToken")
        if not page_token:
            return out


def fetch_upcoming(
    days_ahead: int = 14, now: datetime | None = None
) -> list[CalendarEvent]:
    """Événements entre maintenant et now+days_ahead. [] si pas d'OAuth."""
    if not is_configured():
        log.info("%s absent — calendar fetch retourne []", _ENV_VAR)
        return []

    now = now or datetime.now(UTC)
    time_min = now.isoformat()
    time_max = (now + timedelta(days=days_ahead)).isoformat()

    service = service_for()
    calendar_ids = _selected_calendar_ids(service)
    if not calendar_ids:
        log.warning("aucun calendar selected=True — vérifie côté Google UI")
        return []

    events: list[CalendarEvent] = []
    for cid in calendar_ids:
        page_token: str | None = None
        fetched_for_cal = 0
        while True:
            resp = service.events().list(
                calendarId=cid,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
                maxResults=min(250, _MAX_EVENTS_PER_CALENDAR - fetched_for_cal),
                pageToken=page_token,
            ).execute()
            for raw in resp.get("items", []):
                ev = _normalize_event(raw, cid)
                if ev is not None:
                    events.append(ev)
                    fetched_for_cal += 1
                    if fetched_for_cal >= _MAX_EVENTS_PER_CALENDAR:
                        break
            if fetched_for_cal >= _MAX_EVENTS_PER_CALENDAR:
                break
            page_token = resp.get("nextPageToken")
            if not page_token:
                break

    events.sort(key=lambda e: e.start)
    return events


def create_tentative_event(
    *,
    summary: str,
    start: datetime,
    end: datetime,
    description: str = "",
    location: str = "",
    calendar_id: str = "primary",
) -> dict[str, Any]:
    """Pose un event tentative+private dans le calendar (whitelist policies.md).

    `transparency=transparent` pour ne pas bloquer le free/busy de Sylvain
    (l'event est un placeholder pas une dispo bloquée).
    """
    service = service_for()
    body: dict[str, Any] = {
        "summary": summary,
        "start": {"dateTime": start.astimezone(UTC).isoformat()},
        "end": {"dateTime": end.astimezone(UTC).isoformat()},
        "status": "tentative",
        "visibility": "private",
        "transparency": "transparent",
    }
    if description:
        body["description"] = description
    if location:
        body["location"] = location
    return service.events().insert(calendarId=calendar_id, body=body).execute()
