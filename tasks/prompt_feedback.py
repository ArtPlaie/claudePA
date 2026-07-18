"""Routeur des réponses de Sylvain aux mails de rapport de veille.

Sylvain répond à un mail de rapport (serendipity, sorties locales…). Ce task lit
sa réponse dans l'inbox du compte PA (IMAP + app-password, cf. plus bas), la
**classe**, et route selon l'intention :

- **prompt_feedback** — il critique/ajuste une veille, ou corrige un fait mémoire
  → on écrit `feedback/<ts>-<veille>.md` (pending) ; la routine Claude Code
  `/adapt_prompt` (daily) applique l'édition du prompt / de la core-memory.

- **calendar** — il demande d'ajouter/réserver un événement ("réserve l'escalade
  dimanche 10h") → on extrait {titre, début, fin, lieu} et on crée l'event
  **directement** sur son agenda via l'API Google Calendar (`_lib/gcal.py`).
  Direct = validé par Sylvain lui-même (sa réponse EST l'instruction explicite).
  Trace committée dans `calendar/<ts>-<veille>.md`.

- **other** — rien d'actionnable → on marque lu et on log.

Auth :
- **Lecture inbox PA** : IMAP + mot de passe d'application (`GMAIL_USER` /
  `GMAIL_APP_PASSWORD`), le MÊME credential que le SMTP d'envoi de mail-report.
  Pas d'OAuth, rien à régénérer. (IMAP à activer sur le compte PA.)
- **Écriture agenda** : OAuth du compte de Sylvain, scope calendar.events
  (`GCAL_TOKEN_JSON`), cf. gcal.py.
- **Classification/extraction** : LLM (haiku), `ANTHROPIC_API_KEY`.

Idempotent : dédup sur le Message-ID (feedback/ + calendar/) et flag IMAP \\Seen
posé après traitement.
"""
from __future__ import annotations

import email
import imaplib
import json
import logging
import os
import re
from datetime import UTC, datetime, timedelta
from email.header import decode_header, make_header
from email.message import Message
from email.utils import parseaddr
from typing import Any

from tasks._lib import gcal, llm, memory, notify, paths, schedule
from tasks._lib.memory import MarkdownDoc

TASK = "prompt_feedback"
log = logging.getLogger(TASK)

IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993

REPORT_SUBJECT_PREFIX = "claudePA —"

# Titre lisible -> slug de veille. DOIT rester synchro avec le dict NICE de
# .github/workflows/mail-report.yml (source des sujets).
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
DEFAULT_EVENT_MINUTES = 60  # durée par défaut d'un event sans fin explicite

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


def _strip_quoted(text: str) -> str:
    out: list[str] = []
    for ln in text.replace("\r\n", "\n").split("\n"):
        if any(m.match(ln) for m in _QUOTE_MARKERS):
            break
        out.append(ln)
    return "\n".join(out).strip()


def _slug_for_subject(subject: str) -> str | None:
    if REPORT_SUBJECT_PREFIX not in subject:
        return None
    tail = subject.split(REPORT_SUBJECT_PREFIX, 1)[1]
    for title, slug in NICE_TO_SLUG.items():
        if title.lower() in tail.lower():
            return slug
    return None


def _already_ingested(message_id: str) -> bool:
    """Dédup : ce Message-ID a-t-il déjà produit un feedback OU un event ?"""
    if not message_id:
        return False
    for d in (paths.FEEDBACK, paths.CALENDAR):
        if not d.exists():
            continue
        for p in d.glob("*.md"):
            try:
                doc = MarkdownDoc.read(p)
            except OSError:
                continue
            if str(doc.front_matter.get("source_message_id", "")) == message_id:
                return True
    return False


# --------------------------------------------------------------------------- #
# Classification + extraction (LLM)
# --------------------------------------------------------------------------- #
def _parse_json_object(text: str) -> dict[str, Any]:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("no JSON object found")
    return json.loads(text[start : end + 1])


