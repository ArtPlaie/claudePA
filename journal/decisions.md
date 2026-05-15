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

