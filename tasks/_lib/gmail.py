"""Wrapper Gmail API — deux comptes : `perso` (read-only) et `pa` (read/write).

Le contrat OPSEC (cf. policies.md) :
- Compte Sylvain (`perso`) — scope `gmail.readonly`. Rien ne sort jamais
  de ce compte. Utilisé par `mail_review` pour lister les threads
  inbound sans réponse et produire des suggestions de relance texte.
- Compte PA (`pa`) — scope `gmail.modify`. C'est depuis lui que partent
  les mails (briefings longs vers Sylvain, communications externes
  validées). Les drafts d'envoi sont validés sur Telegram avant exec.

Secrets attendus (env vars) :
- `GMAIL_TOKEN_PERSO_JSON` — refresh token user info JSON pour compte perso
- `GMAIL_TOKEN_PA_JSON`    — idem pour compte PA

Format : sortie standard de google-auth-oauthlib (`Credentials.to_json()`).

Toutes les fonctions retournent des dataclasses normalisées plutôt que
les blobs Gmail bruts, pour découpler le code métier de l'API Google.
Si une env var manque, `service_for()` lève RuntimeError — appelle
`is_configured()` d'abord pour les chemins gracieux.
"""
from __future__ import annotations

import base64
import json
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from email.mime.text import MIMEText
from typing import Any, Literal

log = logging.getLogger(__name__)

Account = Literal["perso", "pa"]

SCOPES: dict[Account, list[str]] = {
    "perso": ["https://www.googleapis.com/auth/gmail.readonly"],
    "pa": ["https://www.googleapis.com/auth/gmail.modify"],
}

_ENV_VAR: dict[Account, str] = {
    "perso": "GMAIL_TOKEN_PERSO_JSON",
    "pa": "GMAIL_TOKEN_PA_JSON",
}


@dataclass
class GmailMessage:
    """Vue normalisée d'un message Gmail."""

    id: str
    thread_id: str
    date: datetime
    from_addr: str
    from_name: str
    to: list[str]
    cc: list[str]
    subject: str
    snippet: str
    body_text: str
    labels: list[str] = field(default_factory=list)
    in_reply_to: str = ""
    references: list[str] = field(default_factory=list)
    message_id_header: str = ""

    @property
    def is_unread(self) -> bool:
        return "UNREAD" in self.labels

    @property
    def is_inbox(self) -> bool:
        return "INBOX" in self.labels


@dataclass
class GmailThread:
    """Vue normalisée d'un thread Gmail."""

    id: str
    messages: list[GmailMessage]

    @property
    def last(self) -> GmailMessage:
        return self.messages[-1]

    @property
    def subject(self) -> str:
        for m in self.messages:
            if m.subject:
                return m.subject
        return ""


def is_configured(account: Account) -> bool:
    return bool(os.environ.get(_ENV_VAR[account]))


def service_for(account: Account) -> Any:
    """Construit un service Gmail authentifié. Lève RuntimeError si pas configuré."""
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    raw = os.environ.get(_ENV_VAR[account])
    if not raw:
        raise RuntimeError(
            f"{_ENV_VAR[account]} absent — lance scripts/setup_gmail_oauth.py"
        )
    info = json.loads(raw)
    creds = Credentials.from_authorized_user_info(info, scopes=SCOPES[account])
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def _addr_from_header(h: str) -> tuple[str, str]:
    """Parse 'Foo Bar <foo@bar.com>' → ('foo@bar.com', 'Foo Bar')."""
    m = re.match(r"\s*(.*?)\s*<([^>]+)>\s*$", h)
    if m:
        name = m.group(1).strip().strip('"')
        return m.group(2).strip().lower(), name
    return h.strip().lower(), ""


def _addrs_from_header(h: str) -> list[str]:
    if not h:
        return []
    return [_addr_from_header(p)[0] for p in h.split(",") if p.strip()]


