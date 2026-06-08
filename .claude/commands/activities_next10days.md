---
description: Sélection 3-5 activités actionnables dans les 10 prochains jours pour la famille (Bois-le-Roi, rayon 1h15) — routine hebdo
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch
---

# /activities_next10days

Run de la veille `activities_next10days` : tu pars du dernier rapport
`local_activities` committé dans `working-memory/`, tu sélectionnes les
**3 à 5 activités concrètement actionnables dans les 10 prochains jours**
et tu produces un livrable ranked dans `working-memory/`, committé sur `main`.

Tu tournes comme une **session Claude Code** (pas un copier-coller chat) :
tu as les outils, tu lis la mémoire en direct, tu écris les fichiers et tu
pushes toi-même. Suis les étapes dans l'ordre.

---

## Règle d'or — le livrable est un mail, pas un rapport machine

Sylvain (et Isa) lisent ça dans la boîte Gmail. Ça doit se lire comme un mail
rédigé par un **excellent assistant humain** : court, décidé, des sorties
évidentes à choisir, rien de robotique.

- **Pas de remplissage.** Si rien d'actionnable dans les 10 jours, dis-le en
  une ligne et stop. On ne force pas une short-list pour faire joli.
- **Zéro back-office visible.** Pas de méta du type « input: stale »,
  « selected: 3 », « fenêtre = 10j », rappel de méthode. Juste les sorties à
  choisir et quoi réserver.
- **Pas de jargon d'IA.** N'écris pas « score », « de-dup », « rank ». Le
  classement se voit dans l'ordre, pas dans un vocabulaire de machine.
- **N'invente jamais** un événement, une date, une météo. Dans le doute :
  « à reconfirmer » ou « météo non vérifiée ».

## Étape 0 — Gardes (avant tout)

1. **Panic** : si le fichier `.panic` existe à la racine du repo, **arrête
   immédiatement** sans rien produire, sans commit. (`test -f .panic`.)
2. **Mode vacances** : lis `core-memory/current-location.md`. Si
   `vacation_mode: true`, cette tâche n'est **pas** `vacation_safe` (cf.
   `schedule.yaml` / `policies.md` — seules `daily_digest`,
   `location_context`, `sliding_window` tournent en vacances). Donc :
   écris un log de skip
   `working-memory/<YYYY-MM-DD-HHMM>-activities_next10days-skip.md`
   (front matter `task: activities_next10days`, `status: skipped`, `reason:
   vacation_mode`), commit + push, et **arrête**.

## Étape 1 — Charger le contexte (lecture directe, pas d'inlining)

Lis ces fichiers maintenant — ils portent le profil, la localisation et
l'OPSEC. Ne réécris jamais une version périmée de mémoire : c'est la source.

- `core-memory/family.md` — Isa, les 3 enfants (âges, contraintes pratiques
  sieste / fatigue / compatibilité sorties), échéances famille proches.
- `core-memory/current-location.md` — zone géo active (Bois-le-Roi ou autre),
  dates de présence, rayon de déplacement effectif.
- `core-memory/profile.md` — profil Sylvain (goûts, style, ce qui vaut le
  détour, ce qui ne vaut pas).
- `core-memory/policies.md` — OPSEC, validation humaine, budget.

**Style** (cf. `CLAUDE.md`) : direct, dense, decisif, ton "bro", FR informel.
Tu tranches — c'est toute la valeur de cette tâche : une short-list ranked,
pas un buffet. Pas de sycophantie, pas de paragraphe d'intro inutile.
"Je ne sais pas" plutôt que bullshit.

## Étape 2 — Mission (sélection ranked)

### Source — dernier rapport local_activities

Cherche le fichier `local_activities` le plus récent dans `working-memory/` :

```bash
ls -t working-memory/*-local_activities.md 2>/dev/null | head -1
```

Lis-le. Si aucun fichier n'existe ou si le plus récent date de **plus de
30 jours**, note-le dans le livrable (`input: none` ou `input: stale`) et
écris dans la section Notes : "Liste source absente ou obsolète (>30j) —
relancer `/local_activities` pour régénérer." Tu produis quand même le
fichier working-memory (status: no_input ou status: stale_input) et tu
commites + pushes normalement.

### Fenêtre temporelle

Calcule la fenêtre : **aujourd'hui → aujourd'hui + 10 jours** (inclus).

### Filtre & rank

Pour chaque entrée de la liste source :

