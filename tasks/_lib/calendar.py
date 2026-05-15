"""Wrapper Google Calendar — stub tant que l'OAuth n'est pas wiré.

Quand `GCAL_TOKEN_JSON` sera disponible en env (secret GitHub avec refresh
token OAuth), implémenter `fetch_upcoming` via google-api-python-client.

Pour l'instant la fonction retourne [] dans tous les cas, ce qui permet
aux tâches dépendantes (`location_context`, `daily_digest`) de tourner
sans crasher.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime

log = logging.getLogger(__name__)


@dataclass
class CalendarEvent:
    summary: str
    start: datetime
    end: datetime
    location: str = ""
    description: str = ""


def fetch_upcoming(
    days_ahead: int = 14, now: datetime | None = None
) -> list[CalendarEvent]:
    """Événements entre maintenant et now+days_ahead. [] si pas d'OAuth."""
    token_json = os.environ.get("GCAL_TOKEN_JSON")
    if not token_json:
        log.info("GCAL_TOKEN_JSON absent — calendar fetch retourne []")
        return []
    # TODO: implémenter avec google-api-python-client une fois l'OAuth wiré.
    # Étapes :
    # 1. Construire Credentials.from_authorized_user_info(json.loads(token_json))
    # 2. service = build("calendar", "v3", credentials=creds)
    # 3. service.events().list(calendarId="primary", timeMin=..., timeMax=...)
    log.warning("GCAL_TOKEN_JSON présent mais fetch non implémenté — TODO")
    return []
