# Policies — autonomie, budget, OPSEC, garde-fous

> Source de vérité pour les agents au runtime. Modifiable manuellement
> par Sylvain à tout moment, ou via une proposition `self_reflection`
> validée.

## Budget tokens

| Paramètre | Valeur | Notes |
|---|---|---|
| Budget mensuel cible | $30 / mois | À ajuster après V1 mesurée |
| Alerte Telegram | 80 % du budget | Notif non-bloquante sur le bot perso |
| Refus d'appel | 100 % du budget | Toute nouvelle requête échoue jusqu'au reset mensuel |
| Reset | Le 1er du mois, 00:00 UTC | |
| Compteur | `core-memory/usage.json` (généré) | Mis à jour après chaque appel par `_lib/llm.py` |

## Autonomie — whitelist d'actions sans validation

Les actions ci-dessous **n'ont pas besoin** de passer par `drafts/` :

- Labellisation / archivage Gmail (sans envoi).
- Création de drafts Gmail (visibles dans l'app, pas envoyés).
- Ajout d'un événement *tentative* (visibilité privée) dans le calendar
  perso de Sylvain.
- Ajout d'entrées dans `digests/findings.md`.
- Mise à jour de `core-memory/current-location.md` par la tâche
  `location_context`.
- Notifications Telegram informatives (briefings, digests, alertes).

**Tout le reste passe par `drafts/`** — notamment :

- Envoi de mail (interdit techniquement au démarrage : pas de scope
  `gmail.send`).
- Réservation, achat, dépense.
- Post public (réseaux sociaux, commentaire externe).
- Modification de `core-memory/profile.md`, `policies.md`, ou
  `CLAUDE.md`.
- Ajout / suppression d'une tâche dans `schedule.yaml`.
- Acceptation / refus d'invitation calendrier partagé.

## OPSEC

Sylvain a un profil crypto public (@ArtPlaie). Risque de ciblage réel.

**Ne jamais exposer dans une communication externe** :

- Adresse précise (Bois-le-Roi est public, le numéro de rue ne l'est pas).
- Détails patrimoniaux (montants, comptes, plateformes spécifiques).
- Prénoms / âges / écoles des enfants.
- Plans de déplacement futurs (vacances, dates d'absence).
- Détails du système de sécurité domicile.

**Règle simple** : si un brouillon mentionne une de ces catégories, il
doit être marqué `opsec_review: required` dans le front matter et passer
par validation explicite Sylvain (pas validation automatique même si
whitelist).

## Sécurité technique

- Aucun secret en clair dans le repo. Tout via GitHub Secrets ou
  variables d'env injectées par les workflows.
- `.env` local jamais commité (cf. `.gitignore`).
- Pas de `git push --force` sur main.
- Tokens OAuth rotation : trimestrielle. Une tâche `secrets_rotation`
  notifiera Sylvain quand un refresh est nécessaire (V2).

## Idempotence & retry

- Chaque tâche écrit un `run_id` (uuid) dans le front matter de son
  fichier working-memory.
- Une relance manuelle d'un workflow ne doit pas re-créer un draft pour
  la même fenêtre temporelle (vérification par hash de contenu + date).
- Backoff exponentiel sur Anthropic API et Gmail API : 2s, 4s, 8s, 16s.

## Erreurs & alertes

- Toute exception non gérée → notif Telegram bot perso + écriture
  `working-memory/...-error.md` avec traceback.
- Si une tâche échoue 2 fois de suite → notif "FYI tâche X dégradée"
  sur Telegram perso.
- Si `sliding_window` échoue à produire un digest mensuel, **aucune
  purge** n'est effectuée (idempotence safety).

## Évolution de l'autonomie

Plan d'élargissement progressif (à valider tâche par tâche) :

1. **Semaines 1-4** : tout en draft.
2. **Semaines 5-8** : si confiance, ajouter scope `gmail.send` pour
   relances triviales pré-validées par template.
3. **Mois 3+** : envisager auto-réservation pour activités locales déjà
   pré-approuvées par Sylvain (whitelist nominative).

## Contacts d'urgence (pour le code, pas pour le LLM)

- Mainteneur : Sylvain Ribes.
- Canal d'alerte critique : Telegram bot perso.
- Si Telegram down : email principal de Sylvain (configuré via secret
  `EMERGENCY_EMAIL`).
