"""Revue des mails reçus sur compte perso — détecte oublis, drafte relances.

Contrat (cf. policies.md + SPEC.md) :
- Compte perso strictement **read-only**. Aucune action Gmail (envoi,
  draft, label) n'est jamais exécutée sur la boîte de Sylvain.
- Sortie = drafts markdown dans `drafts/`, à valider via Telegram.
  Quand validé, Sylvain copie/envoie depuis son client mail. La
  validation marque le draft `archived` (cf. apply_draft.py), sans
  toucher à Gmail.
- Fréquence : tous les 5 jours (cadence_days=5 dans schedule.yaml).
  Window de pull = cadence + 1 pour rattraper un run sauté.

Pipeline :
1. Pull threads `in:inbox` des N+1 derniers jours, hors catégories
   Gmail "promotions/social/forums/updates" (newsletters/transac).
2. Filtres locaux : skip si Sylvain a déjà répondu, ou si le dernier
   inbound a moins de 2 jours (pas encore un oubli).
3. Haiku classifie les candidats en un batch → flag `needs_reply`.
4. Sonnet drafte une relance courte par mail à traiter.
5. Drafts écrits dans `drafts/` (front matter avec `fingerprint=thread_id`
   pour éviter les doublons), récap Telegram.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime, timedelta
from typing import Any

from tasks._lib import dedup, gmail, llm, memory, notify, schedule

TASK = "mail_review"
log = logging.getLogger(TASK)

# Mail inbound dont l'âge est inférieur à ce seuil = pas encore un "oubli"
MIN_AGE_DAYS_BEFORE_FOLLOWUP = 2

# Plafonds de sécurité (coût + bruit)
MAX_THREADS_TO_FETCH = 100
MAX_THREADS_TO_CLASSIFY = 40
MAX_DRAFTS_TO_GENERATE = 8

# Filtre Gmail server-side. -category:* exclut les onglets non-perso.
GMAIL_QUERY_BASE = (
    "in:inbox "
    "-category:promotions -category:social -category:forums -category:updates"
)

DRAFT_EXPIRES_DAYS = 14


def _last_inbound(thread: gmail.GmailThread, my_email: str) -> gmail.GmailMessage | None:
    """Dernier message du thread qui n'est pas envoyé par Sylvain."""
    for m in reversed(thread.messages):
        if m.from_addr != my_email:
            return m
    return None


def _already_replied(thread: gmail.GmailThread, my_email: str) -> bool:
    """Sylvain a-t-il répondu après le dernier inbound ?"""
    last_in = _last_inbound(thread, my_email)
    if last_in is None:
        return True  # thread sans inbound : rien à relancer
    return any(
        m.from_addr == my_email and m.date > last_in.date for m in thread.messages
    )


def _select_candidates(
    threads: list[gmail.GmailThread],
    my_email: str,
    now: datetime,
) -> list[gmail.GmailThread]:
    cutoff = now - timedelta(days=MIN_AGE_DAYS_BEFORE_FOLLOWUP)
    out: list[gmail.GmailThread] = []
    for t in threads:
        if not t.messages:
            continue
        last_in = _last_inbound(t, my_email)
        if last_in is None:
            continue
        if last_in.date > cutoff:
            continue
        if _already_replied(t, my_email):
            continue
        out.append(t)
    return out


def _parse_json_array(text: str) -> list[dict[str, Any]]:
    """Tolère prefix/suffix narratif. Cherche le premier [ ... ] valide."""
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1 or end < start:
        raise ValueError("no JSON array found")
    return json.loads(text[start : end + 1])


