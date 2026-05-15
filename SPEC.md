# Spec — Assistant personnel cloud `claudePA`

## Context

Tu veux un **assistant personnel autonome hébergé dans le cloud**, qui exécute
des **tâches récurrentes de veille et de synthèse** à intervalles différents,
sans avoir à le relancer. Il doit produire des comptes-rendus contextualisés,
être joignable en temps réel, et rester économique en tokens.

Objectifs centraux :
- Externaliser la charge mentale des veilles (mails, opportunités Sydney/Suisse,
  formations AI/AI Safety, activités locales, investissements, briefings monde,
  réseau social).
- Avoir un **point unique de mémoire** que toutes les tâches partagent.
- Garder un humain dans la boucle pour toute action à effet externe (envoi,
  réservation, dépense).
- Pouvoir ajouter une nouvelle veille en quelques minutes (modularité).
- Donner à l'assistant une capacité de **réflexion sur lui-même** encadrée.

Décisions cadres validées :
- **Hébergement** : GitHub Actions (cron) + Cloudflare Workers (webhook entrant).
- **Canal temps réel** :
  - Telegram : **bot perso (1:1 Sylvain)** + **groupe commun** (Sylvain + Isa,
    pour briefings famille, activités, plannings). Bot + groupe **à créer**
    (rien d'existant aujourd'hui).
  - **Deux comptes email** :
    - Compte principal Sylvain : **read-only** (mail_review tire dedans pour
      détecter oublis / suggérer relances ; rien ne sort de ce compte).
    - Compte PA dédié `pa@…` à créer (proposition : Gmail dédié, pas de
      domaine perso existant) : **read + write**, c'est depuis ce compte que
      sont envoyés les mails post-validation. Drafts d'envoi validés sur
      Telegram perso avant exécution.
  - **Filtres mail** : skip newsletters et transactionnel (Amazon, banques,
    notifs GitHub, etc.) — Haiku classifie en amont.
  - WhatsApp via Twilio en option future.
- **Stockage** : repo git, markdown structuré, secrets via GitHub Secrets.
- **Autonomie** : tout en brouillon, validation humaine systématique au début.
- **Style des outputs** : direct, dense, "bro", pas de sycophantie, pas de
  signature/persona (économie tokens, Sylvain sait à qui il parle). Français
  informel par défaut, anglais si le contexte l'impose.
- **Profil** : bio v3 fournie (`sylvain_bio_v3_operationnel.md`), à copier
  telle quelle dans `core-memory/profile.md`. Mise à jour au fil de l'eau.
- **Localisation** : Bois-le-Roi 77590 ; localisation dynamique via calendrier.
- **Horizon Australie** : 6-18 mois → veille soutenue + prep dossier visa.
- **Onboarding** : pas de shadow mode. On active **toutes** les tâches V1
  dès la fin de la Phase 1 ; tri du bruit au fil de l'eau via les SKIP
  (mémorisés, cf. plus bas).
