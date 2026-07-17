---
description: Veille sorties/activités locales famille (Île-de-France, rayon 1h15) — routine mensuelle
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch
---

# /local_activities

Run de la veille `local_activities` : agenda du mois à venir pour la famille
Ribes — sorties nature/famille, culture/art (Isa-friendly), intellectuel
(Sylvain-friendly), et bonus weekends bloquables. Rayon 1h15 depuis la base
actuelle lue dans `current-location.md`.

Tu tournes comme une **session Claude Code** (pas un copier-coller chat) :
tu as les outils, tu lis la mémoire en direct, tu écris les fichiers et tu
pushes toi-même. Suis les étapes dans l'ordre.

---

## Règle d'or — le livrable est un mail, pas un rapport machine

Sylvain (et Isa) lisent ça dans la boîte Gmail. Ça doit se lire comme un mail
rédigé par un **excellent assistant humain** : phrases qui respirent, sections
évidentes, rien de robotique.

- **Recherche large, sortie courte.** Fouille *vraiment* beaucoup : multiplie
  les requêtes WebSearch (angles, lieux, sources et agendas différents) pour
  ramasser au moins **2× plus de sorties candidates** que ce que tu garderas —
  tu veux du **choix** avant de trier, pas trois liens trouvés vite fait. Le tri
  reste impitoyable et la sortie courte ; c'est l'amont qui s'élargit, pas le
  mail.
- **Pas de minimum, pas de remplissage.** Si une catégorie n'a rien de solide
  ce mois-ci, dis-le en **une demi-ligne** et passe. Jamais de listing pour
  faire du volume — cinq super sorties valent mieux que quinze médiocres.
- **Zéro back-office visible.** Pas de méta du type « fenêtre = 4-6 semaines »,
  « filtre appliqué », « items_kept: 12 », rappel de méthode. On veut les
  sorties, pas le making-of.
- **Pas de jargon d'IA.** N'écris pas « score », « de-dup », « fit ». Écris
  humain. Le tri et les filtres restent **internes** — ils ne s'écrivent pas
  dans le mail.
- **N'invente jamais** un événement, une date, un lieu. Dans le doute : « à
  reconfirmer sur le site » + le lien.

## Étape 0 — Gardes (avant tout)

1. **Panic** : si le fichier `.panic` existe à la racine du repo, **arrête
   immédiatement** sans rien produire, sans commit. (`test -f .panic`.)
2. **Mode vacances** : lis `core-memory/current-location.md`. Si
   `vacation_mode: true`, cette tâche n'est **pas** `vacation_safe` (cf.
   `schedule.yaml` / `policies.md`). Donc : écris un log de skip
   `working-memory/<YYYY-MM-DD-HHMM>-local_activities-skip.md`
   (front matter `task: local_activities`, `status: skipped`, `reason:
   vacation_mode`), commit + push, et **arrête**.

## Étape 1 — Charger le contexte (lecture directe, pas d'inlining)

Lis ces fichiers maintenant — ils portent le profil, la famille et l'OPSEC.
Ne réécris jamais une version périmée de mémoire : c'est la source.

- `core-memory/profile.md` — qui est Sylvain (intello, retraité trading algo,
  lecteur non-fiction, profil quanti).
- `core-memory/family.md` — Isa (peintre, astro/lumière), 3 enfants : Anna (8),
  Tristan (5), César (20 mois), contraintes logistiques famille.
- `core-memory/current-location.md` — **où est Sylvain** : c'est de là que
  tu déduis la zone géo et le rayon des sorties. Déjà lu en étape 0.
- `core-memory/policies.md` — OPSEC, validation humaine, budget.

**Style** (cf. `CLAUDE.md`) : direct, dense, evidence-based, ton "bro" utile
pour la famille, FR informel, pas de sycophantie, pas de persona. Sylvain et
Isa sont calibrés culturellement : ne réexplique pas ce qu'est une expo
Pompidou ou une Nuit Blanche. "Je ne sais pas" plutôt que bullshit. Si une
date est ambiguë sur le site officiel, marque-le.

## Étape 2 — Mission (web search systématique)