def _classify_batch(
    candidates: list[gmail.GmailThread], my_email: str
) -> dict[str, dict[str, Any]]:
    """Haiku classifie en un appel. Retourne {thread_id: {needs_reply, reason}}."""
    if not candidates:
        return {}

    items = []
    for t in candidates:
        last_in = _last_inbound(t, my_email)
        if last_in is None:
            continue
        items.append({
            "id": t.id,
            "from": f"{last_in.from_name} <{last_in.from_addr}>".strip(),
            "subject": t.subject[:200],
            "snippet": last_in.snippet[:400],
            "age_days": (datetime.now(UTC) - last_in.date).days,
            "thread_size": len(t.messages),
        })

    prompt = (
        "Tu tries des mails reçus par Sylvain. Pour chacun, décide si une "
        "réponse de sa part est attendue (vraie demande, question, RDV à "
        "confirmer, action attendue de lui), ou si c'est purement informatif "
        "/ une notif auto / un mail sans attente de réponse.\n\n"
        "Réponds en JSON pur, un objet par mail, dans le MÊME ordre, format :\n"
        '[{"id": "<id>", "needs_reply": true|false, "reason": "<≤15 mots, fr>"}]\n\n'
        "Sois strict : besoin d'une vraie attente côté expéditeur pour "
        '"needs_reply": true. Pas de blabla, juste le JSON.\n\n'
        f"Mails à classer :\n{json.dumps(items, ensure_ascii=False, indent=1)}"
    )

    resp = llm.call(
        tier="haiku",
        messages=[{"role": "user", "content": prompt}],
        task=TASK,
        max_tokens=2048,
        temperature=0.0,
    )

    try:
        parsed = _parse_json_array(resp.text)
    except (ValueError, json.JSONDecodeError) as e:
        log.warning("classification JSON parse failed: %s — raw=%r", e, resp.text[:400])
        return {}

    return {
        str(row.get("id")): {
            "needs_reply": bool(row.get("needs_reply")),
            "reason": str(row.get("reason", "")),
        }
        for row in parsed
        if isinstance(row, dict) and row.get("id")
    }


def _draft_reply_text(thread: gmail.GmailThread, my_email: str) -> str:
    """Sonnet drafte la réponse. Retourne le texte brut du message."""
    last_in = _last_inbound(thread, my_email)
    assert last_in is not None

    history_lines: list[str] = []
    for m in thread.messages[-4:]:  # garde 4 derniers messages max
        who = "Sylvain" if m.from_addr == my_email else (m.from_name or m.from_addr)
        date_s = m.date.strftime("%Y-%m-%d")
        body_extract = (m.body_text or m.snippet)[:600].strip()
        history_lines.append(f"--- {date_s} — {who} ---\n{body_extract}")
    history = "\n\n".join(history_lines)

    prompt = (
        "Tu écris une réponse mail courte à la place de Sylvain. Style :\n"
        "- direct, dense, 2-4 phrases\n"
        "- ton bro / informel\n"
        "- français par défaut, anglais si le mail entrant est en anglais\n"
        "- pas de signature (juste le corps), pas de formules pompeuses\n"
        "- pas de \"j'espère que tu vas bien\", on entre dans le sujet\n"
        "- si une info manque pour répondre vraiment, drafte une réponse "
        "qui pose la question manquante plutôt que d'inventer.\n\n"
        f"Sujet du thread : {thread.subject}\n"
        f"Dernier expéditeur : {last_in.from_name or last_in.from_addr}\n\n"
        f"Historique récent :\n{history}\n\n"
        "Réponds UNIQUEMENT avec le texte de la réponse, rien d'autre. "
        "Pas de préambule, pas de \"Voici la réponse :\"."
    )

    resp = llm.call(
        tier="sonnet",
        messages=[{"role": "user", "content": prompt}],
        task=TASK,
        max_tokens=600,
        temperature=0.5,
    )
    return resp.text.strip()


