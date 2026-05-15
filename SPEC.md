# Spec — Assistant personnel cloud `claudePA`

## Context

Assistant personnel autonome hébergé dans le cloud, qui exécute des
tâches récurrentes de veille et de synthèse à intervalles différents,
sans avoir à le relancer. Il produit des comptes-rendus contextualisés,
est joignable en temps réel, et reste économique en tokens.

Objectifs centraux :

- Externaliser la charge mentale des veilles (mails, opportunités
  Sydney/Suisse, formations AI/AI Safety, activités locales, briefings
  monde, réseau social).
- Avoir un **point unique de mémoire** que toutes les tâches partagent.
- Garder un humain dans la boucle pour toute action à effet externe
  (envoi, réservation, dépense).
- Pouvoir ajouter une nouvelle veille en quelques minutes (modularité).
- Donner à l'assistant une capacité de **réflexion sur lui-même**
  encadrée.

Décisions cadres validées :

- **Hébergement** : GitHub Actions (cron) + Cloudflare Workers (webhook
  entrant).
- **Canal temps réel** :
  - Telegram : **bot perso (1:1 Sylvain)** + **groupe commun**
    (Sylvain + Isa).
  - Email PA dédié (Gmail OAuth) en **lecture seule au démarrage** (le
    PA peut lire et drafter, **pas envoyer** sans validation explicite).
  - WhatsApp via Twilio en option future.
- **Stockage** : repo git, markdown structuré, secrets via GitHub
  Secrets.
- **Autonomie** : tout en brouillon, validation humaine systématique au
  début.
- **Profil** : bio v3 fournie, copiée dans `core-memory/profile.md`.
- **Localisation** : Bois-le-Roi 77590 ; localisation dynamique via
  calendrier.
- **Horizon Australie** : 6-18 mois → veille soutenue + prep dossier
  visa.
- **Hors scope V1** : veille investissement (Sylvain gère son patrimoine
  en direct).
- **OPSEC** : le PA ne doit jamais exposer adresse précise, détails
  patrimoniaux, ni infos famille dans des communications externes.

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  GitHub Repo (claudePA)                   │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │core-memory │  │working-memory│  │ digests/findings │  │
│  │ (perm.)    │  │ (30j gliss.) │  │ (rollups)        │  │
│  └────────────┘  └──────────────┘  └──────────────────┘  │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ tasks/     │  │ drafts/      │  │ inbox/           │  │
│  │ (code py)  │  │ (à valider)  │  │ (messages in)    │  │
│  └────────────┘  └──────────────┘  └──────────────────┘  │
└──────────────────────────────────────────────────────────┘
        ▲                    ▲                  ▲
        │ cron               │ webhook          │ user
        │                    │                  │
┌───────┴────────┐  ┌────────┴────────┐         │
│ GitHub Actions │  │ CF Workers (gw) │◄────────┘
│ (workflows YML)│  │ /telegram /mail │ messages entrants
└───────┬────────┘  └────────┬────────┘
        │                    │
        ▼                    ▼
