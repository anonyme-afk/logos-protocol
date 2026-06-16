# Logos-Lite — Compatible modèles 3B à 13B

> *"Ce que le modèle peut comprendre est plus important que ce qui est optimal."*

---

## Pourquoi Logos-Lite existe

Logos v4/v5 utilise :
- Symboles unicode : `∅`, `✓`, `Δ`, `⊕`, `!!`
- Blocs structurés : `[L3: ...]`, `[L4: ...]`, `[TREE:v5]`
- Aliases complexes : `@e1=ConnectionPoolExhaustionException`

Les modèles <7B paramètres tokenisent souvent les symboles unicode en fragments illisibles,
et ne suivent pas de schémas structurés sans capacités de raisonnement suffisantes.

Logos-Lite est le sous-ensemble qui fonctionne sur **tout modèle ≥3B**.

---

## Format Logos-Lite

### Règle d'or : ASCII seulement, majuscules pour les résultats

```
# AUTORISÉ en Logos-Lite
t-1d   t+1d   t-2h   Nh    (temps en ASCII)
FAIL   OK     SKIP   DONE  (résultats en MAJUSCULES)
fix:X  check:X  find:X  deploy:X  test:X  (actions avec colon)
A->B   A<-B   (causalité en ASCII)
| (séparateur)
stuck  frustrated  confused  (état émotionnel, mots simples)

# INTERDIT en Logos-Lite (remplacer par ASCII)
∅  → FAIL ou NULL
✓  → OK
Δ+ → IMPROVED
!!  → KEEP ou EXACT
[L3: ...] → format linéaire simple
[TREE:v5] → liste avec indentation
@alias → utiliser le mot entier ou abréviation commune
```

---

## Correspondances v4 → Lite

| Logos v4 | Logos-Lite | Commentaire |
|----------|-----------|-------------|
| `y:8h fix:auth x` | `t-1d 8h fix:auth FAIL` | `y:` → `t-1d`, `x` → `FAIL` |
| `find:localStorage=ROOT` | `find:localStorage ROOT` | `=ROOT` → `ROOT` séparé |
| `@bug1=!!token_issue` | `bug1=token_issue` | pas de `@` ni `!!` |
| `[TREE:v5] ├─ ...` | indentation simple | arbre → liste indentée |
| `!!DEAD:JWT_correct` | `DEAD:JWT_correct` | `!!` → préfixe `DEAD:` |
| `Δ+perf:40%` | `perf+40%` | `Δ+` → suffixe `+` |
| `[H: y:8h JWT]` | `[H: t-1d JWT]` | même structure, ASCII |

---

## Exemple complet Logos-Lite

**Session debug JWT sur Llama 7B / Mistral 7B :**

```
[LOGOS-LITE]
Format: t-1d=yest t+1d=tom Nh=dur fix:X check:X find:X = actions
FAIL OK DONE = results | = sep [H: summary] after each response

Turn 1 compressed:
t-1d 8h fix:auth FAIL | check:JWT FAIL | check:localStorage ROOT
fix:add_setItem DONE | test:3/3 OK
```

**vs Logos v4 :**
```
y:8h fix:auth x | check:JWT x | find:localStorage=ROOT
fix:add_setItem ok | test:3/3 ok
```

Token count différence : ~15% de plus en Lite (ASCII prend légèrement plus de place).
Mais le modèle *comprend* au lieu de *parser du bruit*.

---

## Tree Lite : version arbre sans unicode

```
[TREE-LITE]
ROOT: debug:auth t-1d 8h
  HYP:JWT.expiry   -> T2 -> DEAD:JWT_correct
  HYP:server_cfg   -> T4 -> DEAD:cfg_correct
  HYP:localStorage -> T6 -> ROOT_CAUSE
    fix:add_setItem -> test:3/3 -> SOLVED
```

vs Tree v5 avec unicode :
```
[TREE:v5]
ROOT: debug:auth y:8h
├─ HYP:JWT.expiry → T2 → !!DEAD:expiry_correct
├─ HYP:server_cfg → T4 → !!DEAD:cfg_correct
└─ HYP:localStorage → T6 → !!ROOT_CAUSE
```

Logos-Lite Tree est légèrement plus verbeux mais ne contient aucun caractère qui puisse
être mal tokenisé par un petit modèle.

---

## Prompt Logos-Lite (26 tokens)

```
LOGOS-LITE compact log. Rules: t-1d=yesterday t+1d=tom Nh=dur
fix:X check:X find:X = actions FAIL OK DONE = results | = sep
After each response: [H: 10-word summary in Lite format]
```

---

## Test de compatibilité pour votre modèle

Envoyez cette phrase au modèle :

```
Décompresse et explique en français normal :
t-1d 8h fix:auth FAIL | check:db FAIL | find:localStorage ROOT | fix:add_setItem OK
```

Si le modèle répond correctement → utilisez Logos-Lite.
Si le modèle est confus → revenez au langage naturel.

---

## Quand passer de Lite à v4

Si votre modèle supporte correctement Logos-Lite, testez ensuite :

```
[H: y:8h fix:auth x | find:localStorage=ROOT]
```

Si `y:` et `=ROOT` et `x` sont bien compris → le modèle supporte v4 complet.
Si confusion → restez en Lite.

La plupart des modèles 7B+ (Llama 3 8B, Mistral 7B, Qwen 7B) supportent v4.
Les modèles 3-4B (Phi-3 mini, Llama 3.2 3B) ont besoin de Lite.

---

*Logos-Lite : parce qu'une compression qui marche à 1.4× vaut mieux qu'une compression parfaite qui casse tout.*
