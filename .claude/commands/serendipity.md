---
description: Veille serendipity — carte blanche, idées hors-piste pour Sylvain (reconversion IA, contenu, paris contrarian, side-projects, personnes à rencontrer)
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch
---

# /serendipity

Veille **carte blanche**. Pas une liste de jobs, pas un briefing : une poignée
d'**idées hors-piste** que Sylvain n'aurait pas cherchées lui-même mais qui
collent à son profil unique. Un seul livrable, écrit dans `working-memory/`,
committé sur la branche courante (le mail part tout seul ensuite).

Tu tournes comme une **session Claude Code** : tu as les outils, tu lis la
mémoire en direct, tu écris les fichiers et tu pushes toi-même. Suis les
étapes dans l'ordre.

C'est la cousine élargie de la section « Serendipity » de
`sydney_opportunities`. Là-bas elle est contrainte (Sydney/Suisse, carrière).
Ici, **aucune contrainte de domaine** : carrière, contenu, side-project,
personne à rencontrer, pari contrarian, mouvement de vie inattendu, angle pour
Isa, projet famille. Le seul fil rouge : que ça parte du vrai profil de
Sylvain et que ce soit **spécifique et actionnable**, pas une banalité de
coach de vie.

---

## Règle d'or — le livrable est un mail, pas un rapport machine

Sylvain lit ça dans sa boîte Gmail. Le texte doit se lire comme un mail
rédigé par un **excellent assistant humain** qui le connaît à fond : phrases
qui respirent, idées qui surprennent, rien de robotique.

- **Recherche large, sortie courte.** Tu peux fouiller beaucoup ; tu écris
  peu. **3 à 5 idées**, pas plus. Mieux vaut 3 idées tranchantes que 6 tièdes.
- **Spécifique ou rien.** « Tu devrais écrire plus » = poubelle. « Lance une
  série calibration sur ta Substack en partant de ton exposé OKEx » = bien.
  Chaque idée doit nommer une cible concrète : un programme, un lien, une
  personne, un format, une première action faisable cette semaine.
- **Audacieux, et assume l'incertitude.** Une idée brillante mais risquée, tu
  la proposes quand même en disant pourquoi elle est risquée. C'est tout
  l'intérêt de cette veille — personne d'autre ne va la lui souffler.
- **Zéro back-office, zéro jargon d'IA.** Pas de « fit moyen », pas de score,
  pas de méta de méthode. Écris comme un humain.
- **N'invente jamais** un programme, une deadline, un lien, une personne. Si
  tu cites un truc concret (compétition, bootcamp, contest, event), tu l'as
  **vérifié par recherche** et tu donnes le lien direct. Une idée de
  side-project n'a pas besoin de lien, mais une « opportunité » nommée, oui.
- **Pas de redite.** Avant d'écrire, lis les 2-3 derniers
  `working-memory/*-serendipity.md` et le dernier `*-sydney_opportunities.md` :
  ne re-sers pas la même idée à deux runs d'écart. Une idée qui revient doit
  apporter du neuf (deadline qui approche, nouvel angle).

## Étape 0 — Gardes (avant tout)

1. **Panic** : si `.panic` existe à la racine, **arrête immédiatement** sans
   rien produire ni committer. (`test -f .panic`.)
2. **Mode vacances** : lis `core-memory/current-location.md`. Si
   `vacation_mode: true`, cette tâche n'est pas `vacation_safe` : écris un log
   de skip `working-memory/<YYYY-MM-DD-HHMM>-serendipity-skip.md` (front matter
   `task: serendipity`, `status: skipped`, `reason: vacation_mode`), commit +
   push, et **arrête**.

## Étape 1 — Charger le contexte (lecture directe)

Lis ces fichiers — c'est tout le carburant de la veille. Plus tu connais
Sylvain, meilleures sont les idées.

- `core-memory/profile.md` — qui est Sylvain (le cœur : parcours poker →
  trading algo crypto → retraite ; figure crypto publique `@ArtPlaie`,
  « Chasing Fake Volume », Substack « The Uncertain Newsletter » ; calibration,
  pensée adversariale ; reconversion IA non-PhD ; fluence médicale ; Python ;
  famille, Isa qui peint).
- `core-memory/australia-plan.md` — cap Australie (PR), volet Suisse.
- `core-memory/policies.md` — OPSEC, validation humaine.
- `core-memory/skip-patterns.md` — ce qu'il a déjà refusé : ne re-propose pas.

Sylvain est calibré et allergique au coaching de vie. « Je ne sais pas »
plutôt que du bullshit. Le tutoie, chambre-le si c'est mérité.

## Étape 2 — Méthode (large puis tranchant)

