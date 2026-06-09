---
description: Veille jobs AI / AI Safety + formations type MATS/fellowships — routine hebdo
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch
---

# /ai_jobs_formations

Run de la veille `ai_jobs_formations` : focus **formations AI Safety structurées**
(MATS, ARENA, fellowships, résidences) + **postes** AI Safety / alignment /
governance, filtrés pour profil quanti non-PhD. Un seul livrable, écrit dans
`working-memory/`, committé sur `main`.

Tu tournes comme une **session Claude Code** (pas un copier-coller chat) :
tu as les outils, tu lis la mémoire en direct, tu écris les fichiers et tu
pushes toi-même. Suis les étapes dans l'ordre.

---

## Règle d'or — le livrable est un mail, pas un rapport machine

Sylvain lit ça dans sa boîte Gmail. Ça doit se lire comme un mail rédigé par
un **excellent assistant humain** : phrases qui respirent, sections évidentes,
rien de robotique.

- **Recherche large, sortie courte.** Fouille *vraiment* beaucoup : multiplie
  les requêtes WebSearch (angles, synonymes, orgs et job boards différents) pour
  ramasser au moins **2× plus de candidats bruts** que ce que tu garderas — tu
  veux du **choix** avant de trier, pas trois liens trouvés vite fait. Le tri
  reste impitoyable et la sortie courte ; c'est l'amont qui s'élargit, pas le
  mail.
- **Pas de minimum, pas de remplissage.** Si une section n'a rien de solide,
  dis-le en **une demi-ligne en français** et passe, ou omets-la. Jamais de
  listing pour faire du volume — un mail court et juste vaut mieux.
- **Zéro back-office visible.** Pas de méta du type « fenêtre = 6 mois »,
  « filtre appliqué », « jobs_kept: 4 », rappel de méthode ou de contexte.
  Sylvain veut les **résultats**, pas le making-of.
- **Pas de jargon d'IA.** N'écris pas « fit faible/moyen/fort », « score »,
  « de-dup », « source primaire ». Écris humain. Les scores et filtres servent
  ton tri **interne** — ils ne s'écrivent pas dans le mail.
- **N'invente jamais** un poste, une deadline, un lien. Dans le doute : « à
  reconfirmer » + le lien.

## Étape 0 — Gardes (avant tout)

1. **Panic** : si le fichier `.panic` existe à la racine du repo, **arrête
   immédiatement** sans rien produire, sans commit. (`test -f .panic`.)
2. **Mode vacances** : lis `core-memory/current-location.md`. Si
   `vacation_mode: true`, cette tâche n'est **pas** `vacation_safe` (cf.
   `schedule.yaml` / `policies.md` → seules `daily_digest`,
   `location_context`, `sliding_window` tournent en vacances). Donc :
   écris un log de skip `working-memory/<YYYY-MM-DD-HHMM>-ai_jobs_formations-skip.md`
   (front matter `task: ai_jobs_formations`, `status: skipped`, `reason:
   vacation_mode`), commit + push, et **arrête**.

## Étape 1 — Charger le contexte (lecture directe, pas d'inlining)

Lis ces fichiers maintenant — ils portent le profil, le plan et l'OPSEC.
Ne réécris jamais une version périmée de mémoire : c'est la source.

- `core-memory/profile.md` — qui est Sylvain (profil quanti non-PhD,
  exposition AI Safety, stack pro, parcours poker → trading algo → PA).
- `core-memory/australia-plan.md` — statut visa PR, horizon, ville cible,
  contraintes famille (Isa peintre, 3 enfants), volet Suisse secondaire.
- `core-memory/policies.md` — OPSEC, validation humaine, budget.
- `core-memory/current-location.md` — où est Sylvain (déjà lu en étape 0).
- `core-memory/skip-patterns.md` — patterns déjà refusés (à consulter avant
  toute suggestion de draft ou candidature).

**Style** (cf. `CLAUDE.md`) : direct, dense, evidence-based, ton "bro", FR
informel (EN si la source l'impose), pas de sycophantie, pas de persona.
Sylvain est calibré sur l'écosystème AI Safety : ne réexplique pas ce qu'est
MATS, ARENA, MIRI, Anthropic, etc. "Je ne sais pas" plutôt que bullshit.

## Étape 2 — Mission (web search systématique)

Active **WebSearch** et cite chaque entrée avec un **lien direct**. Window =
aujourd'hui + 6 mois (focus sur ce qui a une deadline dans cette fenêtre, ou
rolling). Pour les listings d'emploi, retiens tout poste dont la **date de
clôture n'est pas dépassée** même si publié avant.

**Volume de recherche** : ne te contente pas d'une requête par cible. Pour les
formations comme pour les postes, scanne **chaque org de la liste canonique
individuellement** (pas une seule recherche fourre-tout), ajoute des angles
(« careers », « fellowship 2026 », « open roles », pages job boards type
80,000 Hours / AI Safety jobs / EA jobs) et constitue un vivier d'au moins
**2× plus de candidats** que ce que tu retiendras. Tu tries après (strong fit
only) ; d'abord tu ramasses large pour avoir le choix.

Trois sections obligatoires, dans cet ordre :

### A. Formations AI / AI Safety (programmes structurés)

Tu cherches des **appels en cours** (deadline pas dépassée, ou ouverte sur
rolling basis). Cibles canoniques à vérifier systématiquement via web search :

- **MATS** (ML Alignment & Theory Scholars) — cohortes hiver/été, Berkeley.
- **ARENA** (Alignment Research Engineer Accelerator) — Londres + remote.
- **SERI MATS** / dérivés.
- **GovAI Fellowship** (Oxford).
- **AI Safety Camp**.
- **Astra Fellowship** (Constellation).
- **PIBBSS Fellowship**.
- **OpenPhil / LTFF** fellowships et grants individuels.
- **Apollo Research**, **METR**, **Redwood Research** — programmes de stage
  ou de résidence.
