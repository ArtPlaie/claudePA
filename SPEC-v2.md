# Spec v2 — Assistant personnel `claudePA` via Routines

> Refonte complète. Drop GitHub Actions cron, drop Telegram, drop Cloudflare
> Worker, drop SDK wrapper, drop compteur budget custom. Tout sur **Routines
> Claude Code** (infra Anthropic cloud). Interaction temps réel via sessions
> Claude Code (web / mobile / CLI).

## Contexte

Assistant personnel autonome de Sylvain Ribes. Tâches récurrentes de veille
et de synthèse, hébergées sur Routines (Anthropic-managed cloud). Mémoire en
markdown versionné dans un repo GitHub privé. Validation humaine en session
Claude Code interactive — pas de canal externe.

Objectifs centraux :
- Externaliser la charge mentale des veilles (mails, opportunités
  Sydney/Suisse, formations AI/AI Safety, activités locales, briefings monde,
  réseau social).
- Point unique de mémoire que toutes les tâches partagent.
- Humain dans la boucle pour toute action à effet externe.
- Ajouter une nouvelle veille en quelques minutes (modularité).
- Réflexion mensuelle encadrée sur la trajectoire et l'utilité.

Cadres validés :
- **Hébergement** : Routines Claude Code (Anthropic cloud). Plan Max requis.
- **Source de vérité** : repo `claudePA` privé sur GitHub.
- **Canal temps réel** : sessions Claude Code (claude.ai/code en web/mobile,
  CLI en local). Sylvain "fait le point" quand il veut ; aucune notif push.
- **Connectors** (MCP claude.ai) :
  - Gmail compte Sylvain (read scopes uniquement),
  - Gmail compte PA dédié (read + write),
  - Google Calendar (read),
  - GitHub (lecture/écriture du repo claudePA),
  - Brave Search ou Tavily.
- **Style** : direct, dense, "bro", evidence-based, pas de sycophantie, pas
  de signature/persona, FR informel par défaut.
- **Profil** : `core-memory/profile.md` (copie bio v3).
- **Localisation** : Bois-le-Roi 77590, dynamique via routine `location_context`.
- **Horizon Australie** : 6-18 mois → veille soutenue + prep dossier visa PR.
- **Onboarding** : pas de shadow mode. Activation directe en fin Phase 1.
- **Hors scope V1** : investissement, WhatsApp, Telegram.
- **OPSEC** : repo privé. Aucune sortie externe sans validation. Whitelist
  stricte dans `policies.md`.

---

## Architecture

```
┌───────────────────────────────────────────────────────────┐
│            GitHub Repo claudePA (privé)                    │
│  core-memory/   working-memory/   digests/   drafts/       │
│  journal/       prompts/          tasks/_lib/              │
└───────────────────────────────────────────────────────────┘
                         ▲
                         │ clone + push main (unrestricted)
                         │
              ┌──────────┴───────────┐
              │  Routines Anthropic   │
              │  N routines = 1 par   │
              │  veille. Schedule     │
              │  trigger. Prompt      │
              │  source dans          │
              │  prompts/<task>.md    │
              └──────────┬───────────┘
                         │
              ┌──────────┴───────────┐
              │  MCP connectors :     │
              │  Gmail, Calendar,     │
              │  GitHub, Brave        │
              └──────────────────────┘

  Interactif : Sylvain ouvre Claude Code (web/mobile/CLI)
  → session avec les mêmes connectors → revue drafts,
  exécution, commit sur main. Sessions de routines
  consultables dans claude.ai/code.
```

Une **routine** =
- prompt sauvegardé (référence : `prompts/<task>.md` versionné dans le repo),
- repo claudePA cloné à chaque run,
- environnement avec network policy `Custom` (Trusted + endpoints des
  connectors hors MCP si besoin), env vars (clés API hors MCP),
