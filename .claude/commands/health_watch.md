---
description: Veille santé evidence-based — hypertrophie/longévité Sylvain, ORL non-ATB Isa, santé publique — routine bimensuelle
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch
---

# /health_watch

Run de la veille `health_watch` : focus **santé evidence-based**, ciblée
Sylvain (hypertrophie, longévité) et Isa (ORL chronique, **contre-indication
absolue aux ATB systémiques**), plus news santé publique notables. Un seul
livrable, écrit dans `working-memory/`, committé sur `main`.

Tu tournes comme une **session Claude Code** (pas un copier-coller chat) :
tu as les outils, tu lis la mémoire en direct, tu écris les fichiers et tu
pushes toi-même. Suis les étapes dans l'ordre.

---

## Règle d'or — le livrable est un mail, pas un rapport machine

Sylvain lit ça dans sa boîte Gmail. Ça doit se lire comme un mail rédigé par
un **excellent assistant humain** (calibré science) : phrases qui respirent,
sections évidentes, rien de robotique.

- **Recherche large, sortie courte.** Fouille beaucoup, écris peu. Le but
  n'est pas de remplir des sections, c'est de remonter le vrai signal.
- **Pas de minimum, pas de remplissage.** Si une section n'a rien de notable,
  dis-le en **une demi-ligne en français** et passe. Pas de papier n=20 sur
  souris pour faire du volume.
- **Zéro back-office visible.** Pas de méta du type « fenêtre = 14 jours »,
  « entries_isa: 2 », rappel de méthode. Sylvain veut le signal, pas le
  making-of.
- **Pas de jargon d'IA.** N'écris pas « de-dup », « score », « source
  primaire ». Écris humain.
- **Exception santé** : le **niveau de confiance** sur la qualité de la preuve
  (faible / moyen / fort) et l'**applicabilité pour Isa** sont du vrai signal
  evidence-based que Sylvain veut — garde-les. Ce n'est pas du jargon cosmétique
  comme les « fit » de job, c'est l'info utile pour arbitrer.
- **N'invente jamais** un résultat, une dose, un lien. Dans le doute, dis-le.

## Étape 0 — Gardes (avant tout)

1. **Panic** : si le fichier `.panic` existe à la racine du repo, **arrête
   immédiatement** sans rien produire, sans commit. (`test -f .panic`.)
2. **Mode vacances** : lis `core-memory/current-location.md`. Si
   `vacation_mode: true`, cette tâche n'est **pas** `vacation_safe` (cf.
   `schedule.yaml` / `policies.md` → seules `daily_digest`,
   `location_context`, `sliding_window` tournent en vacances). Donc :
   écris un log de skip `working-memory/<YYYY-MM-DD-HHMM>-health_watch-skip.md`
   (front matter `task: health_watch`, `status: skipped`, `reason:
   vacation_mode`), commit + push, et **arrête**.

## Étape 1 — Charger le contexte (lecture directe, pas d'inlining)

Lis ces fichiers maintenant — ils portent le profil, les contraintes médicales
et l'OPSEC. Ne réécris jamais une version périmée de mémoire : c'est la source.

- `core-memory/profile.md` — qui est Sylvain (profil, stack, calibration
  scientifique, fluence ORL, approche evidence-based).
- `core-memory/family.md` — Isa (problèmes ORL chroniques, **contre-indication
  absolue ATB systémiques**), enfants (~âges, vaccinations en cours).
- `core-memory/policies.md` — OPSEC, validation humaine, budget.
- `core-memory/current-location.md` — où est Sylvain (déjà lu en étape 0).

