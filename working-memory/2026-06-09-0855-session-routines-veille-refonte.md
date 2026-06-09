---
task: session-handover
run_at: 2026-06-09T08:55:21+00:00
status: completed
---

# Handover — refonte des veilles : forme « mail humain » + fiabilité mail/mémoire

Session du 2026-06-09. Tout est livré et poussé sur `main` (dernier commit
`224ddd4`). Rien en cours, rien de bloqué. Ce qui suit = contexte pour la
prochaine sesh (Sylvain a dit qu'on rediscutera).

## Ce qui a été fait

### 1. Refonte du contenu/forme des 6 commands de veille
Déclencheur : le rapport `sydney_opportunities` reçu par mail était illisible
(syntaxe markdown brute, front matter visible, retours chariot partout, méta
de back-office, jargon d'IA, contenu hors-cible).

Principes appliqués aux **6** commands (`.claude/commands/*.md` — l'autoritatif,
PAS `prompts/*.md` qui reste le fallback déprécié) via un bloc **« Règle d'or »**
en tête de chaque :
- Le livrable se lit comme un **mail rédigé par un humain** : sections claires,
  pas de syntaxe visible, pas de front matter dans le corps.
- **Recherche large, sortie courte.** Pas de minimum, pas de remplissage : si
  une section n'a rien, deux mots en français et on passe.
- **Zéro back-office, zéro jargon d'IA** (« fit faible/moyen/fort », « score »,
  « de-dup »…). Les scores/filtres servent le tri **interne**, jamais écrits.
- Front matter réduit à `task/run_at/status` (métriques cosmétiques virées).

Spécifiques :
- **sydney** (référence, réécrit en entier) : immigration AU coupée sauf PR /
  travel facility ; jobs en **strong fit OU junior iconoclaste** uniquement
  (plus de « fit faible », plus de « rien de senior » — Sylvain se reconvertit,
  il veut justement le junior atypique) ; filtre trading rendu **silencieux** ;
  invest/cofounding encouragé à scour des sources ; serendipity gardée.
- **ai_jobs_formations** : levé la contradiction « pas de junior » (le junior en
  reconversion est désormais une cible explicite).
- **health_watch** : niveaux de confiance + applicabilité Isa **conservés**
  (vrai signal evidence-based, pas du jargon cosmétique).

### 2. Rendu mail (mail-report.yml)
Le pipeline envoyait le `.md` en **texte brut** → cause des retours chariot et
du front matter visible. Corrigé : retire le front matter, **rend le markdown
en HTML** (police système, sections, liens cliquables), fallback texte. Sujet
humanisé (map task → nom lisible).

### 3. Mail découplé de `main`
Le mail dépendait d'un push sur `main`, que le **proxy Claude Code interdit**
souvent aux routines/sessions (branche `claude/**`). `mail-report.yml` se
déclenche désormais `on: push` sur `main` **ET** `claude/**` → le mail part
quelle que soit la branche.

### 4. Mémoire garantie sur `main` (nouveau workflow `sync-veille-to-main.yml`)
Point soulevé par Sylvain : au-delà du mail, les rapports + handovers **DOIVENT**
finir sur `main`, sinon le run suivant (qui clone `main`) ne retrouve pas la
working-memory → mémoire inter-run cassée. Comme le proxy bloque le push `main`
côté routine, c'est **garanti par l'infra GitHub** : la GHA, sur push `claude/**`,
recopie rapports de veille + `*-session-*.md` + ajouts `findings.md` sur `main`
(noms horodatés uniques → zéro conflit, findings en append, push GITHUB_TOKEN
→ pas de re-trigger → pas de double mail, retry anti-course).
Conséquence : les commands poussent **juste sur la branche courante**
(`git push -u origin HEAD`, étape 5), les 2 GHA font le reste.

### 5. CLAUDE.md
- Callout en tête : **Préférence ferme de Sylvain** — il ne veut JAMAIS avoir à
  lire les onglets Claude Code ; ne jamais bloquer un livrable sur une question
  de branche.
- Garde-fous + section Phase réécrits : mail multi-branche + garantie mémoire
  par l'infra.

## État repo
- Branche : `main` et `claude/wizardly-goodall-ptbq10` alignées sur `224ddd4`
  (+ ce handover).
- 3 commits de la session : `82b2bb6` (refonte commands + HTML), `567b591`
  (découplage mail + préférence ferme), `224ddd4` (sync GHA + garantie mémoire).

## Prochain pas concret (pour la prochaine sesh)
1. **Run now sur la routine `sydney_opportunities`** et vérifier de bout en bout :
   (a) le mail reçu est propre (HTML, pas de front matter, lisible humain) —
   Sylvain a déjà reçu des mails ce matin, « pas mal », à raffiner ;
   (b) le rapport + findings sont bien **arrivés sur `main`** via la sync GHA.
2. **Seul risque connu à confirmer** : la sync push sur `main` suppose **pas de
   branch protection** sur `main` (repo solo → normalement OK). Si la GHA
   `sync-veille-to-main` échoue au push, c'est ça → câbler un PAT en secret.
   Vérifier le 1er run de cette GHA (ce handover devrait déjà l'avoir déclenchée).
3. **Itérer la forme** d'après les vrais mails reçus (Sylvain veut en rediscuter) :
   ajuster ton/longueur/structure si besoin, sur sydney d'abord puis propager.
4. Restent à créer côté `claude.ai/code/routines` : les routines pour les 5
   veilles autres que sydney (toggle *unrestricted pushes* ON sur chacune).
5. `prompts/*.md` (fallback déprécié) à purger à terme — pas touché cette sesh.
