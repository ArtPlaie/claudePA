---
task: session-handover
run_at: 2026-06-08T19:48:45+00:00
status: completed
branch: main
type: interactive-session
---

## Résumé

Grosse session : **migration des 6 veilles en routines terminée**, **envoi
email des rapports câblé et validé end-to-end**, **mécanisme handover
inter-session fiabilisé**, et **recentrage de `sydney_opportunities`**
(reconversion IA, plus de trading). Tout est sur `main`. Prochaine étape
prévue par Sylvain : **retravailler les prompts/commands dans une autre
session**, et **créer les 5 routines restantes** côté UI.

## Ce qui a été fait (tout sur `main`)

1. **Doc migration routines landée sur main** (`accf41f`) — était bloquée
   sur une branche feature. SPEC.md / CLAUDE.md / `prompts/*` rapatriés.
2. **Mécanisme handover inter-session** (`accf41f`) — CLAUDE.md : au
   démarrage, lire `ls -t working-memory/*-session-*.md | head -1` ; en fin
   de session, écrire le handover **et le pousser sur main** (sinon invisible,
   car les sessions s'ouvrent depuis main). Les `*-session-*.md` sont
   **exemptés de la purge** `sliding_window` (`1813195`).
3. **`journal/decisions.md`** — entrée 2026-06-08 sur la bascule routines
   (ajoutée sur dérogation explicite de Sylvain).
4. **6 commands de veille** dans `.claude/commands/` : `sydney_opportunities`
   (pilote), `weekly_briefing`, `ai_jobs_formations`, `local_activities`,
   `activities_next10days`, `health_watch`. Patron commun : gardes
   panic/vacances → lecture core-memory en direct → mission (web search) →
   working-memory → findings dédupliqués → commit/push main. `prompts/*.md` =
   mode dégradé historique (bandeau en tête).
5. **Envoi email = GHA auto-dispatch** (`4d64992`). Découverte clé : le SMTP
   brut (465/587) est **bloqué dans une routine** (proxy egress = 443 only) ;
   l'API Gmail OAuth marche en HTTPS mais le token PA n'est pas configuré.
   Solution retenue : la routine **pousse son rapport sur main**, et
   `.github/workflows/mail-report.yml` se déclenche `on: push` (paths filtrés
   sur `working-memory/*-<veille>.md`), lit le rapport et l'envoie en **SMTP
   depuis GHA** (secrets `GMAIL_USER`/`GMAIL_APP_PASSWORD`/`MAIL_TO`, déjà en
   place). Le helper OAuth `tasks/send_report.py` a été **supprimé**.
6. **`sydney_opportunities` recentré** (`00309f7`) : **plus de trading /
   finance quanti** ; sections = jobs IA pour profil en reconversion +
   **Formations IA** (MATS/ARENA/AISF/fellowships) + **Investissement /
   cofounding** + **Serendipity** (carte blanche, créativité max).
7. **core-memory nettoyée** (`2cf9a35`) : `australia-plan.md` + `profile.md`
   ne listent plus la finance quanti comme cible (exclusion explicite).
   Aligne toutes les veilles, pas seulement sydney.

## Validé end-to-end ✅

- Routine `sydney_opportunities` créée + `Run now` → rapport produit
  (`working-memory/2026-06-08-1636-sydney_opportunities.md`, 6 sections).
- **Bug trouvé + corrigé** : la routine poussait sur une branche `claude/*`
  (pas main) → `mail-report` ne se déclenchait pas. **Cause : "Allow
  unrestricted branch pushes" n'était pas ON.** Sylvain l'a **activé** (onglet
  Permissions, dans le form Edit routine, à côté de Connectors/Behavior).
- Rapport fast-forwardé sur main → `mail-report.yml` run #1 **success** →
  log `OK — envoyé`. **Mail reçu.** La chaîne complète fonctionne.

## Prochain pas concret

1. **Retravailler les prompts** (intention de Sylvain pour la prochaine
   session). ⚠️ **Important** : la version **autoritative est
   `.claude/commands/<nom>.md`**, PAS `prompts/<nom>.md` (ce dernier est le
   fallback copier-coller historique, avec bandeau). Éditer les **commands**.
   Confirmer avec Sylvain lesquelles et dans quel sens.
2. **Créer les 5 routines restantes** sur `claude.ai/code/routines` (une par
   command). Pour CHACUNE : repo `artplaie/claudepa`, **Allow unrestricted
   branch pushes = ON** (sinon pas de push main → pas de mail), réseau Full,
   prompt `Lance /<nom>. Suis les étapes finales de la command.`. Crons :
   - weekly_briefing `0 17 * * 0` · ai_jobs_formations `30 5 * * 2` ·
     local_activities `0 7 1 * *` · activities_next10days `0 16 * * 4` ·
     health_watch `0 7 * * 5`.
3. La routine sydney existante est en trigger **quotidien** (UI) au lieu de
   hebdo — à ajuster si on ne veut pas un run/jour.

## Points ouverts / à arbitrer

- **Cadence bimensuelle** (`ai_jobs_formations`, `health_watch`, cadence_days
  14) non exprimable en cron → soit hebdo (2× trop), soit `... 1,15 * *`.
- **Connecteur Calendar** : utile pour `activities_next10days` (la command
  note l'absence d'accès agenda). À brancher quand on créera la routine.
- **Connecteurs sur la routine sydney** : Gmail/Calendar/Drive sont activés
  mais inutiles pour cette veille (surface d'écriture sans validation) — à
  retirer si on veut limiter.
- Branche `claude/funny-gauss-191f1z` (run sydney) mergée dans main par
  fast-forward → stale, supprimable.
- `prompts/sydney_opportunities.md` désynchro du command (recentrage non
  reporté) — OK car déprécié, mais à garder en tête si on garde le fallback.

## État repo

- Branche : `main` (à jour, ce handover inclus). HEAD avant handover =
  `d8f31bd`.
- `mail-report.yml` actif et validé. Secrets SMTP en place.
- 6 commands écrites ; 1 routine créée (sydney, perms OK), 5 à créer.
- Pas de PR.
