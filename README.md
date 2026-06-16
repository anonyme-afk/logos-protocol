# LOGOS 🗜️
### Token compression pour LLMs — sans réentraînement, sans friction

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-5.0-blue.svg)](spec/GRAMMAR_v5.md)
[![Honest](https://img.shields.io/badge/benchmarks-honest-green.svg)](spec/HONEST_BENCHMARKS.md)

> **Étendez votre session Claude/GPT de 3 à 7×** en compressant l'historique automatiquement.
> Zéro friction. Zéro réentraînement. Fonctionne aujourd'hui.

---

## Le vrai problème

Chaque message re-envoie l'**intégralité** de l'historique de conversation.
À la 20ème question : 3000+ tokens d'historique, dont 80% sont redondants.

Logos compresse cet historique **automatiquement, à chaque tour** (v5 PRC).

---

## Benchmarks honnêtes

> Les premières versions (v1-v3) annonçaient 8-20× basé sur des comptages de *caractères*.
> Les vrais chiffres en tokens BPE :

| Usage | CR réel mesuré | Vaut le coup ? |
|-------|----------------|----------------|
| Phrase isolée | 1.5-2× | 🟡 Marginal |
| Paragraphe | 2-3× | ✅ Oui |
| Historique de session | **3-7×** | ✅✅ Absolument |
| Concepts répétés (@alias) | **5-15× par réutilisation** | ✅✅ Majeur |

---

## Quick Start (30 secondes)

**Option 1 — Zéro friction (recommandé) :**
Collez ce prompt au début d'une nouvelle conversation :

```
[LOGOS:v5]
After each response, append [H: <10-token Logos summary of this exchange>].
Read all [H:] blocks silently before each new response.
Format: y:=yest -Nd=past fix:x ok FAIL -> <- | @alias
```

C'est tout. Le modèle compresse automatiquement à chaque tour.

**Option 2 — CLI local :**
```bash
git clone https://github.com/anonyme-afk/logos-protocol
python tools/logos-v4.py cheatsheet
python tools/logos-v4.py auto "Yesterday I spent all night fixing the auth bug"
python tools/logos-v4.py session
```

---

## Syntaxe v4 (bracket-free — le vrai format qui marche)

```
TIME:     y:=hier  +1d:=demain  -Nd:=il y a N jours  Nh=durée
RÉSULTAT: x=échec  ok=succès  !=critique préfixe
ACTION:   fix:X  check:X  find:X  deploy:X  test:X
CAUSAL:   A->B=A cause B  A<-B=A parce que B
ÉTAT:     frustrated  stuck  blocked  (mot simple, toujours en fin)
SEP:      |  (séparateur de clauses)
ALIAS:    @x=définition  (rentable seulement si utilisé 3+ fois)
VERBATIM: !!x  (jamais compressé — pour les infos critiques)
```

**Exemple :**
```
"Hier j'ai passé la nuit à corriger le bug d'auth, échec, je suis bloqué"
→  y:8h fix:auth x | stuck
   11 tokens → 6 tokens  (CR ~1.8×)

"J'ai essayé fix:auth, échec. Vérifié db, pas ça. Maintenant bloqué."
→  fix:auth x | check:db x | stuck
   27 tokens → 9 tokens  (CR ~3×)
```

---

## Les 3 Problèmes Structurels Résolus (v5)

### Problème 1 : La friction du /pack

**Avant (v1-v4)** : devoir taper `/pack` toutes les 10 minutes casse le flow.

**v5 PRC** : le modèle compresse automatiquement le tour précédent à chaque réponse.
Zéro action utilisateur. [→ GRAMMAR_v5.md](spec/GRAMMAR_v5.md)

### Problème 2 : Élitisme des modèles

**Avant** : modèles <7B = ❌ inutilisable.

**Logos-Lite** : format ASCII-only sans symboles unicode. Compatible 3B+.
CR réduit (~1.3-1.8×) mais ça *marche*. [→ LOGOS_LITE.md](spec/LOGOS_LITE.md)

### Problème 3 : Perte des chemins secondaires

**Avant** : compression 1200→65 tokens = hypothèses rejetées disparues.
À T15, l'IA re-explore ce qu'elle a déjà réfuté.

**Tree PACK avec !!DEAD** : les branches mortes sont préservées avec leur verdict.
+30% de tokens vs classic pack. Économise ~200 tokens si changement de direction.
Rentable dès que prob(changement de cap) > 12%. [→ GRAMMAR_v5.md](spec/GRAMMAR_v5.md)

---

## Compatibilité

| Modèle | Format | CR attendu |
|--------|--------|-----------|
| <3B params | Langage naturel | — |
| 3B-7B | **Logos-Lite** | 1.3-1.8× |
| 7B-13B | Logos v4 (sans L3/L4) | 1.5-2.5× |
| 13B-70B | Logos v4 complet | 2-4× |
| Claude 3+, GPT-4+, Gemini 1.5+ | Logos v5 + PRC | 3-7× |

Test rapide : `python tools/logos-v4.py compat-check`

---

## Structure du repo

```
logos-protocol/
├── README.md
├── spec/
│   ├── GRAMMAR_v5.md         ← v5 : PRC + Tree + Lite (les 3 problèmes résolus)
│   ├── GRAMMAR_v4.md         ← v4 : bracket-free (le vrai format efficace)
│   ├── GRAMMAR_v3.md         ← v3 : niveaux L1-L4
│   ├── GRAMMAR_v2.md         ← v2 : ICL + @alias
│   ├── GRAMMAR.md            ← v1 : original
│   ├── LOGOS_LITE.md         ← format pour modèles 3B-13B
│   ├── HONEST_BENCHMARKS.md  ← vrais chiffres mesurés
│   ├── OPERATORS.md          ← référence rapide
│   └── BENCHMARK.md          ← framework de test
├── research/
│   ├── AUTO_DISCOVERY.md     ← 6 cycles de découverte automatique
│   ├── PAROXYSM_v2.md        ← 6 problèmes non résolus (maintenant résolus)
│   └── PAROXYSM.md           ← fondations théoriques
├── examples/
│   ├── examples-by-domain.md ← 6 domaines
│   └── v2-full-session.md    ← exemple de session complète
├── prompts/
│   ├── system-prompts-v5.md  ← prompts v5 avec PRC
│   └── system-prompts-v3.md  ← prompts v3
├── tools/
│   ├── logos-v4.py           ← CLI v4 (zero dep, auto-detect)
│   ├── logos-v3.py           ← CLI v3
│   └── logos-compress.py     ← CLI v1
└── tests/
    └── community_benchmarks.csv
```

---

## Ce qui reste impossible (honnêteté)

1. **L'extension navigateur** reste le Saint Graal. PRC réduit la friction à ~0, mais une extension qui injecte le pack et repart proprement sans aucune action = pas encore fait.
2. **Le plafond de Shannon** : ~2-3× max par message, ~5-7× max pour les sessions. Aucun format ne peut faire mieux sans perte d'information.
3. **Les petits modèles** : Logos-Lite aide, mais un modèle 3B reste fondamentalement limité. Ce n'est pas un problème de format, c'est un problème de capacité.

---

## Contribuer

**10 minutes** : prenez un message que vous avez envoyé à une IA cette semaine, compressez-le en Logos, testez la décompression, ajoutez une ligne à `tests/community_benchmarks.csv`.

**Plus grand** : portez logos-v4.py en JavaScript/TypeScript pour les extensions navigateur.

---

*Né de la frustration des rate limits. Affiné par l'auto-discovery. Honnête sur ses limites.*
MIT License.
