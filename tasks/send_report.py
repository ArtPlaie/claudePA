"""Envoi du compte rendu d'une routine par mail (API Gmail HTTPS, compte PA).

Pourquoi ce module : depuis une routine / Claude Code on the web, le SMTP
brut (465/587) est bloqué par le proxy egress (seul le 443 sort). L'API
Gmail OAuth passe en HTTPS → c'est la voie pour envoyer un mail depuis une
routine. On réutilise `tasks/_lib/gmail.py` (compte PA, scope gmail.modify,
env var `GMAIL_TOKEN_PA_JSON`).

Usage (en fin de command de veille) :

    uv run python -m tasks.send_report \
        --file working-memory/2026-06-08-0530-sydney_opportunities.md \
        --subject "claudePA — veille Sydney 2026-06-08"

Le corps du mail = le contenu du fichier (le rapport committé). Destinataire
= `--to` sinon env var `MAIL_TO` sinon défaut `sylvain.ribes@gmail.com`.

Best-effort : si le compte PA n'est pas configuré (`GMAIL_TOKEN_PA_JSON`
absent), on log et on sort en 0 — le rapport reste committé, le run n'est
pas cassé pour un souci de mail.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from tasks._lib import gmail

log = logging.getLogger("send_report")

DEFAULT_TO = "sylvain.ribes@gmail.com"


def send_report(
    *,
    body: str,
    subject: str,
    to: list[str] | None = None,
) -> bool:
    """Envoie `body` par mail via le compte PA. False si non configuré."""
    if not gmail.is_configured("pa"):
        log.info("compte PA non configuré (GMAIL_TOKEN_PA_JSON absent) — skip envoi")
        return False

    recipients = to or [os.environ.get("MAIL_TO", DEFAULT_TO)]
    service = gmail.service_for("pa")
    gmail.send_message(service, to=recipients, subject=subject, body=body)
    log.info("rapport envoyé à %s", ", ".join(recipients))
    return True


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser(description="Envoie un compte rendu de routine par mail.")
    ap.add_argument("--file", help="Fichier markdown à envoyer comme corps (ex: le working-memory).")
    ap.add_argument("--body", help="Corps direct (alternative à --file).")
    ap.add_argument("--subject", required=True, help="Sujet du mail.")
    ap.add_argument("--to", action="append", help="Destinataire(s) ; défaut env MAIL_TO ou constante.")
    args = ap.parse_args()

    if args.file:
        body = Path(args.file).read_text(encoding="utf-8")
    elif args.body:
        body = args.body
    else:
        ap.error("fournir --file ou --body")

    sent = send_report(body=body, subject=args.subject, to=args.to)
    return 0 if sent or True else 1  # toujours 0 : best-effort


if __name__ == "__main__":
    raise SystemExit(main())