┌─────────────────────────────────────┐
│ Anthropic API (Haiku/Sonnet/Opus)   │
│ + Gmail / Calendar / Brave Search   │
│ + Telegram Bot API                  │
└─────────────────────────────────────┘
```

Une **tâche** = un workflow GitHub Actions qui :

1. checkout le repo
2. installe les deps (`uv` + `anthropic` SDK)
3. lance un script Python `tasks/<task>.py`
4. ce script lit le contexte, appelle un agent Claude avec les outils
   requis, écrit son log dans `working-memory/`, met à jour
   `digests/findings.md` si besoin, pose un brouillon dans `drafts/` si
   action externe, notifie via Telegram, et commit-push.

---

## Stack technique

| Couche | Choix |
|---|---|
| Langage scripts | Python 3.12 (écosystème SDK Anthropic + intégrations mûr) |
| Package mgr | `uv` (rapide, simple) |
| Orchestration cron | GitHub Actions (`schedule:` cron par workflow) |
| Webhook entrant | Cloudflare Workers (free tier, déclenche `workflow_dispatch`) |
| LLM | Anthropic SDK, tiers `haiku` / `sonnet` / `opus` (mapping dans `tasks/_lib/llm.py`) |
| Email | Gmail API (OAuth refresh token en secret) |
| Calendrier | Google Calendar API |
| Messagerie | Telegram Bot API (BotFather, gratuit) |
| Web search | Brave Search API ou Tavily (à choisir au moment du build) |
| Secrets | GitHub Secrets (env vars dans workflows) |
| Lint/format | `ruff` + `pyright` |

---

## Structure du repo

```
claudePA/
├── README.md
├── CLAUDE.md                          # instructions sessions Claude Code
├── SPEC.md                            # ce document
├── schedule.yaml                      # registre central des tâches
├── pyproject.toml                     # deps Python (à venir)
├── .github/
│   └── workflows/
│       ├── _scaffold.yml              # template réutilisable
│       ├── task-mail-review.yml
│       ├── task-local-activities.yml
│       ├── task-weekly-briefing.yml
│       ├── task-...                   # un fichier par tâche
│       ├── sliding-window.yml         # daily, gère expiration
│       └── on-webhook.yml             # workflow_dispatch depuis CF Worker
├── tasks/
│   ├── _lib/
│   │   ├── memory.py                  # lit/écrit core + working + digests
│   │   ├── llm.py                     # wrapper Anthropic + sélection modèle
│   │   ├── gmail.py
│   │   ├── calendar.py
│   │   ├── telegram.py
│   │   ├── search.py
│   │   ├── notify.py                  # validation/draft pipeline
│   │   └── schedule.py                # calcule étalement
│   ├── mail_review.py
│   ├── local_activities.py
│   ├── activities_next10days.py
│   ├── ai_jobs_formations.py
│   ├── sydney_opportunities.py
│   ├── weekly_briefing.py
│   ├── network_followups.py
│   ├── location_context.py
│   ├── self_reflection.py
│   └── sliding_window.py
├── core-memory/
│   ├── profile.md                     # bio Sylvain
│   ├── australia-plan.md              # visa PR, leads Sydney
│   ├── family.md                      # Isa, enfants, échéances
│   ├── people.md                      # réseau, anniversaires
│   ├── current-location.md            # mis à jour par location_context
│   └── policies.md                    # autonomie, budget, OPSEC
├── working-memory/                    # 30j glissants
│   └── YYYY-MM-DD-HHMM-<task>.md
├── digests/
│   ├── monthly/YYYY-MM.md             # rollup mensuel auto
│   └── findings.md                    # pépites cross-task
├── drafts/                            # actions en attente validation
│   └── YYYY-MM-DD-<action>.md
├── inbox/                             # messages entrants
└── cloudflare-worker/
    └── src/index.ts                   # gateway webhook
