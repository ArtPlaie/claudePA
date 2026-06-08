# claudePA — instructions Claude Code

> Lu automatiquement par Claude Code à chaque session sur ce repo.
> Sert de handover permanent pour : (1) les **routines** (veilles
> récurrentes), (2) les workflows GitHub Actions (tasks Python
> restantes), (3) les sessions interactives Sylvain.

## Ce que c'est

Assistant personnel autonome de Sylvain Ribes. Mémoire en markdown
versionné dans ce repo. **Deux chemins d'exécution coexistent** :

- **Claude Code Routines** *(autorité depuis 2026-06)* : les **veilles**
  (`weekly_briefing`, `ai_jobs_formations`, `sydney_opportunities`,
  `local_activities`, `activities_next10days`, `health_watch`) tournent
  comme routines schedulées sur l'infra Anthropic. Logique dans
  `.claude/commands/<task>.md`, la routine clone le repo, exécute la
  command, commit + push sur `main`.
- **GitHub Actions** *(legacy, en place)* : les tâches Python
  historiques (`daily_digest`, `mail_review`, `location_context`,
  `sliding_window`) restent sur GHA + Cloudflare Worker pour le cron.

Voir `SPEC.md` pour l'architecture complète et la section
"Orchestration — Claude Code Routines" pour la bascule.

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
| `.claude/commands/` | **Slash commands versionnées** — logique des veilles (une par routine). |
| `tasks/` | Code Python des **tasks GHA legacy** (`daily_digest`, `mail_review`, `location_context`, `sliding_window`). `_lib/` partagé. |
| `.github/workflows/` | Workflows pour les tasks GHA legacy + `panic.yml` (kill switch). Plus utilisé pour les veilles. |
| `schedule.yaml` | Source de vérité : fréquences, canaux, modèles, whitelist vacances. Référence pour les routines aussi (cadences). |
| `cloudflare-worker/` | Gateway webhook — cron des tasks GHA + (futur) Telegram/Gmail entrants + `/panic`. Pas sur le chemin des veilles. |

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
- **Sélection modèle** :
  - **Routines (veilles)** : le modèle est configuré sur la routine
    elle-même (UI `claude.ai/code/routines`). Pas de tier code-side.
  - **Tasks GHA legacy** : tier dans `tasks/_lib/llm.py` —
    `haiku` (fetch/dédup/classif), `sonnet` (défaut synthèse/drafts),
    `opus` (self-reflection, analyse stratégique).
- **Prompt caching** : pertinent pour les tasks GHA (`_lib/llm.py` met
  `profile.md` + `policies.md` en cache). Pour les routines, la session
  lit ces fichiers directement — pas de gestion de cache à faire.
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

**Défaut = routine.** Le chemin GHA n'est requis que si la tâche a besoin
de credentials OAuth persistants (Gmail r/w, Calendar) ou tourne sur la
mémoire sans web search.

### Chemin A — routine (veilles, défaut)

1. Crée `.claude/commands/<nom>.md`. Structure attendue :
   - lecture obligatoire au démarrage : `core-memory/profile.md`,
     `policies.md`, `family.md`, `current-location.md` (pas d'inlining,
     la session lit en direct) ;
   - check `.panic` (exit) + `vacation_mode` (skip hors whitelist) ;
   - mission de la veille, méthode (web search, sources), format de sortie ;
   - étapes finales : écrire `working-memory/YYYY-MM-DD-HHMM-<nom>.md`
     (front matter standard), appender `digests/findings.md` si pertinent,
     `git add && git commit && git push` sur `main`.
2. Ajoute une entrée dans `schedule.yaml` (cadence indicative, model, canal).
3. Crée la routine sur `claude.ai/code/routines` :
   - prompt : `Lance /<nom>. Suis les étapes finales de la command.` ;
   - repo : `artplaie/claudepa` ; *Allow unrestricted branch pushes* = ON ;
   - environnement : réseau **Full** (les veilles citent des liens directs) ;
   - trigger scheduled selon `schedule.yaml` (cron custom via
     `/schedule update` si le preset ne suffit pas, min 1 h).
4. `Run now` une fois, vérifie le commit + le `working-memory/...md` produit.

### Chemin B — task GHA (legacy, OAuth-dépendant)

