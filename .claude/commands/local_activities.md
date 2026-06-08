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
  lecteur non-fiction, Magic/Dominion, profil quanti).
- `core-memory/family.md` — Isa (peintre, astro/lumière), 3 enfants (~2, ~5,
  ~8 ans), contraintes logistiques famille.
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

**Zone géo** : déduite de `core-memory/current-location.md`. Base habituelle
= Bois-le-Roi (77590), rayon 1h15 max porte-à-porte voiture ou RER R. Paris
intra-muros accessible mais pas le défaut — le 77/91/78/Orléanais/89/51 ouest
sont OK aussi. Si Sylvain est ailleurs, adapte la zone en conséquence.

**Filtre dur global** : pas de brocantes lambda, pas de randos Facebook sans
encadrement crédible, pas de spectacles enfants bas de gamme (princesses Disney
en mall), pas d'ateliers loisirs créatifs sans dimension artistique réelle, pas
de networking corporate creux, pas de tourist traps, pas d'escape games
commerciaux. Toute entrée de ce type est un échec de filtre.

Quatre sections obligatoires, dans cet ordre :

### A. Famille / nature / plein air

Sorties compatibles 3 enfants (~2 à ~8 ans). Critères :
- Trajet ≤ 1h15.
- Quelque chose pour le petit (parc, espace ouvert, possibilité poussette).
- Quelque chose pour l'aîné (curiosité, jeu d'observation, mini-défi).
- Logistique faisable (parking, accès, toilettes/change, restau ou pique-nique).

Cibles canoniques à scanner via web search :
- Fermes pédagogiques 77/91, vergers cueillette saison, événements
  ONF/réserves naturelles (Fontainebleau, Chamarande, vallée du Loing).
- Châteaux famille avec parc (Fontainebleau, Vaux-le-Vicomte, Champs-sur-Marne,
  Courances).
- Événements parcs régionaux (Gâtinais, Vexin, Oise-Pays-de-France).
- Festivals plein air famille de qualité (filtre : pas les fêtes médiévales
  clichées sauf si vraiment notable).

### B. Art / culture (Isa-friendly)

Critères : expos/galeries/ateliers/spectacles de qualité, compatibles avec les
goûts d'Isa (peinture contemporaine et figurative, thèmes astro/nature/lumière
en bonus), accessibles en demi-journée pour Sylvain+Isa avec ou sans enfants.

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
bloquer à l'avance dans le calendrier (ex : "Festival ciné plein air 12-14
juin au Domaine de Chamarande", "Nuit des étoiles 9 août au Bois de Vincennes").

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
window: <YYYY-MM-DD> → <YYYY-MM-DD>
items_kept: <n>
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

Densité cible : **8-15 entrées totales** sur les 4 catégories. Pas plus
(sinon c'est du remplissage).

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
