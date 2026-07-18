"""Pont I/O entre la boîte mail du PA et la routine `/adapt_prompt`.

Ce task est volontairement **bête** (zéro LLM, zéro décision) : il ne fait que
les entrées/sorties que la routine Claude Code ne peut pas faire elle-même
(pas d'accès réseau externe dans son sandbox). Tout le *raisonnement* — décider
quoi éditer, quels events créer — est fait par la routine `/adapt_prompt`.

Deux moitiés, à chaque run :

1. **Récupère** les réponses non-lues de Sylvain (inbox du compte PA, IMAP +
   app-password) et les dépose BRUTES dans `replies/<ts>-<veille>.md` (pending).
   Aucune classification : la routine lira le texte et décidera de tout (mail
   mixte « ajuste le ton ET réserve samedi ET corrige X » → géré nativement).

2. **Exécute** les events que la routine a mis en file : les `calendar/*.md` en
   `status: requested` (écrits par la routine, qui ne peut pas appeler l'API)
   sont créés sur l'agenda de Sylvain via l'API Calendar (`_lib/gcal.py`), puis
   passés en `status: created`.

Auth :
- Lecture inbox PA : IMAP + `GMAIL_USER` / `GMAIL_APP_PASSWORD` (même
  app-password que le SMTP de mail-report ; pas d'OAuth).
- Écriture agenda : OAuth compte Sylvain, `GCAL_TOKEN_JSON` (scope calendar.events).

Idempotent : réponses dédupliquées sur Message-ID + flag IMAP \\Seen ; events
actionnés une seule fois (requested → created).
"""
from __future__ import annotations

import email
import imaplib
import logging
import os
import re
from datetime import UTC, datetime, timedelta
from email.header import decode_header, make_header
from email.message import Message
from email.utils import parseaddr
from typing import Any

from tasks._lib import gcal, memory, notify, paths, schedule
from tasks._lib.memory import MarkdownDoc

TASK = "prompt_feedback"
log = logging.getLogger(TASK)

IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993

REPORT_SUBJECT_PREFIX = "claudePA —"

# Titre lisible -> slug de veille. Synchro avec le dict NICE de mail-report.yml.
NICE_TO_SLUG: dict[str, str] = {
    "Sydney & Suisse": "sydney_opportunities",
    "Briefing de la semaine": "weekly_briefing",
    "Jobs & formations IA": "ai_jobs_formations",
    "Sorties locales": "local_activities",
    "À faire ces 10 jours": "activities_next10days",
    "Veille santé": "health_watch",
    "Serendipity": "serendipity",
}

MAX_MESSAGES = 40
DEFAULT_EVENT_MINUTES = 60
QUOTED_CONTEXT_CHARS = 2000

_QUOTE_MARKERS = [
    re.compile(r"^>"),
    re.compile(r"^\s*Le\s.+\sa\s.crit\s*:\s*$"),
    re.compile(r"^\s*On\s.+\swrote:\s*$"),
    re.compile(r"^\s*-{2,}\s*Original Message\s*-{2,}", re.I),
    re.compile(r"^\s*_{5,}\s*$"),
]


# --------------------------------------------------------------------------- #
# Parsing mail
# --------------------------------------------------------------------------- #
def _decode_header(raw: str | None) -> str:
    if not raw:
        return ""
    try:
        return str(make_header(decode_header(raw)))
    except Exception:  # noqa: BLE001
        return raw


def _plain_body(msg: Message) -> str:
    plain = ""
    html = ""
    for part in msg.walk():
        if part.get_content_maintype() == "multipart":
            continue
        if part.get("Content-Disposition", "").startswith("attachment"):
            continue
        try:
            payload = part.get_payload(decode=True)
        except Exception:  # noqa: BLE001
            continue
        if payload is None:
            continue
        charset = part.get_content_charset() or "utf-8"
        text = payload.decode(charset, errors="replace")
        ctype = part.get_content_type()
        if ctype == "text/plain" and not plain:
            plain = text
        elif ctype == "text/html" and not html:
            html = text
    if plain:
        return plain
    if html:
        return re.sub(r"<[^>]+>", "", html)
    return ""


def _split_new_and_quoted(text: str) -> tuple[str, str]:
    """Sépare le texte neuf (en tête) du message cité (rapport d'origine)."""
    lines = text.replace("\r\n", "\n").split("\n")
    for i, ln in enumerate(lines):
        if any(m.match(ln) for m in _QUOTE_MARKERS):
            return "\n".join(lines[:i]).strip(), "\n".join(lines[i:]).strip()
    return "\n".join(lines).strip(), ""


