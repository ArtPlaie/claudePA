# Setup Google Calendar OAuth — runbook

Procédure one-time pour générer le refresh token Google Calendar utilisé
par les tâches `daily_digest`, `weekly_lookahead` et `location_context`.

Un seul compte ici : **perso** (Sylvain). Scope `calendar` (read + write)
pour permettre aux tâches futures de poser des events tentatives (cf.
`policies.md` whitelist).

Compter ~5 min si tu as déjà fait Gmail (le projet GCP est partagé).

## 1. Enable Calendar API (1 min)

Le projet Google Cloud `claudepa` créé pour Gmail (cf. `setup-gmail.md`)
est réutilisé. Il ne reste qu'à activer l'API Calendar.

1. https://console.cloud.google.com → sélectionner le projet `claudepa`.
2. APIs & Services > **Library** → cherche "Google Calendar API" > **Enable**.

L'OAuth consent screen est déjà configuré (test users : compte perso +
compte PA). Pas de nouvelle déclaration de scope nécessaire — `flow.run_local_server`
le déclare à la volée.

## 2. Réutiliser l'OAuth client existant (0 min)

Le `oauth-client.json` Desktop téléchargé pour Gmail fonctionne pour
Calendar. Aucun nouveau client à créer.

Si tu l'as perdu : APIs & Services > Credentials > clique sur `claudepa-cli`
> Download JSON.

## 3. Générer le refresh token (2 min)

Depuis le repo cloné en local :

```bash
uv sync
uv run python scripts/setup_calendar_oauth.py --client-secrets ~/oauth-client.json
```

→ s'ouvre dans le browser. Connecte-toi avec ton compte **perso**.
Page d'avertissement "Google hasn't verified this app" → "Advanced" →
"Go to claudepa (unsafe)" → autorise le scope `calendar`.

Le script imprime un JSON sur une ligne.

## 4. Coller le token en GitHub Secret (1 min)

GitHub > repo `claudePA` > Settings > Secrets and variables > Actions > **New repository secret**.

| Nom | Valeur |
|---|---|
| `GCAL_TOKEN_JSON` | JSON imprimé par le script |

## 5. Vérifier les calendars visibles

Le wrapper `_lib/calendar.py` fetch **tous** les calendars marqués
`selected: true` côté UI Google (primary + partagés visibles dans la
sidebar gauche du Calendar web).

Si un calendar partagé (Isa, famille) n'apparaît pas dans le digest :
ouvre https://calendar.google.com, vérifie que la case du calendar est
cochée dans la sidebar gauche, puis re-déclenche la tâche.

## 6. Trigger un run de test

```bash
# Via l'UI Actions du repo, manuellement
# Workflow: task-daily-digest → Run workflow
```

Vérifier la notif Telegram : la section "À préparer (5j)" doit apparaître
si des events qualifiants existent dans les 5 prochains jours.

## En cas de souci

Identique au troubleshooting Gmail (cf. `docs/setup-gmail.md`) :

- **"invalid_grant"** au runtime → le refresh token a été révoqué.
  Solution : re-run `setup_calendar_oauth.py` et mets à jour le secret.
- **"access_denied"** au consent → le compte n'est pas dans la liste des
  test users du projet `claudepa`. Va sur OAuth consent screen et
  ajoute-le.
- **Pas de refresh_token reçu** → l'app a déjà été autorisée. Va sur
  https://myaccount.google.com/permissions, révoque l'accès à `claudepa`,
  puis re-run le script.

## Coût et sécurité

- Calendar API quota gratuit : 1M de requêtes/jour. On en consomme
  ~5 par run de `daily_digest` et ~10 par run de `weekly_lookahead`.
  Aucun coût Google.
- Le refresh token (`GCAL_TOKEN_JSON`) **est** un secret critique : il
  donne un accès read+write au calendar. Garde-le uniquement en GitHub
  Secrets.
