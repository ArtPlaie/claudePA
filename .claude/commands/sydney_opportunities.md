---
description: Veille Sydney + Suisse (jobs intello, news visa PR, leads) — routine hebdo
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch
---

# /sydney_opportunities

Run de la veille `sydney_opportunities` : focus **Sydney + Suisse**, jobs
intellectuellement stimulants, news visa/PR Australie, leads pour la
relocalisation 6-18 mois. Un seul livrable, écrit dans `working-memory/`,
committé sur `main`.

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

Quatre sections obligatoires, dans cet ordre :

### 1. News visa / immigration Australie

- Skilled migration / employer-sponsored / Global Talent (subclass
  189/186/491/858), points-test, processing times, **renouvellement travel
  facility PR** (si tu trouves une source officielle sur les dates, signale-la).
- News régulation crypto / fintech / AI / data côté visa.
- Source primaire **obligatoire** : `homeaffairs.gov.au` + presse établie
  (SMH, AFR, ABC). Préfère toujours gov.au à l'analyse de presse, et précise
  la date de la page consultée.

### 2. Leads emploi Sydney (cette semaine)

Scanne les postes ouverts matchant le profil. Cibles canoniques à vérifier
systématiquement via web search :

- **Anthropic Sydney/APAC**, **OpenAI/DeepMind APAC** (si présence).
- **CSIRO Data61** (responsible AI), **Australian AI Safety Institute** ou
  équivalent gouvernemental (DISR / Industry).
- **Atlassian**, **Canva** — rôles seniors AI/ML/quanti/data.
- Finance quanti : **Macquarie**, **AMP Capital**, **Optiver Sydney**,
  **IMC**, **Akuna**, **SIG** ; hedge funds (**Regal**, **Munro**, **Bell
  AM**) — systematic / quant.
- Think tanks / policy : **Lowy Institute**, **Centre for Independent
  Studies**, **Tech Council of Australia**.
- Universités (Macquarie, Sydney, UNSW, ANU) — postes **non-académiques**
  (AI policy fellow, industry liaison, research engineer).

Pour chaque lead : titre · org · **lien direct** · seniority · remote
(oui/non) · fit (faible/moyen/fort) · note 2-3 lignes (angle + risque).

### 3. Suisse — leads secondaires (mention courte)

- **ETH AI Center**, **EPFL AI Center**, **CLST**, **CeSIA** (FR), startups
  IA suisses, finance quanti CH (Pictet quant, CFM Geneva, etc.).
- Permis B = contrat préalable obligatoire (pas de frontalier). Si rien de
  signal-fort : `(rien de notable côté CH cette semaine)`.

### 4. Veille soft (contexte décision famille)

- 1-3 entrées **non-emploi** substantielles : immo locatif Sydney, écoles
  internationales, scène galeries (pour Isa), events crypto/AI APAC.
- Filtre : substantiel uniquement, pas de tourisme.

**Filtre dur** (toutes sections) : pas de junior / process / corporate sans
substance, pas de PhD-required strict, pas de poste US-only sans relocation
AU possible, pas de buzz sans fond. Si la session ramène 0 opportunité
concrète, dis-le — pas de remplissage. N'invente jamais un poste ou un lien ;
si un opening est douteux, écris `(statut à reconfirmer)`.

## Étape 3 — Écrire le livrable dans working-memory

Écris `working-memory/<YYYY-MM-DD-HHMM>-sydney_opportunities.md` (HHMM = UTC).
Front matter standard :

```yaml
---
task: sydney_opportunities
run_at: <YYYY-MM-DDTHH:MM:SS+00:00>
status: completed
news_visa: <n>
leads_sydney: <n>
leads_ch: <n>
---
```

Puis les 4 sections ci-dessus (densité **500-1000 mots**, dense pas verbeux),
suivies de :

- **### Suggestion australia-plan.md** — si un lead concret a émergé (org +
  rôle + statut), propose UNE ligne au format
  `- [YYYY-MM-DD] <org> — <rôle/contexte> — <statut>`. **Ne modifie pas**
  `core-memory/australia-plan.md` toi-même : c'est une suggestion que Sylvain
  validera. Sinon `(rien à appender cette semaine)`.
- **### Candidature mûre ?** — si un job ouvert a un fit fort + deadline
  proche, propose un angle de candidature en 5-8 bullets (angles + risque
  adversaire, pas de cover letter). Avant : vérifie `core-memory/skip-patterns.md`,
  si pattern proche → n'insiste pas. Pas de création de draft/envoi
  automatique : Sylvain décide.

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

## Étape 6 — Envoi email (best-effort, SMTP `claudePA@gmail.com`)

Envoie le rapport par mail à Sylvain via SMTP Gmail. Si `GMAIL_USER`,
`GMAIL_APP_PASSWORD` ou `MAIL_TO` ne sont pas définis, **skip en silence**
(ne casse pas le run — le rapport reste committé dans `working-memory/`).

Le corps du mail = le **rapport complet** (le fichier working-memory que tu
viens d'écrire, en texte). Subject avec la date et les compteurs. Exécute,
en remplaçant `WM_FILE` par le chemin réel du fichier produit à l'étape 3 :

```bash
WM_FILE="working-memory/<le-fichier-produit>.md"
if [ -n "$GMAIL_USER" ] && [ -n "$GMAIL_APP_PASSWORD" ] && [ -n "$MAIL_TO" ]; then
  WM_FILE="$WM_FILE" python3 - <<'PY'
import os, smtplib, ssl, datetime
from email.message import EmailMessage

body = open(os.environ["WM_FILE"], encoding="utf-8").read()
msg = EmailMessage()
msg["From"] = os.environ["GMAIL_USER"]
msg["To"] = os.environ["MAIL_TO"]
msg["Subject"] = f"claudePA — veille Sydney {datetime.date.today():%Y-%m-%d}"
run = os.environ.get("CLAUDE_CODE_REMOTE_SESSION_ID")
header = f"Run: https://claude.ai/code/{run}\n\n" if run else ""
msg.set_content(header + body)

with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as s:
    s.login(os.environ["GMAIL_USER"], os.environ["GMAIL_APP_PASSWORD"])
    s.send_message(msg)
print("email sent to", os.environ["MAIL_TO"])
PY
fi
```

Note : l'app-password ne s'affiche jamais dans le repo ni les logs (il vient
de l'env var de la routine). N'envoie pas le mail si l'étape 0 a skip le run.