def _classify(new_text: str, full_context: str, subject: str, now_local: datetime) -> dict[str, Any]:
    """Classe la réponse et, si calendar, extrait l'événement. LLM haiku."""
    today = now_local.strftime("%A %Y-%m-%d %H:%M")
    prompt = (
        "Sylvain a répondu à un mail de rapport de son assistant perso. "
        "Classe l'intention de sa réponse et, si c'est une demande d'agenda, "
        "extrais l'événement.\n\n"
        f"Aujourd'hui : {today} (fuseau Europe/Paris). Résous les dates "
        "relatives (« dimanche », « ce week-end », « demain », « jeudi prochain ») "
        "par rapport à cette date.\n\n"
        "Intentions possibles :\n"
        "- \"calendar\" : il veut AJOUTER / RÉSERVER / BLOQUER un créneau dans son "
        "agenda (une sortie, un RDV, une activité datée).\n"
        "- \"prompt_feedback\" : il critique ou ajuste le comportement de la veille "
        "(ton, longueur, type d'idées), OU corrige une info fausse.\n"
        "- \"other\" : ni l'un ni l'autre (remerciement, blabla).\n\n"
        "Réponds en JSON PUR, rien d'autre :\n"
        "{\"intent\": \"calendar|prompt_feedback|other\", "
        "\"event\": {\"summary\": \"...\", \"start\": \"YYYY-MM-DDTHH:MM:SS\", "
        "\"end\": \"YYYY-MM-DDTHH:MM:SS\", \"all_day\": false, "
        "\"location\": \"...\", \"description\": \"...\"}}\n\n"
        "Règles event (uniquement si intent=calendar) :\n"
        "- start OBLIGATOIRE. Si l'heure n'est pas précisée mais le jour oui, "
        "mets all_day=true et start=\"YYYY-MM-DD\".\n"
        "- end : si non précisé, laisse \"\" (une durée par défaut sera appliquée).\n"
        "- summary : court et clair. location/description : tire-les du contexte "
        "(le rapport cité) si utile, sinon \"\".\n"
        "- Si tu ne peux pas déterminer de date/jour du tout, intent=\"other\".\n\n"
        f"Sujet du mail : {subject}\n\n"
        f"Réponse de Sylvain (texte neuf) :\n{new_text[:1500]}\n\n"
        f"Contexte (rapport cité, pour lieu/détails) :\n{full_context[:3000]}"
    )
    resp = llm.call(
        tier="haiku",
        messages=[{"role": "user", "content": prompt}],
        task=TASK,
        max_tokens=600,
        temperature=0.0,
    )
    try:
        return _parse_json_object(resp.text)
    except (ValueError, json.JSONDecodeError) as e:
        log.warning("classify JSON parse failed: %s — raw=%r", e, resp.text[:300])
        return {"intent": "other"}


def _normalize_times(event: dict[str, Any]) -> tuple[str, str, bool] | None:
    """Retourne (start_iso, end_iso, all_day) normalisés, ou None si start invalide."""
    start_raw = str(event.get("start", "")).strip()
    if not start_raw:
        return None
    all_day = bool(event.get("all_day")) or len(start_raw) == 10
    end_raw = str(event.get("end", "")).strip()

    if all_day:
        try:
            from datetime import date

            sd = date.fromisoformat(start_raw[:10])
        except ValueError:
            return None
        ed = None
        if end_raw:
            try:
                ed = date.fromisoformat(end_raw[:10])
            except ValueError:
                ed = None
        # Google : date de fin exclusive. Défaut / dégénéré → jour suivant.
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


def _write_calendar_record(
    *, slug: str, subject: str, from_addr: str, message_id: str,
    event: dict[str, Any], created: gcal.CreatedEvent | None,
    status: str, run_at: datetime, note: str = "",
) -> str:
    ts = run_at.strftime("%Y-%m-%dT%H-%M-%S")
    path = paths.CALENDAR / f"{ts}-{slug}.md"
    fm: dict[str, Any] = {
        "task": TASK,
        "created_at": run_at.isoformat(),
        "kind": "calendar",
        "veille": slug,
        "report_subject": subject,
        "from_addr": from_addr,
        "source_message_id": message_id,
        "status": status,  # created | pending_no_auth | error
    }
    if created is not None:
        fm["event_id"] = created.id
        fm["event_link"] = created.html_link
    if note:
        fm["note"] = note
    body = (
        "\n## Événement\n\n"
        f"- **Titre** : {event.get('summary', '(sans titre)')}\n"
        f"- **Début** : {event.get('start', '?')}\n"
        f"- **Fin** : {event.get('end', '?')}\n"
        f"- **Lieu** : {event.get('location', '') or '—'}\n"
        f"- **Statut** : {status}\n"
    )
    MarkdownDoc(front_matter=fm, body=body).write(path)
    return path.name


def _handle_calendar(
    *, slug: str, subject: str, from_addr: str, message_id: str,
    event: dict[str, Any], run_at: datetime, channel: str,
) -> str:
    """Crée l'event sur l'agenda. Retourne un libellé pour le récap."""
    norm = _normalize_times(event)
    if norm is None:
        notify.alert(
            f"prompt_feedback — demande d'agenda sur `{slug}` mais date illisible :\n"
            f"« {str(event.get('summary', ''))[:120]} »\nPrécise le jour/heure et renvoie.",
            channel=channel,
        )
        _write_calendar_record(
            slug=slug, subject=subject, from_addr=from_addr, message_id=message_id,
            event=event, created=None, status="error", run_at=run_at,
            note="date illisible",
        )
        return f"{slug}: date illisible (non créé)"

    start_iso, end_iso, all_day = norm
    event["start"], event["end"], event["all_day"] = start_iso, end_iso, all_day
    summary = str(event.get("summary") or "(sans titre)")

    if not gcal.is_configured():
        notify.alert(
            f"prompt_feedback — event à créer sur `{slug}` (« {summary[:80]} », "
            f"{start_iso}) mais GCAL_TOKEN_JSON absent. Configure l'OAuth agenda "
            f"(scripts/setup_gmail_oauth.py --account gcal) puis renvoie ta réponse.",
            channel=channel,
        )
        _write_calendar_record(
            slug=slug, subject=subject, from_addr=from_addr, message_id=message_id,
            event=event, created=None, status="pending_no_auth", run_at=run_at,
        )
        return f"{slug}: '{summary[:40]}' NON créé (OAuth agenda absent)"

    service = gcal.service_for()
    created = gcal.create_event(
        service,
        summary=summary,
        start=start_iso,
        end=end_iso,
        all_day=all_day,
        location=str(event.get("location") or ""),
        description=str(event.get("description") or ""),
    )
    _write_calendar_record(
        slug=slug, subject=subject, from_addr=from_addr, message_id=message_id,
        event=event, created=created, status="created", run_at=run_at,
    )
    when = start_iso if all_day else start_iso.replace("T", " ")
    notify.alert(
        f"📅 Event créé : « {summary} » — {when}\n{created.html_link}",
        channel=channel,
    )
    return f"{slug}: event « {summary[:40]} » créé ({when})"


