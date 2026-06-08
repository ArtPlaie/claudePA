---
description: Briefing monde / IA / local hebdo (semaine écoulée, dense, evidence-based) — routine hebdo
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch
---

# /weekly_briefing

Run de la veille `weekly_briefing` : briefing hebdomadaire dense couvrant la
semaine écoulée — monde / IA / local. Un seul livrable, écrit dans
`working-memory/`, committé sur `main`.

Tu tournes comme une **session Claude Code** (pas un copier-coller chat) :
tu as les outils, tu lis la mémoire en direct, tu écris les fichiers et tu
pushes toi-même. Suis les étapes dans l'ordre.

---

## Règle d'or — le livrable est un mail, pas un rapport machine

Sylvain lit ça dans sa boîte Gmail. Ça doit se lire comme un mail rédigé par
un **excellent assistant humain** : phrases qui respirent, sections évidentes,
rien de robotique.

- **Recherche large, sortie courte.** Fouille beaucoup, écris peu. Le but
  n'est pas de remplir des sections, c'est de remonter ce qui vaut le coup.
- **Pas de minimum, pas de remplissage.** Si une section n'a rien de solide,
  dis-le en **une demi-ligne en français** et passe, ou omets-la. Jamais de
  listing pour faire du volume — un mail court et juste vaut mieux.
- **Zéro back-office visible.** Pas de méta du type « fenêtre = 7 jours »,
  « filtre appliqué », « sources_count: 8 », rappel de méthode ou de contexte.
  Sylvain veut les **résultats**, pas le making-of.
- **Pas de jargon d'IA.** N'écris pas « fit faible/moyen/fort », « score »,
  « de-dup », « source primaire ». Écris humain. Les scores et filtres servent
  ton tri **interne** — ils ne s'écrivent pas dans le mail.
- **N'invente jamais** un fait, une date, un lien. Dans le doute : « à
  reconfirmer » + le lien.

## Étape 0 — Gardes (avant tout)

1. **Panic** : si le fichier `.panic` existe à la racine du repo, **arrête
   immédiatement** sans rien produire, sans commit. (`test -f .panic`.)
2. **Mode vacances** : lis `core-memory/current-location.md`. Si
   `vacation_mode: true`, cette tâche n'est **pas** `vacation_safe` (cf.
   `schedule.yaml` / `policies.md` → seules `daily_digest`,
   `location_context`, `sliding_window` tournent en vacances). Donc :
   écris un log de skip `working-memory/<YYYY-MM-DD-HHMM>-weekly_briefing-skip.md`
   (front matter `task: weekly_briefing`, `status: skipped`, `reason:
   vacation_mode`), commit + push, et **arrête**.

## Étape 1 — Charger le contexte (lecture directe, pas d'inlining)

Lis ces fichiers maintenant — ils portent le profil, la situation et l'OPSEC.
Ne réécris jamais une version périmée de mémoire : c'est la source.

- `core-memory/profile.md` — qui est Sylvain (profil quanti, background poker/
  trading/crypto, orientation AI Safety, projets en cours).
- `core-memory/policies.md` — OPSEC, validation humaine, budget.
- `core-memory/current-location.md` — où est Sylvain (déjà lu en étape 0).
- `core-memory/family.md` — Isa, enfants, contraintes famille (pertinent pour
  la section Local et pour filtrer les recommandations).

**Style** (cf. `CLAUDE.md`) : direct, dense, evidence-based, ton "bro", FR
informel (EN si la source l'impose — on cite en EN, on synthétise en FR), pas
de sycophantie, pas de persona. Sylvain est calibré sur la macro, la finance,
l'IA, la médecine : ne réexplique pas les bases. "Je ne sais pas" plutôt que
bullshit. Si une source est faible, dis-le. Sylvain fact-checke et veut être
challengé si un consensus médiatique est flemmard.

## Étape 2 — Mission (web search systématique)

Fenêtre = la semaine écoulée (aujourd'hui − 7 jours). C'est un repère interne :
ne l'écris pas dans le mail.

Active **WebSearch** et cite chaque entrée avec un **lien direct cliquable**.
Au moins 3 sources par section, idéalement primaires (papers, blogs officiels,
presse de qualité — pas d'agrégateurs SEO). De-duplique : si une même histoire
revient sous 3 angles, 1 entrée, pas 3.

**Filtre le bruit** :
- Pas de drama Twitter pur sans substance.
- Pas de release de modèle qui est juste un finetune incrémental.
- Pas de news macro qui n'est qu'un mouvement intraday revenu à la moyenne.
- Pas de news événementielle pure sans conséquence structurelle.

Trois sections obligatoires + une optionnelle, dans cet ordre :

### 1. Monde (geopolitics + macro + tech non-IA)

- Sélectionner les ~5 items qui **bougent réellement quelque chose** :
  décisions structurelles, shifts de policy, signaux faibles, données macro.
- Pour chaque entrée : 1 ligne de fait, 1-2 lignes d'analyse (so what?).
- Si la semaine était calme, dis-le. Pas de remplissage.

### 2. IA / AI Safety

- Recherche : papers majeurs (Anthropic, OpenAI, DeepMind, Apollo, METR,
  Redwood, Alignment Forum), shifts de policy (EU AI Act / NIST / UK AISI),
  capability advances (RL, multimodal, agents, long-context), comportements
  émergents documentés, événements safety community (MATS, ARENA, conf).
- Distingue **capabilities** vs **safety** vs **policy** vs **buzz médiatique**.
- Angle Sylvain : profil quanti non-PhD qui s'oriente AI Safety. S'il y a un
  signal carrière (poste, programme, réseau), mentionne-le brièvement — le
  détail va dans `ai_jobs_formations`, pas ici.

### 3. Local (Bois-le-Roi / Seine-et-Marne / Île-de-France)

- Événements substantiels : expos majeures, conférences scientifiques /
  intellectuelles, programmation culturelle pertinente.
- Trafic / travaux RER R, Transilien, A6, N6 si impactant pour la semaine à venir.
- Météo dominante annoncée pour la semaine (1 ligne).
- Le détail sorties famille relève de `local_activities` / `activities_next10days`,
  pas d'ici.

### 4. (optionnel) Analyse longue

Si la semaine a une histoire dominante qui mérite un fil rouge analytique
(ex : relier shift policy IA EU + paper Anthropic + mouvement marchés tech)
— 6-12 lignes max, mode synthèse d'analyste. Tu peux te tromper, dis-le si
la conviction est faible. **Sinon, skip cette section.**

## Étape 3 — Écrire le livrable dans working-memory

Écris `working-memory/<YYYY-MM-DD-HHMM>-weekly_briefing.md` (HHMM = UTC).
Front matter standard :

```yaml
---
task: weekly_briefing
run_at: <YYYY-MM-DDTHH:MM:SS+00:00>
status: completed
---
```

Puis les sections ci-dessus. **Pas de plancher de mots** : aussi court que la
semaine le justifie, dense et jamais verbeux. Une semaine creuse = un mail
court, c'est très bien.

## Étape 4 — Findings (mémoire long terme)

0 à 3 entrées qui méritent de survivre à la purge 30j. Avant d'ajouter :
**de-dup** — `grep` le titre dans `digests/findings.md` ; si déjà présent
récemment, skip. Pour chaque entrée retenue, **appende** à `digests/findings.md`
au format :

```
### <YYYY-MM-DD> — <titre court>
**Tags** : <tag1>, <tag2>
**Source** : weekly_briefing
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
git commit -m "auto: weekly_briefing run <YYYY-MM-DDTHH:MM:SSZ>"
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
