"""Ingestion des réponses de Sylvain aux mails de rapport de veille.

Boucle d'auto-tuning des prompts, moitié GHA (ce fichier) :

    rapport de veille  --mail-report.yml-->  mail à Sylvain
    Sylvain répond au mail  ("ton trop mou, sois plus sérieux")
    -> la réponse atterrit dans l'inbox du compte PA (l'expéditeur du rapport)
    -> CE task lit l'inbox PA, identifie la veille visée, écrit un
       `feedback/<ts>-<veille>.md` (status: pending)
    -> la routine Claude Code `/adapt_prompt` (daily) lit ce pending, édite
       `.claude/commands/<veille>.md` en conséquence, commit sur main.

Pourquoi une GHA et pas la routine directement : une routine Claude Code n'a
pas d'accès Gmail (pas d'OAuth dans son env, cf. CLAUDE.md Chemin A vs B).
Seul le chemin GHA (token PA, scope modify) peut lire l'inbox. La routine, elle,
sait éditer un prompt de façon chirurgicale — d'où le découpage en deux temps.

Contrat :
- Compte **PA** (r/w, scope modify) : c'est lui qui envoie les rapports
  (`GMAIL_USER`), donc les réponses de Sylvain y reviennent. On lit l'inbox,
  on marque le message lu après ingestion (anti-re-traitement).
- On n'ingère QUE les réponses venant de Sylvain (`MAIL_TO`) sur un thread
  dont le sujet matche un rapport de veille connu — pas de mail tiers.
- Idempotent : dédup sur le message-id source (backstop au flag `is:unread`).
"""
from __future__ import annotations

import logging
import os
import re
from datetime import UTC, datetime, timedelta
from typing import Any

from tasks._lib import gmail, memory, notify, paths, schedule
from tasks._lib.memory import MarkdownDoc

TASK = "prompt_feedback"
log = logging.getLogger(TASK)

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

# Fenêtre de recherche des réponses (large : Sylvain peut répondre en différé).
LOOKBACK_DAYS = 30
MAX_THREADS = 60

# Lignes qui marquent le début du texte cité dans une réponse mail.
_QUOTE_MARKERS = [
    re.compile(r"^>"),
    re.compile(r"^\s*Le\s.+\sa\s.crit\s*:\s*$"),  # "Le … a écrit :"
    re.compile(r"^\s*On\s.+\swrote:\s*$"),
    re.compile(r"^\s*-{2,}\s*Original Message\s*-{2,}", re.I),
    re.compile(r"^\s*_{5,}\s*$"),
]


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
    """Backstop dédup : un feedback pour ce message-id existe déjà ?"""
    if not paths.FEEDBACK.exists():
        return False
    for p in paths.FEEDBACK.glob("*.md"):
        try:
            doc = MarkdownDoc.read(p)
        except OSError:
            continue
        if str(doc.front_matter.get("source_message_id", "")) == message_id:
            return True
    return False


def _mark_read(service: Any, message_id: str) -> None:
    try:
        service.users().messages().modify(
            userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
        ).execute()
    except Exception as e:  # noqa: BLE001 — best-effort, la dédup fichier couvre
        log.warning("mark-read a échoué (msg=%s): %s", message_id, e)


def _write_feedback(
    *,
    slug: str,
    subject: str,
    feedback_text: str,
    msg: gmail.GmailMessage,
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
        "from_addr": msg.from_addr,
        "source_message_id": msg.id,
        "source_thread_id": msg.thread_id,
        "status": "pending",
    }
    body = (
        "\n## Feedback de Sylvain (réponse au rapport)\n\n"
        f"{feedback_text}\n"
    )
    MarkdownDoc(front_matter=fm, body=body).write(path)
    return path.name


def run(cfg: dict[str, Any]) -> None:
    run_at = datetime.now(UTC)

    if not gmail.is_configured("pa"):
        log.warning("GMAIL_TOKEN_PA_JSON absent — skip prompt_feedback")
        memory.write_run_log(
            task=TASK, run_at=run_at, status="skipped",
            summary="GMAIL_TOKEN_PA_JSON manquant", suffix="skip",
        )
        return

    sylvain = (os.environ.get("MAIL_TO") or "").strip().lower()
    if not sylvain:
        log.warning("MAIL_TO absent — impossible d'identifier les réponses de Sylvain")
        memory.write_run_log(
            task=TASK, run_at=run_at, status="skipped",
            summary="MAIL_TO manquant", suffix="skip",
        )
        return

    service = gmail.service_for("pa")
    pa_email = gmail.get_profile_email(service)
    log.info("compte PA : %s — cherche les réponses de %s", pa_email, sylvain)

    since = run_at - timedelta(days=LOOKBACK_DAYS)
    thread_ids = gmail.list_threads_since(
        service, since,
        query_extra='in:inbox is:unread subject:claudePA',
        max_threads=MAX_THREADS,
    )
    log.info("threads inbox non-lus 'claudePA' : %d", len(thread_ids))

    created: list[str] = []
    scanned = 0
    for tid in thread_ids:
        thread = gmail.get_thread(service, tid)
        # Dernier message qui n'est pas le PA lui-même = la réponse de Sylvain.
        reply = next(
            (m for m in reversed(thread.messages) if m.from_addr != pa_email),
            None,
        )
        if reply is None:
            continue
        scanned += 1
        if reply.from_addr != sylvain:
            log.info("thread %s : dernier msg pas de Sylvain (%s), skip", tid, reply.from_addr)
            continue
        slug = _slug_for_subject(reply.subject or thread.subject)
        if slug is None:
            log.info("thread %s : sujet non mappé à une veille, skip", tid)
            continue
        if _already_ingested(reply.id):
            log.info("thread %s : déjà ingéré (msg=%s), mark-read", tid, reply.id)
            _mark_read(service, reply.id)
            continue

        feedback_text = _strip_quoted(reply.body_text or reply.snippet)
        if not feedback_text:
            log.info("thread %s : réponse vide après strip, skip", tid)
            _mark_read(service, reply.id)
            continue

        name = _write_feedback(
            slug=slug,
            subject=reply.subject or thread.subject,
            feedback_text=feedback_text,
            msg=reply,
            run_at=run_at,
        )
        _mark_read(service, reply.id)
        created.append(f"{slug} ({name})")
        notify.alert(
            f"prompt_feedback — feedback reçu sur `{slug}` :\n"
            f"« {feedback_text[:200]} »\n"
            f"→ la routine /adapt_prompt ajustera le prompt au prochain run.",
            channel=cfg.get("channel", "perso"),
        )

    if created:
        summary = f"{len(created)} feedback(s) ingéré(s) : {', '.join(created)}"
    else:
        summary = f"RAS. {len(thread_ids)} threads non-lus scannés, 0 feedback."
    log.info(summary)

    memory.write_run_log(
        task=TASK, run_at=run_at, status="completed",
        summary=summary,
        extra={
            "threads_scanned": scanned,
            "feedback_created": len(created),
            "pa_email": pa_email,
        },
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    return schedule.run_guarded(TASK, run)


if __name__ == "__main__":
    raise SystemExit(main())
