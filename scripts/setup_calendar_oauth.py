"""Bootstrap one-time du refresh token Google Calendar.

À lancer **en local** sur un poste avec navigateur. Lance un serveur HTTP
éphémère sur localhost, ouvre le flow de consent OAuth dans le browser,
récupère le code, échange contre un refresh token, et imprime sur stdout
le JSON à coller en GitHub Secret `GCAL_TOKEN_JSON`.

Usage :

    python scripts/setup_calendar_oauth.py --client-secrets ~/oauth-client.json

Le fichier `oauth-client.json` est celui téléchargé depuis Google Cloud
Console > APIs & Services > Credentials > OAuth client ID type "Desktop".
Le même client peut être réutilisé pour Gmail + Calendar (cf. setup-calendar.md).

Connecte-toi au browser avec le compte **perso** de Sylvain (un seul
compte ici, contrairement à Gmail qui en a deux).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tasks._lib.calendar import SCOPES  # noqa: E402


def run(client_secrets: Path) -> None:
    from google_auth_oauthlib.flow import InstalledAppFlow

    if not client_secrets.exists():
        sys.exit(f"client secrets file not found: {client_secrets}")

    flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets), scopes=SCOPES)
    # Force consent + offline pour garantir qu'on reçoit un refresh_token,
    # même si l'utilisateur a déjà autorisé l'app pour ce scope.
    creds = flow.run_local_server(
        port=0,
        prompt="consent",
        access_type="offline",
        open_browser=True,
    )

    if not creds.refresh_token:
        sys.exit(
            "Pas de refresh_token reçu. Révoque l'accès dans "
            "https://myaccount.google.com/permissions puis relance."
        )

    print()
    print("=" * 60)
    print("OAuth OK pour Google Calendar")
    print(f"Scopes: {creds.scopes}")
    print("=" * 60)
    print()
    print("Colle ce JSON dans GitHub Secrets (Settings > Secrets > Actions) :")
    print("  Nom : GCAL_TOKEN_JSON")
    print("  Valeur :")
    print()
    print(json.dumps(json.loads(creds.to_json()), separators=(",", ":")))
    print()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--client-secrets",
        type=Path,
        required=True,
        help="Chemin vers oauth-client.json (Desktop OAuth client)",
    )
    args = ap.parse_args()
    run(args.client_secrets)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
