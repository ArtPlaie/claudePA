# prompts/ — prompts auto-suffisants pour le chat web Claude

> **Statut (révision 2026-06)** : ce dossier est le **mode dégradé
> historique**. Décision prise de basculer les veilles sur **Claude Code
> Routines** (cf. `SPEC.md` § "Orchestration — Claude Code Routines"). La
> logique de chaque veille migre vers `.claude/commands/<task>.md`, et la
> routine planifiée tourne sur l'infra Anthropic avec web search natif,
> commit + push sur `main`.
>
> Tant que la command correspondante n'existe pas, le fichier
> `prompts/<task>.md` ci-dessous reste utilisable en copier-coller dans
> une nouvelle conversation sur https://claude.ai. Une fois la command
> en place et la routine validée, le prompt sera retiré de ce dossier.

## Usage

1. Ouvre une nouvelle conv claude.ai.
2. Sélectionne le modèle conseillé (voir tableau ci-dessous).
3. Active **Web search** dans les outils (obligatoire pour toutes les veilles).
4. Copie-colle l'intégralité du fichier `prompts/<task>.md` comme premier message.
5. Pour les tâches qui demandent un input (`activities_next10days`, `self_reflection`),
   colle l'input demandé dans le message suivant.

## Catalogue

| Fichier | Modèle conseillé | Fréquence cible | Web search ? | Input utilisateur |
|---|---|---|---|---|
| `weekly_briefing.md` | Sonnet 4.6 (Opus 4.7 pour la version "analyse longue") | hebdo, dimanche soir | oui | — |
| `ai_jobs_formations.md` | Sonnet 4.6 | tous les 14 j | oui | — |
| `sydney_opportunities.md` | Sonnet 4.6 | hebdo, mercredi | oui | — |
| `local_activities.md` | Sonnet 4.6 | mensuel | oui | — |
| `activities_next10days.md` | Haiku 4.5 | hebdo, jeudi soir | non | la liste produite par `local_activities` du mois en cours |
| `health_watch.md` | Sonnet 4.6 | tous les 14 j | oui | — |
| `self_reflection.md` | Opus 4.7 | mensuel, le 15 | non | working-memory + decisions du mois écoulé |

## Conventions de sortie

Chaque prompt demande à la fin un bloc **front matter YAML** + corps en markdown,
équivalent à ce qu'écrirait la tâche dans `working-memory/`. Tu peux copier ce bloc
manuellement dans `working-memory/YYYY-MM-DD-HHMM-<task>.md` après chaque run pour
préserver la continuité de la mémoire.

Les findings importants doivent aussi être appendés à `digests/findings.md` au format
documenté en haut de ce fichier.

> Note : ce copier-coller manuel disparaît côté routine — la command
> écrit `working-memory/` et appende `findings.md` toute seule avant de
> commit-push.

## Mises à jour

Ces prompts sont une **photo** des fichiers `core-memory/*` et `SPEC.md` à la date
de création. Si tu édites `profile.md`, `policies.md`, `family.md`, `current-location.md`
ou `australia-plan.md`, il faut regénérer les prompts (ou les éditer à la main aux
endroits annotés `<!-- core-memory:* -->`).

C'est précisément ce défaut que la bascule routine corrige : les commands
de `.claude/commands/` lisent les fichiers core-memory **en direct** au
run, donc une édition de `profile.md` est prise en compte immédiatement.