def _slug_for_subject(subject: str) -> str | None:
    if REPORT_SUBJECT_PREFIX not in subject:
        return None
    tail = subject.split(REPORT_SUBJECT_PREFIX, 1)[1]
    for title, slug in NICE_TO_SLUG.items():
        if title.lower() in tail.lower():
            return slug
    return None


def _reply_already_dumped(message_id: str) -> bool:
    if not message_id or not paths.REPLIES.exists():
        return False
    for p in paths.REPLIES.glob("*.md"):
        try:
            doc = MarkdownDoc.read(p)
        except OSError:
            continue
        if str(doc.front_matter.get("source_message_id", "")) == message_id:
            return True
    return False


def _dump_reply(
    *, slug: str, subject: str, from_addr: str, message_id: str,
    new_text: str, quoted: str, run_at: datetime,
) -> str:
    ts = run_at.strftime("%Y-%m-%dT%H-%M-%S")
    path = paths.REPLIES / f"{ts}-{slug}.md"
    fm = {
        "task": TASK,
        "created_at": run_at.isoformat(),
        "veille": slug,
        "report_subject": subject,
        "from_addr": from_addr,
        "source_message_id": message_id,
        "status": "pending",
    }
    body = f"\n## Réponse de Sylvain\n\n{new_text}\n"
    if quoted:
        body += (
            "\n## Contexte (rapport cité, tronqué)\n\n"
            f"{quoted[:QUOTED_CONTEXT_CHARS]}\n"
        )
    MarkdownDoc(front_matter=fm, body=body).write(path)
    return path.name


# --------------------------------------------------------------------------- #
# Partie 1 — récupération des réponses
# --------------------------------------------------------------------------- #
def _fetch_replies(cfg: dict[str, Any], run_at: datetime) -> tuple[list[str], int]:
    user = (os.environ.get("GMAIL_USER") or "").strip()
    pwd = (os.environ.get("GMAIL_APP_PASSWORD") or "").replace(" ", "")
    sylvain = (os.environ.get("MAIL_TO") or "").strip().lower()
    if not (user and pwd and sylvain):
        log.warning("secrets IMAP absents (GMAIL_USER/APP_PASSWORD/MAIL_TO) — skip fetch")
        return [], 0

    imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    dumped: list[str] = []
    scanned = 0
    try:
        imap.login(user, pwd)
        imap.select("INBOX")
        typ, data = imap.search(None, "UNSEEN", "FROM", sylvain, "SUBJECT", "claudePA")
        nums = data[0].split() if typ == "OK" and data and data[0] else []
        log.info("compte PA %s — %d réponse(s) non-lue(s)", user, len(nums))
        for num in nums[:MAX_MESSAGES]:
            typ, msgdata = imap.fetch(num, "(RFC822)")
            if typ != "OK" or not msgdata or not isinstance(msgdata[0], tuple):
                continue
            m = email.message_from_bytes(msgdata[0][1])
            subject = _decode_header(m.get("Subject"))
            from_addr = parseaddr(m.get("From", ""))[1].lower()
            message_id = (m.get("Message-ID") or "").strip()
            if from_addr != sylvain:
                continue
            slug = _slug_for_subject(subject)
            if slug is None:
                log.info("sujet non mappé, skip : %r", subject)
                continue
            if _reply_already_dumped(message_id):
                imap.store(num, "+FLAGS", "\\Seen")
                continue
            new_text, quoted = _split_new_and_quoted(_plain_body(m))
            if not new_text:
                imap.store(num, "+FLAGS", "\\Seen")
                continue
            name = _dump_reply(
                slug=slug, subject=subject, from_addr=from_addr,
                message_id=message_id, new_text=new_text, quoted=quoted, run_at=run_at,
            )
            imap.store(num, "+FLAGS", "\\Seen")
            dumped.append(f"{slug} ({name})")
            scanned += 1
            notify.alert(
                f"prompt_feedback — réponse reçue sur `{slug}` :\n"
                f"« {new_text[:200]} »\n→ /adapt_prompt la traitera au prochain run.",
                channel=cfg.get("channel", "perso"),
            )
    finally:
        try:
            imap.logout()
        except Exception:  # noqa: BLE001
            pass
    return dumped, scanned