1. **Filtre date** : retiens uniquement ce qui tombe dans les 10 jours.
2. **Filtre contraintes** :
   - Trajet ≤ 1h15 depuis la zone géo lue dans `current-location.md`
     (défaut = Bois-le-Roi 77).
   - Compatibilité enfants si sortie famille : sieste du petit (~2 ans
     l'après-midi), fatigue cadet, logistique poussette.
   - Filtres durs déjà censés être appliqués par `local_activities` mais
     à re-vérifier : pas de brocantes lambda, randos FB, spectacles
     tout-petits bas de gamme, tourist traps, networking corporate creux.
3. **Météo** : si WebSearch est disponible, récupère une prévision
   Météo-France (ou service crédible) pour la zone et la fenêtre. Intègre
   au raisonnement : plein air sous pluie battante → bascule sur option
   couverte. **Cite la source.** Si météo non accessible, écris
   explicitement "météo non vérifiée".
4. **Rank** : valeur perçue × dispo × urgence résa. Sors **3 à 5 entrées**
   maximum, dans l'ordre de priorité.

**Si rien dans la liste ne tombe dans les 10j** : écris explicitement
"Aucune entrée actionnable dans la fenêtre — voir directement la liste
mensuelle pour les semaines suivantes." Pas de remplissage.

### Décisions à trancher explicitement

- La meilleure entrée **famille** du weekend (si du contenu existe).
- La meilleure entrée **Sylvain + Isa** (si du contenu existe).
- La meilleure entrée **Sylvain solo** (si du contenu existe).

Si une case est vide faute d'options, dis-le en une ligne.

### Note sur l'agenda calendar

La routine n'a pas de connecteur Google Calendar actif. Si un conflit
calendrier est détectable via le contexte mémoire (ex. `family.md` ou
`current-location.md`), signale-le. Sinon, mentionne : "agenda non vérifié
— à croiser manuellement avant résa."

## Étape 3 — Écrire le livrable dans working-memory

Écris `working-memory/<YYYY-MM-DD-HHMM>-activities_next10days.md` (HHMM = UTC).
Front matter standard :

```yaml
---
task: activities_next10days
run_at: <YYYY-MM-DDTHH:MM:SS+00:00>
status: completed
---
```

Puis les sections suivantes :

### À résa cette semaine (si applicable)
- **<événement>** — <date> — résa avant <date> sur <lien>

### Top sélection (ranked)

1. **<titre>** — <date> — <lieu>
   - Pour qui : famille / Sylvain+Isa / Sylvain solo
   - Trajet : ~<X> min, <mode>
   - Pourquoi celle-là (vs les autres de la liste) : <1-2 lignes>
   - Logistique : <horaire conseillé, contraintes>
   - Lien : <url>

2. ... (jusqu'à 5)

### Météo
<résumé 2 lignes des conditions attendues sur la fenêtre, source citée,
ou "non vérifiée">

### Notes
- Activités de la liste source **clairement à reporter** (météo, conflit,
  délai dépassé) : signaler brièvement.
- Agenda calendar : vérification manuelle recommandée ou conflit détecté.
- Si liste source absente / obsolète : instruction de relancer
  `/local_activities`.

Densité cible : **300-600 mots**, dense pas verbeux. Pas de paragraphes
d'intro inutiles.

## Étape 4 — Findings (mémoire long terme)

0 à 3 entrées qui méritent de survivre à la purge 30j. Pour cette veille,
les findings sont rares (activités ponctuelles ≠ mémoire long terme) —
retenir uniquement si une découverte a une valeur récurrente (ex. nouveau
lieu ou format à tester régulièrement avec la famille). Avant d'ajouter :
**de-dup** — `grep` le titre/lieu dans `digests/findings.md` ; si déjà
présent récemment, skip. Pour chaque entrée retenue, **appende** à
`digests/findings.md` au format :

```
### <YYYY-MM-DD> — <titre court>
**Tags** : activities, famille, <…>
**Source** : activities_next10days
**Lien** : <url>
**Pourquoi ça compte** : <2-3 lignes>
**Suite** : <action attendue, ou "info pure">
```

Si rien ne mérite l'archive, ne touche pas à `findings.md`.

## Étape 5 — Commit + push

OPSEC avant commit : aucune adresse précise de domicile, info enfant
nominative, ni donnée patrimoniale dans le livrable (cf. `policies.md`).

```bash
git add working-memory/ digests/findings.md
git commit -m "auto: activities_next10days run <YYYY-MM-DDTHH:MM:SSZ>"
git push origin main   # retry x4 backoff 2/4/8/16s si erreur réseau
```

Ne push jamais en `--force`. Si rien n'a été produit (cas skip déjà géré en
étape 0), ne crée pas de commit vide.

## Étape 6 — Envoi email (automatique, hors routine)

Tu n'as **rien à faire ici**. L'envoi du rapport par mail est géré par la
GitHub Action `.github/workflows/mail-report.yml`, qui se déclenche toute
seule quand ton rapport `working-memory/…-<task>.md` arrive sur `main`
(étape 5). Elle lit le fichier et l'envoie en SMTP depuis l'infra GHA, où le
SMTP fonctionne — contrairement au sandbox de la routine, qui ne peut sortir
qu'en HTTPS/443.

Donc : assure-toi juste que l'étape 5 a bien **push le rapport sur `main`**.
Si l'étape 0 a skip le run, aucun rapport n'est poussé → aucun mail (normal).
