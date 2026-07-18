"""Wrapper Google Calendar API — écriture d'événements sur l'agenda de Sylvain.

Auth : OAuth, token du **compte de Sylvain** (pas le PA), scope
`calendar.events`. Les events sont donc créés directement sur SON agenda, il
les possède (pas d'invitation, pas de partage de calendrier à gérer).

Secret attendu (env var) :
- `GCAL_TOKEN_JSON` — refresh token user info JSON, scope calendar.events.
  Généré par `scripts/setup_gmail_oauth.py --account gcal`.

Contrat (cf. policies.md) : la création d'event n'est PAS une action externe
"sensible" au sens OPSEC — elle reste sur l'agenda privé de Sylvain, et n'est
déclenchée QUE par une réponse mail explicite de sa part ("réserve X samedi").
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any

log = logging.getLogger(__name__)

ENV_VAR = "GCAL_TOKEN_JSON"
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

# Sylvain vit à Bois-le-Roi (cf. current-location.md). Fuseau par défaut des
# événements créés si aucun autre n'est fourni.
DEFAULT_TZ = "Europe/Paris"


@dataclass
class CreatedEvent:
    id: str
    html_link: str
    summary: str
    start: str
    end: str


def is_configured() -> bool:
    return bool(os.environ.get(ENV_VAR))


def service_for() -> Any:
    """Construit un service Calendar authentifié. Lève RuntimeError si pas configuré."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    raw = os.environ.get(ENV_VAR)
    if not raw:
        raise RuntimeError(
            f"{ENV_VAR} absent — lance scripts/setup_gmail_oauth.py --account gcal"
        )
    info = json.loads(raw)
    creds = Credentials.from_authorized_user_info(info, scopes=SCOPES)
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def _endpoint(
    *, all_day: bool, dt_iso: str, tz: str
) -> dict[str, str]:
    """Construit un bloc start/end Calendar. all_day → 'date', sinon 'dateTime'+tz."""
    if all_day:
        # dt_iso peut être 'YYYY-MM-DD' ou un datetime ISO ; on garde la date.
        return {"date": dt_iso[:10]}
    return {"dateTime": dt_iso, "timeZone": tz}


def create_event(
    service: Any,
    *,
    summary: str,
    start: str,
    end: str,
    all_day: bool = False,
    location: str = "",
    description: str = "",
    timezone: str = DEFAULT_TZ,
    calendar_id: str = "primary",
) -> CreatedEvent:
    """Insère un événement sur l'agenda. `start`/`end` = ISO local (ou date si all_day)."""
    body: dict[str, Any] = {
        "summary": summary,
        "start": _endpoint(all_day=all_day, dt_iso=start, tz=timezone),
        "end": _endpoint(all_day=all_day, dt_iso=end, tz=timezone),
    }
    if location:
        body["location"] = location
    if description:
        body["description"] = description

    created = service.events().insert(calendarId=calendar_id, body=body).execute()
    return CreatedEvent(
        id=created.get("id", ""),
        html_link=created.get("htmlLink", ""),
        summary=summary,
        start=start,
        end=end,
    )


def now_local(tz: str = DEFAULT_TZ) -> datetime:
    from zoneinfo import ZoneInfo

    return datetime.now(ZoneInfo(tz))
