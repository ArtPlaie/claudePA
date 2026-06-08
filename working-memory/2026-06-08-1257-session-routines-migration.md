---
task: session-handover
run_at: 2026-06-08T12:57:00+00:00
model: claude-opus-4-7
status: completed
branch: claude/planner-prompts-chat-RcLEn
type: interactive-session
---

## Résumé

Session de design : décision de **migrer l'orchestration des veilles** de
GitHub Actions + Cloudflare Worker vers les **Claude Code Routines**. Doc
mise à jour (SPEC.md, CLAUDE.md, prompts/README.md) et pushée. **Aucun code
de veille écrit encore** — le pilote `sydney_opportunities` est le prochain
pas. Repris dans une autre session via ce fichier.

## Contexte / pourquoi

Les veilles (`weekly_briefing`, `ai_jobs_formations`, `sydney_opportunities`,
`local_activities`, `activities_next10days`, `health_watch`) n'ont jamais été
codées : le chemin Python/SDK n'avait pas de web search wiré (décision Brave
vs Tavily restée ouverte), d'où le mode dégradé `prompts/*.md` copié-collé
dans claude.ai.

Les Routines (vérifiées dans la doc : `code.claude.com/docs/en/routines`)
ferment ce trou : session Claude Code complète, planifiée, sur infra
Anthropic, **WebSearch natif**, clone le repo, commit + push. Ça supprime CF
Worker (pour les veilles), `_lib/llm.py`, la clé API, le gate budget, et la
décision search API. Bonus : la session lit `core-memory/*.md` en direct →
fin de la "photo" qui périme dans les prompts.

## Décisions prises cette session

1. **Bascule veilles → Routines** (GHA/CF gardés pour tasks Python legacy +
   futur PA Telegram inbound).
2. **Logique dans `.claude/commands/<task>.md`** versionnée ; le prompt de la
   routine reste trivial (`Lance /<task>. Suis les étapes finales.`).
3. **Push direct sur `main`** (option *Allow unrestricted branch pushes* ON).
4. **Réseau routine = Full** (les veilles citent des liens directs vers pages
   officielles ; Trusted bloque WebFetch sur domaines arbitraires).
5. **Livraison v1 = le repo** (lire le rapport committé sur GitHub/mobile).
   Connecteur Telegram/email = plus tard.
6. **Pilote = `sydney_opportunities`** avant de convertir les autres.

> Ces décisions sont d'archi → à consigner dans `journal/decisions.md` par
> Sylvain (écriture agent interdite sur ce fichier). Pas encore fait.

## Fait (committé + pushé sur la branche)

- `514a359` — SPEC.md : section autoritative "Orchestration — Claude Code
  Routines" (pourquoi, modèle command+routine, config décidée, mapping
  veille→command→routine, phasage A/B/C), stack technique mise à jour,
  bannières *(historique)* sur les sections GHA/CF.
- `e48312c` — CLAUDE.md + prompts/README.md alignés (deux chemins
  d'exécution, "Pour ajouter une tâche" en flow A=routine / B=GHA, debug,
  budget, phase actuelle ; README marqué mode dégradé historique).

## Prochain pas — Pilote `sydney_opportunities` (Phase A)

1. Créer `.claude/commands/sydney_opportunities.md` à partir de
   `prompts/sydney_opportunities.md`, en :
   - **retirant** le bloc profil/plan/OPSEC inliné → remplacer par "lis
     `core-memory/profile.md`, `policies.md`, `australia-plan.md`,
     `current-location.md` en direct" ;
   - **ajoutant** les étapes finales : check `.panic` + `vacation_mode` ;
     écrire `working-memory/YYYY-MM-DD-HHMM-sydney_opportunities.md` (front
     matter standard) ; appender `digests/findings.md` si findings ; `git
     add && commit && push` sur `main`.
2. Côté UI `claude.ai/code/routines` (Sylvain) : créer la routine, repo
   `artplaie/claudepa`, unrestricted branch pushes ON, env réseau Full,
   trigger scheduled hebdo (mer, cf. schedule.yaml), prompt = `Lance
   /sydney_opportunities. Suis les étapes finales de la command.`
3. `Run now`, vérifier le commit + le fichier working-memory produit.
4. Si la boucle tourne → Phase B : convertir les 5 autres veilles pareil.

## Encore à arbitrer (pas tranché)

- Sort des 4 tasks GHA actives (`daily_digest`, `mail_review`,
  `location_context`, `sliding_window`) : rester GHA ou migrer routine ?
- Livraison réelle des rapports (repo seul vs push Telegram/email).
- Reprise du PA Telegram inbound (hors scope de cette migration).

## État repo

- Branche : `claude/planner-prompts-chat-RcLEn` (pushée, à jour).
- Working tree propre avant ce fichier.
- Pas de PR créée (pas demandé).
