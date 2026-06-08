---
description: Veille Sydney + Suisse — reconversion IA (jobs, formations, invest/cofounding, serendipity) — routine hebdo
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch
---

# /sydney_opportunities

Run de la veille `sydney_opportunities` : focus **Sydney + Suisse**, axé
**reconversion vers l'IA** — formations IA, jobs IA ouverts à un profil non-PhD,
opportunités d'investissement/cofounding, et une section serendipity en
créativité max. **Pas de trading / finance quanti.** News visa/PR Australie en
contexte. Un seul livrable, écrit dans `working-memory/`, committé sur `main`.

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
   écris un log de skip `working-memory/<YYYY-MM-DD-HHMM>-sydney_opportunities-skip.md`
   (front matter `task: sydney_opportunities`, `status: skipped`, `reason:
   vacation_mode`), commit + push, et **arrête**.

## Étape 1 — Charger le contexte (lecture directe, pas d'inlining)

Lis ces fichiers maintenant — ils portent le profil, le plan et l'OPSEC.
Ne réécris jamais une version périmée de mémoire : c'est la source.

- `core-memory/profile.md` — qui est Sylvain (profil quanti non-PhD,
  exposition AI Safety, stack pro).
- `core-memory/australia-plan.md` — statut visa PR, horizon, ville cible,
  ce qu'on cherche / ne cherche pas, contraintes famille (Isa peintre,
  3 enfants), volet Suisse secondaire.
- `core-memory/policies.md` — OPSEC, validation humaine, budget.
- `core-memory/current-location.md` — où est Sylvain (déjà lu en étape 0).
- `core-memory/skip-patterns.md` — patterns déjà refusés (à consulter avant
  toute suggestion de draft).

**Style** (cf. `CLAUDE.md`) : direct, dense, evidence-based, ton "bro", FR
informel (EN si la source l'impose), pas de sycophantie, pas de persona.
Sylvain est calibré : ne réexplique pas le système visa AU ni l'écosystème
AI Safety. "Je ne sais pas" plutôt que bullshit.

## Étape 2 — Mission (web search systématique)

Active **WebSearch** et cite chaque entrée avec un **lien direct**. Window =
aujourd'hui − 7 jours pour les news/openings récents ; pour les listings
d'emploi, retiens tout poste dont la **date de clôture n'est pas dépassée**
même si publié avant.

Six sections obligatoires, dans cet ordre :

### 1. News visa / immigration Australie

- Skilled migration / employer-sponsored / Global Talent (subclass
  189/186/491/858), points-test, processing times, **renouvellement travel
  facility PR** (si tu trouves une source officielle sur les dates, signale-la).
- News régulation IA / data côté visa et talent.
- Source primaire **obligatoire** : `homeaffairs.gov.au` + presse établie
  (SMH, AFR, ABC). Préfère toujours gov.au à l'analyse de presse, et précise
  la date de la page consultée.

### 2. Jobs IA — Sydney + Suisse (ouverts à un profil en reconversion)

Postes ouverts dans l'IA accessibles à quelqu'un qui **se reconvertit** vers
l'IA depuis un profil quanti non-PhD (calibration, pensée adversariale,
Python, macro/finance). On vise : AI Safety / alignement (technique appliqué,
ops, policy, eval, red-teaming, governance, comms), research engineering,
product/data senior dans des boîtes IA. Cibles canoniques :

- **Anthropic Sydney/APAC**, **OpenAI/DeepMind APAC** (si présence).
- **CSIRO Data61** (responsible AI), **Australian AI Safety Institute** ou
  équivalent gouvernemental (DISR / Industry).
- **Atlassian**, **Canva** — équipes AI/ML/data.
- Startups IA AU/CH, think tanks / policy : **Lowy Institute**, **Centre for
  Independent Studies**, **Tech Council of Australia**.
- Universités (Macquarie, Sydney, UNSW, ANU, **ETH/EPFL AI Center**, **CeSIA**)
  — postes **non-académiques** (AI policy fellow, industry liaison, research
  engineer).
- Suisse : permis B = contrat préalable obligatoire (pas de frontalier).

Pour chaque lead : titre · org · **lien direct** · seniority · remote
(oui/non) · fit (faible/moyen/fort) · note 2-3 lignes (angle de reconversion + risque).

> ⛔️ **EXCLU explicitement** (demande de Sylvain) : trading, market making,
> finance quanti, hedge funds, "quant researcher / systematic strategies".
> Ne propose **aucun** poste de ce type, même très bien payé. Si
> `australia-plan.md` mentionne encore la finance quanti comme cible,
> **ignore-le** : ce n'est plus une cible.