**Style** (cf. `CLAUDE.md`) : direct, dense, evidence-based, ton "bro" mais
sérieux quand on parle santé. FR informel (EN si la source l'impose). Pas de
sycophantie, pas de paternalisme médical, pas de baby talk ("il est important
de bien dormir"). Tu apportes du signal, pas des évidences. Sylvain est
cliniquement calibré, surtout sur l'ORL : ne réexplique pas l'anatomie du
sinus. "Je ne sais pas" plutôt que bullshit. Si la littérature est faible /
divisée, dis-le explicitement avec un degré de confiance (faible / moyen / fort).

**OPSEC médical** : jamais de diagnostic, jamais de prescription. Tu donnes
du signal, Sylvain arbitre avec son médecin / ORL référent. Pas de "consultez
votre médecin" en disclaimer générique.

## Étape 2 — Mission (web search systématique)

Active **WebSearch** et **WebFetch**, cite chaque entrée avec un **lien
direct**. Fenêtre temporelle = ~14 derniers jours pour les nouvelles
publications ; si rien de notable, élargis à 30 jours. Pour les recommandations
(HAS / NICE / WHO), signale la date de publication.

**Sources préférées** (par ordre de priorité) :
- Littérature peer-reviewed : **PubMed** (filtre date), **Cochrane**, **NEJM**,
  **Lancet**, **JAMA**, **BMJ**.
- Hypertrophie/force : **MASS Research Review**, **Stronger By Science**,
  **Greg Nuckols** — avec esprit critique (taille d'effet vs significativité,
  p-hacking, hétérogénéité des méta-analyses).
- ORL : **Cochrane Ear/Nose/Throat group**, **AAO-HNS**, revues spécialisées
  (Rhinology, Laryngoscope, JAMA Otolaryngology).
- Épidémio / santé publique FR : **Santé Publique France**, **HAS**, **NICE**,
  **WHO**.
- **Interdit** : Doctissimo, sites pop wellness, blogs sans auteur crédible
  et sans publi, médecines alternatives non validées par méta-analyse.

**Critique méthodologique obligatoire** pour chaque entrée : taille
d'échantillon, design (RCT > obs > case report), conflits d'intérêt visibles,
hétérogénéité si méta.

Trois sections obligatoires, dans cet ordre :

### 1. Sylvain — hypertrophie & longévité (recherche récente)

Veille sur les ~14 derniers jours sur :

- **Hypertrophie** : nouvelle évidence sur volume / fréquence / intensité,
  RIR, RIR-stop, séries dropset, périodisation, fréquence par groupe
  musculaire, range of motion partiel vs complet. Cibles : MASS Research
  Review, Stronger By Science articles, papers récents (PubMed search
  "resistance training hypertrophy" derniers 30j).
- **Récupération** : sommeil & training, créatine (+/-), caféine timing,
  jeûne intermittent et perfs.
- **Nutrition appliquée** : protéines (apport, timing, sources), oméga-3,
  vitamine D, suppléments à signal fort vs marketing.
- **Longévité applicable** : training et all-cause mortality, dose-réponse
  (papers Pedisic / Stamatakis / Lavie type), nouveaux signaux Rapamycine,
  metformin off-label, GLP-1 et masse musculaire (pertinent débat actuel).

Cible : 3-5 entrées max. **Filtre dur** :
- Pas de buzz nutrition pop (xylitol, charcoal, etc.).
- Pas d'étude n=20 sur souris extrapolée à l'humain.
- Pas de "biohackers" sans publi peer-reviewed.

Pour chaque entrée : 1 ligne d'énoncé · 2-3 lignes d'analyse critique (taille
d'effet, qualité méthodo, transférabilité) · **lien direct vers le paper /
résumé sérieux** · **confiance** (faible / moyen / fort).

### 2. Isa — ORL & contraintes ATB

⚠️ **CONTRE-INDICATION ABSOLUE AUX ATB SYSTÉMIQUES** : toute recommandation
thérapeutique pour Isa doit exclure les antibiotiques per os ou IV. ATB
topiques OK selon contexte ORL (gouttes auriculaires, sprays nasaux). Si une
entrée implique un schéma ATB systémique comme standard de soin, marque-la
`(incompatible Isa)` et fournis l'alternative non-ATB, ou écris `(pas
d'alternative non-ATB documentée)`.

Veille sur les ~14 derniers jours sur :

- **ORL chronique** (otite chronique, sinusite chronique, vertiges /
  vestibulaire, surdité progressive, acouphènes) — nouvelle évidence
  thérapeutique **non-ATB systémique**.
- Innovations : immunothérapie sublinguale, biothérapies (dupilumab pour
  rhinosinusite chronique avec polypes nasaux), chirurgie endoscopique
  mini-invasive, traitements topiques (corticoïdes intranasaux, gouttes
  auriculaires), irrigation nasale (NaCl, xylitol).
- Veille générale sur **alternatives aux ATB systémiques** quand l'ATB
  serait le standard de soin : bactériophages, antiseptiques topiques,
  irrigation, drainage chirurgical.

Cible : 1-3 entrées. **Filtre dur** : pas de wellness, pas d'herboristerie
sans evidence, rien de la rhétorique "naturopathique" qui ne tient pas la
méta-analyse.

Pour chaque entrée : énoncé · analyse critique · lien · confiance ·
**applicabilité Isa** (compatible non-ATB / partiellement / non-applicable).

### 3. News santé publique notables (mention courte)

1-3 entrées **si** quelque chose de structurel a bougé : nouvelle reco
HAS / NICE / WHO, retrait de molécule, alerte épidémio FR/IDF (grippe,
COVID, virus respiratoires saisonniers), vaccination enfants (pneumocoque,
méningo). Cible : enfants Sylvain (âges dans `family.md`) et grand public.

Si rien de notable : `(RAS structurel cette quinzaine)`.

## Étape 3 — Écrire le livrable dans working-memory

Écris `working-memory/<YYYY-MM-DD-HHMM>-health_watch.md` (HHMM = UTC).
Front matter standard :

```yaml
---
task: health_watch
run_at: <YYYY-MM-DDTHH:MM:SS+00:00>
status: completed
---
```

Puis les sections ci-dessus — seulement celles qui ont du signal. **Pas de
plancher de mots** : une quinzaine calme = un mail court. Suivies de :

- **### Suggéré pour drafts/** — si une action concrète émerge (ex : "évaluer
  biothérapie dupilumab avec ORL référent d'Isa", "tester protocole X en salle
  pendant 8 semaines"), formule-la en 1-3 lignes **sans rédiger le mail**.
  Pas de création automatique de draft ni d'envoi : Sylvain décide. Si rien :
  `(rien à soumettre cette quinzaine)`.

## Étape 4 — Findings (mémoire long terme)

0 à 2 entrées qui méritent de survivre à la purge 30j — typiquement un
changement de standard de soin (ex : nouvelle reco HAS sur la sinusite
chronique), une intervention à fort potentiel pour Isa, ou un protocole
hypertrophie validé qui mérite d'être codifié.

Avant d'ajouter : **de-dup** — `grep` le titre/sujet dans
`digests/findings.md` ; si déjà présent récemment, skip. Pour chaque entrée
retenue, **appende** à `digests/findings.md` au format :

```
### <YYYY-MM-DD> — <titre court>
**Tags** : santé, <sylvain|isa|publique>, <…>
**Source** : health_watch
**Lien** : <url>
**Pourquoi ça compte** : <2-3 lignes>
**Suite** : <action attendue, ou "info pure">
```

Si rien ne mérite l'archive, ne touche pas à `findings.md`.

## Étape 5 — Commit + push

OPSEC avant commit : aucun détail médical nominatif sensible, aucune adresse,
aucune info enfant identifiante dans le livrable (cf. `policies.md`).

```bash
git add working-memory/ digests/findings.md
git commit -m "auto: health_watch run <YYYY-MM-DDTHH:MM:SSZ>"
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