- connectors activés (Gmail × 2, Calendar, GitHub, Brave),
- trigger schedule (cron custom via `/schedule update`, minimum 1h),
- exécute autonome, commit + push direct sur `main`.

Branche par défaut `main`. **"Allow unrestricted branch pushes"** activé sur
le repo dans la config Routines : les routines committent directement sur
main pour les écritures append-only (memory, digests, journal, drafts). Sans
ça, chaque update mémoire = PR à merger, friction inacceptable. Les actions
à effet externe restent gatées par la validation interactive (pas par le
merge).

---

## Stack technique

| Couche | Choix |
|---|---|
| Orchestration cron | Routines (Anthropic cloud) |
| Langage helpers | Python 3.12 minimal (`uv`), pour glue rare non-LLM |
| LLM | Modèle réglé par routine (Haiku / Sonnet / Opus) |
| Gmail / Calendar / GitHub | MCP connectors claude.ai |
| Web search | Brave Search ou Tavily, idéalement via MCP |
| Secrets | Environment variables de l'environnement Routine (UI claude.ai) |
| Lint/format | `ruff` |

Pas de wrapper Anthropic SDK. Pas de `_lib/llm.py`. Pas de compteur budget
custom (quota d'abonnement Max suffit, visible sur claude.ai/settings/usage).

---

## Structure du repo

```
claudePA/
├── README.md
├── CLAUDE.md                       # instructions globales lues à chaque session
├── ROUTINES.md                     # registre humain des routines (doc, pas exécuté)
├── pyproject.toml                  # deps Python minimales
├── prompts/                        # source de vérité versionnée des prompts
│   ├── mail_review.md
│   ├── local_activities.md
│   ├── activities_next10days.md
│   ├── ai_jobs_formations.md
│   ├── sydney_opportunities.md
│   ├── weekly_briefing.md
│   ├── daily_digest.md
│   ├── health_watch.md
│   ├── network_followups.md
│   ├── location_context.md
│   ├── findings_index.md
│   ├── self_reflection.md
│   └── sliding_window.md
├── tasks/
│   └── _lib/
│       ├── memory.py               # I/O working-memory + front matter
│       ├── dedup.py                # hash findings cross-task
│       └── skip.py                 # check skip-patterns avant draft
├── core-memory/
│   ├── profile.md
│   ├── australia-plan.md
│   ├── family.md
│   ├── people.md
│   ├── current-location.md         # incl. flag vacation_mode
│   ├── skip-patterns.md
│   └── policies.md
├── working-memory/                 # 30j glissants, 1 fichier par run
│   └── YYYY-MM-DD-HHMM-<task>.md
├── journal/
│   └── decisions.md                # append-only
├── digests/
│   ├── daily/YYYY-MM-DD.md         # daily_digest écrit ici, lu en checkin
│   ├── weekly/YYYY-MM-DD.md
│   ├── monthly/YYYY-MM.md
│   ├── findings.md                 # append-only, cross-task
│   ├── findings-by-tag.md          # index auto
│   └── findings-by-month.md        # index auto
└── drafts/
    └── YYYY-MM-DD-<action>.md
```

**Supprimé vs v1** : `.github/workflows/` (sauf éventuel CI lint),
`cloudflare-worker/`, `schedule.yaml`, `inbox/`, `tasks/_lib/llm.py`,
`tasks/_lib/telegram.py`, `tasks/_lib/notify.py`, `tasks/_lib/schedule.py`,
`tasks/apply_draft.py`.

`prompts/<task>.md` = source de vérité. La routine en config Routines pointe
vers le contenu de ce fichier. Modifier un prompt = éditer ce fichier +
`/schedule update <routine>` pour synchroniser (ou copier-coller via UI).

`ROUTINES.md` = doc humaine listant chaque routine (nom, cron, modèle,
connectors, env vars requises). Sert de référence ; pas lu par le système.

---

## Mémoire à deux étages

**Core memory** (`core-memory/*.md`) — permanente, jamais purgée.
- `profile.md` : bio Sylvain (copie de `sylvain_bio_v3_operationnel.md`).
- `australia-plan.md`, `family.md`, `people.md` : inchangé.
- `current-location.md` : ville + horizon + flag `vacation_mode: true|false`
  (mis à jour quotidiennement par `location_context`).
- `skip-patterns.md` : append-only. Alimenté en session interactive quand
  Sylvain `skip` un draft. Consulté avant tout nouveau draft.
- `policies.md` : whitelist autonomie, OPSEC, whitelist vacances.

**Journal** (`journal/decisions.md`) — append-only, externe à la fenêtre
glissante. Décisions importantes (techniques, perso, famille). Référence
pour `self_reflection`.

**Working memory** (`working-memory/YYYY-MM-DD-HHMM-<task>.md`) — fenêtre 30j.
Front matter standardisé :

```markdown
---
task: mail_review
run_at: 2026-05-15T08:00:00+02:00
model: claude-sonnet-4-6
status: completed
drafts_created: [drafts/2026-05-15-relance-jean-dupont.md]
findings_added: 1
---

## Résumé
<3-5 lignes>

## Détails
<corps>

## Suggestions
<liste actionable>
```

**Digests** :
- `findings.md` : append-only, pépites cross-task, dédup 90j par hash
  `(type, titre, org)`.
- `monthly/YYYY-MM.md` : rollup auto produit avant purge.
- `weekly/YYYY-MM-DD.md` : sortie de `weekly_briefing`.
- **`daily/YYYY-MM-DD.md`** (nouveau) : sortie de `daily_digest`. C'est ce
  que Sylvain lit en check-in matinal — équivalent pull du push Telegram v1.

**Drafts** (`drafts/`) :

```markdown
---
created_at: 2026-05-15T08:05:00+02:00
type: email_send
to: jean@dupont.com
priority: medium
expires_at: 2026-05-22
status: pending
---

## Action proposée
Envoyer une relance à Jean Dupont (dernier contact il y a 11 jours, sujet :
proposition collab X).

## Brouillon
> Bonjour Jean, …

## Pourquoi
<justification basée sur core+working memory>
```

`status` : `pending` | `applied` | `skipped` | `expired`.

---

## Sliding window

Routine `sliding_window` quotidienne à 03:00 local (Routines applique son
jitter de ±30min, OK) :
1. Liste les `working-memory/*.md` plus vieux que 30j.
2. Pour chaque mois M sortant, agent Haiku produit `digests/monthly/YYYY-MM.md`.
3. Vérifie le digest existe → supprime les fichiers du mois.
4. Commit `chore: rollup monthly digest <YYYY-MM>` sur main.

Si le digest échoue, la routine s'arrête sans purge. Sylvain le voit au
prochain check-in (run status rouge sur claude.ai/code + vieux fichiers
encore présents).

---

## Catalogue des routines (V1)

Minimum interval Routines = 1h, donc tout passe. Routines bi-mensuelles via
cron custom (`/schedule update`).

| # | Routine | Schedule | Modèle | Output principal |
|---|---|---|---|---|
| 1 | **mail_review** | Lun + Sam, 08:00 | Sonnet | drafts/ + working-memory/ |
| 2 | **local_activities** | 1er du mois, 09:00 | Sonnet | findings.md |
| 3 | **activities_next10days** | Jeu, 18:00 | Haiku | digests/daily/<date>-activities.md |
| 4 | **ai_jobs_formations** | Mar 1 & 3 du mois, 07:30 | Sonnet | findings.md |
| 5 | **sydney_opportunities** | Mer, 07:30 | Sonnet | findings.md + drafts/ |
| 6 | **weekly_briefing** | Dim, 19:00 | Sonnet (+ Opus pour analyse) | digests/weekly/<date>.md |
| 7 | **daily_digest** | Tous les jours, 07:30 | Haiku | digests/daily/<date>.md |
| 8 | **health_watch** | Ven 1 & 3 du mois, 09:00 | Sonnet | findings.md |
| 9 | **network_followups** | Lun 1 & 3 du mois, 18:00 | Haiku | drafts/ |
| 10 | **location_context** | Tous les jours, 06:00 | Haiku | core-memory/current-location.md |
| 11 | **findings_index** | Sam, 04:00 | Haiku | digests/findings-by-*.md |
| 12 | **self_reflection** | 15 du mois, 20:00 | Opus | drafts/<date>-self-reflection.md |
| 13 | **sliding_window** | Tous les jours, 03:00 | Haiku | digests/monthly/*.md |

Routines fait son propre jitter (jusqu'à 30min selon routine ID), pas besoin
d'étalement explicite.

---

## Sélection des modèles

Réglé dans la config de chaque routine (sélecteur UI ou `/schedule update`) :

| Tier | Modèle | Usage |
|---|---|---|
| Haiku 4.5 | `claude-haiku-4-5-20251001` | Ingestion mails, classification, daily_digest, location, dédup, rollup, findings_index |
| Sonnet 4.6 | `claude-sonnet-4-6` | Synthèse, drafts, briefings (majorité) |
| Opus 4.7 | `claude-opus-4-7` | Self-reflection mensuelle, analyse stratégique weekly_briefing |

Prompt caching natif côté Claude Code.

---

## Interaction temps réel

**Aucune notification push, aucun canal externe.** Sylvain ouvre Claude Code
quand il veut faire le point.

### Check-in
Sylvain dit `fait le point` (ou shortcut perso). La session :
1. Lit `digests/daily/<today>.md` (généré le matin par `daily_digest`).
2. Liste les `drafts/*.md` `status: pending`, triés par `priority`.
3. Synthèse en 5-10 lignes.

Sylvain enchaîne en langage naturel : `approve 1, 3 ; skip 2 ; edit 4`.

### Validation drafts en session
- `approve <draft>` → la session exécute via les connectors MCP (Gmail send,
  Calendar create, …), met à jour le front matter `status: applied`, commit.
- `skip <draft> [raison]` → append à `core-memory/skip-patterns.md`
  (`type | sujet | date | raison`), marque `status: skipped`, commit.
- `edit <draft>` → conversation pour amender, puis re-prompt approve/skip.

Pas besoin de `apply_draft.py` : Claude appelle directement les connectors
dans la session.

### Ad-hoc
Sylvain peut lancer un prompt de routine à la volée :
`lance un briefing Sydney maintenant`. La session exécute le prompt de
`sydney_opportunities` immédiatement sans attendre le créneau, et commit
ses outputs comme une routine normale.

Alternative : `Run now` sur la routine via UI claude.ai/code/routines.

### Kill switch
- Toggle "Pause" sur chaque routine via UI, OU
- Commit `.panic` à la racine. Chaque prompt débute par `Si .panic existe à
  la racine, exit immédiat sans rien faire`. Suppression du fichier =
  réactivation.

---

## Validation humaine — pipeline

Toute action à effet externe passe par `drafts/`. Pipeline identique à v1,
mais la validation se fait en session Claude Code au lieu de Telegram.

Avant écriture d'un draft, la routine vérifie :
1. `core-memory/skip-patterns.md` : si pattern récent matche → annule,
   log working-memory (via `tasks/_lib/skip.py`).
2. `tasks/_lib/dedup.py` : hash `(type, titre, org)` déjà vu sur 90j → skip.

Whitelist d'autonomie (`policies.md`) — exécutées sans drafter :
- Labels Gmail (sans envoi).
- Création drafts Gmail dans compte PA (sans envoi).
- Append à `findings.md`, `current-location.md`, `skip-patterns.md`.
- Append à `journal/decisions.md` (sur input Sylvain uniquement).
- Évènement tentative dans calendar perso non partagé.

Tout le reste → draft + validation interactive.

`expires_at` dans le front matter : si Sylvain n'a pas check-iné avant cette
date, la routine `sliding_window` (ou une routine dédiée si besoin) marque
`status: expired`. Pas de mémorisation comme skip (un timeout ≠ refus
explicite).

---

## Garde-fous

- **Idempotence** : chaque routine commence par lister les outputs déjà
  produits pour la fenêtre courante et exit si match. Évite les doublons sur
  re-run manuel.
- **Conflits push** : routines peuvent committer simultanément sur main.
  Chaque prompt finit par `git pull --rebase origin main && git push`. En
  cas d'échec, retry une fois ; si re-échec, écrire `working-memory/...-error.md`.
- **Erreurs** : exception non gérée → working-memory `*-error.md` + statut
  rouge sur la session Routines. Visible au check-in.
- **Secrets** : env vars de l'environnement Routine claude.ai. Jamais dans
  le repo. `.gitignore` pour les credentials locaux dev.
- **Audit trail** : `git log` = journal complet.
- **Mode vacances** : flag `vacation_mode: true` dans `current-location.md`.
  Chaque routine lit le flag au démarrage ; si actif et non-whitelist
  vacances (`policies.md` : `daily_digest`, `location_context`, alertes
  critiques uniquement) → exit silencieux avec log.
- **Skip patterns** : consultés avant chaque draft.
- **OPSEC** : repo privé. `policies.md` liste les attributs Sylvain qui ne
  doivent jamais sortir d'une comm externe (adresse précise, détails
  patrimoniaux, infos enfants).
- **Pas de budget custom** : quota Max d'Anthropic. Si dépassé → routines
  rejetées, visible sur claude.ai/settings/usage. Activer "Extra usage" en
  fallback si besoin.
- **Research preview** : Routines est en preview. API/limites peuvent
  changer. Pour un projet perso solo, acceptable. Header beta daté côté
  trigger API si jamais on en ajoute un.

---

## Auto-amélioration encadrée

Routine `self_reflection` mensuelle (15, 20:00, Opus) :
1. Lit `digests/monthly/<mois>.md`, working-memory, `policies.md`,
   `CLAUDE.md`, `journal/decisions.md`, `skip-patterns.md`.
2. Évalue : qu'est-ce qui a marché, qu'est-ce qui a été ignoré, où je suis
   sous-/sur-actif, qu'est-ce qui te coûte du temps quand même. Croise
   patterns SKIP (que faut-il arrêter de proposer) et décisions journal
   (trajectoire vs intentions).
3. Produit `drafts/YYYY-MM-15-self-reflection.md` avec :
   - bilan synthétique,
   - propositions classées (P0 = config, P1 = nouvelles routines, P2 =
     refactor code/prompts),
   - pour les P0, diff prêt à appliquer sur `CLAUDE.md`, `policies.md` ou
     un fichier `prompts/`.
4. Sylvain valide en session : `approve P0` → applique le diff, commit. P1
   et P2 = discussion live, code généré en session.

---

## Phasage

**Phase 0 — Setup compte & repo (~1h)**
- Repo `claudePA` privé sur GitHub.
- Plan Anthropic Max confirmé pour activer Routines.
- Connectors claude.ai : Gmail Sylvain (RO), Gmail PA (RW), Calendar (RO),
  GitHub claudePA, Brave Search (ou Tavily).
- Environnement Routines `claudePA-default` :
  - Network access `Custom` (Trusted + domaines connectors si hors MCP).
  - Env vars : tokens API non-MCP.
  - Setup script : `uv sync` pour les helpers Python.
- Activer "Allow unrestricted branch pushes" sur le repo.
- Bootstrap repo : `CLAUDE.md`, `policies.md`, `profile.md`, `family.md`,
  `current-location.md` (vacation_mode: false), `skip-patterns.md` vide,
  `journal/decisions.md` vide, `pyproject.toml`.

**Phase 1 — Cœur (1 session)**
- Helpers Python : `tasks/_lib/memory.py`, `dedup.py`, `skip.py`.
- Prompts pilote : `prompts/daily_digest.md`, `mail_review.md`,
  `weekly_briefing.md`, `sliding_window.md`, `self_reflection.md`,
  `location_context.md`.
- Création des 6 routines correspondantes via `/schedule` ou UI web.
- Bootstrap : `Run now` sur `daily_digest` puis `mail_review` pour amorcer
  la mémoire et vérifier le pipeline.
- Validation end-to-end : un draft notifié, check-in en session, `approve`
  → mail envoyé via Gmail MCP, commit `status: applied`.

**Phase 2 — Catalogue V1 complet**
- Restantes : `local_activities`, `activities_next10days`,
  `ai_jobs_formations`, `sydney_opportunities`, `health_watch`,
  `network_followups`, `findings_index`.
- Tri du bruit par SKIP → enrichit `skip-patterns.md`.

**Phase 3 — Raffinements**
- `adversarial_review` (second agent critique sur drafts sensibles).
- Routines additionnelles : `arxiv_alignment`, `sunday_planning`,
  `visa_australia_tracker`, `isa_support`, `household_followup`.
- Évaluation chiffrement SOPS+age pour `core-memory/` si sensibilité justifie.
- Optimisations cache, refactor prompts.

---

## Critères de validation (end-to-end)

1. **Routine déclenche** : routine schedulée tourne au bon moment, run visible
   sur claude.ai/code, commit sur main.
2. **Mémoire** : un run lit `core-memory/profile.md` (visible dans transcript
   session).
3. **Sliding window** : à J+31, un fichier working-memory ancien disparaît et
   son contenu est dans `digests/monthly/`.
4. **Validation interactive** : draft `mail_review` → session "fait le point"
   le présente → `approve` envoie le mail via Gmail MCP, met `status: applied`,
   commit.
5. **Skip patterns actifs** : nouveau draft matchant un pattern récent annulé
   avant écriture (log working-memory).
6. **De-dup** : un finding inséré 2× (même hash) n'apparaît qu'une fois.
7. **Mode vacances** : flag `true` → routines non-whitelistées exit
   silencieusement (log).
8. **Panic** : `.panic` committé → prochaine routine exit immédiat. Supression
   = réactivation.
9. **Self-reflection** : produit un draft cohérent, P0 diff s'applique
   proprement quand `approve`.

---

## Diff vs Spec v1

**Supprimé** :
- Tout Telegram (bot perso, groupe famille, BotFather, signature webhook,
  routage `channel: perso|famille`).
- Cloudflare Worker et endpoints `/telegram`, `/gmail`, `/panic`.
- `.github/workflows/` (tous les `task-*.yml`, `panic.yml`, `apply-draft.yml`,
  `on-webhook.yml`, `bootstrap.yml`, `_scaffold.yml`, `sliding-window.yml`).
- `tasks/_lib/llm.py`, `_lib/telegram.py`, `_lib/notify.py`, `_lib/schedule.py`,
  `tasks/apply_draft.py`.
- `schedule.yaml` (remplacé par config Routines + `ROUTINES.md` doc).
- Compteur budget tokens (`core-memory/usage.json`).
- Dossier `inbox/` (plus de messages entrants).

**Ajouté** :
- `prompts/<task>.md` : source de vérité versionnée des prompts.
- `digests/daily/` et `digests/weekly/` : consultés en pull au check-in.
- `ROUTINES.md` : doc humaine des routines (cron, connectors, env vars).
- Validation interactive en session Claude Code.

**Conservé** :
- `core-memory/`, `working-memory/`, `digests/`, `drafts/`, `journal/`.
- `tasks/_lib/memory.py`, `dedup.py`, `skip.py`.
- Sliding window, skip patterns, dedup cross-task, vacation mode,
  self-reflection.
- `CLAUDE.md` adapté à la nouvelle archi.