# --------------------------------------------------------------------------- #
# Partie 2 — exécution des events demandés par la routine
# --------------------------------------------------------------------------- #
def _normalize_times(event: dict[str, Any]) -> tuple[str, str, bool] | None:
    start_raw = str(event.get("start", "")).strip()
    if not start_raw:
        return None
    all_day = bool(event.get("all_day")) or len(start_raw) == 10
    end_raw = str(event.get("end", "")).strip()
    if all_day:
        from datetime import date
        try:
            sd = date.fromisoformat(start_raw[:10])
        except ValueError:
            return None
        ed = None
        if end_raw:
            try:
                ed = date.fromisoformat(end_raw[:10])
            except ValueError:
                ed = None
        if ed is None or ed <= sd:
            ed = sd + timedelta(days=1)
        return sd.isoformat(), ed.isoformat(), True
    try:
        sdt = datetime.fromisoformat(start_raw)
    except ValueError:
        return None
    edt = None
    if end_raw:
        try:
            edt = datetime.fromisoformat(end_raw)
        except ValueError:
            edt = None
    if edt is None or edt <= sdt:
        edt = sdt + timedelta(minutes=DEFAULT_EVENT_MINUTES)
    return sdt.isoformat(), edt.isoformat(), False


def _actuate_calendar(cfg: dict[str, Any], run_at: datetime) -> list[str]:
    """Crée les events `calendar/*.md` en status=requested. Retourne les libellés."""
    if not paths.CALENDAR.exists():
        return []
    channel = cfg.get("channel", "perso")
    done: list[str] = []
    for p in sorted(paths.CALENDAR.glob("*.md")):
        try:
            doc = MarkdownDoc.read(p)
        except OSError:
            continue
        fm = doc.front_matter
        if fm.get("status") != "requested":
            continue
        summary = str(fm.get("summary") or "(sans titre)")

        norm = _normalize_times(fm)
        if norm is None:
            fm["status"] = "error"
            fm["note"] = "date illisible (start manquant/invalide)"
            doc.write(p)
            notify.alert(
                f"prompt_feedback — event « {summary[:80]} » non créé : date illisible.",
                channel=channel,
            )
            done.append(f"{summary[:40]} : erreur date")
            continue

        if not gcal.is_configured():
            notify.alert(
                f"prompt_feedback — event « {summary[:80]} » en attente : "
                f"GCAL_TOKEN_JSON absent. Configure l'OAuth agenda "
                f"(scripts/setup_gmail_oauth.py --account gcal).",
                channel=channel,
            )
            # On laisse status=requested : sera créé au prochain run une fois l'OAuth en place.
            done.append(f"{summary[:40]} : en attente OAuth")
            continue

        start_iso, end_iso, all_day = norm
        try:
            service = gcal.service_for()
            created = gcal.create_event(
                service,
                summary=summary,
                start=start_iso,
                end=end_iso,
                all_day=all_day,
                location=str(fm.get("location") or ""),
                description=str(fm.get("description") or ""),
            )
        except Exception as e:  # noqa: BLE001
            log.warning("création event échouée (%s): %s", p.name, e)
            fm["status"] = "error"
            fm["note"] = f"{type(e).__name__}: {e}"
            doc.write(p)
            notify.alert(
                f"prompt_feedback — échec création event « {summary[:80]} » : "
                f"{type(e).__name__}. Voir {p.name}.",
                channel=channel,
            )
            done.append(f"{summary[:40]} : échec API")
            continue

        fm["status"] = "created"
        fm["created_event_at"] = run_at.isoformat()
        fm["event_id"] = created.id
        fm["event_link"] = created.html_link
        fm["start"], fm["end"], fm["all_day"] = start_iso, end_iso, all_day
        doc.write(p)
        when = start_iso if all_day else start_iso.replace("T", " ")
        notify.alert(
            f"📅 Event créé : « {summary} » — {when}\n{created.html_link}",
            channel=channel,
        )
        done.append(f"{summary[:40]} créé ({when})")
    return done


# --------------------------------------------------------------------------- #
# Run
# --------------------------------------------------------------------------- #
def run(cfg: dict[str, Any]) -> None:
    run_at = datetime.now(UTC)

    dumped, scanned = _fetch_replies(cfg, run_at)
    events = _actuate_calendar(cfg, run_at)

    parts = []
    if dumped:
        parts.append(f"{len(dumped)} réponse(s) déposée(s) : {', '.join(dumped)}")
    if events:
        parts.append(f"{len(events)} event(s) : {'; '.join(events)}")
    summary = " | ".join(parts) if parts else "RAS (aucune réponse, aucun event en file)"
    log.info(summary)

    memory.write_run_log(
        task=TASK, run_at=run_at, status="completed",
        summary=summary,
        extra={
            "replies_dumped": len(dumped),
            "events_actuated": len(events),
        },
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    return schedule.run_guarded(TASK, run)


if __name__ == "__main__":
    raise SystemExit(main())
