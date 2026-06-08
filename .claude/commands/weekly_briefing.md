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

**Fenêtre temporelle** = aujourd'hui − 7 jours. Note-la en tête du livrable.

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
window: <date-7j> → <date>
status: completed
sources_count: <n>
---
```

Puis les sections ci-dessus (densité **600-1200 mots** total, dense pas
verbeux — si l'analyse longue dépasse, OK mais le reste reste tight).

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

## Étape 6 — Envoi email du rapport (API Gmail HTTPS, compte PA)

⚠️ Le **SMTP brut (465/587) ne marche PAS** depuis une routine : le proxy
egress ne laisse sortir que le 443. On envoie donc via l'**API Gmail OAuth
en HTTPS**, wrappée dans `tasks/send_report.py` (compte PA, env var
`GMAIL_TOKEN_PA_JSON`). Best-effort : si le compte PA n'est pas configuré,
le helper log et sort en 0 — le rapport reste committé, le run n'est pas
cassé.

Après le push, en remplaçant `WM_FILE` par le chemin réel produit à l'étape 3 :

```bash
uv run python -m tasks.send_report \
  --file "working-memory/<le-fichier-produit>.md" \
  --subject "claudePA — briefing hebdo $(date -u +%Y-%m-%d)"
```

Prérequis côté routine (une fois) : setup script `uv sync` (installe les
deps Google) + env var `GMAIL_TOKEN_PA_JSON` (token OAuth compte PA, déjà en
GitHub Secrets). Destinataire = env var `MAIL_TO` sinon défaut. N'envoie pas
si l'étape 0 a skip le run.
