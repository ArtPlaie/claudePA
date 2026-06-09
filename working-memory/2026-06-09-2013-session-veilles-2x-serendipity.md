---
task: session-handover
run_at: 2026-06-09T20:13:07+00:00
status: completed
branch: main (tout poussé directement sur main, autorisé par CLAUDE.md)
---

# Handover — session 2026-06-09 : recherche +2x & nouvelle veille `serendipity`

## Résumé

Session de tuning des prompts de veille + création d'une nouvelle veille
`serendipity`. Tout est sur `main`, routines à jour au prochain run.

## Ce qui a été fait

1. **Toutes les veilles : encourager ~2× plus de recherche brute.** Reformulé le
   bullet « Recherche large, sortie courte » (de « fouille beaucoup » mou → exiger
   explicitement 2× plus de candidats bruts avant tri, pour avoir du CHOIX) et
   ajouté un bloc concret « Volume de recherche » dans chaque section Mission.
   Touche : `sydney_opportunities`, `weekly_briefing`, `ai_jobs_formations`,
   `health_watch`, `local_activities`. `activities_next10days` (re-classeur, pas
   de fan-out web) → consigne plus légère : élargir par recherche fraîche si la
   liste source est maigre. **Garde-fou conservé partout : sortie courte + tri
   impitoyable, c'est l'amont qui s'élargit, pas le mail.**

2. **Nouvelle veille `serendipity`** (`.claude/commands/serendipity.md`, model
   **opus**, samedi 08:00 UTC, canal perso). Objet : exploration libre, idées
   off-scope à haute valeur ajoutée « ce à quoi Sylvain n'a pas pensé ».
   - **2 itérations de cadrage suite à feedback Sylvain** :
     (a) v1 trop career/IA-orientée (leviers « pari contrarian / asymétrie
     d'ex-trader / détournement d'edge ») → **bannissement explicite du registre
     boulot** (couvert par les 3 veilles carrière) ;
     (b) v2 encore trop ancrée (menu de leviers + exemples genre Magic → l'agent
     ressortait du banal « fais une partie de Magic avec ton aîné »).
   - **v3 finale = exploration libre, zéro ancrage** : plus aucun menu de
     catégories ni d'exemples. Juste 2 garde-fous (scope = pas le boulot ;
     qualité = non-évident ou rien) + techniques anti-banal encodées sans
     diriger le contenu : « pars de la compréhension pas de la recombinaison »,
     « dépasse la première vague — les 10 premières idées sont évidentes, la
     valeur commence à la 20ᵉ/40ᵉ », ancrage web obligatoire, variation d'un run
     à l'autre (grep des rapports passés).
   - **Branchements infra faits** : `schedule.yaml` (entrée serendipity),
     `mail-report.yml` (path + regex + dict NICE → sujet "Serendipity"),
     `sync-veille-to-main.yml` (path + regex). Donc mail + synchro main OK.

3. **Désambiguïsation** : `sydney_opportunities` §4 « Serendipity » →
   renommée **« Wildcard carrière »** (contenu carrière inchangé) pour ne pas
   entrer en collision avec la nouvelle veille `serendipity` (vie/hors-boulot).

4. **Corrections mémoire (profil)** :
   - **Famille** (l'agent confondait les genres) : `profile.md` + `family.md`
     (table prénom/sexe/âge) + `local_activities.md` corrigés →
     **Anna (fille, 8), Tristan (garçon, 5), César (garçon, 20 mois)**.
     « l'aîné » → « l'aînée » dans `local_activities`.
   - **Magic/Dominion supprimé** du profil (c'est sa fille qui joue, info trop
     niche) — retiré de `profile.md` et de l'inline `local_activities.md`.

## Décisions

- **Modèles** : Sylvain bascule les 6 veilles classiques en **Sonnet** (assez
  bon, plus rapide ; le fan-out +2x charge l'amont pas le raisonnement).
  `serendipity` reste en **Opus** (créativité / pensée latérale).
- **Push sur main** : les fichiers SOURCE (commands, schedule, workflows) ne sont
  PAS synchronisés par `sync-veille-to-main.yml` (qui ne copie que les rapports
  working-memory + findings). Donc une routine clonant `main` ne les voit pas
  s'ils restent sur une branche `claude/**`. **Toute modif de fichier source DOIT
  être poussée sur `main` directement** (autorisé explicitement par CLAUDE.md).
  C'est le bug qui a fait tourner le serendipity du 09:18 « en carte blanche ».

## État repo

- Tout est sur `main` (dernier commit `1e33386`), working tree propre.
- 6 commands de veille + serendipity + 2 workflows + schedule.yaml + profile.md
  + family.md à jour sur `main`.

## Prochain pas concret

- **Sylvain** : finir de basculer les routines en Sonnet (sauf serendipity =
  Opus) côté UI `claude.ai/code/routines`, puis **Run now** sur `serendipity`
  pour valider la v3 (doit sortir du non-évident hors-boulot, pas du banal type
  « partie de Magic »). Si la routine serendipity n'existe pas encore en tant que
  telle dans l'UI, la créer (prompt : `Lance /serendipity. Suis les étapes
  finales de la command.`, repo artplaie/claudepa, Opus, réseau Full, unrestricted
  branch pushes ON, trigger hebdo samedi).
- **Calibrage à surveiller** : runtime des veilles (flag 5 min CLAUDE.md) vu le
  +2x recherche ; et fréquence serendipity (hebdo peut être trop → repli
  `cadence_days: 14` si ça radote malgré l'anti-dup).
- **Reste optionnel** : purge des `prompts/*.md` legacy (contiennent encore
  Magic) — laissés intacts car non utilisés par les routines, marqués « retiré à
  terme ».
