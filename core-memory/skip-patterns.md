# Skip patterns

> Append-only. Chaque SKIP Telegram sur un draft enregistre ici le pattern
> refusé. `_lib/notify.py` consulte ce fichier avant chaque nouveau draft.
>
> Format : un bloc YAML par entrée, séparé par `---`. Sylvain peut éditer
> à la main pour nettoyer, élargir, ou ajouter des patterns proactifs.
>
> Champs :
> - `type` : email_send | event_book | reminder | content_post | …
> - `subject_match` : substring ou regex matchée dans le sujet du draft
> - `reason` : raison libre (optionnelle, fournie par Sylvain en reply)
> - `expires` : date après laquelle le pattern n'est plus appliqué (90j par défaut)
> - `created_at` : date du SKIP

# Patterns actifs

(vide au démarrage — alimenté au fil des SKIP)
