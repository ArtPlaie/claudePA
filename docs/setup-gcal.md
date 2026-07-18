# Setup Google Calendar OAuth — runbook (prendre par la main)

But : donner à claudePA le droit d'**écrire des événements sur l'agenda de
Sylvain**. Utilisé par la tâche `prompt_feedback` pour créer les events que la
routine `/adapt_prompt` met en file (quand tu réponds « réserve X samedi » à un
mail de rapport).

Ce qu'on génère : un secret GitHub **`GCAL_TOKEN_JSON`** (un refresh token OAuth,
scope `calendar.events`, sur **ton compte perso** `sylvain.ribes@gmail.com`).

⏱️ ~15 min, **une seule fois**. À faire **sur un ordi avec navigateur** (pas le
téléphone). Tu réutilises le projet Google Cloud et le client OAuth que tu as
déjà créés pour les tokens Gmail — pas besoin d'en refaire.

---

## Vue d'ensemble (3 briques)

1. **Google Cloud** : activer l'API Calendar + publier l'app (pour que le token
   n'expire pas).
2. **Ton ordi** : lancer un script qui ouvre le navigateur, tu autorises, il
   imprime un JSON.
3. **GitHub** : coller ce JSON dans le secret `GCAL_TOKEN_JSON`.

---

## Étape 1 — Activer l'API Google Calendar (1 min)

1. Va sur https://console.cloud.google.com
2. Connecte-toi avec ton compte **perso** (`sylvain.ribes@gmail.com`).
3. En haut, dans le **sélecteur de projet** (barre du haut), choisis le projet
   **`claudepa`** (celui créé pour les tokens Gmail).
4. Menu ☰ (en haut à gauche) → **APIs & Services** → **Library**
   (« Bibliothèque »).
5. Cherche **`Google Calendar API`** → clique dessus → bouton **Enable**
   (« Activer »).

> Sans ça, le token se génère mais toute création d'event renvoie une erreur 403.

---

## Étape 2 — Publier l'app (30 s) — IMPORTANT

C'est ce qui empêche le token de **mourir au bout de 7 jours** (le bug qui a tué
le token du compte PA : une app en mode « Testing » expire ses refresh tokens
sous 7 jours).

1. Toujours dans **APIs & Services** → **OAuth consent screen** (« Écran de
   consentement OAuth »). *(Selon la version de la console, ça peut s'appeler
   « Google Auth Platform » → « Audience ».)*
2. Regarde **Publishing status** (« État de publication »).
   - S'il est sur **Testing** → clique **PUBLISH APP** (« Publier l'application »)
     → confirme.
   - S'il est déjà sur **In production** → rien à faire.

> Usage perso, un seul utilisateur (toi) : pas besoin de la review Google. Tu
> garderas juste un écran d'avertissement « app non vérifiée » au moment
> d'autoriser (étape 4), c'est normal et sans risque pour ta propre app.

---

## Étape 3 — Récupérer le fichier client OAuth (`oauth-client.json`)

Tu en as besoin pour le script. Deux cas :

**Cas A — tu l'as encore** (ex. `~/oauth-client.json` ou
`client_secret_....json` dans tes Téléchargements) → note son chemin, passe à
l'étape 4.

**Cas B — tu l'as perdu** → re-télécharge-le (le même client marche pour
Calendar, pas besoin d'en créer un nouveau, mais tu peux) :
1. **APIs & Services** → **Credentials** (« Identifiants »).
2. Sous **OAuth 2.0 Client IDs**, tu dois voir une entrée type **Desktop**
   (« Ordinateur de bureau »), genre `claudepa-cli`.
   - Si elle existe : clique l'icône ⬇️ (Download) au bout de la ligne →
     **Download JSON**.
   - Si elle n'existe pas : **+ CREATE CREDENTIALS** → **OAuth client ID** →
     Application type = **Desktop app** → Name `claudepa-cli` → **Create** →
     **Download JSON**.
3. Enregistre le fichier en local, par ex. `~/oauth-client.json`. **Ne le
   commit jamais.**

---

## Étape 4 — Générer le token (le script)

Tu as besoin du **repo cloné en local** avec **`uv`** installé (comme quand tu as
fait les tokens Gmail).