```

---

## Modèle de mémoire à deux étages

**Core memory** (`core-memory/*.md`) — permanente, jamais purgée.
Voir le dossier `core-memory/` pour le détail.

**Working memory** (`working-memory/YYYY-MM-DD-HHMM-<task>.md`) —
fenêtre glissante 30 jours. Un fichier par exécution de tâche, format
standardisé :

```markdown
---
task: mail_review
run_at: 2026-05-15T08:00:00+02:00
model: sonnet
tokens_in: 12450
tokens_out: 1820
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

**Digests** (`digests/`) — survivance long terme.

- `findings.md` : append-only, pépites jugées importantes (opportunité
  Sydney concrète, formation pertinente, contact à recontacter). Index
  avec date + tag.
- `monthly/YYYY-MM.md` : rollup auto produit avant purge de la working
  memory.

**Drafts** (`drafts/`) — actions en attente d'approbation humaine.
Format :

```markdown
---
created_at: 2026-05-15T08:05:00+02:00
type: email_send
to: jean@dupont.com
priority: medium
expires_at: 2026-05-22
---

## Action proposée
Envoyer une relance à Jean Dupont (dernier contact: il y a 11 jours,
sujet: proposition collaboration X).

## Brouillon
> Bonjour Jean, ...

## Pourquoi
<justification basée sur core+working memory>

## Pour valider
Réponds OK / EDIT / SKIP via Telegram, ou édite ce fichier puis tag
`approved`.
```

---

## Sliding window — mécanique

Workflow `sliding-window.yml` tourne **quotidiennement à 03:00 UTC** :

1. Liste les fichiers `working-memory/*.md` plus vieux que 30 jours.
2. Pour chaque mois M qui sort de la fenêtre, lance un agent Haiku qui
   ingère tous les fichiers de M et produit `digests/monthly/YYYY-MM.md`
   (résumé thématique : mails clés, déclics, leads, décisions
   reportées).
3. Vérifie que le digest mensuel existe, puis supprime les fichiers de
   working-memory de M.
4. Commit `chore: rollup monthly digest <YYYY-MM>`.

Garde-fous :

- Ne purge jamais sans avoir produit le digest (vérification
  idempotente).
- Si le digest échoue, le workflow alerte via Telegram et ne supprime
  rien.

---

## Catalogue des tâches (V1)

Voir `schedule.yaml` pour la source de vérité (cron, canal, modèle).

| # | Tâche | Fréquence | Canal | Tier |
|---|---|---|---|---|
| 1 | **mail_review** : revue mails 5j passés, oublis, suggestions relance | 5 j | perso | sonnet |
| 2 | **local_activities** : agenda activités locales (1h15 isochrone) | 30 j | famille | sonnet |
| 3 | **activities_next10days** : sélection actionnable dans 10j | 7 j | famille | haiku |
| 4 | **ai_jobs_formations** : veille formations + jobs AI / AI Safety | 14 j | perso | sonnet |
| 5 | **sydney_opportunities** : focus Sydney + Suisse (jobs + visa PR) | 7 j | perso | sonnet |
| 6 | **weekly_briefing** : monde / IA / local, faits + analyse | 7 j | famille | sonnet (+opus pour analyse) |
| 7 | **network_followups** : anniversaires, relances dormantes | 14 j | perso | haiku |
| 8 | **location_context** : détecte voyages dans calendar + chats | 1 j | perso | haiku |
| 9 | **self_reflection** : méta-réflexion + propositions amélioration | 30 j | perso | opus |
| 10 | **sliding_window** : rollup mensuel + purge | 1 j | perso | haiku |

### Stratégie d'étalement

Comme les fréquences sont distinctes (5 / 7 / 14 / 30) et qu'on assigne
chacune à un jour de semaine + heure différents, les collisions sont
rares. Le `schedule.yaml` documente le plan ; un script
`tasks/_lib/schedule.py` vérifie au commit qu'aucun couple
(jour, ±30min) n'est sur-chargé.

**Premier jour (bootstrap)** : workflow manuel `bootstrap.yml` qui
lance toutes les tâches en séquence pour amorcer la mémoire. C'est
l'exception au principe d'étalement.

---

## Tâches additionnelles suggérées (à activer plus tard)

- `arxiv_alignment` : veille papers AI Safety (arXiv + Alignment Forum) — 7j
- `sunday_planning` : prépare agenda semaine à partir de calendar +
  drafts — 7j
- `morning_kickoff` : 3 lignes le matin sur Telegram (agenda, 1
  reminder) — 1j
- `visa_australia_tracker` : suit dates limites, frais, docs visa PR — 14j
- `isa_support` : veille opportunités peinture (galeries, expos
  collectives, appels à candidature thème étoiles / aurores), conseils
  Instagram artistes — 30j
- `household_followup` : entretien maison (humidité, ventilation),
  rappels saisonniers (haies, sinistres MAIF en cours) — 30j
- `health_longevity_watch` : veille santé / longévité, evidence-based — 30j

---

## Sélection des modèles

| Tier | Usage |
|---|---|
| `haiku` | Fetch / dédup / classification (ingestion mails, RSS, search, location detection) |
| `sonnet` | Synthèse / drafts / briefings (la majorité des tâches) |
| `opus` | Réflexion stratégique / méta (self-reflection, analyse weekly briefing) |

Mapping concret tier → model ID : centralisé dans `tasks/_lib/llm.py`
(facile à mettre à jour quand de nouveaux modèles sortent).

Prompt caching activé partout (`profile.md` + `policies.md` mis en
cache au début de chaque appel — économie ~80 % sur les tokens d'entrée
répétés).

---

## Canal temps réel — Telegram + email

**Telegram — deux canaux** (setup 5 min via BotFather) :

- **Bot perso (1:1 Sylvain)** : drafts à valider, alertes carrière /
  Sydney / formations, mail review, self-reflection, tout ce qui est
  perso ou sensible.
- **Groupe commun (Sylvain + Isa)** : briefings monde, agenda activités
  famille, sélections sorties weekend, sujets famille (anniversaires
  enfants à venir, jalons Isa peinture).

Routage par tâche défini dans `schedule.yaml` (`channel: perso|famille`).

**Email PA dédié** (Gmail OAuth) — `pa@<domaine>` ou Gmail dédié :

- Reçoit les briefings longs (digest hebdo, rapports mensuels).
- **Read-only au démarrage** : le PA peut lire les mails entrants et
  drafter des réponses dans Gmail (visibles dans l'app), mais **n'a pas
  les scopes OAuth pour envoyer**. Les drafts sont notifiés sur
  Telegram perso pour validation, et c'est Sylvain qui clique
  "envoyer" depuis Gmail dans un premier temps.
- Évolution : ajout du scope `gmail.send` une fois la confiance
  établie (estimation : après 4-6 semaines de fonctionnement propre).

**Cloudflare Worker** (gratuit, 100k req/jour) :

- 1 endpoint `/telegram` (webhook Telegram, gère bot perso + groupe).
- 1 endpoint `/gmail` (push notifs Gmail via Pub/Sub) — V2.
- Vérifie signature, dépose le payload via GitHub API dans `inbox/`,
  déclenche `workflow_dispatch` sur `on-webhook.yml` avec metadata
  (chat_id, type).

---

## Validation humaine

Toute action externe passe par `drafts/`. Le workflow de validation :

1. Tâche crée `drafts/YYYY-MM-DD-<action>.md` avec front matter
   `status: pending`.
2. Notification Telegram avec lien direct et 3 boutons inline :
   OK / EDIT / SKIP.
3. Réponse Telegram → Cloudflare Worker → workflow `apply-draft.yml` :
   - `OK` : execute l'action (envoi mail, réservation), passe
     `status: applied`.
   - `EDIT` : ouvre conversation Telegram pour amender.
   - `SKIP` : passe `status: skipped`.
4. Si pas de réponse avant `expires_at`, draft passe `status: expired`.

Whitelist d'autonomie : voir `core-memory/policies.md`.

---

## Garde-fous

Voir `core-memory/policies.md` pour le détail (budget tokens,
idempotence, rate limits, erreurs, secrets, audit trail).

---

## Auto-amélioration encadrée

Tâche `self_reflection` (mensuelle, tier `opus`) :

1. Lit `digests/monthly/<mois>.md`, `working-memory/`, `policies.md`,
   `CLAUDE.md`.
2. Évalue : qu'est-ce qui a bien marché, qu'est-ce qui a été ignoré,
   où suis-je sous-/sur-actif, qu'est-ce qui te coûte du temps quand
   même.
3. Produit `drafts/YYYY-MM-15-self-reflection.md` avec :
   - bilan synthétique
   - liste de propositions classées (P0 = config, P1 = nouvelles
     tâches, P2 = refactor code)
   - pour les P0, un diff prêt à appliquer sur `CLAUDE.md` ou
     `policies.md`.
4. Sylvain valide via Telegram. Si OK et P0, un workflow applique le
   diff automatiquement. P1/P2 → décision de coder ensemble dans une
   session normale.

---

## Phasage

**Phase 0 — Squelette** ✅ *(en cours)*
Scaffolding du repo : structure dossiers, `CLAUDE.md`, `SPEC.md`,
`profile.md`, `policies.md`, `family.md`, `australia-plan.md`,
`schedule.yaml`, `README.md`, `.gitignore`.

**Phase 1 — MVP**
- `pyproject.toml` + `tasks/_lib/` (`memory.py`, `llm.py`, `notify.py`).
- Workflow `_scaffold.yml` réutilisable + un workflow
  `hello-world.yml` qui prouve le cron.
- Telegram bot + Cloudflare Worker entrant.
- 3 tâches pilote : `weekly_briefing`, `mail_review`, `self_reflection`.
- Pipeline drafts / validation.

**Phase 2 — Catalogue complet**
- Reste des tâches du catalogue V1.
- Intégrations Gmail + Calendar + Brave Search / Tavily.
- Bootstrap workflow.

**Phase 3 — Raffinements**
- Tâches additionnelles suggérées.
- WhatsApp Twilio si besoin.
- Optimisations cache, rotation OAuth.

---

## Critères de validation (end-to-end)

À chaque phase, on vérifie :

1. **Cron déclenche** : un workflow programmé tourne au bon moment et
   commit.
2. **Mémoire** : un nouveau run lit bien `core-memory/profile.md`
   (visible dans le log de tokens cache hit).
3. **Sliding window** : à J+31, un fichier working-memory ancien
   disparaît et son contenu est dans le digest mensuel.
4. **Validation humaine** : un draft notifie Telegram, OK applique
   l'action, SKIP ne fait rien, `expires_at` fonctionne.
5. **Inbox** : un message Telegram entrant déclenche un workflow et
   l'agent répond dans le même chat.
6. **Budget** : forcer le compteur à 80 % déclenche bien l'alerte.
7. **Self-reflection** : produit un draft cohérent et le diff sur
   `CLAUDE.md` s'applique proprement quand validé.

---

## Questions ouvertes à régler en début d'implémentation

- Choix entre **Brave Search** et **Tavily** (les deux ont une API).
  Bench sur un cas concret au moment du build.
- Budget tokens cible exact (proposition : $30/mois pour la V1, à
  ajuster).
- Email PA dédié : domaine perso (`pa@<domaine>`) ou nouveau Gmail
  dédié ?
- Le groupe Telegram famille existe déjà ou on en crée un nouveau
  dédié au PA ?
- Quels mails entrants doivent être ingérés (juste le PA ou aussi
  forward depuis le mail principal) ?