- **Hors scope V1** : veille investissement (sortie du catalogue — Sylvain gère
  son patrimoine en direct, ne veut pas que le PA s'en mêle).
- **OPSEC** : le PA ne doit jamais exposer adresse précise, détails
  patrimoniaux, ni infos famille dans des communications externes (mails
  envoyés, messages publics). Whitelist stricte sur ce qui sort du repo.

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
4. ce script lit le contexte, appelle un agent Claude avec les outils requis,
   écrit son log dans `working-memory/`, met à jour `digests/findings.md` si
   besoin, pose un brouillon dans `drafts/` si action externe, notifie via
   Telegram, et commit-push.

---

## Stack technique

| Couche | Choix |
|---|---|
| Langage scripts | Python 3.12 (écosystème SDK Anthropic + intégrations mûr) |
| Package mgr | `uv` (rapide, simple) |
| Orchestration cron | GitHub Actions (`schedule:` cron par workflow) |
| Webhook entrant | Cloudflare Workers (free tier, déclenche `workflow_dispatch`) |
| LLM | Anthropic SDK : `claude-haiku-4-5-20251001`, `claude-sonnet-4-6`, `claude-opus-4-7` |
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
├── CLAUDE.md                          # instructions globales agent
├── schedule.yaml                      # registre central des tâches (cron + offset)
├── pyproject.toml                     # deps Python
├── .github/
│   └── workflows/
│       ├── _scaffold.yml              # template réutilisable
│       ├── task-mail-review.yml
│       ├── task-local-activities.yml
│       ├── task-weekly-briefing.yml
│       ├── task-...                   # un fichier par tâche
│       ├── sliding-window.yml         # daily, gère expiration
│       ├── panic.yml                  # kill switch (manuel + via Telegram)
│       ├── apply-draft.yml            # exécute un draft validé
│       └── on-webhook.yml             # workflow_dispatch depuis CF Worker
├── tasks/
│   ├── _lib/
│   │   ├── memory.py                  # lit/écrit core + working + digests + dedup
│   │   ├── llm.py                     # wrapper Anthropic + sélection modèle
│   │   ├── gmail.py
│   │   ├── calendar.py
│   │   ├── telegram.py
│   │   ├── search.py
│   │   ├── notify.py                  # validation/draft pipeline + skip patterns
│   │   ├── dedup.py                   # hash titre+org pour findings cross-task
│   │   └── schedule.py                # calcule étalement
│   ├── mail_review.py
│   ├── local_activities.py
│   ├── activities_next10days.py
│   ├── ai_jobs_formations.py
│   ├── sydney_opportunities.py
│   ├── weekly_briefing.py
│   ├── daily_digest.py                # 3-5 lignes Telegram matinal
│   ├── health_watch.py                # veille santé (Sylvain + contraintes Isa)
│   ├── network_followups.py
│   ├── location_context.py            # détecte voyages + flag mode vacances
│   ├── findings_index.py              # regénère index findings par tag/mois
│   ├── self_reflection.py
│   └── sliding_window.py              # rollup + purge
├── core-memory/
│   ├── profile.md                     # bio Sylvain (copie de bio v3)
│   ├── australia-plan.md              # visa PR, leads Sydney
│   ├── family.md                      # Isa, enfants, échéances
│   ├── people.md                      # réseau, anniversaires, dernier contact
│   ├── current-location.md            # ville + flag mode vacances
│   ├── skip-patterns.md               # patterns refusés (alimenté par les SKIP)
│   └── policies.md                    # autonomie, budget, OPSEC, garde-fous
├── working-memory/                    # 30j glissants, 1 fichier par exécution
│   └── YYYY-MM-DD-HHMM-<task>.md
├── journal/
│   └── decisions.md                   # décisions importantes (versionné, append)
├── digests/
│   ├── monthly/YYYY-MM.md             # rollup mensuel auto
│   ├── findings.md                    # pépites cross-task (append-only)
│   ├── findings-by-tag.md             # index auto regénéré (findings_index)
│   └── findings-by-month.md           # index auto regénéré (findings_index)
├── drafts/                            # actions en attente validation
│   └── YYYY-MM-DD-<action>.md
├── inbox/                             # messages entrants (Telegram/email)
└── cloudflare-worker/
    └── src/index.ts                   # gateway webhook
```

---

## Modèle de mémoire à deux étages

**Core memory** (`core-memory/*.md`) — permanente, jamais purgée.
- `profile.md` : bio Sylvain (copie de `sylvain_bio_v3_operationnel.md`).
  Identité, famille, parcours, compétences, projets, localisation,
  relocalisation, intérêts, veille carrière, sécurité, maison, fitness,
  style de communication. Versionné, éditable manuellement à tout moment.
- `australia-plan.md` : timeline visa PR (renouvellement travel facility),
  villes cibles, contacts, leads, échéances.
- `family.md` : Isa (peinture / Instagram aurores, ORL, contre-indication
  antibiotiques), enfants (~8/5/2 ans), événements à anticiper (rentrée,
  anniversaires, RDV pédiatre, etc.).
- `people.md` : réseau pro/perso, dernier contact, sujets en cours.
- `current-location.md` : ville actuelle + horizon + **flag `vacation_mode: true|false`**
  (mis à jour par `location_context`). En mode vacances, les tâches non
  critiques (briefings longs, mail_review) sont mises en pause ; seules
  les alertes critiques et `daily_digest` minimal passent.
- `skip-patterns.md` : append-only. Chaque SKIP d'un draft enregistre le
  pattern (type d'action, sujet, raison libre si fournie). `notify.py` le
  consulte avant de proposer un nouveau draft similaire.
- `policies.md` : budget mensuel tokens, plafonds, whitelist autonomie,
  règles OPSEC (rien d'externe ne sort sans validation).

**Journal** (`journal/decisions.md`) — append-only, externe à la fenêtre
glissante. On y consigne les décisions importantes (techniques, perso,
famille) au fil de l'eau. Le `self_reflection` mensuel s'en sert comme
référence d'or pour évaluer la trajectoire.

**Working memory** (`working-memory/YYYY-MM-DD-HHMM-<task>.md`) — fenêtre
glissante 30 jours. Un fichier par exécution de tâche, format standardisé :

```markdown
---
task: mail_review
run_at: 2026-05-15T08:00:00+02:00
model: claude-sonnet-4-6
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
- `findings.md` : append-only, pépites jugées importantes (opportunité Sydney
  concrète, deal d'invest, formation pertinente). Index avec date + tag.
- `monthly/YYYY-MM.md` : rollup auto produit avant purge de la working memory.

**Drafts** (`drafts/`) — actions en attente d'approbation humaine. Format :

```markdown
---
created_at: 2026-05-15T08:05:00+02:00
type: email_send
to: jean@dupont.com
priority: medium
expires_at: 2026-05-22
---

## Action proposée
Envoyer une relance à Jean Dupont (dernier contact: il y a 11 jours, sujet:
proposition collaboration X).

## Brouillon
> Bonjour Jean, ...

## Pourquoi
<justification basée sur core+working memory>

## Pour valider
Réponds OK / EDIT / SKIP via Telegram, ou édite ce fichier puis tag `approved`.
```

---

## Sliding window — mécanique

Workflow `sliding-window.yml` tourne **quotidiennement à 03:00 UTC** :
1. Liste les fichiers `working-memory/*.md` plus vieux que 30 jours.
2. Pour chaque mois M qui sort de la fenêtre, lance un agent Haiku qui ingère
   tous les fichiers de M et produit `digests/monthly/YYYY-MM.md` (résumé
   thématique : mails clés, déclics, leads, décisions reportées).
3. Vérifie que le digest mensuel existe, puis supprime les fichiers de
   working-memory de M.
4. Commit `chore: rollup monthly digest <YYYY-MM>`.

Garde-fous :
- Ne purge jamais sans avoir produit le digest (vérification idempotente).
- Si le digest échoue, le workflow alerte via Telegram et ne supprime rien.

---

## Catalogue des tâches (V1)

Chaque tâche = un workflow + un script. Modèle suggéré entre parenthèses.

| # | Tâche | Fréquence | Jour/heure | Modèle | Canal |
|---|---|---|---|---|---|
| 1 | **mail_review** : revue mails 5j passés (compte Sylvain read-only + PA RW), oublis, drafts relance | 5 j | Lun/Sam 08:00 | Sonnet | perso |
| 2 | **local_activities** : agenda activités locales famille/art/intellect (1h15 max isochrone) | 30 j | 1er du mois 09:00 | Sonnet | famille |
| 3 | **activities_next10days** : sélection actionnable dans 10j depuis liste | 7 j | Jeudi 18:00 | Haiku | famille |
| 4 | **ai_jobs_formations** : veille formations (MATS, ARENA, masters) + jobs AI/AI Safety | 14 j | Mar 07:30 | Sonnet | perso |
| 5 | **sydney_opportunities** : focus Sydney + Suisse (jobs intello + visa PR news) | 7 j | Mer 07:30 | Sonnet | perso |
| 6 | **weekly_briefing** : monde / IA / local, faits + analyse, post groupe Telegram | 7 j | Dim 19:00 | Sonnet (+ Opus pour l'analyse) | famille |
| 7 | **daily_digest** : 3-5 lignes (drafts pendants, RDV du jour, 1 alerte) | 1 j | 07:30 | Haiku | perso |
| 8 | **health_watch** : veille santé evidence-based (Sylvain ; Isa ORL + contre-indication antibiotiques systémiques) | 14 j | Ven 09:00 | Sonnet | perso |
| 9 | **network_followups** : anniversaires, relances dormantes | 14 j | Lun 18:00 | Haiku | perso |
| 10 | **location_context** : détecte voyages dans calendar + chats, gère flag vacances | 1 j | 06:00 | Haiku | — |
| 11 | **findings_index** : regénère `findings-by-tag.md` + `findings-by-month.md` | 7 j | Sam 04:00 | Haiku | — |
| 12 | **self_reflection** : meta-réflexion + suggestions amélioration | 30 j | 15 du mois 20:00 | Opus | perso |
| 13 | **sliding_window** : rollup mensuel + purge working-memory | 1 j | 03:00 UTC | Haiku | — |

Note : ces fréquences ne sont **pas figées**. Le `schedule.yaml` central les
définit et tu peux les ajuster à la volée.

### Stratégie d'étalement

Comme les fréquences sont distinctes (5/7/14/30) et qu'on assigne chacune à
un jour de semaine + heure différents, les collisions sont rares. Le
`schedule.yaml` documente le plan ; un script `tasks/_lib/schedule.py`
vérifie au commit qu'aucun couple (jour, ±30min) n'est sur-chargé.

**Premier jour (bootstrap)** : workflow manuel `bootstrap.yml` qui lance
toutes les tâches en séquence pour amorcer la mémoire. C'est l'exception
que tu mentionnais.

---

## Tâches additionnelles suggérées (à activer plus tard)

- **arxiv_alignment** : veille papers AI Safety (arXiv + Alignment Forum) — 7j
- **sunday_planning** : prépare agenda semaine à partir de calendar + drafts — 7j
- **visa_australia_tracker** : suit dates limites, frais, docs visa PR — 14j
- **isa_support** : veille opportunités peinture (galeries, expos collectives,
  appels à candidature thème étoiles/aurores), conseils Instagram artistes — 30j
- **household_followup** : entretien maison (humidité, ventilation),
  rappels saisonniers (haies, sinistres MAIF en cours) — 30j
- **adversarial_review** (V2) : sur les outputs sensibles (lead Sydney, choix
  formation, draft de relance), un second agent Sonnet reformule la critique
  adversariale. Coût marginal, calibrage amélioré.

---

## Sélection des modèles

| Tier | Modèle | Usage |
|---|---|---|
| Fetch / dédup / classification | `claude-haiku-4-5-20251001` | Ingestion mails, RSS, résultats search, location detection |
| Synthèse / drafts / briefings | `claude-sonnet-4-6` | La majorité des tâches |
| Réflexion stratégique / méta | `claude-opus-4-7` | Self-reflection mensuelle, analyse du weekly briefing |

Prompt caching activé partout (profile.md + policies.md mis en cache au début
de chaque appel — économie ~80% sur les tokens d'entrée répétés).

---

## Canal temps réel — Telegram + email

**Telegram — deux canaux** (setup 5 min via BotFather) :
- **Bot perso (1:1 Sylvain)** : drafts à valider, alertes carrière /
  Sydney / formations, mail review, self-reflection, tout ce qui est
  perso ou sensible.
- **Groupe commun (Sylvain + Isa)** : briefings monde, agenda activités
  famille, sélections sorties weekend, sujets famille (anniversaires
  enfants à venir, jalons Isa peinture). Le bot poste dedans, les deux
  peuvent répondre/valider.

Routage par tâche défini dans `schedule.yaml` (`channel: perso|famille`).

**Email PA dédié** (Gmail OAuth) — `pa@<domaine>` ou Gmail dédié :
- Reçoit les briefings longs (digest hebdo, rapports mensuels).
- **Read-only au démarrage** : le PA peut lire les mails entrants et
  drafter des réponses dans Gmail (visibles dans l'app), mais **n'a pas
  les scopes OAuth pour envoyer**. Les drafts sont notifiés sur Telegram
  perso pour validation, et c'est Sylvain qui clique "envoyer" depuis
  Gmail dans un premier temps.
- Évolution : ajout du scope `gmail.send` une fois la confiance établie
  (estimation : après 4-6 semaines de fonctionnement propre).

**Cloudflare Worker** (gratuit, 100k req/jour) :
- 1 endpoint `/telegram` (webhook Telegram, gère bot perso + groupe).
- 1 endpoint `/gmail` (push notifs Gmail via Pub/Sub) — V2.
- Vérifie signature, dépose le payload via GitHub API dans `inbox/`,
  déclenche `workflow_dispatch` sur `on-webhook.yml` avec metadata
  (chat_id, type).

---

## Validation humaine

Toute action externe passe par `drafts/`. Le workflow de validation :

1. Tâche crée `drafts/YYYY-MM-DD-<action>.md` avec front matter `status: pending`.
   Avant écriture, `notify.py` consulte `skip-patterns.md` : si le draft
   matche un pattern refusé récemment, il est annulé silencieusement
   (juste loggé en working-memory).
2. Notification Telegram avec lien direct et 3 boutons inline : OK / EDIT / SKIP.
3. Réponse Telegram → Cloudflare Worker → workflow `apply-draft.yml` :
   - `OK` : execute l'action (envoi mail, réservation), passe `status: applied`.
   - `EDIT` : ouvre conversation Telegram pour amender.
   - `SKIP` : passe `status: skipped` **et** append le pattern dans
     `core-memory/skip-patterns.md` (type, sujet, date, raison optionnelle
     si Sylvain en fournit une via reply texte). Sylvain peut éditer ce
     fichier à la main pour ajouter / nettoyer.
4. Si pas de réponse avant `expires_at`, draft passe `status: expired`
   (pas de mémorisation comme skip — un timeout ≠ un refus explicite).

**De-duplication cross-task** : `_lib/dedup.py` hash `(type, titre, org)`
des findings et drafts. Un finding déjà présent dans les 90 derniers jours
n'est pas réinséré ; un draft équivalent annule la nouvelle proposition.
Évite que `sydney_opportunities` et `ai_jobs_formations` proposent le même
job deux fois.

Whitelist d'autonomie (dans `policies.md`) — actions qui ne nécessitent pas
validation :
- Labellisation Gmail (sans envoi).
- Création drafts Gmail dans le compte PA (sans envoi).
- Ajout d'événement tentative dans calendar perso (non partagé).
- Ajout d'entrées dans `findings.md` et `journal/decisions.md` (sur input
  Sylvain seulement pour decisions).
- Mise à jour de `current-location.md` (incluant flag vacances détecté).
- Append à `skip-patterns.md` après un SKIP utilisateur.

Tout le reste passe par drafts.

---

## Garde-fous

- **Budget tokens** : limite mensuelle définie dans `policies.md` (ex: $30/mois).
  `tasks/_lib/llm.py` tient un compteur dans `core-memory/usage.json`, refuse
  les appels au-delà du plafond et alerte Telegram à 80%.
- **Idempotence** : chaque tâche écrit son `run_id` ; relance d'un workflow
  ne re-crée pas de drafts pour la même fenêtre.
- **Rate limits** : backoff exponentiel sur Anthropic et Gmail.
- **Erreurs** : tout exception non gérée → notif Telegram + écriture
  `working-memory/...-error.md`.
- **Secrets** : jamais en clair dans le repo ; GitHub Secrets pour CI, .env
  local jamais commité (`.gitignore`).
- **Audit trail** : git log = journal complet, tout est versionné.
- **Mode vacances** : flag `vacation_mode: true` dans `current-location.md`.
  Chaque tâche lit ce flag au démarrage ; si actif et que la tâche n'est
  pas dans la whitelist vacances (`policies.md` : `daily_digest`,
  `location_context`, alertes critiques uniquement), elle skip son run et
  loggue.
- **Panic / kill switch** : workflow `panic.yml` déclenchable :
  - manuellement depuis l'onglet Actions GitHub,
  - via commande Telegram `/panic` (le worker dispatch le workflow).
  Effet : crée un fichier sentinelle `.panic` à la racine, lu par chaque
  tâche au démarrage → exit immédiat. Sylvain le supprime à la main pour
  réactiver. Notif Telegram de confirmation quand activé/désactivé.
- **Skip patterns** : `notify.py` consulte `skip-patterns.md` avant chaque
  draft pour éviter de re-proposer du déjà refusé.
- **Chiffrement OPSEC** (V2) : passage de `profile.md`, `family.md`,
  `people.md` sous SOPS+age si la sensibilité du contenu le justifie.
  Trade-off : un peu de friction d'édition, vrai gain en cas de leak
  GitHub. À évaluer après quelques mois.

---

## Auto-amélioration encadrée

Tâche `self_reflection` (mensuelle, Opus) :
1. Lit `digests/monthly/<mois>.md`, `working-memory/`, `policies.md`,
   `CLAUDE.md`, `journal/decisions.md`, `skip-patterns.md`.
2. Évalue : qu'est-ce qui a bien marché, qu'est-ce qui a été ignoré, où
   suis-je sous-/sur-actif, qu'est-ce qui te coûte du temps quand même.
   Croise avec les patterns SKIP (que faut-il arrêter de proposer) et les
   décisions du journal (trajectoire vs intentions).
3. Produit `drafts/YYYY-MM-15-self-reflection.md` avec :
   - bilan synthétique
   - liste de propositions classées (P0 = config, P1 = nouvelles tâches,
     P2 = refactor code)
   - pour les P0, un diff prêt à appliquer sur `CLAUDE.md` ou `policies.md`.
4. Tu valides via Telegram. Si OK et P0, un workflow applique le diff
   automatiquement. P1/P2 → tu décides de coder ensemble dans une session
   normale.

---

## Phasage

**Phase 0 — Squelette (1 session)**
- Scaffolding du repo (structure dossiers, `CLAUDE.md`, template `profile.md`,
  `pyproject.toml`, `schedule.yaml`, `_lib/`).
- Création compte Gmail PA dédié + bot Telegram (perso) + groupe Telegram
  famille (avec bot ajouté).
- Récupération secrets : `ANTHROPIC_API_KEY`, OAuth Gmail (Sylvain read-only
  + PA RW), Google Calendar, Telegram bot token, IDs chats perso/famille.
- README expliquant le projet.
- Workflow `hello-world.yml` qui prouve que le cron tourne et commit un
  fichier.
- Workflow `panic.yml` + sentinelle `.panic` pris en compte par `_lib/llm.py`.

**Phase 1 — Cœur (2-3 sessions)**
- Telegram bot + Cloudflare Worker entrant (OK/EDIT/SKIP/`/panic`).
- Intégration Anthropic SDK (`_lib/llm.py` avec caching + sélection modèle
  + plafond budget).
- Mémoire (`_lib/memory.py`, `_lib/dedup.py`, `_lib/notify.py`) + sliding
  window + skip patterns + journal/decisions.
- Tâches pilote : `weekly_briefing`, `mail_review`, `daily_digest`,
  `self_reflection`, `location_context`, `sliding_window`.
- Pipeline drafts/validation complet.

**Phase 2 — Catalogue V1 complet (activation directe, pas de shadow mode)**
- Reste des tâches V1 : `local_activities`, `activities_next10days`,
  `ai_jobs_formations`, `sydney_opportunities`, `health_watch`,
  `network_followups`, `findings_index`.
- Intégrations Brave Search ou Tavily (benchmark rapide pour choisir).
- Workflow `bootstrap.yml` (lance toutes les tâches en séquence le J0).
- Tri du bruit via SKIP → skip-patterns.md s'enrichit.

**Phase 3 — Raffinements**
- `adversarial_review` (second agent critique sur outputs sensibles).
- Tâches additionnelles (`arxiv_alignment`, `sunday_planning`,
  `visa_australia_tracker`, `isa_support`, `household_followup`).
- Évaluation chiffrement SOPS+age pour `core-memory/` sensible.
- Évaluation ajout scope `gmail.send` sur compte Sylvain (compte PA déjà
  RW depuis le départ).
- WhatsApp Twilio si besoin.
- Optimisations cache.

---

## Critères de validation (end-to-end)

À chaque phase, on vérifie :

1. **Cron déclenche** : un workflow programmé tourne au bon moment et commit.
2. **Mémoire** : un nouveau run lit bien `core-memory/profile.md` (visible
   dans le log de tokens cache hit).
3. **Sliding window** : à J+31, un fichier working-memory ancien disparaît et
   son contenu est dans le digest mensuel.
4. **Validation humaine** : un draft notifie Telegram, OK applique l'action,
   SKIP ne fait rien **et écrit dans `skip-patterns.md`**, expires_at fonctionne.
5. **Skip patterns actifs** : un nouveau draft matchant un pattern récent
   est annulé avant notif (visible dans working-memory).
6. **De-dup** : un finding inséré 2 fois (même hash) n'apparaît qu'une fois.
7. **Mode vacances** : flag à `true` → tâches non-whitelistées skippent leur
   run (log visible), `daily_digest` reste actif.
8. **Panic** : `/panic` Telegram crée `.panic`, prochain run de n'importe
   quelle tâche exit immédiatement avec notif. Suppression du fichier =
   réactivation.
9. **Inbox** : un message Telegram entrant déclenche un workflow et l'agent
   répond dans le même chat.
10. **Budget** : forcer le compteur à 80% déclenche bien l'alerte.
11. **Self-reflection** : produit un draft cohérent et le diff sur `CLAUDE.md`
    s'applique proprement quand validé.

---

## Fichiers à créer en priorité

1. **`CLAUDE.md`** (racine) — instructions pour **toutes les sessions Claude
   Code futures** sur ce repo. Contenu détaillé ci-dessous.
2. `schedule.yaml` — registre des tâches (cron, channel, model tier,
   whitelist vacances).
3. `core-memory/profile.md` — copie de `sylvain_bio_v3_operationnel.md`.
4. `core-memory/policies.md` — budget tokens, whitelist autonomie, règles
   OPSEC, contacts d'urgence, whitelist mode vacances.
5. `core-memory/family.md` — Isa, enfants, échéances famille.
6. `core-memory/current-location.md` — Bois-le-Roi 77590, `vacation_mode: false`.
7. `core-memory/skip-patterns.md` — vide au démarrage, alimenté par les SKIP.
8. `journal/decisions.md` — vide au démarrage, append-only.
9. `tasks/_lib/llm.py` — wrapper Anthropic avec sélection modèle, caching,
   compteur budget, lecture sentinelle `.panic`.
10. `tasks/_lib/memory.py` — lecture/écriture standardisée + lecture
    `vacation_mode` et skip-patterns.
11. `tasks/_lib/dedup.py` — hash pour findings/drafts cross-task.
12. `tasks/_lib/notify.py` — pipeline drafts + consultation skip-patterns.
13. `.github/workflows/_scaffold.yml` — template réutilisable.
14. `.github/workflows/panic.yml` — kill switch (workflow_dispatch + via worker).
15. `cloudflare-worker/src/index.ts` — endpoints `/telegram`, `/panic`.

---

## CLAUDE.md — contenu cible

Le `CLAUDE.md` à la racine est lu automatiquement par Claude Code à chaque
session. Il sert de **handover permanent** pour :
- les agents qui tournent dans les workflows GitHub Actions ;
- les sessions Claude Code interactives où Sylvain code des évolutions.

Structure proposée :

```markdown
# claudePA — instructions pour Claude Code

## Ce que c'est
Assistant personnel autonome de Sylvain Ribes. Tâches récurrentes hébergées
sur GitHub Actions. Mémoire en markdown versionné dans ce repo.

## Contexte utilisateur
Lis systématiquement `core-memory/profile.md` avant toute tâche. Style à
respecter : direct, dense, concis, evidence-based, ton "bro", pas de
sycophantie, pas de baby talk, "je ne sais pas" plutôt que bullshit.
**Pas de signature, pas de persona** : Sylvain sait à qui il parle,
économie tokens. Français informel par défaut, anglais si le contexte
l'impose.

## Architecture en une page
- `core-memory/` : permanent (profil, family, policies, australia-plan,
  current-location avec flag vacances, skip-patterns).
- `working-memory/` : 30j glissants, un fichier par run de tâche.
- `journal/decisions.md` : décisions importantes, append-only.
- `digests/` : rollups mensuels + findings cross-task + index auto.
- `drafts/` : actions en attente de validation humaine.
- `inbox/` : messages entrants Telegram/email.
- `tasks/` : code Python des tâches, `_lib/` partagé.
- `.github/workflows/` : un workflow par tâche, cron déclaré dans le YAML.
- `schedule.yaml` : source de vérité des fréquences et canaux.

## Conventions
- Chaque run de tâche écrit `working-memory/YYYY-MM-DD-HHMM-<task>.md` avec
  front matter standardisé (voir `_lib/memory.py`).
- Au démarrage de chaque tâche : vérifier sentinelle `.panic` (exit si
  présente) et `vacation_mode` (skip si actif et hors whitelist).
- Avant de créer un draft : consulter `skip-patterns.md` pour ne pas
  re-proposer du déjà refusé.
- Aucune action externe (envoi, réservation) sans passer par `drafts/` +
  validation Telegram. Voir `core-memory/policies.md`.
- OPSEC : ne jamais exposer adresse précise, patrimoine, infos enfants
  dans une comm externe. Si doute → drafter et notifier.
- Sélection modèle dans `_lib/llm.py` :
  - Haiku 4.5 pour fetch/dédup/classification.
  - Sonnet 4.6 par défaut.
  - Opus 4.7 pour self-reflection et analyse stratégique uniquement.
- Prompt caching activé sur `profile.md` + `policies.md` à chaque appel.
- Mails : compte Sylvain en read-only (jamais d'envoi depuis ce compte
  sans validation explicite et ajout du scope). Compte PA en read/write,
  drafts envoyés post-validation Telegram.

## Pour ajouter une tâche
1. Crée `tasks/<nom>.py` (template dans `tasks/_lib/template.py`).
2. Ajoute une entrée dans `schedule.yaml` (cron, channel, model tier).
3. Crée `.github/workflows/task-<nom>.yml` à partir de `_scaffold.yml`.
4. Run en local en mode dry-run : `python -m tasks.<nom> --dry-run`.
5. Vérifie qu'un fichier working-memory est bien produit.
6. Commit, push. Le cron prendra le relais.

## Pour modifier le comportement global
- Édite `core-memory/policies.md` (budget, whitelist, OPSEC).
- Édite ce `CLAUDE.md` pour les conventions structurelles.
- Pour des changements de profil : `core-memory/profile.md` directement.

## Pour les sessions interactives Claude Code (handover)
- Vérifie d'abord le statut : `git log -10`, `ls working-memory/ | tail -5`,
  `cat digests/findings.md | tail -30`.
- Lis `core-memory/profile.md` et `core-memory/policies.md` avant de
  proposer un changement de comportement.
- Les drafts en attente sont dans `drafts/` avec front matter `status: pending`.
- Pour debug une tâche cassée : check le dernier run dans Actions GitHub,
  puis `working-memory/...-error.md` correspondant.
- Toute évolution structurelle (nouveau type de mémoire, refactor `_lib/`)
  doit être discutée avec Sylvain avant implémentation.

## Garde-fous techniques
- Pas de secret en clair dans le repo.
- Pas de `git push --force` sur main.
- Tests d'idempotence avant merge d'une nouvelle tâche.
- Si une tâche dépasse 5 min de runtime, investigation requise.
```

---

## Questions ouvertes à régler en début d'implémentation

- Choix entre **Brave Search** et **Tavily** (les deux ont une API). On
  benchmarke sur un cas concret au moment du build.
- Budget tokens cible exact (proposition : $30/mois pour la V1, à ajuster
  après 1er mois de mesure réelle).
- Adresse exacte du Gmail PA à créer (proposition : `sylvain.pa@gmail.com`
  ou `ribes.pa@gmail.com` — à choisir au moment du setup).
- Nom du groupe Telegram famille à créer.
- Politique mail_review : agit-il sur tous les threads du compte Sylvain
  (sauf newsletters/transactionnel filtrés), ou seulement sur des labels
  spécifiques ? Hypothèse de travail : tout sauf filtrés.
