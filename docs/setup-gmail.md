# Setup Gmail OAuth — runbook

Procédure one-time pour générer les refresh tokens des deux comptes
Gmail utilisés par claudePA.

Comptes :
- **perso** = ton compte principal Sylvain → scope `gmail.readonly`.
- **pa** = `sylvainribes.claudepa@gmail.com` → scope `gmail.modify`.

À faire **depuis un poste avec navigateur** (portable, pas mobile).
Compter ~20 min.

## 1. Créer le projet Google Cloud (5 min)

Le projet héberge l'OAuth client. Un seul projet pour les deux comptes
ça marche, mais il faut qu'il soit créé depuis un des deux Google
accounts qui l'utilisent (les credentials sont reliés au project owner).

1. Aller sur https://console.cloud.google.com
2. Connecté avec le compte **perso** (Sylvain), créer un nouveau projet :
   - Nom : `claudepa` (ou ce que tu veux)
3. Une fois le projet créé, sélectionne-le.
4. APIs & Services > **Library** → cherche "Gmail API" → **Enable**.

## 2. Configurer l'OAuth consent screen (5 min)

1. APIs & Services > **OAuth consent screen**.
2. User Type = **External** → Create.
3. Remplis :
   - App name : `claudepa`
   - User support email : ton email perso
   - Developer contact : ton email perso
   - Le reste : skip (Save and Continue).
4. Scopes : skip cette étape (Save and Continue), on les déclare dans le code.
5. Test users : **Add Users** → ajoute les **deux** adresses
   (perso + `sylvainribes.claudepa@gmail.com`). Sans ça, l'app en mode
   "Testing" refusera le consent.
6. Save and Continue → Back to Dashboard.

L'app reste en mode "Testing" — c'est exprès. Le refresh token n'expire
pas tant que tu n'ajoutes pas/retires pas de test user. Pas besoin de
passer en "Production" (qui demanderait une review Google).

## 3. Créer l'OAuth client (2 min)

1. APIs & Services > **Credentials** > Create Credentials > **OAuth client ID**.
2. Application type = **Desktop app**.
3. Name = `claudepa-cli`.
4. Create → **Download JSON**. Tu obtiens un fichier genre
   `client_secret_xxx.apps.googleusercontent.com.json`. Stocke-le en
   local (par ex. `~/oauth-client.json`), ne le commit pas.

## 4. Générer les refresh tokens (5 min)

Depuis le repo cloné en local, avec `uv` installé :

```bash
uv sync
```

### Token perso (compte Sylvain, read-only)

```bash
uv run python scripts/setup_gmail_oauth.py --account perso --client-secrets ~/oauth-client.json
```

→ s'ouvre dans le browser. Connecte-toi avec ton compte **perso**.
Page d'avertissement "Google hasn't verified this app" → "Advanced" →
"Go to claudepa (unsafe)" → autorise le scope `gmail.readonly`.

Le script imprime un JSON sur une ligne.

### Token pa (compte PA, read/write)

```bash
uv run python scripts/setup_gmail_oauth.py --account pa --client-secrets ~/oauth-client.json
```

→ même flow, mais connecte-toi cette fois avec
`sylvainribes.claudepa@gmail.com`. Autorise le scope `gmail.modify`.

## 5. Coller les tokens en GitHub Secrets (2 min)

GitHub > repo `claudePA` > Settings > Secrets and variables > Actions > **New repository secret**.

Crée deux secrets :

| Nom | Valeur |
|---|---|
| `GMAIL_TOKEN_PERSO_JSON` | JSON imprimé par `--account perso` |
| `GMAIL_TOKEN_PA_JSON`    | JSON imprimé par `--account pa` |

## 6. Activer mail_review

Dans `schedule.yaml`, passe `mail_review.enabled` à `true`, commit,
push. Le prochain cron (06:00 UTC quotidien, gated cadence 5j) lancera
la première revue.

Pour tester sans attendre :

```bash
# Trigger manuel du workflow
gh workflow run task-mail-review.yml
# (ou via l'onglet Actions du repo)
```

## En cas de souci

- **"invalid_grant"** au runtime → le refresh token a été révoqué.
  Causes typiques : tu as retiré le compte des test users, > 6 mois
  d'inactivité (rare), tu as modifié les scopes côté code. Solution :
  re-run le script `setup_gmail_oauth.py` et mets à jour le secret.
- **"access_denied"** au consent → le compte n'est pas dans la liste
  des test users (étape 2.5).
- **Pas de refresh_token reçu** → l'app a déjà été autorisée. Va sur
  https://myaccount.google.com/permissions, révoque l'accès à
  `claudepa`, puis re-run le script.

## Coût et sécurité

- Gmail API quota gratuit : 1 milliard d'unités/jour. On en consomme
  ~1k par run de `mail_review`. Aucun coût.
- Le `oauth-client.json` n'est **pas** un secret critique (les
  `client_id`/`client_secret` côté Desktop sont publics par design).
  Mais ne le commit pas par hygiène.
- Le refresh token (`GMAIL_TOKEN_*_JSON`) **est** un secret critique :
  il donne accès aux mails. Garde-le uniquement en GitHub Secrets.
