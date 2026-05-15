---
task: session_bootstrap
run_at: 2026-05-15T19:09:00+00:00
status: completed
phase: 1
session_kind: interactive
---

## Résumé

Session interactive Sylvain : on est passé de Phase 0 (scaffold seul, aucun
code de tâche) à **Phase 1 fonctionnelle de bout en bout** — la boucle
Telegram → CF Worker → GH Actions → réponse Telegram tourne en prod sur
`claude/main`.

Premier ping/pong validé : `ping` → ACK `✓ reçu, je travaille dessus…`
(< 2s) → `pong` (~30-60s via shortcut respond.py). Premier vrai appel
Sonnet validé sur question libre.

## Ce qui a été livré

**`tasks/_lib/`** — fondations :
- `paths.py`, `memory.py` (MarkdownDoc + front matter, working-memory I/O, findings)
- `schedule.py` (gates panic/vacances/cadence, run_guarded)
- `dedup.py` (fingerprint canon, fenêtre 90j sur drafts)
- `telegram.py` (client httpx best-effort, no-op si env vide)
- `notify.py` (skip-patterns match/register, create_draft, alert)
- `llm.py` (tiers haiku/sonnet/opus, prompt caching profile+policies,
  compteur `usage.json`, alerte 80%, refus 100%)
- `inbox.py`, `calendar.py` (stubs prêts pour OAuth Gmail/GCal)
- `template.py` (squelette tâche)

**Tâches** :
- `sliding_window` (rollup mensuel + purge >30j, idempotent)
- `location_context` (détection voyages + flag vacation_mode)
- `respond` (réponse temps-réel aux messages inbox, shortcut ping/pong)
- `apply_draft` (OK/SKIP/EDIT sur drafts, idempotent)

**Workflows GH Actions** :
- `panic.yml` (kill switch, dispatchable manuel + via Worker)
- `task-sliding-window.yml` (cron 03:00 UTC)
- `task-location-context.yml` (cron 04:00 UTC)
- `on-webhook.yml` (workflow_dispatch depuis Worker, lance respond.py)
- `apply-draft.yml` (workflow_dispatch depuis Worker pour validation drafts)

**Cloudflare Worker** (`cloudflare-worker/`) :
- TypeScript strict, déployé sur `claudepa-gateway.claudepa.workers.dev`
- Vérifie X-Telegram-Bot-Api-Secret-Token, whitelist chat_id perso
- /panic et /resume → dispatch panic.yml
- /help, /start → réponse statique
- Message libre → dépose inbox/ via Contents API + dispatch on-webhook
- callback_query inline → dispatch apply-draft

**Config** :
- `pyproject.toml` + `uv.lock` (anthropic, pyyaml, httpx, ruff/pyright)
- `schedule.yaml` mis à jour : canal `famille` déprécié (Isa pas sur
  Telegram), toutes les tâches sortent sur `perso`
- 0 tâche `enabled: true` — tout dort jusqu'à activation explicite

## Décisions clés (voir journal/decisions.md)

- Archi spec V2 conservée : Worker (CF, gratuit, h24) + Actions (à la
  demande, gratuit), latence 30-90s sur questions ouvertes, $0/mois.
  Sylvain confirme portable plus tard si besoin (~50 lignes JS spécifiques).
- Canal famille déprécié.
- Default branch GitHub renommée `claude/main` (par Sylvain dans l'UI).

## Dettes / TODO non bloquants

- `TELEGRAM_WEBHOOK_SECRET` est actuellement `testsecret123` (faible).
  Bug `wrangler secret put` sur Windows PowerShell : le paste Ctrl+V est
  reçu comme un seul "caractère" bracketé. Workaround = dashboard
  Cloudflare (paste navigateur OK). À rotater proprement, + refaire
  setWebhook avec la même valeur.
- Branche orphelin `main` côté remote (créée puis abandonnée pour
  `claude/main`). Suppression refusée par GH côté agent (403, sans
  doute auto-protection). À supprimer en UI quand Sylvain veut.
- Branche `claude/explore-menu-ATz4Y` peut être supprimée — tout est
  sur `claude/main`.
- `_lib/calendar.py` et `_lib/gmail.py` (à créer) restent à wirer
  contre OAuth Google. Bloquera `location_context` réel et `mail_review`.

## Secrets en place

**GitHub Repo Secrets** (Settings → Secrets → Actions) :
- `ANTHROPIC_API_KEY` ✓
- `TELEGRAM_BOT_TOKEN` ✓
- `TELEGRAM_CHAT_PERSO` ✓ (= 385233312)
- `TELEGRAM_CHAT_FAMILLE` non set (intentionnel)
- `GCAL_TOKEN_JSON` non set (à venir)

**Cloudflare Worker Secrets** :
- `TELEGRAM_BOT_TOKEN` ✓ (re-set via dashboard après bug paste wrangler)
- `TELEGRAM_WEBHOOK_SECRET` = `testsecret123` ⚠️ à rotater
- `TELEGRAM_CHAT_PERSO` ✓
- `GITHUB_TOKEN` ✓ (fine-grained PAT, scope Actions+Contents sur claudePA)

**Worker vars** (publiques, dans wrangler.toml) :
- `GITHUB_REPO` = `ArtPlaie/claudePA`
- `GITHUB_REF` = `claude/main`

## Prochaine session — plan suggéré

1. **Activer `daily_digest`** (`enabled: true` dans schedule.yaml). Premier
   vrai use case quotidien : 3-5 lignes Telegram matin. Test sur 2-3 jours
   pour calibrer le bruit.
2. **OAuth Gmail** (compte Sylvain read-only + compte PA à créer/à wirer
   read-write). Débloquer `mail_review` + dépose des premiers drafts.
3. **OAuth Google Calendar** → débloquer `location_context` réel +
   `daily_digest` enrichi.
4. Reste du catalogue V1 au fil de l'eau (`weekly_briefing`,
   `sydney_opportunities`, etc.).

## Tests effectués cette session

- 12 checks `_lib/` (markdown roundtrip, fingerprint, gates, dedup, drafts, …)
- 5 checks `sliding_window` (digest produit, purge idempotente, no-op)
- 4 checks `location_context` (no-op sans signaux, vacances détectées,
  no-rewrite si décision identique, JSON malformé)
- 3 checks `respond` (réponse normale, panic silent, ping → pong shortcut)
- 4 checks `apply_draft` (SKIP enregistre pattern, OK approve, idempotent,
  routage chat_id → channel)
- 1 test live Telegram : ping → ACK Worker → pong via GH Actions ✓
- 1 test live Telegram : question libre → réponse Sonnet ✓
