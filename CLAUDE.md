# claudePA — instructions Claude Code

> Lu automatiquement par Claude Code à chaque session sur ce repo.
> Sert de handover permanent pour : (1) les agents qui tournent dans
> les workflows GitHub Actions, (2) les sessions interactives Sylvain.

## Ce que c'est

Assistant personnel autonome de Sylvain Ribes. Tâches récurrentes
hébergées sur GitHub Actions. Mémoire en markdown versionné dans ce
repo. Voir `SPEC.md` pour l'architecture complète.

## Contexte utilisateur (à lire AVANT toute tâche)

- `core-memory/profile.md` — bio opérationnelle Sylvain (identité,
  famille, parcours, objectifs, style).
- `core-memory/policies.md` — budget tokens, autonomie, OPSEC, garde-fous.
- `core-memory/family.md` — Isa, enfants, échéances famille.
- `core-memory/current-location.md` — où est Sylvain (incl. flag
  `vacation_mode`), mis à jour quotidiennement par `location_context`.
- `core-memory/skip-patterns.md` — patterns refusés (alimenté par les
  SKIP), à consulter avant tout nouveau draft.
- `journal/decisions.md` — décisions importantes append-only.

**Style à respecter** : direct, dense, concis, ton "bro", evidence-based.
**Pas de signature, pas de persona** (Sylvain sait à qui il parle, on
économise les tokens). Pas de sycophantie, pas de baby talk, pas de ton
corporate ou thérapeutique. "Je ne sais pas" plutôt que bullshit.
Français informel par défaut, anglais si le contexte l'impose. Sylvain
fact-checke et veut être challengé quand c'est justifié.

## Architecture en une page

| Dossier | Rôle |
|---|---|
| `core-memory/` | Permanent. Profil, family, policies, australia-plan, people, current-location (+ flag vacances), skip-patterns. Jamais purgé. |
| `working-memory/` | Fenêtre glissante 30j. Un fichier par run de tâche. |
| `journal/decisions.md` | Décisions importantes append-only. Référence pour `self_reflection`. |
| `digests/monthly/` | Rollup mensuel produit avant purge. |
| `digests/findings.md` | Pépites cross-task, append-only. Index auto regénérés par `findings_index`. |
| `drafts/` | Actions en attente de validation humaine (front matter `status: pending`). |
| `inbox/` | Messages entrants Telegram / email. |
| `tasks/` | Code Python des tâches. `_lib/` partagé (memory, llm, dedup, notify, …). |
| `.github/workflows/` | Un workflow par tâche, cron déclaré dans le YAML. Inclut `panic.yml` (kill switch). |
| `schedule.yaml` | Source de vérité : fréquences, canaux, modèles, whitelist vacances. |
| `cloudflare-worker/` | Gateway webhook (Telegram + Gmail entrants + `/panic`). |

## Conventions

- **Format working-memory** : `working-memory/YYYY-MM-DD-HHMM-<task>.md`
  avec front matter standardisé (voir `tasks/_lib/memory.py` une fois créé).
- **Au démarrage de chaque tâche** : (a) vérifier la sentinelle `.panic`
  à la racine — si présente, exit immédiat ; (b) lire `vacation_mode`
  dans `current-location.md` — si `true` et tâche hors whitelist
  vacances (`policies.md`), skip avec log.
- **Avant tout draft** : consulter `core-memory/skip-patterns.md` via
  `_lib/notify.py` ; si match récent, annuler silencieusement (log only).
- **De-dup cross-task** : findings et drafts passent par `_lib/dedup.py`
  (hash type+titre+org), fenêtre 90j, pour ne pas re-proposer la même
  opportunité depuis plusieurs veilles.
- **Validation humaine systématique** : aucune action externe (envoi
  mail, réservation, dépense, post public) sans passer par `drafts/`
  + validation Telegram. Voir `core-memory/policies.md` pour la
  whitelist d'actions autorisées sans validation. Un `SKIP` Telegram
  enregistre le pattern dans `skip-patterns.md`.
- **OPSEC** : ne jamais exposer adresse précise, détails patrimoniaux,
  ni infos enfants dans une comm externe. Si doute → drafter et notifier.
- **Sélection modèle** dans `tasks/_lib/llm.py` :
  - tier `haiku` : fetch, dédup, classification (mails, RSS, search)
  - tier `sonnet` : synthèse, drafts, briefings (défaut)
  - tier `opus` : self-reflection mensuelle, analyse stratégique
