---
task: session_handover
run_at: 2026-05-17T09:01:00+00:00
status: completed
phase: 1.5
session_kind: interactive
---

## Résumé

Session interactive Sylvain : on attaque la pipeline Gmail + on règle
le pb de latence cron. À l'arrivée : **mail_review V1 opérationnelle
end-to-end** (pull → classification Haiku → drafting Sonnet → drafts
markdown → notif Telegram), **crons GH migrés vers CF Worker Triggers**
(précision ~1 min vs 30min-2h), **branche par défaut switchée à `main`**.

Premier vrai run en prod : 11 threads scannés, 3 needs_reply détectés
par Haiku, 3 drafts générés par Sonnet (relances Isa piscine, AFFINE
seminar, invitation cohor). Notif Telegram reçue après fix Markdown
parsing. Pipeline validée bout en bout.

## Ce qui a été livré

**OAuth Gmail (2 comptes)** :
- `tasks/_lib/gmail.py` (297 lignes) : wrapper deux comptes —
  `perso` scope `gmail.readonly`, `pa` scope `gmail.modify`. Helpers
  `service_for()`, `list_threads_since()`, `get_thread()`,
  `create_draft()`, `send_message()`, MIME builder, parsing multipart
  (text/plain + fallback text/html stripped), normalisation
  `GmailMessage`/`GmailThread`. Tokens lus depuis env vars
  `GMAIL_TOKEN_PERSO_JSON` / `GMAIL_TOKEN_PA_JSON`.
- `scripts/setup_gmail_oauth.py` : bootstrap one-time du refresh token
  via google-auth-oauthlib en local. Lance serveur localhost éphémère,
  ouvre browser, imprime JSON à coller en GH Secret.
- `docs/setup-gmail.md` : runbook complet GCP project → OAuth consent
  screen (External / Testing, ajouter les 2 comptes en test users) →
  OAuth client Desktop → run script → GH Secrets. Troubleshooting
  invalid_grant / access_denied / pas de refresh_token.
- Deps `pyproject.toml` : `google-auth`, `google-auth-oauthlib`,
  `google-api-python-client`.

**Tâche mail_review V1** (`tasks/mail_review.py`, 352 lignes) :
- Pull threads `in:inbox` des 6j (cadence+1) hors catégories Gmail
  promotions/social/forums/updates.
- Filtres locaux : skip si Sylvain a répondu, skip si dernier inbound
  < 2j (pas encore un oubli).
- Haiku batch classifie {needs_reply, reason} sur ≤40 threads en un
  appel (~$0.005).
- Sonnet drafte une relance courte 2-4 phrases par mail flaggé,
  style direct/bro/fr, sans signature.
- Drafts markdown dans `drafts/` avec front matter
  `type: mail_review_followup`, `action: review_only` (compte perso
  reste strictement read-only par contrat — Sylvain copie/envoie
  manuellement depuis son client). Dédup par fingerprint thread_id
  (fenêtre 90j).
- Récap Telegram perso.

**Workflow + activation** :
- `.github/workflows/task-mail-review.yml` avec input `force: bool` au
  workflow_dispatch (bypass cadence/vacances en dev, jamais panic).
- `schedule.yaml` : `mail_review.enabled: true`.

**Crons via Cloudflare Worker** :
- `cloudflare-worker/wrangler.toml` : section `[triggers].crons`
  avec les 4 patterns (daily-digest 5h30, mail-review 6h,
  sliding-window 3h, location-context 4h). `GITHUB_REF` passé de
  `claude/main` à `main`.
- `cloudflare-worker/src/index.ts` : ajout du handler `scheduled()`
  qui lit `event.cron`, mappe via `CRON_TO_WORKFLOW`, dispatche le
  workflow GH via `dispatchWorkflow()` (déjà en place). `ctx.waitUntil()`
  pour garantir l'attente du dispatch.
- 4 YAML workflows GH : section `schedule:` retirée, seul
  `workflow_dispatch:` reste (évite double exécution CF + GH cron).
- Note crons dans `schedule.yaml` : champ `cron:` désormais INDICATIF
  (lecture humaine), source de vérité = wrangler.toml + index.ts.

**Force flag cross-cutting** :
- `tasks/_lib/schedule.py` : nouvelle fonction `_force_flag()` qui lit
  env `FORCE`, `preflight()` bypasse cadence + vacances si force=true.
  N'override JAMAIS panic ni `enabled: false`.

**Fix Telegram parsing** :
- `tasks/_lib/notify.py` : `notify.alert()` passe maintenant
  `parse_mode=None` par défaut. Évite les 400 Bad Request silencieuses
  sur les `_` non-escapés (titres de drafts, noms de fichiers).

**Branche par défaut switchée à `main`** :
- Auparavant `claude/main` (legacy). Sylvain a fait le switch
  Settings > General. Workflows + crons CF dispatch vers `main`.
- `claude/main` distante existe encore en zombie — peut être supprimée.

**CLAUDE.md** : section "Pour ajouter une nouvelle tâche" updatée
(workflow `workflow_dispatch:` only + cron dans CF Worker). Section
"Phase de développement actuelle" → 1.5.

## Décisions clés

- **Compte perso strictement read-only** (cf. policies.md). mail_review
  pose le texte de relance dans `drafts/`, Sylvain copie/envoie manuellement.
  Aucune action Gmail automatique sur perso. Le compte PA reste wiré
  côté `_lib/gmail.py` mais non consommé en V1 — il sera utilisé par
  les briefings longs et network_followups.