1. Crée `tasks/<nom>.py` (template : `tasks/_lib/template.py`).
2. Ajoute une entrée dans `schedule.yaml`.
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

> ⚠️ Le contexte ne suit PAS d'une session à l'autre : chaque session
> démarre dans un container neuf qui re-clone le repo. **La seule mémoire
> inter-session est le handover committé dans `working-memory/`.** Sylvain
> ouvre toujours ses sessions depuis `main` → un handover pushé sur une
> branche de feature est invisible. Lis-le au démarrage, écris-le à la fin.

Avant toute proposition d'évolution :

1. **Lis le dernier handover de session** (contexte de la session
   précédente : décisions, prochain pas en cours) :
   ```bash
   ls -t working-memory/*-session-*.md 2>/dev/null | head -1 | xargs cat
   ```
   S'il décrit un travail en cours, c'est ta priorité par défaut — ne
   repars pas de zéro sur autre chose sans raison.
2. **État du repo** :
   ```bash
   git log --oneline -10
   ls working-memory/ | tail -5
   tail -50 digests/findings.md
   ls drafts/ | head -20
   ```
3. **Lis** `core-memory/profile.md` et `core-memory/policies.md`.
4. **Drafts en attente** : `grep -l 'status: pending' drafts/*.md`.
5. **Debug d'une tâche cassée** :
   - **Routine** : ouvre le run sur `claude.ai/code/routines`, lis le
     transcript (statut vert ≠ tâche réussie — vérifier ce qui a été
     committé).
   - **Task GHA** : check le dernier run dans l'onglet Actions du repo,
     puis le `working-memory/...-error.md` correspondant.
6. **Évolution structurelle** (nouveau type de mémoire, refactor
   `_lib/`, nouveau canal de notif) → discuter avec Sylvain avant
   d'implémenter. Pas d'initiative architecturale en autonomie.

### Fin de session — écrire le handover

Quand une session interactive s'arrête sur un travail non terminé (ou une
décision d'archi prise) :

1. Écris `working-memory/YYYY-MM-DD-HHMM-session-<slug>.md` avec front
   matter `task: session-handover` (résumé, décisions, **prochain pas
   concret**, état repo / branche).
2. **Pousse-le sur `main`**, jamais seulement sur la branche de feature de
   la session — sinon la prochaine session (ouverte depuis `main`) ne le
   verra pas. C'est la règle qui rend la mémoire inter-session fiable.
   *(Le nom doit contenir `-session-` pour être récupéré par la commande
   de lecture au démarrage.)*

## Garde-fous techniques

- Pas de secret en clair dans le repo. GitHub Secrets pour les tasks
  GHA ; env vars de l'environnement routine pour les veilles.
- Pas de `git push --force` sur main.
- Tests d'idempotence avant merge d'une nouvelle tâche : un re-run
  ne doit pas re-créer un draft pour la même fenêtre.
- Si une tâche dépasse 5 min de runtime, investigation requise.
- Budget tokens :
  - **Tasks GHA** : plafond mensuel dans `core-memory/policies.md`,
    `_lib/llm.py` gate à 80% (alerte) / 100% (refus).
  - **Routines** : consommation sur l'abonnement claude.ai (pas de
    clé API). Cap journalier de runs côté Anthropic, visible sur
    `claude.ai/code/routines`.

## Phase de développement actuelle

Voir `SPEC.md` section "Phasage" + "Orchestration — Claude Code Routines".
Statut courant : **Phase 1.5 + migration orchestration en cours**.

- **Tasks GHA actives** : `daily_digest`, `mail_review`,
  `location_context`, `sliding_window`. OAuth Gmail wiré (perso readonly
  + PA modify). Crons opérés par CF Worker.
- **Veilles** : migrent vers routines (`.claude/commands/`). Pilote =
  `sydney_opportunities`. Suivront : `weekly_briefing`,
  `ai_jobs_formations`, `local_activities`, `activities_next10days`,
  `health_watch`. `prompts/*.md` est le mode dégradé historique
  (copier-coller dans claude.ai) — sera retiré au fur et à mesure que
  les commands prennent le relais.
- **Encore à arbitrer** : sort des 4 tasks GHA actives (rester GHA ou
  migrer routine) ; livraison des rapports de veille (lire dans le repo
  vs pousser sur Telegram/email) ; reprise du PA Telegram inbound.
- Branche par défaut = `main`.
