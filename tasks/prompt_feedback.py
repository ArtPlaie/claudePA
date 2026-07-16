"""Ingestion des réponses de Sylvain aux mails de rapport de veille.

Boucle d'auto-tuning des prompts, moitié GHA (ce fichier) :

    rapport de veille  --mail-report.yml-->  mail à Sylvain
    Sylvain répond au mail  ("ton trop mou, sois plus sérieux")
    -> la réponse atterrit dans l'inbox du compte PA (l'expéditeur du rapport)
    -> CE task lit l'inbox PA, identifie la veille visée, écrit un
       `feedback/<ts>-<veille>.md` (status: pending)
    -> la routine Claude Code `/adapt_prompt` (daily) lit ce pending, édite
       `.claude/commands/<veille>.md` en conséquence, commit sur main.

Auth : **IMAP + mot de passe d'application** — le MÊME credential que
`mail-report.yml` utilise pour envoyer en SMTP (`GMAIL_USER` /
`GMAIL_APP_PASSWORD`). SMTP envoie, IMAP lit ; app-password commun, pas d'OAuth,
donc rien à régénérer et pas d'expiration 7j comme un refresh token en Testing.
(Prérequis côté compte PA : IMAP activé dans Gmail → Paramètres →
Transfert et POP/IMAP → Activer IMAP.)

Pourquoi une GHA et pas la routine directement : une routine Claude Code n'a pas
d'accès mail (cf. CLAUDE.md Chemin A vs B). La routine, elle, sait éditer un
prompt de façon chirurgicale — d'où le découpage en deux temps.

Contrat :
- On n'ingère QUE les réponses venant de Sylvain (`MAIL_TO`) sur un mail dont le
  sujet matche un rapport de veille connu — pas de mail tiers.
- Idempotent : dédup sur le Message-ID (backstop au flag IMAP \\Seen posé après
  ingestion).
"""
from __future__ import annotations

import email
import imaplib
import logging
import os
import re
from datetime import UTC, datetime
from email.header import decode_header, make_header
from email.message import Message
from email.utils import parseaddr
from typing import Any

from tasks._lib import memory, notify, paths, schedule
from tasks._lib.memory import MarkdownDoc

TASK = "prompt_feedback"
log = logging.getLogger(TASK)

IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993

# Préfixe du sujet des rapports (cf. mail-report.yml : "claudePA — {title} …").
REPORT_SUBJECT_PREFIX = "claudePA —"

# Titre lisible -> slug de veille. DOIT rester synchro avec le dict NICE de
# .github/workflows/mail-report.yml (source des sujets). Si tu ajoutes une
# veille au mail, ajoute-la aussi ici, sinon sa réponse n'est pas ingérée.
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

# Lignes qui marquent le début du texte cité dans une réponse mail.
_QUOTE_MARKERS = [
    re.compile(r"^>"),
    re.compile(r"^\s*Le\s.+\sa\s.crit\s*:\s*$"),  # "Le … a écrit :"
    re.compile(r"^\s*On\s.+\swrote:\s*$"),
    re.compile(r"^\s*-{2,}\s*Original Message\s*-{2,}", re.I),
    re.compile(r"^\s*_{5,}\s*$"),
]


def _decode_header(raw: str | None) -> str:
    if not raw:
        return ""
    try:
        return str(make_header(decode_header(raw)))
    except Exception:  # noqa: BLE001 — header exotique : on garde le brut
        return raw


def _plain_body(msg: Message) -> str:
    """Extrait le text/plain d'un message email. Fallback text/html stripped."""
    plain = ""
    html = ""
    for part in msg.walk():
        ctype = part.get_content_type()
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
    """Garde le texte neuf en tête de réponse, coupe le message cité."""
    out: list[str] = []
    for ln in text.replace("\r\n", "\n").split("\n"):
        if any(m.match(ln) for m in _QUOTE_MARKERS):
            break
        out.append(ln)
    return "\n".join(out).strip()


def _slug_for_subject(subject: str) -> str | None:
    """Reverse-map un sujet de réponse (Re: claudePA — <titre> (date)) -> slug."""
    if REPORT_SUBJECT_PREFIX not in subject:
        return None
    tail = subject.split(REPORT_SUBJECT_PREFIX, 1)[1]  # " <titre> (date)"
    for title, slug in NICE_TO_SLUG.items():
        if title.lower() in tail.lower():
            return slug
    return None


