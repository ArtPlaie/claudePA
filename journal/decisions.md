# Journal des décisions

> Append-only. On y consigne les décisions importantes (techniques, perso,
> famille, carrière) au fil de l'eau. Le `self_reflection` mensuel s'en
> sert comme référence d'or pour évaluer la trajectoire vs intentions.
>
> Écriture autonome interdite par les agents (cf. `policies.md`) — Sylvain
> ajoute les entrées ou autorise explicitement un draft d'ajout.
>
> Format : section par décision, datée, courte (3-10 lignes).

---

## 2026-05-15 — Lancement claudePA

**Décision** : créer un assistant personnel cloud (`claudePA`) hébergé sur
GitHub Actions, avec mémoire en markdown versionné, validation humaine
systématique, ton "bro" sans sycophantie. Spec complète dans `SPEC.md`.

**Pourquoi** : externaliser la charge mentale des veilles (Sydney, AI/AI
Safety, mails, activités locales, santé), garder un humain dans la boucle,
préparer le départ Australie 6-18 mois.

**À évaluer dans 3 mois** : ratio signal/bruit, fréquence des SKIP, coût
tokens réel vs budget $30/mois, utilité réelle du `weekly_briefing` famille.

---

## 2026-05-15 — Phase 1 livrée + déprécation canal famille

Décisions prises pendant la session de bootstrap (cf.
`working-memory/2026-05-15-1909-session-bootstrap.md`).

1. **Archi V2 spec retenue** : Cloudflare Worker (gratuit, h24, edge) +
   GitHub Actions (gratuit, à la demande). Pas de VPS. Latence aller-
   retour 30-90s sur questions ouvertes (cold start Actions), <2s sur
   commandes simples. Coût hosting : $0. Portable plus tard si besoin
   (~50 lignes JS spécifiques CF, le reste est du Python standard).

2. **Canal `famille` déprécié** : Isa n'utilise pas Telegram. Les 3
   tâches qui étaient sur `channel: famille` (`local_activities`,
   `activities_next10days`, `weekly_briefing`) basculent sur `perso`.
   Le code garde le concept au cas où elle reviendrait, mais aucun
   `TELEGRAM_CHAT_FAMILLE` n'est en place.

3. **Default branch renommée `claude/main`** (au lieu de `main`).
   `GITHUB_REF` du Worker pointe dessus.

4. **Validation humaine systématique conservée pour V1** : `apply_draft.py`
   marque `approved` sur OK mais aucun actuator externe n'est wiré
   (pas de gmail.send, pas de paiement). Sylvain exécute à la main.
   Plan d'élargissement semaine 5-8 selon `policies.md`.

**À évaluer dans 1 mois** : latence ressentie sur questions ouvertes (le
cold start est-il acceptable au quotidien ?), bug paste PowerShell ↔
wrangler résolu durablement via dashboard CF, premier mois de
`daily_digest` actif (signal/bruit).

---

## 2026-06-08 — Migration orchestration des veilles vers Claude Code Routines

Décisions prises pendant la session de design (cf.
`working-memory/2026-06-08-1257-session-routines-migration.md`). Entrée
ajoutée sur dérogation explicite de Sylvain.

1. **Bascule veilles → Routines** : les veilles (`weekly_briefing`,
   `ai_jobs_formations`, `sydney_opportunities`, `local_activities`,
   `activities_next10days`, `health_watch`) passent de GitHub Actions + CF
   Worker à des **Claude Code Routines** schedulées sur l'infra Anthropic.
   Logique versionnée dans `.claude/commands/<task>.md`, prompt de routine
   trivial. **Pourquoi** : WebSearch natif (résout la décision Brave/Tavily
   restée ouverte), supprime `_lib/llm.py`/clé API/gate budget pour les
   veilles, et la session lit `core-memory/*.md` en direct (fin de la
   "photo" qui périme dans `prompts/`). GHA/CF gardés pour les tasks Python
   legacy + futur PA Telegram inbound.

2. **Push direct sur `main`** pour les routines (unrestricted branch pushes
   ON), réseau **Full**, livraison v1 = lire le rapport committé dans le
   repo (connecteur Telegram/email plus tard).

3. **Mémoire inter-session fixée** : les handovers se pushent sur `main`
   (pas sur une branche feature) et sont lus au démarrage de chaque session
   — sinon invisibles, car Sylvain ouvre toujours depuis `main`. Les
   `working-memory/*-session-*.md` sont exemptés de la purge 30j.

4. **Pilote = `sydney_opportunities`** avant de convertir les 5 autres
   veilles. Pas encore codé au moment de cette entrée.

**À évaluer dans 1 mois** : la boucle routine tourne-t-elle sans
babysitting (commit fiable, pas de faux "vert") ? Qualité du web search
natif vs attentes ; faut-il finalement migrer aussi les 4 tasks GHA.

---

## 2026-07-20 — adapt_prompt : serendipity ajustée
Retour Sylvain : "pas que des trucs à faire, ras-le-bol du grandiloquent
('boss', armoiries), et la structure Hook ça me fait chier". Fait : scope
élargi aux idées pures (pas juste activités/events), garde-fou de ton ajouté
(traiter comme un pote normal, pas de callback exploits/pompeux), structure
"Hook" retirée du format de sortie. (auto via /adapt_prompt)

