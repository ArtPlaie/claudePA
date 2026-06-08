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

Pour chaque programme : nom · org · format (résidentiel / hybride / remote) ·
durée · **deadline** · **lien direct** · fit profil · fit géo · urgence ·
note 2-3 lignes (pourquoi ça vaut le coup pour Sylvain spécifiquement, ou
pourquoi c'est faible).

**Score chaque entrée** sur 3 dimensions :
- **Fit profil** (quanti non-PhD, AI Safety appliqué) : faible / moyen / fort
- **Fit géo / famille** (Sydney > Suisse > remote > Londres > US strict-no) :
  compatible / friction / bloquant
- **Urgence** : deadline imminente (< 30j) / fenêtre normale / rolling

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
- Filtres seniority : pas de junior pur, pas de PhD-required strict.

Pour chaque lead : titre · org · localisation (+ remote ?) · seniority visible ·
**deadline ou "rolling"** · **lien direct** · fit profil · fit géo · urgence ·
note 2-3 lignes (angle d'attaque si Sylvain candidate : quel point fort pousser,
quel angle adversaire à anticiper).

### C. Veille adjacente (si signal fort)

- Conférences / workshops avec **CFP ouvert** (NeurIPS safety workshop,
  ICML safety workshop, EAG / EAGx, AI safety summits) — mention si la
  participation pourrait débloquer du réseau.
- Concours / bounties (METR challenges, eval bounties Anthropic) — mention
  uniquement si ROI temps correct pour profil quanti.
- Format : liste courte, 1 ligne par entrée.

**Filtre dur** (toutes sections) : ce qui est **clos**, **deadline dépassée**,
ou **inapproprié au profil** est éliminé sans mention. Pas de junior / process /
corporate vide, pas de PhD-required strict, pas de postes US-only sans remote /
relocation AU possible. Si la session ramène 0 opportunité concrète, dis-le —
pas de remplissage. N'invente jamais un poste ou un lien ; si un opening est
douteux, écris `(source à reconfirmer)`.

## Étape 3 — Écrire le livrable dans working-memory

Écris `working-memory/<YYYY-MM-DD-HHMM>-ai_jobs_formations.md` (HHMM = UTC).
Front matter standard :

```yaml
---
task: ai_jobs_formations
run_at: <YYYY-MM-DDTHH:MM:SS+00:00>
status: completed
formations_kept: <n>
jobs_kept: <n>
---
```

Puis les 3 sections ci-dessus (densité **700-1500 mots**, dense pas verbeux),
suivies de :

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
  --subject "claudePA — AI jobs & formations $(date -u +%Y-%m-%d)"
```

Prérequis côté routine (une fois) : setup script `uv sync` (installe les
deps Google) + env var `GMAIL_TOKEN_PA_JSON` (token OAuth compte PA, déjà en
GitHub Secrets). Destinataire = env var `MAIL_TO` sinon défaut. N'envoie pas
si l'étape 0 a skip le run.