def _already_ingested(message_id: str) -> bool:
    """Backstop dédup : un feedback pour ce Message-ID existe déjà ?"""
    if not message_id or not paths.FEEDBACK.exists():
        return False
    for p in paths.FEEDBACK.glob("*.md"):
        try:
            doc = MarkdownDoc.read(p)
        except OSError:
            continue
        if str(doc.front_matter.get("source_message_id", "")) == message_id:
            return True
    return False


def _write_feedback(
    *,
    slug: str,
    subject: str,
    feedback_text: str,
    from_addr: str,
    message_id: str,
    run_at: datetime,
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


def run(cfg: dict[str, Any]) -> None:
    run_at = datetime.now(UTC)

    user = (os.environ.get("GMAIL_USER") or "").strip()
    pwd = (os.environ.get("GMAIL_APP_PASSWORD") or "").replace(" ", "")
    sylvain = (os.environ.get("MAIL_TO") or "").strip().lower()

    missing = [
        n for n, v in (
            ("GMAIL_USER", user), ("GMAIL_APP_PASSWORD", pwd), ("MAIL_TO", sylvain)
        ) if not v
    ]
    if missing:
        log.warning("secrets manquants : %s — skip prompt_feedback", ", ".join(missing))
        memory.write_run_log(
            task=TASK, run_at=run_at, status="skipped",
            summary=f"secrets manquants : {', '.join(missing)}", suffix="skip",
        )
        return

    imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    try:
        imap.login(user, pwd)
        imap.select("INBOX")
        # Réponses non-lues de Sylvain sur un rapport claudePA.
        typ, data = imap.search(
            None, "UNSEEN", "FROM", sylvain, "SUBJECT", "claudePA"
        )
        nums = data[0].split() if typ == "OK" and data and data[0] else []
        log.info("compte PA %s — %d réponse(s) non-lue(s) candidate(s)", user, len(nums))

        created: list[str] = []
        scanned = 0
        for num in nums[:MAX_MESSAGES]:
            typ, msgdata = imap.fetch(num, "(RFC822)")
            if typ != "OK" or not msgdata or not isinstance(msgdata[0], tuple):
                continue
            m = email.message_from_bytes(msgdata[0][1])
            scanned += 1

            subject = _decode_header(m.get("Subject"))
            from_addr = parseaddr(m.get("From", ""))[1].lower()
            message_id = (m.get("Message-ID") or "").strip()

            if from_addr != sylvain:
                continue
            slug = _slug_for_subject(subject)
            if slug is None:
                log.info("sujet non mappé à une veille, skip : %r", subject)
                continue
            if _already_ingested(message_id):
                imap.store(num, "+FLAGS", "\\Seen")
                continue

            feedback_text = _strip_quoted(_plain_body(m))
            if not feedback_text:
                imap.store(num, "+FLAGS", "\\Seen")
                continue

            name = _write_feedback(
                slug=slug, subject=subject, feedback_text=feedback_text,
                from_addr=from_addr, message_id=message_id, run_at=run_at,
            )
            imap.store(num, "+FLAGS", "\\Seen")
            created.append(f"{slug} ({name})")
            notify.alert(
                f"prompt_feedback — feedback reçu sur `{slug}` :\n"
                f"« {feedback_text[:200]} »\n"
                f"→ la routine /adapt_prompt ajustera le prompt au prochain run.",
                channel=cfg.get("channel", "perso"),
            )
    finally:
        try:
            imap.logout()
        except Exception:  # noqa: BLE001
            pass

    if created:
        summary = f"{len(created)} feedback(s) ingéré(s) : {', '.join(created)}"
    else:
        summary = f"RAS. {len(nums)} réponse(s) non-lue(s) scannée(s), 0 feedback."
    log.info(summary)

    memory.write_run_log(
        task=TASK, run_at=run_at, status="completed",
        summary=summary,
        extra={
            "candidates": len(nums),
            "scanned": scanned,
            "feedback_created": len(created),
            "pa_email": user,
        },
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    return schedule.run_guarded(TASK, run)


if __name__ == "__main__":
    raise SystemExit(main())