- **Prompt caching** : `profile.md` + `policies.md` mis en cache au
  début de chaque appel.
- **Mails** : compte Sylvain en **read-only** (pas d'envoi sans ajout
  explicite du scope + validation). Compte PA dédié en **read/write**,
  drafts d'envoi notifiés sur Telegram perso pour validation, exécution
  post-OK. Filtres newsletters + transactionnel via Haiku en amont.
- **Telegram** : routage par `channel: perso|famille` dans `schedule.yaml`.
  - `perso` = bot 1:1 Sylvain (sensibles, carrière, mail review)
  - `famille` = groupe Sylvain + Isa (briefings, agenda, sorties)
- **Panic / kill switch** : `/panic` sur Telegram OU déclenchement manuel
  de `.github/workflows/panic.yml` → crée `.panic` à la racine. Toutes
  les tâches exit au prochain run. Sylvain supprime le fichier pour
  réactiver.

## Pour ajouter une nouvelle tâche

1. Crée `tasks/<nom>.py` (template : `tasks/_lib/template.py`).
2. Ajoute une entrée dans `schedule.yaml` (cron INDICATIF, channel, model tier).
3. Crée `.github/workflows/task-<nom>.yml` à partir de `_scaffold.yml` —
   **sans `schedule:` côté GH**, uniquement `workflow_dispatch:` (les
   crons natifs GH ont 30min-2h de delay, on les a abandonnés).
4. Ajoute le cron réel dans `cloudflare-worker/wrangler.toml` ([triggers].crons)
   + le mapping dans `cloudflare-worker/src/index.ts` (CRON_TO_WORKFLOW).
   Limite free plan = 5 cron triggers max.
5. Redéploie le worker : `cd cloudflare-worker && npx wrangler deploy`.
6. Run en local en mode dry-run : `python -m tasks.<nom> --dry-run`.
7. Vérifie qu'un fichier `working-memory/...` est bien produit.
8. Commit, push sur `main`. Le worker dispatchera au prochain créneau.

## Pour modifier le comportement global

- Politique d'autonomie / budget / OPSEC → `core-memory/policies.md`.
- Conventions structurelles → ce `CLAUDE.md`.
- Profil utilisateur → `core-memory/profile.md` (édition directe OK).
- Fréquence ou canal d'une tâche → `schedule.yaml`.

## Handover — démarrer une session interactive Claude Code

Avant toute proposition d'évolution :

1. **État du repo** :
   ```bash
   git log --oneline -10
   ls working-memory/ | tail -5
   tail -50 digests/findings.md
   ls drafts/ | head -20
   ```
2. **Lis** `core-memory/profile.md` et `core-memory/policies.md`.
3. **Drafts en attente** : `grep -l 'status: pending' drafts/*.md`.
4. **Debug d'une tâche cassée** : check le dernier run dans
   l'onglet Actions du repo GitHub, puis le
   `working-memory/...-error.md` correspondant.
5. **Évolution structurelle** (nouveau type de mémoire, refactor
   `_lib/`, nouveau canal de notif) → discuter avec Sylvain avant
   d'implémenter. Pas d'initiative architecturale en autonomie.

## Garde-fous techniques

- Pas de secret en clair dans le repo. Tout via GitHub Secrets.
- Pas de `git push --force` sur main.
- Tests d'idempotence avant merge d'une nouvelle tâche : un re-run
  ne doit pas re-créer un draft pour la même fenêtre.
- Si une tâche dépasse 5 min de runtime, investigation requise.
- Budget tokens mensuel : voir `core-memory/policies.md`. Au-delà
  de 80%, alerte Telegram. Au-delà de 100%, refus d'appel.

## Phase de développement actuelle

Voir `SPEC.md` section "Phasage". Statut courant : **Phase 1.5 — boucle
Telegram end-to-end + 4 tâches actives** (daily_digest, mail_review,
location_context, sliding_window). OAuth Gmail wiré (perso readonly +
PA modify). Crons opérés par CF Worker (précision ~1 min vs delays GH).
Branche par défaut = `main`. Catalogue V1 restant à coder : weekly_briefing,
ai_jobs_formations, sydney_opportunities, daily_digest++ (calendar),
network_followups, health_watch, self_reflection.
