---
description: Veille Sydney + Suisse — reconversion IA (jobs, formations, invest/cofounding, wildcard carrière) — routine hebdo
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch
---

# /sydney_opportunities

Veille **Sydney + Suisse** pour un profil **en reconversion vers l'IA** :
jobs IA, formations, invest/cofounding, wildcard carrière. Un seul livrable, écrit
dans `working-memory/`, committé sur `main` (le mail part tout seul ensuite).

Tu tournes comme une **session Claude Code** : tu as les outils, tu lis la
mémoire en direct, tu écris les fichiers et tu pushes toi-même. Suis les
étapes dans l'ordre.

---

## Règle d'or — le livrable est un mail, pas un rapport machine

Sylvain lit ça dans sa boîte Gmail. Le texte doit se lire comme un mail
rédigé par un **excellent assistant humain** : phrases qui respirent,
sections évidentes, rien de robotique.

- **Recherche large, sortie courte.** Fouille *vraiment* beaucoup : multiplie
  les requêtes WebSearch (angles, synonymes, orgs et sources différentes) pour
  ramasser au moins **2× plus de candidats bruts** que ce que tu garderas — tu
  veux du **choix** avant de trier, pas trois liens trouvés vite fait. Le tri
  reste impitoyable et la sortie courte ; c'est l'amont qui s'élargit, pas le
  mail.
- **Pas de minimum, pas de remplissage.** Si une section n'a rien de solide,
  tu le dis en **une demi-ligne en français** (« Rien de fort côté jobs cette
  semaine. ») ou tu l'omets. Jamais de listing pour faire du volume.
- **Zéro back-office visible.** Pas de méta du type « window = 7 jours »,
  « filtre dur appliqué », « jobs_ia: 6 », rappels de contexte, justification
  de méthode. Sylvain s'en fout. Il veut **les résultats**, point.
- **Pas de jargon d'IA.** N'écris pas « fit faible/moyen/fort », « source
  primaire obligatoire », « de-dup ». Écris comme un humain : « ça colle
  bien », « à creuser », « bof ».
- **N'invente jamais** un poste, une formation, un lien. Si un opening est
  douteux, dis « à reconfirmer » et donne le lien. Pas de lien mort.

## Étape 0 — Gardes (avant tout)

1. **Panic** : si `.panic` existe à la racine, **arrête immédiatement** sans
   rien produire ni committer. (`test -f .panic`.)
2. **Mode vacances** : lis `core-memory/current-location.md`. Si
   `vacation_mode: true`, cette tâche n'est pas `vacation_safe` : écris un log
   de skip `working-memory/<YYYY-MM-DD-HHMM>-sydney_opportunities-skip.md`
   (front matter `task: sydney_opportunities`, `status: skipped`, `reason:
   vacation_mode`), commit + push, et **arrête**.

## Étape 1 — Charger le contexte (lecture directe)

Lis ces fichiers — ils portent le profil, le plan et l'OPSEC. Ne réécris
jamais une version périmée : c'est la source.

- `core-memory/profile.md` — qui est Sylvain.
- `core-memory/australia-plan.md` — statut PR, horizon, ville cible, ce qu'on
  cherche / pas, contraintes famille, volet Suisse secondaire.
- `core-memory/policies.md` — OPSEC, validation humaine, budget.
- `core-memory/skip-patterns.md` — patterns déjà refusés.

Sylvain est calibré : ne réexplique pas le système visa AU ni l'écosystème
AI Safety. « Je ne sais pas » plutôt que du bullshit.

## Étape 2 — Qui est la cible (lis ça avant de chercher)

Sylvain **n'a jamais eu de job salarié** : poker pro puis trading algo crypto,
puis retraite anticipée. Il se reconvertit vers l'IA depuis un profil quanti
non-PhD (calibration sous incertitude, pensée adversariale, Python, macro).
Ça change radicalement ce qu'on remonte :