### 3. Formations IA (priorité)

Programmes pour monter en compétence / se reconvertir dans l'IA, adaptés à un
profil quanti non-PhD. Scanne les sessions ouvertes + **deadlines** :

- **MATS**, **ARENA**, **AI Safety Fundamentals** (BlueDot Impact), fellowships
  (Anthropic, GovAI, Apollo, Redwood…), residencies, programmes ETH/EPFL,
  bootcamps techniques sérieux, MOOCs avancés ciblés.
- Pour chaque : nom · org · **lien** · format (remote/in-person) · prochaine
  deadline · fit profil · note 1-2 lignes (pourquoi c'est pertinent pour lui).

### 4. Investissement / cofounding

Opportunités d'**investir** ou de **co-fonder** dans des domaines pertinents
pour son profil (IA, AI safety tooling, crypto×IA, deeptech) :

- Startups qui cherchent un cofounder technique/quant ; deals angel /
  syndicates ; programmes type **Entrepreneur First**, **YC**, accélérateurs
  APAC/EU ; incubateurs AI safety.
- Pour chaque : nom · **lien** · ce qui est cherché (capital / cofounder /
  advisor) · fit · note 1-2 lignes (angle + risque).
- Si rien de solide : `(rien de concret côté invest/cofounding cette semaine)`.

### 5. Serendipity — carte blanche (créativité max)

1-3 idées **hors-piste** que tu proposes librement, en mode créativité
maximale. Pas de filtre de format : projet perso, side-project, angle de
contenu, personne à rencontrer, niche à explorer, pari contrarian,
collaboration, mouvement de carrière inattendu. Sers-toi de tout le profil
(ex-trader algo crypto reconverti, calibration sous incertitude, pensée
adversariale, figure publique crypto FR `@ArtPlaie`, cap Australie, famille).
Sois **audacieux et spécifique**, jamais générique. Assume les idées même
incertaines — c'est exactement le but de cette section. Si une idée est
brillante mais risquée, dis-le et propose-la quand même.

### 6. Veille soft (contexte décision famille)

- 1-2 entrées **non-emploi** substantielles : immo locatif Sydney, écoles
  internationales, scène galeries (pour Isa), events IA APAC.
- Filtre : substantiel uniquement, pas de tourisme.

**Filtre dur** (toutes sections) : **aucun** trading / finance quanti / market
making (exclu sur demande). Pas de junior / process / corporate sans
substance, pas de PhD-required strict, pas de poste US-only sans relocation
AU possible, pas de buzz sans fond. Si une section ne ramène rien de concret,
dis-le — pas de remplissage. N'invente jamais un poste, une formation ou un
lien ; si un opening est douteux, écris `(statut à reconfirmer)`. La section
Serendipity, elle, doit **toujours** proposer quelque chose.

## Étape 3 — Écrire le livrable dans working-memory

Écris `working-memory/<YYYY-MM-DD-HHMM>-sydney_opportunities.md` (HHMM = UTC).
Front matter standard :

```yaml
---
task: sydney_opportunities
run_at: <YYYY-MM-DDTHH:MM:SS+00:00>
status: completed
jobs_ia: <n>
formations: <n>
invest_cofounding: <n>
serendipity: <n>
---
```

Puis les 6 sections ci-dessus (densité **600-1200 mots**, dense pas verbeux),
suivies de :

- **### Candidature / candidature formation mûre ?** — si un job ou une
  formation a un fit fort + deadline proche, propose un angle en 5-8 bullets
  (angles + risque, pas de cover letter). Avant : vérifie
  `core-memory/skip-patterns.md`, si pattern proche → n'insiste pas. Pas de
  création de draft/envoi automatique : Sylvain décide.

## Étape 4 — Findings (mémoire long terme)

0 à 3 entrées qui méritent de survivre à la purge 30j. Avant d'ajouter :
**de-dup** — `grep` le titre/org dans `digests/findings.md` ; si déjà présent
récemment, skip (ne re-propose pas la même opportunité). Pour chaque entrée
retenue, **appende** à `digests/findings.md` au format :

```
### <YYYY-MM-DD> — <titre court>
**Tags** : sydney, <…>
**Source** : sydney_opportunities
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
git commit -m "auto: sydney_opportunities run <YYYY-MM-DDTHH:MM:SSZ>"
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
