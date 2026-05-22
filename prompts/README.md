# prompts/ — prompts auto-suffisants pour le chat web Claude

> Mode dégradé en attendant que l'infra `claudePA` (GitHub Actions + Cloudflare Worker)
> soit complètement câblée. Chaque fichier `<task>.md` est un prompt complet,
> à copier-coller tel quel dans une nouvelle conversation sur https://claude.ai.

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
préserver la continuité de la mémoire quand l'infra sera prête.

Les findings importants doivent aussi être appendés à `digests/findings.md` au format
documenté en haut de ce fichier.

## Mises à jour

Ces prompts sont une **photo** des fichiers `core-memory/*` et `SPEC.md` à la date
de création. Si tu édites `profile.md`, `policies.md`, `family.md`, `current-location.md`
ou `australia-plan.md`, regénère les prompts (ou édite-les à la main aux endroits
annotés `<!-- core-memory:* -->`).