- **AISI UK** — programmes de résidence ou ouverture publique.
- Programmes nationaux : **French Center for AI Safety**, **CeSIA**, etc.
- Masters spécialisés pertinents : **ETH AI Safety**, **EPFL**,
  **MILA / Mila McGill**, **Oxford MSc** — uniquement si format compatible
  (Suisse OK avec contrat = master rémunéré, sinon reporter).

Pour chaque programme retenu : nom, org, format, durée, **deadline**, **lien
direct**, et une phrase qui dit pourquoi ça vaut le coup pour lui. Ne garde que
ce qui colle vraiment — si le fit est mou, ne le mets pas.

Pour ton tri **interne** (jamais écrit dans le mail), évalue le fit profil
(quanti non-PhD, AI Safety appliqué), le fit géo/famille (Sydney > Suisse >
remote > Londres ; US strict-no sans relocation) et l'urgence (deadline < 30j).
Tu ne remontes que le fort fit ; le reste, tu le jettes sans le mentionner.

### B. Postes AI / AI Safety / alignment

Cibles canoniques à scanner via web search :

- **Anthropic**, **OpenAI** (safety/policy/societal-impact teams), **DeepMind**
  safety team, **Apollo**, **METR**, **Redwood**, **Anthropic policy**, **AISI UK**,
  **NIST AISI**, **GovAI**, **CSER Cambridge**, **CHAI Berkeley**, **MIRI**,
  **OpenPhil**, **EA hub orgs** (Rethink Priorities, etc.).
- Roles ciblés : **research engineer**, **evals**, **red-teaming**,
  **policy / governance**, **ops**, **comms / writing**, **TPM / chief of staff**,
  **forecasting / metrics**, **field-building**.
- Filtres géo : **Sydney / Australie**, **Suisse**, **remote-friendly**,
  **Londres** acceptable. Ignore les postes US-only sans remote / sans relocation
  Australie possible.
- Seniority : **le junior et les portes d'entrée atypiques sont les bienvenus**
  — Sylvain se reconvertit, il ne dirige pas un département et n'a pas de CV
  salarié linéaire. Ce qu'on écarte, c'est le PhD-required strict et l'exécutant
  générique sans angle. Ne lui dis jamais « rien de senior ouvert » : il n'en
  veut pas, il veut le junior iconoclaste qui colle à son profil.

Pour chaque poste retenu : titre, org, lieu (+ remote ?), **deadline ou
rolling**, **lien direct**, et une phrase d'angle (le point fort à pousser, le
risque à anticiper). Strong fit uniquement.

### C. Veille adjacente (si signal fort)

- Conférences / workshops avec **CFP ouvert** (NeurIPS safety workshop,
  ICML safety workshop, EAG / EAGx, AI safety summits) — mention si la
  participation pourrait débloquer du réseau.
- Concours / bounties (METR challenges, eval bounties Anthropic) — mention
  uniquement si ROI temps correct pour profil quanti.
- Format : liste courte, 1 ligne par entrée.

**Ce qu'on écarte (sans le mentionner)** : tout ce qui est clos ou deadline
dépassée, l'exécutant générique sans angle, le PhD-required strict, le US-only
sans remote ni relocation AU possible. Le junior iconoclaste, lui, est une
cible — pas un repoussoir. Si la session ne ramène rien de concret, dis-le en
deux mots, pas de remplissage. N'invente jamais un poste ou un lien ; si un
opening est douteux, « à reconfirmer » + le lien.

## Étape 3 — Écrire le livrable dans working-memory

Écris `working-memory/<YYYY-MM-DD-HHMM>-ai_jobs_formations.md` (HHMM = UTC).
Front matter standard :

```yaml
---
task: ai_jobs_formations
run_at: <YYYY-MM-DDTHH:MM:SS+00:00>
status: completed
---
```

Puis les sections ci-dessus — **seulement celles qui ont de la matière**. Pas
de plancher de mots : si une semaine ne sort que deux formations et zéro job
fort, le mail fait quelques lignes. Suivies de :

- **### Candidature mûre ?** — si un poste ou programme a fit fort + deadline
  proche (< 30j), propose un angle de candidature en 5-8 bullets (angles à
  creuser + risque adversaire, pas de cover letter). Avant : vérifie
  `core-memory/skip-patterns.md`, si pattern proche → n'insiste pas. Pas de
  création de draft/envoi automatique : Sylvain décide.

## Étape 4 — Findings (mémoire long terme)

0 à 3 entrées qui méritent de survivre à la purge 30j. Avant d'ajouter :
**de-dup** — `grep` le titre/org dans `digests/findings.md` ; si déjà présent
récemment, skip (ne re-propose pas la même opportunité). Pour chaque entrée
retenue, **appende** à `digests/findings.md` au format :

```
### <YYYY-MM-DD> — <titre court>
**Tags** : ai-safety, <…>
**Source** : ai_jobs_formations
**Lien** : <url>
**Pourquoi ça compte** : <2-3 lignes>
**Suite** : <action attendue, ou "info pure">
```

Si rien ne mérite l'archive, ne touche pas à `findings.md`.

## Étape 5 — Commit + push

OPSEC avant commit : aucune adresse précise, montant, plateforme crypto ou
info enfant dans le livrable (cf. `policies.md`).

```bash
git add working-memory/ digests/findings.md
git commit -m "auto: ai_jobs_formations run <YYYY-MM-DDTHH:MM:SSZ>"
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