def _write_feedback(
    *, slug: str, subject: str, feedback_text: str, from_addr: str,
    message_id: str, run_at: datetime,
) -> str:
    ts = run_at.strftime("%Y-%m-%dT%H-%M-%S")
    path = paths.FEEDBACK / f"{ts}-{slug}.md"
    fm = {
        "task": TASK,
        "created_at": run_at.isoformat(),
        "veille": slug,
        "command_file": f".claude/commands/{slug}.md",
        "report_subject": subject,
        "from_addr": from_addr,
        "source_message_id": message_id,
        "status": "pending",
    }
    body = "\n## Feedback de Sylvain (réponse au rapport)\n\n" f"{feedback_text}\n"
    MarkdownDoc(front_matter=fm, body=body).write(path)
    return path.name


# --------------------------------------------------------------------------- #
# Run
# --------------------------------------------------------------------------- #
def run(cfg: dict[str, Any]) -> None:
    run_at = datetime.now(UTC)
    channel = cfg.get("channel", "perso")

    user = (os.environ.get("GMAIL_USER") or "").strip()
    pwd = (os.environ.get("GMAIL_APP_PASSWORD") or "").replace(" ", "")
    sylvain = (os.environ.get("MAIL_TO") or "").strip().lower()

    missing = [n for n, v in (
        ("GMAIL_USER", user), ("GMAIL_APP_PASSWORD", pwd), ("MAIL_TO", sylvain)
    ) if not v]
    if missing:
        log.warning("secrets manquants : %s — skip", ", ".join(missing))
        memory.write_run_log(
            task=TASK, run_at=run_at, status="skipped",
            summary=f"secrets manquants : {', '.join(missing)}", suffix="skip",
        )
        return

    now_local = gcal.now_local()

    imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    feedbacks: list[str] = []
    events: list[str] = []
    others = 0
    nums: list[bytes] = []
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
            if _already_ingested(message_id):
                imap.store(num, "+FLAGS", "\\Seen")
                continue

            full_body = _plain_body(m)
            new_text = _strip_quoted(full_body)
            if not new_text:
                imap.store(num, "+FLAGS", "\\Seen")
                continue

            classification = _classify(new_text, full_body, subject, now_local)
            intent = str(classification.get("intent", "other"))

            if intent == "calendar" and isinstance(classification.get("event"), dict):
                label = _handle_calendar(
                    slug=slug, subject=subject, from_addr=from_addr,
                    message_id=message_id, event=classification["event"],
                    run_at=run_at, channel=channel,
                )
                events.append(label)
            elif intent == "prompt_feedback":
                name = _write_feedback(
                    slug=slug, subject=subject, feedback_text=new_text,
                    from_addr=from_addr, message_id=message_id, run_at=run_at,
                )
                feedbacks.append(f"{slug} ({name})")
                notify.alert(
                    f"prompt_feedback — feedback reçu sur `{slug}` :\n"
                    f"« {new_text[:200]} »\n"
                    f"→ /adapt_prompt ajustera au prochain run.",
                    channel=channel,
                )
            else:
                others += 1
                log.info("intent=%s (rien à faire) sur %s", intent, slug)

            imap.store(num, "+FLAGS", "\\Seen")
    finally:
        try:
            imap.logout()
        except Exception:  # noqa: BLE001
            pass

    parts = []
    if feedbacks:
        parts.append(f"{len(feedbacks)} feedback(s) : {', '.join(feedbacks)}")
    if events:
        parts.append(f"{len(events)} event(s) : {'; '.join(events)}")
    if others:
        parts.append(f"{others} autre(s) ignoré(s)")
    summary = " | ".join(parts) if parts else f"RAS ({len(nums)} non-lus scannés)"
    log.info(summary)

    memory.write_run_log(
        task=TASK, run_at=run_at, status="completed",
        summary=summary,
        extra={
            "candidates": len(nums),
            "feedback_created": len(feedbacks),
            "events_created": len(events),
            "others": others,
            "pa_email": user,
        },
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    return schedule.run_guarded(TASK, run)


if __name__ == "__main__":
    raise SystemExit(main())
