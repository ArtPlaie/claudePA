---
task: session-handover
run_at: 2026-07-18T21:20:00+00:00
status: completed
branch: claude/email-reply-prompt-adapt-6f81ue (tout aussi poussé sur main)
---

# Handover — session 2026-07-18 : boucle « réponse mail → le PA agit »

## Résumé

Construit une boucle où **Sylvain répond à un mail de rapport de veille** et le
PA agit en conséquence : (1) ajuste le prompt de la veille, (2) corrige un fait
de core-memory, (3) crée des events sur son agenda. Tout est sur `main` et
testé. **Un seul déblocage restant côté Sylvain** : générer le token OAuth
Calendar (`GCAL_TOKEN_JSON`) — guide dédié écrit (`docs/setup-gcal.md`), il le
fait demain.

## Architecture finale (IMPORTANT — 2 pièces, "cerveau + mains")

Contrainte structurelle : une routine Claude Code n'a **aucun accès externe**
(pas d'IMAP, pas d'API Calendar). Une GHA Python en a (tokens). D'où le split :

```
Tu réponds à un rapport (mail, éventuellement MIXTE : "sois concis ET réserve samedi ET corrige X")
   │
[GHA prompt_feedback — mains bêtes, ZÉRO LLM]
   ├─ récupère les réponses non-lues (IMAP compte PA) → replies/<ts>-<veille>.md (pending, brut)
   └─ exécute les events en file : calendar/*.md status=requested → API Calendar → status=created
   │
[Routine /adapt_prompt — SEUL cerveau, daily/2x-j]
   lit replies/ pending, décide TOUT par réponse :
   ├─ édite .claude/commands/<veille>.md   (comportement veille)
   ├─ édite core-memory/*.md               (fait mémoire ; jamais policies/current-location/usage)
   └─ met les events en file → calendar/<ts>-<veille>-<n>.md (status: requested)
   puis marque replies/ done + écrit un récap working-memory/*-adapt_prompt.md (envoyé par mail)
```

- **Pas de classifieur** : la routine (agent) lit le texte brut et gère les mails
  mixtes nativement. La GHA ne fait QUE l'I/O que la routine ne peut pas faire.
- **Propagation main** : la routine pousse sur sa branche `claude/**` ;
  `sync-veille-to-main.yml` recopie sur `main` : récap, `replies/*`, `calendar/*`
  (noms uniques, ungated) + `.claude/commands/*` et `core-memory/*` (gated : SEULEMENT
  si le push contient un `*-adapt_prompt.md`, et `policies.md` exclu en dur).
- **Mail** : `mail-report.yml` envoie le récap `*-adapt_prompt.md` (glob ajouté).

## Auth — le point qui a coûté du temps

- **Lecture inbox PA** : PAS d'OAuth. IMAP + `GMAIL_USER`/`GMAIL_APP_PASSWORD`
  (le MÊME app-password que le SMTP d'envoi de mail-report). Le token OAuth PA
  (`GMAIL_TOKEN_PA_JSON`) était **mort** (`invalid_grant`) → on a pivoté sur IMAP.
  Marche (prouvé : run réel a lu et déposé une réponse).
- **Écriture agenda** : OAuth du **compte perso de Sylvain**, scope
  `calendar.events`, secret `GCAL_TOKEN_JSON` (`tasks/_lib/gcal.py`). PAS ENCORE
  CRÉÉ — c'est le prochain pas.
- **Cause racine des tokens morts** : l'app OAuth est en mode **Testing** →
  Google expire les refresh tokens sous **7 jours**. Fix durable = publier l'app
  (In production). `docs/setup-gmail.md` dit le contraire (faux, à corriger).

## Fichiers clés créés/modifiés (tout sur main)

- `tasks/prompt_feedback.py` — pont I/O bête (IMAP fetch → replies/ ; actuate
  calendar/ → API). Task name gardé "prompt_feedback" (historique) même si le
  rôle a évolué.
- `.claude/commands/adapt_prompt.md` — la routine cerveau (Sylvain a créé la
  routine côté UI, daily 11h ; prompt : « Lance /adapt_prompt. Suis les étapes »).
- `tasks/_lib/gcal.py` — service Calendar + create_event.
- `scripts/setup_gmail_oauth.py` — ajout `--account gcal` (génère GCAL_TOKEN_JSON).
- `.github/workflows/task-prompt-feedback.yml` — cron natif GH toutes les 3h
  (workflow_dispatch aussi). Secrets : GMAIL_USER/APP_PASSWORD, MAIL_TO,
  GCAL_TOKEN_JSON, TELEGRAM_*. (Plus d'ANTHROPIC : plus de LLM côté GHA.)
- `.github/workflows/sync-veille-to-main.yml` — propage replies/calendar +
  commands/core-memory (gated adapt).
- `.github/workflows/mail-report.yml` — glob + NICE `adapt_prompt`.
- dossiers `replies/`, `calendar/` (+ `feedback/` legacy, une entrée applied).
- `core-memory/profile.md` + `family.md` — nettoyés (Isa : retiré
  étoiles/aurores inventées, garde "peint") suite à un vrai feedback de Sylvain.
- `core-memory/policies.md` — whitelist : event depuis réponse mail explicite OK.
- `docs/setup-gcal.md` — **le guide pas-à-pas OAuth Calendar** (à suivre demain).

## Décisions

- Calendar : **OAuth propre** (pas d'invitation .ics) + **création directe** (la
  réponse mail EST l'instruction, pas de re-validation).
- Un seul cerveau (routine) décide tout ; GHA = mains bêtes (choix Sylvain,
  meilleur pour les mails mixtes).
- Cadence routine : viser **2x/jour** (runs à vide quasi gratuits grâce au
  fast-exit « pas de pending → stop »). Sylvain doit régler ça dans l'UI routines.

## PROCHAIN PAS CONCRET (Sylvain, demain)

1. **Suivre `docs/setup-gcal.md`** de bout en bout → obtenir `GCAL_TOKEN_JSON` :
   - activer l'API Calendar dans le projet GCP `claudepa` ;
   - **publier l'app** (OAuth consent screen → Publish) pour tuer l'expiration 7j ;
   - lancer `uv run python scripts/setup_gmail_oauth.py --account gcal
     --client-secrets ~/oauth-client.json`, **connecté avec le compte perso** ;
   - coller le JSON dans le secret GitHub `GCAL_TOKEN_JSON`.
2. **Régler la routine `/adapt_prompt` en 2x/jour** côté UI claude.ai/code/routines.
3. **Test bout-en-bout** : répondre à un rapport « bloque un créneau test demain
   15h » → lancer `task-prompt-feedback` (dépose) → `/adapt_prompt` (met en file)
   → `task-prompt-feedback` (crée) → event sur l'agenda + notif Telegram.

## Points de vigilance

- Tant que `GCAL_TOKEN_JSON` absent : les events restent `status: requested`
  (rien perdu), la GHA notifie « OAuth agenda absent ». Ils se créeront au premier
  run après config.
- Si un token Google remeurt (`invalid_grant`) → c'est le mode Testing (7j).
  Publier l'app règle ça durablement (perso + PA aussi).
- Latence de la boucle : réponse → dépôt (≤3h) → routine (11h / 2x-j) → création
  event (≤3h). Dans la journée, pas instantané. Assumé.
- `docs/setup-gmail.md` contient une **info fausse** (« token n'expire pas en
  Testing ») — à corriger (proposé à Sylvain, pas encore fait).