Active **WebSearch** et **WebFetch**. Cite chaque entrée avec un **lien
direct vers la page officielle** (pas l'agrégateur). Window = aujourd'hui →
fin du mois suivant (~4-6 semaines). Mentionne brièvement un événement M+2
si la résa doit se faire maintenant.

**Volume de recherche** : pour chaque catégorie (famille/nature, art/culture,
intellectuel, weekends), scanne **chaque cible canonique individuellement** et
ajoute des angles (agendas locaux, sites des lieux, « que faire à … ce mois-ci »,
programmations saison). Constitue un vivier d'au moins **2× plus de sorties
candidates** que ce que tu retiendras, puis tri impitoyable (5 super > 15
médiocres). D'abord ramasser large pour avoir le choix, ensuite couper.

**Zone géo** : déduite de `core-memory/current-location.md`. Base habituelle
= Bois-le-Roi (77590), rayon 1h15 max porte-à-porte voiture ou RER R.
**Priorité au 77 local** (Fontainebleau, vallée du Loing, Brie) — creuse-le en
premier et à fond avant d'aller chercher à Paris, qui n'est plus le réflexe
par défaut. 91/78/Orléanais/89/51 ouest en complément si le 77 est sec ce
mois-ci. Si Sylvain est ailleurs, adapte la zone en conséquence.

**Filtre dur global** : pas de brocantes lambda, pas de randos Facebook sans
encadrement crédible, pas de spectacles enfants bas de gamme (princesses Disney
en mall), pas d'ateliers loisirs créatifs sans dimension artistique réelle, pas
de networking corporate creux, pas de tourist traps, pas d'escape games
commerciaux, pas de cueillette (vergers, fermes à cueillette — Sylvain s'en
fout, ne plus en proposer), pas d'événements famille en soirée type ciné plein
air (les gosses sont fracassés le lendemain scolaire — inenvisageable sauf si
vraiment extraordinaire). Toute entrée de ce type est un échec de filtre.

Quatre sections obligatoires, dans cet ordre :

### A. Famille / nature / plein air

Sorties compatibles 3 enfants (~2 à ~8 ans). Critères :
- Trajet ≤ 1h15.
- Quelque chose pour le petit (parc, espace ouvert, possibilité poussette).
- Quelque chose pour l'aînée (curiosité, jeu d'observation, mini-défi).
- Logistique faisable (parking, accès, toilettes/change, restau ou pique-nique).

Cibles canoniques à scanner via web search :
- Fermes pédagogiques 77/91, événements ONF/réserves naturelles
  (Fontainebleau, Chamarande, vallée du Loing). Pas de cueillette (cf. filtre
  dur global).
- Châteaux famille avec parc (Fontainebleau, Vaux-le-Vicomte, Champs-sur-Marne,
  Courances).
- Événements parcs régionaux (Gâtinais, Vexin, Oise-Pays-de-France).
- Festivals plein air famille de qualité (filtre : pas les fêtes médiévales
  clichées sauf si vraiment notable).

### B. Art / culture (Isa-friendly)

Critères : expos/galeries/ateliers/spectacles de qualité, compatibles avec les
goûts d'Isa (peinture contemporaine et figurative, thèmes astro/nature/lumière
en bonus), accessibles en demi-journée pour Sylvain+Isa avec ou sans enfants.
**Barre spécifique Paris** : une expo à Paris ne se propose que si elle est
vraiment unique/événementielle (rétrospective majeure, artiste rare,
exclusivité) — jamais une expo de plus juste parce qu'elle existe, ça fait du
bruit pour rien. Le régional (77/91/78) n'a pas cette contrainte de rareté.

Cibles canoniques à scanner :
- Expos majeures Paris (Pompidou, Orsay, Louvre, Jeu de Paume, MAM, Petit
  Palais, Pinault Bourse, LV Foundation).
- Centres d'art régionaux 77/91/78 (Versailles, FRAC IDF, Domaine de
  Chamarande, CAC Brétigny).
- Galeries exposant un artiste sur le thème astro/aurores/lumière/paysage.
- Spectacles vivants substantiels (théâtre, danse contemporaine, musique) Paris
  et région.
- Ateliers d'artiste / portes ouvertes (parcours Marais, Belleville, Montreuil
  — date variable).

### C. Intellectuel (Sylvain-friendly)

Critères : conférences, meetups, salons, événements scientifiques/culturels
substantiels. Format adulte, soirée ou journée sans enfants.

Cibles canoniques à scanner :
- Conférences scientifiques publiques (Collège de France, Cité des Sciences,
  IHES Bures, ENS, IHP).
- Meetups AI/data/tech à Paris (Station F, Hugging Face events, AI4Good,
  Effective Altruism Paris, French Center for AI Safety, CeSIA).
