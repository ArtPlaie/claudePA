---
description: Traite les réponses de Sylvain aux mails de rapport — décide et exécute TOUTES les actions (ajuste prompt, corrige mémoire, met des events en file agenda) — routine
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

# /adapt_prompt

Tu es le **cerveau** de la boucle « Sylvain répond à un mail de rapport → le PA
agit ». Une GHA (`tasks/prompt_feedback.py`) a déjà déposé ses réponses brutes
dans `replies/<ts>-<veille>.md` (`status: pending`). **Ton job : lire chaque
réponse et décider + exécuter TOUT ce qu'elle demande.** Un même mail peut
mélanger plusieurs demandes — tu les gères toutes, sans te limiter à une seule
catégorie.

Trois leviers d'action à ta disposition :

1. **Ajuster une veille** → édite son prompt `.claude/commands/<veille>.md`.
2. **Corriger un fait mémoire** → édite `core-memory/*.md`.
3. **Ajouter un/des event(s) à l'agenda** → tu ne peux pas appeler l'API Calendar
   (pas d'accès réseau), donc tu **mets l'event en file** : un fichier
   `calendar/<ts>-<veille>-<n>.md` en `status: requested`. La GHA le crée au
   passage suivant. (C'est le seul cas où tu délègues l'exécution.)

Tu tournes comme une session Claude Code : lis le repo en direct, édite, commit,
push sur ta branche. L'infra propage sur `main` et envoie le récap par mail.

---

## Étape 0 — Garde

Si `.panic` existe à la racine (`test -f .panic`), **arrête immédiatement** sans
rien produire ni committer.

## Étape 1 — Ramasser les réponses en attente (fast-exit si vide)

```bash
grep -l 'status: pending' replies/*.md 2>/dev/null
```

- **Aucun résultat** → rien à faire. Écris un log léger
  `working-memory/<YYYY-MM-DD-HHMM>-adapt_prompt-skip.md` (front matter
  `task: adapt_prompt`, `status: skipped`, `reason: no pending reply`),
  `git add`, commit, `git push -u origin HEAD`, et **arrête**. (Le nom en `-skip`
  n'envoie aucun mail — normal.) Ce fast-exit rend les runs à vide quasi
  gratuits : la routine peut tourner plusieurs fois par jour sans coût.
- Sinon, traite **chaque** réponse pending.

Avant de traiter, calibre-toi : lis `core-memory/profile.md` (style, faits) et
`core-memory/policies.md` (OPSEC, garde-fous) en diagonale. Et récupère la date
courante pour résoudre les dates relatives (« dimanche », « demain ») :

```bash
TZ=Europe/Paris date "+%A %Y-%m-%d %H:%M"
```

## Étape 2 — Pour chaque réponse : décider + exécuter

Lis le `replies/…md`. Front matter : `veille` (la veille concernée),
`report_subject`. Corps : la **réponse brute de Sylvain** (section « Réponse de
Sylvain ») + un « Contexte (rapport cité) » qui te donne les détails utiles
(lieu, nom de l'activité) pour un event.

Décompose la réponse en **une ou plusieurs intentions** et traite-les toutes :

### a) Ajustement de comportement de veille
Ton, longueur, scope, profondeur, type d'idées → édite le prompt
`.claude/commands/<veille>.md`. **Chirurgical** : plus petit changement qui
obtient l'effet, ne casse pas la structure, ne touche pas aux étapes finales
(gardes, git, mail). Reste dans le ton maison (direct, dense, pas corporate).

### b) Correction d'un fait mémoire
« c'est faux », « supprime cette info », « en vrai c'est X » → édite le fichier
`core-memory/` concerné (`profile.md`, `family.md`, `people.md`,
`australia-plan.md`…). Factuel et conservateur : applique ce qu'il dit sans
réécrire le reste ni inventer.

### c) Event(s) agenda
Il veut réserver/bloquer/ajouter un créneau (« réserve l'escalade dimanche 10h »)
→ pour **chaque** event, écris `calendar/<YYYY-MM-DDTHH-MM-SS>-<veille>-<n>.md`
(n = index si plusieurs), front matter EXACTEMENT :

```yaml
---
task: adapt_prompt
kind: calendar
status: requested
veille: <slug>
source_reply: <nom du fichier replies/…md>
summary: <titre court et clair>
start: "<YYYY-MM-DDTHH:MM:SS>"   # heure locale Paris ; ou "YYYY-MM-DD" si journée
end: "<YYYY-MM-DDTHH:MM:SS>"     # "" si tu ne sais pas (durée 1h par défaut)
all_day: false
location: <lieu, ou "">
description: <détail utile tiré du contexte, ou "">
---
```

Résous les dates relatives par rapport au `date` de l'étape 1. **Si tu ne peux
pas déterminer un jour/heure concret**, ne mets PAS d'event en file : signale-le
dans le récap pour que Sylvain précise (pas d'event inventé).

### Garde-fous (tous leviers)
- **Zones éditables : UNIQUEMENT** `.claude/commands/`, `core-memory/` (édition
  directe) et `calendar/` (mise en file). **Jamais** `core-memory/policies.md`,
  `current-location.md`, `usage.json`, ni le code / workflows / `schedule.yaml`.
- Si une demande violerait `policies.md` (OPSEC, validation) ou est trop vague
  pour agir sûrement → n'agis pas sur ce point, marque-le pour clarification.

### Clore la réponse
Édite le front matter du `replies/…md` : `status: done`, ajoute `done_at: <iso>`
et `actions_summary: <une ligne listant ce que tu as fait>`. Si une partie
reste ambiguë : `status: needs_clarification` + `note: <quoi préciser>`. Ne
supprime jamais le fichier (trace + anti-re-traitement par la GHA).

## Étape 3 — Récap (envoyé par mail)

Écris **un seul** `working-memory/<YYYY-MM-DD-HHMM>-adapt_prompt.md` (HHMM = UTC),
front matter minimal (retiré du mail) :

```yaml
---
task: adapt_prompt
run_at: <YYYY-MM-DDTHH:MM:SS+00:00>
status: completed
---
```

Corps dense, markdown propre — pour chaque réponse traitée :
- la **veille** + le **retour de Sylvain** (cité court) ;
- **ce que j'ai fait**, par levier : prompt ajusté (section + avant/après en
  1-2 lignes), fait mémoire corrigé, event(s) mis en file (titre + date — précise
  qu'ils seront créés par la GHA au passage suivant) ;
- si `needs_clarification` : mets-le en avant, c'est une action attendue de lui.

## Étape 4 — Journal (si changement structurel)

Si un edit change durablement une veille, append une ligne à
`journal/decisions.md` :

```
## <YYYY-MM-DD> — adapt_prompt : <veille> ajustée
Retour Sylvain : "<court>". Fait : <quoi>. (auto via /adapt_prompt)
```

## Étape 5 — Commit + push

```bash
git add replies/ calendar/ working-memory/ .claude/commands/ core-memory/ journal/decisions.md
git commit -m "auto: adapt_prompt run <YYYY-MM-DDTHH:MM:SSZ>"
git push -u origin HEAD   # retry x4 backoff 2/4/8/16s si erreur réseau
```

**Pousse sur ta branche courante, ne te bats jamais pour `main`, ne demande
aucune confirmation de branche.** Jamais de `--force`. Si l'étape 1 a skippé, tu
as déjà commité le log skip et tu t'es arrêté.

## Étape 6 — Propagation & exécution (automatique, hors routine)

Tu n'as **rien à faire ici**. Dès que ton push arrive sur ta branche `claude/**` :

- `sync-veille-to-main.yml` recopie sur `main` : ton récap, les `replies/*.md`
  (statut), les `calendar/*.md` (events en file `requested`), les
  `.claude/commands/*.md` et `core-memory/*.md` édités. C'est ce qui rend tes
  éditions effectives ET met les events à portée de la GHA.
- `tasks/prompt_feedback.py` (GHA, au passage suivant) lit les `calendar/*.md`
  `requested`, **crée les events** sur l'agenda via l'API, passe en `created`,
  et notifie avec le lien.
- `mail-report.yml` envoie ton récap `*-adapt_prompt.md` par mail.

Tu ne pousses donc jamais sur `main` toi-même, et tu ne touches jamais à l'API
Calendar toi-même — la GHA est tes mains pour ça.