def _slug(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s[:50] or "mail"


def _build_draft_body(
    thread: gmail.GmailThread,
    last_in: gmail.GmailMessage,
    reason: str,
    draft_text: str,
) -> str:
    gmail_url = f"https://mail.google.com/mail/u/0/#inbox/{thread.id}"
    snippet = (last_in.body_text or last_in.snippet)[:500].strip()
    return (
        f"## Contexte\n"
        f"- **De** : {last_in.from_name} <{last_in.from_addr}>\n"
        f"- **Date** : {last_in.date.strftime('%Y-%m-%d %H:%M UTC')} "
        f"({(datetime.now(UTC) - last_in.date).days}j)\n"
        f"- **Sujet** : {thread.subject}\n"
        f"- **Pourquoi détecté** : {reason}\n"
        f"- **Lien Gmail** : {gmail_url}\n\n"
        f"## Dernier message reçu\n```\n{snippet}\n```\n\n"
        f"## Brouillon de réponse\n```\n{draft_text}\n```\n\n"
        f"_Compte perso en read-only : copie/colle dans Gmail pour envoyer. "
        f"OK = archive le draft, SKIP = enregistre le pattern._"
    )


def run(cfg: dict[str, Any]) -> None:
    run_at = datetime.now(UTC)

    if not gmail.is_configured("perso"):
        log.warning("GMAIL_TOKEN_PERSO_JSON absent — skip mail_review")
        memory.write_run_log(
            task=TASK,
            run_at=run_at,
            status="skipped",
            summary="GMAIL_TOKEN_PERSO_JSON manquant",
            suffix="skip",
        )
        return

    cadence_days = int(cfg.get("cadence_days", 5))
    window_days = cadence_days + 1
    since = run_at - timedelta(days=window_days)

    service = gmail.service_for("perso")
    my_email = gmail.get_profile_email(service)
    log.info("connecté en tant que %s", my_email)

    thread_ids = gmail.list_threads_since(
        service, since,
        query_extra=GMAIL_QUERY_BASE,
        max_threads=MAX_THREADS_TO_FETCH,
    )
    log.info("threads pull : %d", len(thread_ids))

    threads = [gmail.get_thread(service, tid) for tid in thread_ids]
    candidates = _select_candidates(threads, my_email, run_at)
    log.info("candidats oubli après filtres locaux : %d", len(candidates))

    # On limite avant LLM pour éviter les explosions de coût sur un grand inbox
    candidates = candidates[:MAX_THREADS_TO_CLASSIFY]

    classification = _classify_batch(candidates, my_email)

    to_draft: list[tuple[gmail.GmailThread, dict[str, Any]]] = []
    for t in candidates:
        c = classification.get(t.id, {})
        if not c.get("needs_reply"):
            continue
        fp = dedup.fingerprint("mail_review_followup", t.id)
        if dedup.seen_recently(fp, run_at):
            log.info("dédup skip thread=%s", t.id)
            continue
        to_draft.append((t, c))
        if len(to_draft) >= MAX_DRAFTS_TO_GENERATE:
            break

    log.info("drafts à générer : %d", len(to_draft))

    created: list[str] = []
    for t, c in to_draft:
        last_in = _last_inbound(t, my_email)
        if last_in is None:
            continue
        try:
            draft_text = _draft_reply_text(t, my_email)
        except Exception as e:
            log.warning("draft generation failed thread=%s: %s", t.id, e)
            continue

        title = f"Relance mail — {t.subject[:60] or '(sans sujet)'}"
        body = _build_draft_body(t, last_in, c.get("reason", ""), draft_text)
        path = notify.create_draft(
            type_="mail_review_followup",
            title=title,
            body=body,
            priority="medium",
            expires_in_days=DRAFT_EXPIRES_DAYS,
            fingerprint=dedup.fingerprint("mail_review_followup", t.id),
            extra_fm={
                "thread_id": t.id,
                "from_addr": last_in.from_addr,
                "subject": t.subject,
                "action": "review_only",  # compte perso read-only
            },
            skip_check_subject=t.subject,
        )
        if path is not None:
            created.append(path.name)

    # Récap Telegram
    if created:
        listing = "\n".join(f"• {n}" for n in created[:8])
        more = f"\n(+{len(created) - 8})" if len(created) > 8 else ""
        msg = (
            f"mail_review — {len(created)} oubli(s) détecté(s) "
            f"sur {len(thread_ids)} threads {window_days}j\n{listing}{more}"
        )
    else:
        msg = (
            f"mail_review — RAS. {len(thread_ids)} threads scannés, "
            f"{len(candidates)} candidats, 0 relance à drafter."
        )
    notify.alert(msg, channel=cfg.get("channel", "perso"))

    memory.write_run_log(
        task=TASK,
        run_at=run_at,
        status="completed",
        summary=f"{len(created)} draft(s) créé(s), {len(thread_ids)} threads scannés",
        body=(
            f"## Stats\n"
            f"- threads pull (window {window_days}j) : {len(thread_ids)}\n"
            f"- candidats oubli après filtres : {len(candidates)}\n"
            f"- needs_reply (Haiku) : "
            f"{sum(1 for c in classification.values() if c.get('needs_reply'))}\n"
            f"- drafts créés : {len(created)}\n"
        ),
        extra={
            "threads_scanned": len(thread_ids),
            "candidates": len(candidates),
            "drafts_created": len(created),
            "my_email": my_email,
        },
    )


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    return schedule.run_guarded(TASK, run)


if __name__ == "__main__":
    raise SystemExit(main())
