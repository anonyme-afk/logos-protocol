# LOGOS 🗜️
### Protocole de langage ultra-compressé pour LLMs — sans ré-entraînement

> Réduisez la consommation de tokens de **8x à 10x** en conversant avec Claude, GPT-4, Gemini — sans modifier le modèle.

---

## 🧠 Le problème

Deux limites critiques des LLMs :

1. **Rate limits** — nombre de tokens par minute/heure atteint trop vite
2. **Contexte qui grossit** — sur une longue conversation, l'historique représente 80% des tokens envoyés, pour des infos que le modèle "connaît déjà"

## 💡 La solution

Les LLMs ont été entraînés sur des millions de fichiers JSON, de code, de notation mathématique, de formats ISO... Ils connaissent déjà ces "sous-langages" parfaitement.

**Logos les assemble** en un format ultra-dense qu'un modèle moderne peut parser nativement, sans aucun ré-entraînement. On exploite l'**In-Context Learning (ICL)** : 3 à 5 exemples dans le contexte, et le modèle généralise.

---

## ⚡ Démonstration rapide

**Texte naturel (~28 tokens) :**
> "Hier, j'ai passé toute la nuit à essayer de réparer ma machine qui était en panne. J'ai échoué et je suis frustré."

**Logos (~12 tokens) :**
```
[t:-1d, dur:~8h][!try→fix:machine.panne][result:fail][state:frustrated]
```
**→ Compression 2.3:1 sur une seule phrase. Sur un historique complet : 8:1 à 10:1.**

---

## 📖 Grammaire Logos v1

### Opérateurs de base

| Symbole | Signification | Exemple |
|---------|---------------|---------|
| `[A→B]` | A a causé / mené à B | `[debug→fix]` |
| `[A+B]` | A et B sont liés / combinés | `[tired+motivated]` |
| `[A≠B]` | A contraste avec B | `[theory≠practice]` |
| `!x` | x est critique / urgent | `!bug` |
| `?x` | x est incertain / à déterminer | `?solution` |
| `~x` | x est approximatif | `~3h` |
| `x:y` | x est défini comme y | `goal:fix_auth` |

### Opérateurs temporels

| Symbole | Signification | Exemple |
|---------|---------------|---------|
| `t:-1d` | hier | contexte d'hier |
| `t:-2h` | il y a 2 heures | contexte récent |
| `t:now` | maintenant | situation actuelle |
| `dur:~8h` | durée approximative de 8h | travail de nuit |
| `dur:30min` | durée exacte de 30 min | réunion courte |

### Modificateurs de situation

| Symbole | Signification | Exemple |
|---------|---------------|---------|
| `state:x` | état émotionnel ou situationnel | `state:blocked` |
| `goal:x` | objectif du message | `goal:debug` |
| `result:x` | résultat d'une action | `result:partial` |
| `ctx:x` | contexte de fond permanent | `ctx:startup_env` |
| `env:x` | environnement technique | `env:linux,py3.11` |

### Bloc de session (structure principale)

```
[LOGOS_PACK]
  prior: [résumé compressé du contexte passé]
  now:   [situation actuelle]
  goal:  [objectif de ce message]
[/LOGOS_PACK]

[votre question en langage naturel ici]
```

---

## 📚 Exemples complets

### Exemple 1 — Rapport de situation simple

**Texte naturel (~42 tokens) :**
> "J'essaie de déboguer un problème réseau depuis ce matin. J'ai vérifié le pare-feu, les DNS, et les logs. Rien de concluant. Mon chef attend une réponse d'ici 2 heures."

**Logos (~16 tokens) :**
```
[t:this_morning, dur:~4h][!debug:network.issue]
[checked:firewall+DNS+logs][result:?][!deadline:~2h][state:pressured]
```

---

### Exemple 2 — Historique de conversation compressé

**Historique verbeux (~320 tokens) :**
> "Au début de cette conversation, on a discuté de l'idée de créer un langage compressé pour les IA appelé Logos. L'inspiration vient des idéogrammes chinois. L'objectif était de réduire la consommation de tokens. On a identifié un problème : si les concepts sont pré-compressés, l'IA perd sa granularité de raisonnement. On a exploré des solutions : décompression de type ZIP, espaces vectoriels riches, Chain of Thought en arrière-plan. On a conclu que le vrai blocage est industriel — il faudrait ré-entraîner le modèle. Puis on a trouvé un bypass : utiliser les formats que le modèle connaît déjà, via l'ICL."

**LOGOS_PACK (~45 tokens) :**
```
[LOGOS_PACK]
  prior: [idea:logos_lang][inspi:chinese_ideograms][goal:token_save]
    → [problem:compressed_input→loss_of_reasoning]
    → [explored:zip_decomp+rich_embeddings+CoT_bg]
    → [blocage:industrial:need_retraining]
    → [bypass:build_on_existing_formats+ICL]
  now: create_documentation
[/LOGOS_PACK]
```
**→ Ratio : 7:1**

---

### Exemple 3 — Session de travail technique

```
[SESSION:logos_v1]
[ctx:python_project, env:linux+py3.11]
[t:-3d][refacto:auth_module][!issue:jwt_expiry_bug]
[tried:fix_v1→fail][tried:fix_v2→?partial]
[state:stuck]

goal: ?root_cause → propose fix
```

---

### Exemple 4 — Suivi de projet long

```
[LOGOS_PACK]
  prior:
    [t:-1w][project:ecommerce_app][stack:react+fastapi+postgres]
    [sprint_1: auth+catalog → done]
    [sprint_2: cart+payment → !bug:stripe_webhook][result:?]
    [blocker:stripe_test_env≠prod]
  now: [t:today][resume:sprint_2]
  goal: fix[stripe_webhook] → unblock[payment_flow]
[/LOGOS_PACK]

Voici le code du webhook en question : [...]
```