- **On vise le junior iconoclaste et le strong fit, pas le senior.** Il ne va
  pas diriger un département ni décrocher un rôle qui exige 10 ans
  d'expérience salariée. Inutile de lui dire « rien de senior ouvert » — il
  n'en veut pas. Ce qu'on cherche : des portes d'entrée atypiques où son
  background compte plus qu'un CV linéaire (AI safety appliqué, eval,
  red-teaming, research engineering, policy/comms IA, residencies, rôles de
  fondateur/early dans des boîtes IA).
- **Strong fit uniquement.** Si tu hésites sur le fit, ne le mets pas. Pas de
  « fit faible/moyen ». Pas de poste d'exécutant générique. Pas de listing qui
  exige la citoyenneté AU (il a la **PR**, pas la nationalité) ou qui est
  expiré — ne les liste même pas pour « contexte ».
- **Filtre trading, silencieux.** Ne construis pas la recherche autour du
  trading, et ne propose aucun rôle pur trading / market making / quant /
  hedge fund. Mais n'écris **nulle part** que tu filtres ça — c'est juste
  hors-cible, on n'en parle pas.

Window : openings publiés dans les ~7 derniers jours, plus tout listing dont
la **deadline n'est pas passée** même s'il est plus ancien. Cite chaque entrée
avec un **lien direct** (WebSearch/WebFetch).

**Volume de recherche** : pour chaque section (jobs, formations, invest,
serendipity), lance **plusieurs** requêtes WebSearch sous des angles différents
— mots-clés variés, noms d'orgs ciblées, job boards, synonymes EN/FR — et
constitue un vivier d'au moins **2× plus de candidats** que ce que tu
retiendras. Tu tries ensuite (strong fit only) ; mais d'abord tu ramasses large
pour avoir le choix. Mieux vaut sur-chercher et jeter que passer à côté d'une
porte d'entrée atypique.

## Étape 3 — Écrire le livrable