def _decode_b64(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def _extract_plain(payload: dict[str, Any]) -> str:
    """Walk multipart pour extraire le text/plain. Fallback sur text/html stripped."""
    if not payload:
        return ""

    plain = ""
    html_fallback = ""

    def walk(part: dict[str, Any]) -> None:
        nonlocal plain, html_fallback
        mime = part.get("mimeType", "")
        body = part.get("body", {}) or {}
        data = body.get("data")
        if data and mime == "text/plain" and not plain:
            plain = _decode_b64(data).decode("utf-8", errors="replace")
        elif data and mime == "text/html" and not html_fallback:
            html_fallback = _decode_b64(data).decode("utf-8", errors="replace")
        for sub in part.get("parts", []) or []:
            walk(sub)

    walk(payload)
    if plain:
        return plain
    if html_fallback:
        return re.sub(r"<[^>]+>", "", html_fallback)
    return ""


def _normalize_message(raw: dict[str, Any]) -> GmailMessage:
    headers = {h["name"].lower(): h["value"] for h in raw.get("payload", {}).get("headers", [])}
    from_h = headers.get("from", "")
    from_addr, from_name = _addr_from_header(from_h)
    ts_ms = int(raw.get("internalDate", "0") or 0)
    date = datetime.fromtimestamp(ts_ms / 1000, tz=UTC)
    body_text = _extract_plain(raw.get("payload", {}))
    refs = headers.get("references", "")
    return GmailMessage(
        id=raw["id"],
        thread_id=raw["threadId"],
        date=date,
        from_addr=from_addr,
        from_name=from_name,
        to=_addrs_from_header(headers.get("to", "")),
        cc=_addrs_from_header(headers.get("cc", "")),
        subject=headers.get("subject", ""),
        snippet=raw.get("snippet", "") or "",
        body_text=body_text,
        labels=list(raw.get("labelIds", []) or []),
        in_reply_to=headers.get("in-reply-to", "").strip(),
        references=[r for r in re.split(r"\s+", refs) if r.strip()] if refs else [],
        message_id_header=headers.get("message-id", "").strip(),
    )


def list_threads_since(
    service: Any,
    since: datetime,
    *,
    query_extra: str = "",
    max_threads: int = 200,
) -> list[str]:
    """Retourne les IDs des threads dont au moins un message est postérieur à `since`."""
    epoch = int(since.timestamp())
    q = f"after:{epoch}"
    if query_extra:
        q = f"{q} {query_extra}"

    out: list[str] = []
    page_token: str | None = None
    while True:
        req = service.users().threads().list(
            userId="me",
            q=q,
            maxResults=min(100, max_threads - len(out)),
            pageToken=page_token,
        )
        resp = req.execute()
        for t in resp.get("threads", []):
            out.append(t["id"])
            if len(out) >= max_threads:
                return out
        page_token = resp.get("nextPageToken")
        if not page_token:
            return out


def get_thread(service: Any, thread_id: str) -> GmailThread:
    raw = service.users().threads().get(userId="me", id=thread_id, format="full").execute()
    msgs = [_normalize_message(m) for m in raw.get("messages", [])]
    msgs.sort(key=lambda m: m.date)
    return GmailThread(id=raw["id"], messages=msgs)


def get_profile_email(service: Any) -> str:
    """Adresse email du compte connecté (utile pour détecter 'is_from_me')."""
    return service.users().getProfile(userId="me").execute().get("emailAddress", "").lower()


def _build_mime(
    *,
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
    in_reply_to: str = "",
    references: list[str] | None = None,
) -> str:
    msg = MIMEText(body, _subtype="plain", _charset="utf-8")
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    msg["Subject"] = subject
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    if references:
        msg["References"] = " ".join(references)
    return base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")


def create_draft(
    service: Any,
    *,
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
    thread_id: str = "",
    in_reply_to: str = "",
    references: list[str] | None = None,
) -> dict[str, Any]:
    """Crée un brouillon dans la boîte courante. Retourne le draft Gmail brut."""
    raw = _build_mime(
        to=to, subject=subject, body=body, cc=cc,
        in_reply_to=in_reply_to, references=references,
    )
    message: dict[str, Any] = {"raw": raw}
    if thread_id:
        message["threadId"] = thread_id
    return service.users().drafts().create(
        userId="me", body={"message": message},
    ).execute()


def send_message(
    service: Any,
    *,
    to: list[str],
    subject: str,
    body: str,
    cc: list[str] | None = None,
    thread_id: str = "",
    in_reply_to: str = "",
    references: list[str] | None = None,
) -> dict[str, Any]:
    """Envoie un mail immédiatement. Utilisé uniquement après validation Telegram."""
    raw = _build_mime(
        to=to, subject=subject, body=body, cc=cc,
        in_reply_to=in_reply_to, references=references,
    )
    message: dict[str, Any] = {"raw": raw}
    if thread_id:
        message["threadId"] = thread_id
    return service.users().messages().send(userId="me", body=message).execute()