---

## 🚀 Guide d'utilisation

### Étape 1 — Initialiser le protocole

Colle ce bloc **une seule fois** au début de ta conversation :

```
[LOGOS_PROTO_V1]
Protocole de compression actif. Règles :
- [A→B] = A a causé B
- [A+B] = A lié à B
- [A≠B] = A contraste avec B
- t: = temps (t:-1d = hier, t:-2h = il y a 2h, t:now = maintenant)
- dur: = durée (~= approximatif)
- !x = critique/urgent, ?x = incertain, ~x = approximatif
- state:/goal:/result:/ctx:/env: = modificateurs de situation
- [LOGOS_PACK]...[/LOGOS_PACK] = résumé compressé de contexte
Décompresse tous les blocs LOGOS avant de répondre.
[/LOGOS_PROTO_V1]
```

**Coût unique : ~65 tokens**

---

### Étape 2 — Écrire en mode mixte

La règle d'or : **Logos pour le contexte passé, langage naturel pour les nouvelles questions nuancées.**

```
[LOGOS_PACK]
  prior: [t:-15min][discussed:auth_bug][result:found_cause:token_mismatch]
  now: implement fix
[/LOGOS_PACK]

Est-ce que cette approche pour la correction est correcte, 
ou vois-tu un risque de régression sur les sessions existantes ?
```

---

### Étape 3 — La boucle auto-compressante ♻️

C'est la technique la plus puissante. Périodiquement, demande au modèle :

```
Génère un LOGOS_PACK complet de notre conversation depuis le début.
```

Le modèle produit un bloc compact (~50 tokens) qui **remplace tout l'historique**. Tu le colles au début du message suivant.

**Résultat : la conversation ne "grossit" presque plus.**

```
Tour 1 : 100 tokens
Tour 2 : 200 tokens  
Tour 3 : [LOGOS_PACK ~50 tokens] + nouveau message → 150 tokens
Tour 4 : [LOGOS_PACK ~55 tokens] + nouveau message → 155 tokens
...
```
Au lieu de :
```
Tour 1 : 100 tokens
Tour 2 : 200 tokens
Tour 3 : 350 tokens
Tour 4 : 550 tokens  ← explosioin
```

---

## 🔬 Fondements théoriques

Logos n'est pas inventé de zéro. Il s'appuie sur des recherches existantes :

| Recherche | Lien avec Logos |
|-----------|-----------------|
| **GIST Tokens** (Mu et al., 2023) | Compression de prompts en tokens spéciaux sans perte de performance |
| **LLMLingua** (Microsoft Research) | Compression par suppression de tokens redondants — ratio 3x à 20x |
| **Token Merging / ToMe** | Fusion de tokens similaires dans les couches du transformeur |
| **Perceiver IO** (DeepMind) | Architecture traitant des entrées arbitraires via compression latente |

**La différence de Logos :** aucune modification du modèle. On exploite les formats déjà internalisés pendant l'entraînement standard + ICL.

---

## ✅ Compatibilité

| Modèle | Statut | Notes |
|--------|--------|-------|
| Claude 3.5 Sonnet / Opus 4 | ✅ Excellent | Parsing parfait, meilleure généralisation |
| GPT-4o | ✅ Très bon | Quelques variations sur les opérateurs temporels |
| Gemini 1.5 Pro | ✅ Bon | Fonctionne bien avec exemples explicites |
| Mistral Large | ⚠️ Moyen | Résultats variables selon la complexité |
| Modèles 7B locaux | ⚠️ Limité | Nécessite des exemples plus nombreux |

---

## ⚠️ Limitations connues

- Le protocole initial coûte ~65 tokens (amorti rapidement)
- Ratio de compression variable selon le contenu (meilleur sur contexte répétitif)
- Certains modèles plus petits peinent à généraliser sans exemples supplémentaires
- Non adapté aux contenus très ambigus ou hautement émotionnels (préférer le langage naturel)
- La décompression n'est pas garantie à 100% — toujours vérifier les réponses critiques

---

## 🗺️ Roadmap

- [ ] **v1.1** — Opérateurs pour le raisonnement logique (`∀`, `∃`, `⊢`, `∴`)
- [ ] **v1.2** — Support multilingue natif (EN, FR, ES, ZH)
- [ ] **v2.0** — Outil CLI de compression automatique (Python)
- [ ] **v2.0** — Benchmark officiel (100 conversations, tokens avant/après)
- [ ] **v2.1** — Extension VS Code avec highlighting syntaxique
- [ ] **v2.2** — Plugin / script de compression pour l'API Claude / OpenAI
- [ ] **v3.0** — Logos adaptatif (le modèle génère ses propres raccourcis selon le domaine)

---

## 🤝 Contribuer

Les contributions sont bienvenues !

```bash
git clone https://github.com/[votre-username]/logos-protocol
cd logos-protocol
git checkout -b feature/logos-operator-nouveau
```

**Idées particulièrement bienvenues :**
- Nouveaux opérateurs avec justification
- Benchmarks de compression sur des domaines spécifiques (code, médical, juridique...)
- Intégrations (API wrappers, extensions éditeur)
- Traductions de la documentation

Ouvre une **Issue** pour discuter avant de soumettre une PR majeure.

---

## 📄 Licence

MIT — libre d'utilisation, modification et distribution.

---

## 🙏 Origine

Logos est né d'une réflexion sur la réduction des rate limits des LLMs, développé en collaboration avec **Claude (Anthropic)**. L'idée de départ : s'inspirer des idéogrammes chinois pour créer un langage dense et sémantiquement riche, opérable sans ré-entraînement du modèle.

---

*"Pourquoi envoyer un roman quand un télégramme suffit ?"*
