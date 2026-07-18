"""Bootstrap one-time du refresh token Gmail pour un compte donné.

À lancer **en local** sur un poste avec navigateur. Lance un serveur HTTP
éphémère sur localhost, ouvre le flow de consent OAuth dans le browser,
récupère le code, échange contre un refresh token, et imprime sur stdout
le JSON à coller en GitHub Secret.

Usage :

    # Compte Sylvain perso (read-only)
    python scripts/setup_gmail_oauth.py --account perso --client-secrets ~/oauth-client.json

    # Compte PA (read/write)
    python scripts/setup_gmail_oauth.py --account pa --client-secrets ~/oauth-client.json

    # Agenda de Sylvain (écriture d'événements) — se connecter avec SON compte
    python scripts/setup_gmail_oauth.py --account gcal --client-secrets ~/oauth-client.json

Le fichier `oauth-client.json` est celui téléchargé depuis Google Cloud
Console > APIs & Services > Credentials > OAuth client ID type "Desktop".
Voir docs/setup-gmail.md pour la procédure complète.

Le JSON imprimé en sortie est à coller dans GitHub Secrets :
- `GMAIL_TOKEN_PERSO_JSON` pour --account perso
- `GMAIL_TOKEN_PA_JSON`    pour --account pa
- `GCAL_TOKEN_JSON`        pour --account gcal
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from tasks._lib import gcal  # noqa: E402
from tasks._lib.gmail import SCOPES as GMAIL_SCOPES  # noqa: E402

# Scopes + nom du secret par "account". gcal = agenda de Sylvain (écriture).
_SCOPES: dict[str, list[str]] = {**GMAIL_SCOPES, "gcal": gcal.SCOPES}
_SECRET_NAME: dict[str, str] = {
    "perso": "GMAIL_TOKEN_PERSO_JSON",
    "pa": "GMAIL_TOKEN_PA_JSON",
    "gcal": "GCAL_TOKEN_JSON",
}


def run(account: str, client_secrets: Path) -> None:
    from google_auth_oauthlib.flow import InstalledAppFlow

    if not client_secrets.exists():
        sys.exit(f"client secrets file not found: {client_secrets}")

    flow = InstalledAppFlow.from_client_secrets_file(
        str(client_secrets), scopes=_SCOPES[account]
    )
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

    # creds.to_json() renvoie le format attendu par Credentials.from_authorized_user_info
    print()
    print("=" * 60)
    print(f"OAuth OK pour compte: {account}")
    print(f"Scopes: {creds.scopes}")
    print("=" * 60)
    print()
    print("Colle ce JSON dans GitHub Secrets (Settings > Secrets > Actions) :")
    print(f"  Nom : {_SECRET_NAME[account]}")
    print("  Valeur :")
    print()
    # Round-trip pour s'assurer que c'est du JSON minifié sur une ligne
    print(json.dumps(json.loads(creds.to_json()), separators=(",", ":")))
    print()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--account", choices=["perso", "pa", "gcal"], required=True)
    ap.add_argument(
        "--client-secrets",
        type=Path,
        required=True,
        help="Chemin vers oauth-client.json (Desktop OAuth client)",
    )
    args = ap.parse_args()
    run(args.account, args.client_secrets)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