Écris `working-memory/<YYYY-MM-DD-HHMM>-sydney_opportunities.md` (HHMM = UTC),
avec ce front matter minimal (il sera retiré du mail automatiquement, c'est de
la mémoire interne — n'y mets aucune métrique cosmétique) :

```yaml
---
task: sydney_opportunities
run_at: <YYYY-MM-DDTHH:MM:SS+00:00>
status: completed
---
```

Puis le corps du mail. **Markdown propre** (titres `##`, gras `**` pour les
noms d'org, listes simples, liens `[texte](url)`) — il sera rendu en vrai mail
formaté. Écris en paragraphes normaux : **ne coupe pas tes phrases à la main**
au milieu (pas de retour ligne tous les 76 caractères).

Structure, dans cet ordre, en ne gardant que ce qui a de la matière :

1. **Jobs IA — Sydney + Suisse.** Seulement les strong fit / portes d'entrée
   iconoclastes (cf. étape 2). Pour chacun : titre · **org** · lien · une
   phrase sur l'angle de reconversion + le risque. Rien de fort → une
   demi-ligne (« Rien qui colle vraiment cette semaine. ») et on passe.
2. **Formations IA.** Sessions ouvertes avec **deadline** : MATS, ARENA, AI
   Safety Fundamentals (BlueDot), fellowships (Anthropic, GovAI, Apollo,
   Redwood…), residencies, programmes ETH/EPFL, bootcamps sérieux. Pour
   chacune : nom · lien · format · deadline · une phrase (pourquoi c'est pour
   lui). C'est souvent la section la plus actionnable — soigne-la.
3. **Invest / cofounding.** Boîtes qui cherchent un cofounder technique/quant,
   deals angel/syndicates, EF / YC / accélérateurs APAC-EU, incubateurs AI
   safety. Si un site vaut d'être fouillé pour de vraies idées, **fouille-le**.
   Pour chacun : nom · lien · ce qui est cherché · une phrase. Rien → une ligne.
4. **Wildcard carrière.** 1-3 idées **hors-piste**, créativité max. Projet perso,
   side-project, angle de contenu, personne à rencontrer, pari contrarian,
   mouvement de carrière inattendu. Sers-toi de tout le profil (ex-trader algo
   crypto, calibration, pensée adversariale, figure crypto FR `@ArtPlaie`, cap
   Australie, famille). Audacieux et **spécifique**. Assume l'incertitude :
   une idée brillante mais risquée, tu la dis et tu la proposes quand même.
   C'est la seule section qui doit **toujours** sortir quelque chose.
5. **PR & travel facility** — **uniquement** s'il y a du neuf qui touche
   directement le **renouvellement de sa PR / Resident Return Visa**. Pas de
   news générales d'immigration australienne, pas de processing times de
   visas qui ne le concernent pas : il s'en fout. Rien de précis sur sa
   fenêtre → omets la section entièrement.

Optionnel, seulement si vraiment substantiel pour la décision famille (immo
locatif Sydney, écoles internationales, scène galeries pour Isa) : une ou deux
lignes max. Dans le doute, coupe.

Termine par, **si et seulement si** un job ou une formation a un fit fort + une
deadline proche : un court **« Si tu veux y aller »** — l'angle en quelques
puces (arguments + risque, pas de lettre de motivation). Avant : check
`core-memory/skip-patterns.md`, si pattern proche n'insiste pas. Pas de draft
ni d'envoi auto : Sylvain décide.

## Étape 4 — Findings (mémoire long terme)

0 à 3 entrées qui méritent de survivre à la purge 30j. Avant d'ajouter :
`grep` le titre/org dans `digests/findings.md` ; si déjà présent récemment,
skip. Pour chaque entrée retenue, **appende** à `digests/findings.md` :

```
### <YYYY-MM-DD> — <titre court>
**Tags** : sydney, <…>
**Source** : sydney_opportunities
**Lien** : <url>
**Pourquoi ça compte** : <2-3 lignes>
**Suite** : <action attendue, ou "info pure">
```

Rien à archiver → ne touche pas à `findings.md`.

## Étape 5 — Commit + push

OPSEC avant commit : aucune adresse précise, montant, plateforme crypto ou
info enfant dans le livrable (cf. `policies.md`).

```bash
git add working-memory/ digests/findings.md
git commit -m "auto: sydney_opportunities run <YYYY-MM-DDTHH:MM:SSZ>"
# Pousse simplement sur ta branche courante. Tu n'as PAS à atteindre `main`
# toi-même (le proxy te l'interdit souvent) : deux GHA sur l'infra GitHub s'en
# chargent — mail + synchro du rapport sur `main` (cf. étape 6).
git push -u origin HEAD   # retry x4 backoff 2/4/8/16s si erreur réseau
```

**Ne te bats jamais pour `main`, ne demande aucune confirmation de branche** :
le push ci-dessus suffit, où qu'il aboutisse. Jamais de `--force`. Si l'étape 0
a skippé, pas de commit vide.

## Étape 6 — Envoi email (automatique, hors routine)

Tu n'as **rien à faire ici** une fois le rapport poussé (étape 5). Deux GitHub
Actions tournent sur l'infra GitHub (aucun proxy → elles atteignent `main` sans
souci) dès que ton rapport arrive sur ta branche `claude/**` :

- `mail-report.yml` — retire le front matter, rend le markdown en HTML et
  l'envoie par mail (SMTP depuis GHA ; le sandbox de la routine ne sort qu'en
  HTTPS/443).
- `sync-veille-to-main.yml` — recopie ton rapport (et tes ajouts à
  `findings.md`) sur `main`, pour que la mémoire reste retrouvable au prochain
  run. **Tu n'as donc pas à pousser sur `main` toi-même.**

Si l'étape 0 a skippé, rien n'est poussé → ni mail ni synchro (normal).