- **Crons GH abandonnés** au profit des Cloudflare Cron Triggers
  (gratuit, précis à la minute, limite 5 triggers free plan). Payer
  GH Actions ne résout PAS le cron delay. Pas de fallback `schedule:`
  côté GH (évite double exécution pour les tâches sans cadence_days).
  Risque accepté : si CF Worker down, on perd les crons (uptime CF
  ~99.99%, déploy 1 commande).
- Filtres mail_review : on garde les threads `in:inbox` hors catégories
  Gmail (filtre server-side), puis on skip locallement les threads
  déjà répondus + les inbound < 2j. Pas de classification newsletter
  par Haiku — Gmail le fait déjà gratuitement.
- Dédup par `thread_id` (pas par titre) pour mail_review : un thread
  peut avoir plusieurs sujets quand quelqu'un répond, on identifie le
  thread comme entité unique.

## Dettes / TODO non bloquants

- Compte Gmail PA wiré côté `_lib/gmail.py` mais aucune tâche ne le
  consomme encore. Premier use case naturel : `network_followups` qui
  drafte les relances anniversaires/contacts dormants depuis le PA.
- Le workflow `apply-draft.yml` n'a pas d'actuator pour
  `type: mail_review_followup` — sur OK, il marque `approved` et
  notifie "exécution manuelle". C'est OK par design (compte perso
  read-only) mais en V2 on pourrait pousser le brouillon dans Gmail
  Drafts via le compte perso si on accepte d'élargir le scope à
  `gmail.compose` (à discuter avec Sylvain).
- `_lib/calendar.py` reste un stub (returns []). Wirage OAuth identique
  à `_lib/gmail.py` à faire pour débloquer `location_context` réel +
  `daily_digest` enrichi (RDV du jour).
- Branches zombies sur le remote : `claude/main`, `claude/resume-session-0VKtR`,
  `claude/check-project-status-49qIQ`, `claude/explore-menu-ATz4Y`. Proxy
  git refuse `--delete` (403). Sylvain peut purger via UI GitHub si envie.
- `force` input n'existe que sur task-mail-review.yml. Si besoin de
  bypass cadence sur d'autres tâches, ajouter le même bloc input + env
  FORCE dans leur YAML.

## Secrets en place

**GitHub Repo Secrets** :
- `ANTHROPIC_API_KEY` ✓
- `TELEGRAM_BOT_TOKEN` ✓
- `TELEGRAM_CHAT_PERSO` ✓
- `GMAIL_TOKEN_PERSO_JSON` ✓ (scope readonly, compte sylvainribes@gmail.com)
- `GMAIL_TOKEN_PA_JSON` ✓ (scope modify, compte sylvainribes.claudepa@gmail.com)
- `GCAL_TOKEN_JSON` non set (à venir pour location_context/digest)
- `TOKEN_BUDGET_USD` non set (default $30/mois cf. llm.py)

**Cloudflare Worker Secrets** :
- `TELEGRAM_BOT_TOKEN` ✓
- `TELEGRAM_WEBHOOK_SECRET` = `testsecret123` ⚠️ toujours à rotater
- `TELEGRAM_CHAT_PERSO` ✓
- `GITHUB_TOKEN` ✓ (PAT fine-grained, actions:write + contents:write)

**Worker vars** :
- `GITHUB_REPO` = `ArtPlaie/claudePA`
- `GITHUB_REF` = `main` (mis à jour depuis `claude/main`)
- `[triggers].crons` = 4 patterns déployés ✓

## Prochaine session — plan suggéré

1. **OAuth Google Calendar** sur le même pattern que Gmail
   (`_lib/calendar.py` + bootstrap script + GH secret). Débloque
   `location_context` réel (détection voyages) + `daily_digest`
   enrichi (RDV du jour, conflits agenda).
2. **`weekly_briefing`** : prochain morceau de la V1 — synthèse
   hebdo monde/IA/local, post Telegram dimanche soir. Modèle Sonnet
   avec analyse Opus optionnelle. Premier vrai test de pipeline
   multi-source (RSS / search API à choisir entre Brave et Tavily).
3. **`network_followups`** : premier consommateur du compte PA RW.
   Drafte les relances anniversaires + contacts dormants, envoie
   depuis `sylvainribes.claudepa@gmail.com` après validation.
4. **Purger les branches zombies** côté GitHub UI (cosmétique).
5. **Rotation `TELEGRAM_WEBHOOK_SECRET`** : dashboard CF + relancer
   setWebhook avec la même valeur côté Telegram Bot API.

## Tests effectués cette session

- Lint + compile sur tous les nouveaux fichiers Python (`tasks/_lib/gmail.py`,
  `tasks/mail_review.py`, `scripts/setup_gmail_oauth.py`).
- Smoke tests `_lib/gmail.py` : parsing headers email, decode base64url,
  extraction multipart (text/plain prioritaire, fallback text/html stripped).
- 1 run live `mail_review` : 11 threads → 3 drafts générés
  (commit `c4b63aa`). Notif Telegram tombée après fix `parse_mode=None`.
- 1 run live `mail_review --force` post-fix : RAS (3 drafts existants
  dédupliqués par thread_id fingerprint).
- Validation YAML sur les 4 workflows post-retrait `schedule:`.
- Validation déploiement CF Worker : `Deployed claudepa-gateway triggers`
  + 4 schedules listés en output `wrangler deploy`.