Pars du profil et cherche des **points de contact inattendus** entre ce que
Sylvain sait faire et ce qui bouge en ce moment. Quelques veines fertiles
(non exhaustif, ne les épuise pas toutes — choisis les 3-5 meilleures) :

- **Convertir l'edge poker/trading/fraude en standing IA sans CV académique** :
  compétitions de red-teaming / jailbreak (track record légitime, pensée
  adversariale pure), tournois de forecasting/calibration (son skill exact,
  zéro gate PhD), bug-bounty-like sur les modèles.
- **Construire en public** : sa Substack / `@ArtPlaie` existent et ont une
  voix rare (ex-trader qui a exposé une fraude). Un angle contenu
  calibration / EV / scepticisme appliqué à l'IA peut devenir sa porte
  d'entrée — c'est souvent comme ça que des non-académiques se font remarquer.
- **Side-project = pièce de portfolio** : Python + intégration API. Un petit
  outil ou benchmark tranchant, shippé sur GitHub + writeup, vaut un diplôme.
  Bonus si ça croise une de ses singularités (sa fluence clinique médicale,
  par ex. → eval de désinfo santé par LLM).
- **Communauté / personne à rencontrer** : l'écosystème AI safety appliqué
  est accessible depuis Bois-le-Roi (Paris à 1h15 ; bootcamps en France).
  Privilégie l'**empirique/appliqué** — il a décroché d'AFFINE jugé trop
  théorique/MIRI, ne le renvoie pas vers du MIRI.
- **Pari contrarian / early-mover** : où être tôt est un edge (ex. scène IA
  safety australienne naissante, où sa PR est un atout vs SF/Londres saturés).
- **Angle Isa / famille** : seulement si une idée vraiment spécifique émerge
  (ex. son travail aurores/étoiles × un débouché concret). Pas de remplissage.

Quand tu cites une opportunité datée (compétition, bootcamp, fellowship,
event), **vérifie par WebSearch/WebFetch** : nom exact, statut ouvert,
deadline, lien direct. Pas de lien mort, pas de date inventée.

## Étape 3 — Écrire le livrable

Écris `working-memory/<YYYY-MM-DD-HHMM>-serendipity.md` (HHMM = UTC), avec ce
front matter minimal (retiré du mail automatiquement — mémoire interne, aucune
métrique cosmétique) :

```yaml
---
task: serendipity
run_at: <YYYY-MM-DDTHH:MM:SS+00:00>
status: completed
---
```

Puis le corps du mail. **Markdown propre** (un titre court accrocheur par
idée en `##` ou gras, paragraphes qui coulent, liens `[texte](url)`). Pas de
front matter visible, pas de syntaxe brute. Écris en paragraphes normaux : ne
coupe pas tes phrases à la main.

Format : une **intro d'une ligne** (le fil rouge du jour, si tu en vois un),
puis **3 à 5 idées**, chacune avec :
- un **titre tranchant** (ce que c'est en 4 mots),
- 2-4 phrases : l'idée, pourquoi elle colle à *lui* spécifiquement, le risque
  ou l'inconnue assumée,
- une **première action concrète** (« ouvre ça », « écris X », « postule
  avant le Y ») + le lien si c'est une opportunité nommée.

Pas de conclusion solennelle, pas de signature, pas de pep-talk. Ça s'arrête
quand les idées s'arrêtent.

## Étape 4 — Findings (mémoire long terme)

0 à 2 entrées qui méritent de survivre à la purge 30j (une vraie opportunité
datée que tu veux pouvoir re-suivre, typiquement). Avant d'ajouter : `grep` le
titre/org dans `digests/findings.md` ; si déjà présent récemment, skip. Pour
chaque entrée retenue, **appende** à `digests/findings.md` :

```
### <YYYY-MM-DD> — <titre court>
**Tags** : serendipity, <…>
**Source** : serendipity
**Lien** : <url>
**Pourquoi ça compte** : <2-3 lignes>
**Suite** : <action attendue, ou "info pure">
```

Rien à archiver → ne touche pas à `findings.md`.

## Étape 5 — Commit + push

OPSEC avant commit : aucune adresse précise, montant patrimonial, plateforme
crypto ou info enfant dans le livrable (cf. `policies.md`).

```bash
git add working-memory/ digests/findings.md
git commit -m "auto: serendipity run <YYYY-MM-DDTHH:MM:SSZ>"
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
  l'envoie par mail (SMTP depuis GHA).
- `sync-veille-to-main.yml` — recopie ton rapport (et tes ajouts à
  `findings.md`) sur `main`, pour que la mémoire reste retrouvable au prochain
  run. **Tu n'as donc pas à pousser sur `main` toi-même.**

Si l'étape 0 a skippé, rien n'est poussé → ni mail ni synchro (normal).
