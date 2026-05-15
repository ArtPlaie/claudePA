"""Client Telegram Bot API minimal. Best-effort : no-op si env non configuré."""
from __future__ import annotations

import logging
import os

import httpx

log = logging.getLogger(__name__)

API_BASE = "https://api.telegram.org"


def _chat_id(channel: str) -> str | None:
    if channel == "perso":
        return os.environ.get("TELEGRAM_CHAT_PERSO")
    if channel == "famille":
        return os.environ.get("TELEGRAM_CHAT_FAMILLE")
    return None


def send(channel: str, message: str, *, parse_mode: str | None = "Markdown") -> bool:
    """Envoie un message Telegram. Retourne False si non configuré ou erreur réseau.

    `parse_mode=None` envoie en plain text (utile quand le message contient
    des chars Markdown-significatifs non escapés).
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = _chat_id(channel)
    if not token or not chat:
        log.info("telegram disabled (channel=%s): %s", channel, message[:120])
        return False
    payload: dict[str, str] = {"chat_id": chat, "text": message}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    try:
        r = httpx.post(
            f"{API_BASE}/bot{token}/sendMessage",
            json=payload,
            timeout=10.0,
        )
    except httpx.HTTPError as e:
        log.warning("telegram http error: %s", e)
        return False
    if r.status_code >= 400:
        log.warning("telegram send failed %s: %s", r.status_code, r.text[:200])
        return False
    return True