```bash
cd /chemin/vers/claudePA        # ton clone local du repo
git pull                         # récupère le script à jour (--account gcal)
uv sync                          # installe les deps (si pas déjà fait)
uv run python scripts/setup_gmail_oauth.py --account gcal --client-secrets ~/oauth-client.json
```

Ce qui se passe :
1. Un onglet navigateur s'ouvre sur l'écran de connexion Google.
2. **Choisis / connecte-toi avec ton compte perso `sylvain.ribes@gmail.com`.**
   ⚠️ **PAS** le compte PA — sinon les events atterriraient sur le mauvais agenda.
3. Écran « **Google n'a pas validé cette application** » → clique
   **Paramètres avancés** → **Accéder à claudepa (dangereux)**. (Normal, c'est ta
   propre app.)
4. Écran de permissions : coche/autorise l'accès **Agenda** (« Voir, modifier,
   partager… vos agendas ») → **Continuer**.
5. L'onglet affiche « The authentication flow has completed ». Reviens au
   terminal.
6. Le script imprime un pavé avec, tout en bas, **un JSON sur une seule ligne**
   (commence par `{"token":` ...). C'est ta valeur de secret.

> **Fallback sans le repo** : si tu ne peux pas lancer le script du repo, crée un
> fichier `gcal_token.py` n'importe où et lance-le avec
> `pip install google-auth-oauthlib && python gcal_token.py` :
>
> ```python
> from google_auth_oauthlib.flow import InstalledAppFlow
> import json
> flow = InstalledAppFlow.from_client_secrets_file(
>     "/chemin/vers/oauth-client.json",
>     scopes=["https://www.googleapis.com/auth/calendar.events"],
> )
> creds = flow.run_local_server(port=0, prompt="consent", access_type="offline")
> print(json.dumps(json.loads(creds.to_json()), separators=(",", ":")))
> ```

---

## Étape 5 — Coller le secret sur GitHub (1 min)

1. Repo GitHub `artplaie/claudepa` → **Settings** → **Secrets and variables** →
   **Actions**.
2. **New repository secret**.
   - **Name** : `GCAL_TOKEN_JSON` (exactement ça).
   - **Secret** : colle le JSON d'une ligne de l'étape 4.
3. **Add secret**.

---

## Étape 6 — Tester (1 min)

1. Repo → onglet **Actions** → workflow **task-prompt-feedback** → **Run
   workflow** → branche **`main`** → **Run**.
2. Le run doit être vert. Il ne créera un event que s'il y a un
   `calendar/*.md` en `status: requested` en attente — sinon c'est « RAS ».
3. Test complet de bout en bout : **réponds** à un mail de rapport (genre le
   dernier serendipity) par « bloque un créneau test demain 15h », attends (ou
   lance) `task-prompt-feedback` (dépose la réponse), puis la routine
   `/adapt_prompt` (met l'event en file), puis re-`task-prompt-feedback` (crée
   l'event). Tu reçois une notif Telegram avec le lien, et l'event apparaît sur
   ton agenda.

---

## Dépannage

| Symptôme | Cause | Fix |
|---|---|---|
| `invalid_grant: Bad Request` au run | Token expiré (app en Testing, 7j) ou révoqué | Refais étape 2 (publier) + régénère le token (étape 4) |
| Erreur 403 `Calendar API has not been used` | API pas activée | Étape 1 |
| `Pas de refresh_token reçu` (le script quitte) | Google n'a pas renvoyé de refresh token | Va sur https://myaccount.google.com/permissions, retire l'accès de « claudepa », relance étape 4 |
| Écran « app non vérifiée » bloquant | Normal en unverified | Paramètres avancés → Accéder à claudepa |
| Events créés sur le mauvais agenda | Connecté avec le compte PA au lieu du perso | Régénère en te connectant avec `sylvain.ribes@gmail.com` |
| `redirect_uri_mismatch` | Le client OAuth n'est pas de type **Desktop** | Recrée un client « Desktop app » (étape 3, cas B) |

---

## Rappel : ce runbook vs `docs/setup-gmail.md`

`setup-gmail.md` affirme que le refresh token n'expire pas en mode Testing —
**c'est faux** (Google expire les tokens des apps Testing sous 7 jours ; c'est ce
qui a tué le token PA). L'étape 2 (publier) est la vraie solution durable, et
elle vaut aussi pour les tokens Gmail (`perso`, `pa`) s'ils sont dans le même
projet.
