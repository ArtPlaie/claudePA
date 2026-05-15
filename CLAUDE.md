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
- `core-memory/current-location.md` — où est Sylvain en ce moment
  (mis à jour quotidiennement par la tâche `location_context`).

**Style à respecter** : direct, dense, concis, evidence-based.
Pas de sycophantie, pas de baby talk, pas de ton corporate ou
thérapeutique. "Je ne sais pas" plutôt que bullshit. Français
informel par défaut, anglais si le contexte l'impose. Sylvain
fact-checke et veut être challengé quand c'est justifié.

## Architecture en une page

| Dossier | Rôle |
|---|---|
| `core-memory/` | Permanent. Profil, family, policies, australia-plan, people. Jamais purgé. |
| `working-memory/` | Fenêtre glissante 30j. Un fichier par run de tâche. |
| `digests/monthly/` | Rollup mensuel produit avant purge. |
| `digests/findings.md` | Pépites cross-task, append-only. |
| `drafts/` | Actions en attente de validation humaine (front matter `status: pending`). |
| `inbox/` | Messages entrants Telegram / email. |
| `tasks/` | Code Python des tâches. `_lib/` partagé. |
| `.github/workflows/` | Un workflow par tâche, cron déclaré dans le YAML. |
| `schedule.yaml` | Source de vérité : fréquences, canaux, modèles. |
| `cloudflare-worker/` | Gateway webhook (Telegram + Gmail entrants). |

## Conventions

- **Format working-memory** : `working-memory/YYYY-MM-DD-HHMM-<task>.md`
  avec front matter standardisé (voir `tasks/_lib/memory.py` une fois créé).
- **Validation humaine systématique** : aucune action externe (envoi
  mail, réservation, dépense, post public) sans passer par `drafts/`
  + validation Telegram. Voir `core-memory/policies.md` pour la
  whitelist d'actions autorisées sans validation.
- **OPSEC** : ne jamais exposer adresse précise, détails patrimoniaux,
  ni infos enfants dans une comm externe. Si doute → drafter et notifier.
- **Sélection modèle** dans `tasks/_lib/llm.py` :
  - tier `haiku` : fetch, dédup, classification (mails, RSS, search)
  - tier `sonnet` : synthèse, drafts, briefings (défaut)
  - tier `opus` : self-reflection mensuelle, analyse stratégique
- **Prompt caching** : `profile.md` + `policies.md` mis en cache au
  début de chaque appel.
- **Email PA** : lecture + drafts uniquement au démarrage. Pas de
  scope `gmail.send` tant que la confiance n'est pas établie.
- **Telegram** : routage par `channel: perso|famille` dans `schedule.yaml`.
  - `perso` = bot 1:1 Sylvain (sensibles, carrière, mail review)
  - `famille` = groupe Sylvain + Isa (briefings, agenda, sorties)

## Pour ajouter une nouvelle tâche

1. Crée `tasks/<nom>.py` (template : `tasks/_lib/template.py`).
2. Ajoute une entrée dans `schedule.yaml` (cron, channel, model tier).
3. Crée `.github/workflows/task-<nom>.yml` à partir de `_scaffold.yml`.
4. Run en local en mode dry-run : `python -m tasks.<nom> --dry-run`.
5. Vérifie qu'un fichier `working-memory/...` est bien produit.
6. Commit, push. Le cron prendra le relais au prochain créneau.

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

Voir `SPEC.md` section "Phasage". Statut courant : **Phase 0 — squelette
en place, code des tâches et workflows à venir.**