- Salons/festivals d'idées (Festival Mode d'Emploi, USI Conf, Inria, etc.).
- Conférences finance/crypto si signal fort (rare — filtre haut).
- Événements philo/histoire/sciences humaines de qualité (Forum Philosophique
  Le Monde, Banquet du Livre, etc.).

### D. Bonus — événements weekend famille élargie

1-3 événements **datés sur un weekend précis du mois** que Sylvain peut
bloquer à l'avance dans le calendrier (ex : "Journées du Patrimoine 19-20
septembre au Château de Vaux-le-Vicomte", "Fête de la nature 23-24 mai en
forêt de Fontainebleau"). Pas d'événements en soirée type ciné plein air (cf.
filtre dur global).

**De-dup par site/lieu** : pas 3 entrées sur Fontainebleau pour un même mois
sauf raisons distinctes.

Si le mois est creux (août, hors saison culturelle), dis-le et ne force pas le
contenu. 5 super entrées > 15 médiocres.

## Étape 3 — Écrire le livrable dans working-memory

Écris `working-memory/<YYYY-MM-DD-HHMM>-local_activities.md` (HHMM = UTC).
Front matter standard :

```yaml
---
task: local_activities
run_at: <YYYY-MM-DDTHH:MM:SS+00:00>
status: completed
---
```

Puis les 4 sections (A, B, C, D). Pour chaque entrée :

```
- **<titre>** — <lieu>, <ville> · <date(s)> · <horaire>
  - Trajet : ~<X> min depuis <base actuelle> (mode : voiture / RER R + …)
  - Public : famille complète / Sylvain+Isa / Sylvain seul / Isa seule
  - Coût : gratuit / €X / variable
  - Lien : <url page officielle>
  - Note : <2-3 lignes — pourquoi ça vaut, ce qu'on évite si on y va>
```

Pas de plancher : autant d'entrées qu'il y a de vraies bonnes options, pas
plus. Cinq super sorties valent mieux que quinze médiocres. Une catégorie vide
ce mois-ci ? Une demi-ligne et on passe.

Termine le fichier par :

```
### Top 3 du mois
<3 entrées avec résa/réservation à faire maintenant sinon ça partira — 1 ligne
chacune avec deadline résa>

### Pour findings.md
<1 entrée si quelque chose mérite l'archive long terme — ex : événement annuel
exceptionnel à mémoriser pour l'an prochain. Sinon : (rien à archiver)>
```

**Garde-fous** : si tu doutes d'une date/lieu → `(à reconfirmer sur le site)`.
N'invente jamais d'événement. OPSEC : pas de noms d'enfants, pas d'adresse
précise, pas d'école dans le livrable.

## Étape 4 — Findings (mémoire long terme)

0 à 1 entrée qui mérite de survivre à la purge 30j (rare pour cette tâche —
typiquement un événement annuel exceptionnel ou un lieu découvert qui mérite
d'être mémorisé). Avant d'ajouter : **de-dup** — `grep` le titre/lieu dans
`digests/findings.md` ; si déjà présent récemment, skip. Pour chaque entrée
retenue, **appende** à `digests/findings.md` au format :

```
### <YYYY-MM-DD> — <titre court>
**Tags** : local, <…>
**Source** : local_activities
**Lien** : <url>
**Pourquoi ça compte** : <2-3 lignes>
**Suite** : <action attendue, ou "info pure — à mémoriser pour l'an prochain">
```

Si rien ne mérite l'archive, ne touche pas à `findings.md`.

## Étape 5 — Commit + push

OPSEC avant commit : aucune adresse précise, nom d'enfant, ni info école dans
le livrable (cf. `policies.md`).

```bash
git add working-memory/ digests/findings.md
git commit -m "auto: local_activities run <YYYY-MM-DDTHH:MM:SSZ>"
# Pousse simplement sur ta branche courante. Tu n'as PAS à atteindre `main`
# toi-même (le proxy te l'interdit souvent) : deux GHA sur l'infra GitHub s'en
# chargent — mail + synchro du rapport sur `main` (cf. étape 6).
git push -u origin HEAD   # retry x4 backoff 2/4/8/16s si erreur réseau
```

**Ne te bats jamais pour `main`, ne demande aucune confirmation de branche, ne
renvoie pas Sylvain lire les onglets Claude Code** : le push ci-dessus suffit,
où qu'il aboutisse. Jamais de `--force`. Si l'étape 0 a skippé, pas de commit
vide.

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
