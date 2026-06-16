# Logos v5 — System Prompts

---

## Le Prompt Essentiel : PRC (Progressive Rolling Compression)

### Pourquoi ce prompt existe

Le `/pack` manuel casse le rythme. Ce prompt fait la même chose **automatiquement**,
à chaque tour, sans que vous ayez à intervenir.

### Le prompt (27 tokens — à coller en début de conversation)

```
[LOGOS:v5]
After each response, append [H: <10-token Logos summary of this exchange>].
Read all [H:] blocks silently before each new response.
Format: y:=yest -Nd=past fix:x ok FAIL -> <- | @alias
```

### Ce que ça donne en pratique

```
You: Yesterday I spent all night debugging the JWT auth issue

Claude: Let me help. What error are you seeing exactly?
[H: y:8h debug:JWT -> q:err?]

You: The token expires after 1h even though I configured 24h

Claude: This typically means the server config overrides the client setting.
Check your token validation middleware...
[H: 1h-expire<-cfg_override? check:middleware]

You: Found it — localStorage wasn't saving the refresh token

Claude: That's the root cause. Fix: add localStorage.setItem('refresh_token', token)
after successful auth.
[H: find:localStorage=ROOT fix:add_setItem]
```

**Résultat**: après 10 tours, l'historique compressé fait ~80-100 tokens
au lieu de ~1500 tokens. Sans aucune action de votre part.

---

## Prompt Complet avec Tree PACK

Pour les sessions de debug longues avec plusieurs hypothèses :

```
[LOGOS:v5]
PRC: after each response append [H: <10t Logos v4 summary>]
TREE: when asked /pack, generate [TREE:v5] with !!DEAD branches for rejected hypotheses
Format: y:=yest -Nd=past Nh=dur fix:x ok FAIL -> <- | @alias !!x=verbatim
Compat: ASCII-only if model seems confused by unicode
```

### Exemple de /pack avec Tree

```
You: /pack

Claude:
[TREE:v5]
ROOT: debug:auth y:8h
├─ HYP:JWT.expiry  → T2 → !!DEAD:expiry_correct
├─ HYP:server_cfg  → T4 → !!DEAD:cfg_correct
└─ HYP:localStorage → T6 → !!ROOT_CAUSE
   └─ fix:add_setItem → test:3/3 → !!SOLVED
[VOC: @auth_bug=!!localStorage_not_saving_refresh_token]
```

Copiez ce bloc. Au prochain message, collez-le en haut.
L'IA se souvient de tout, y compris ce qui a été rejeté.

---

## Prompt Logos-Lite (modèles 3B-13B)

Pour les modèles locaux (Ollama, LM Studio, etc.) :

```
LOGOS-LITE: compact log format.
Rules: t-1d=yesterday t+1d=tomorrow Nh=duration
fix:X check:X find:X deploy:X = actions
FAIL OK = results | = separator
Keep [H: 10-word summary] after each response.
```

**Exemple :**
```
t-1d fix:auth FAIL | check:db FAIL | stuck frustrated
```

---

## Choisir son prompt selon la situation

| Situation | Prompt recommandé |
|-----------|------------------|
| Session courte (<5 tours) | Aucun — juste parler normalement |
| Session moyenne (5-20 tours) | PRC essentiel (27 tokens) |
| Debug complexe (>10 tours, hypothèses multiples) | Complet avec Tree |
| Modèle local <13B | Logos-Lite |
| Reprise d'une session | Coller le Tree PACK précédent + PRC essentiel |

---

## La règle des 5 tours

Ne pas activer PRC si vous pensez avoir moins de 5 échanges.
Le boot de 27 tokens n'est rentable qu'à partir du 5ème tour.

Pour moins de 5 tours : parler normalement. Logos n'aide pas.

---

## Anti-patterns confirmés

```
❌ Utiliser Logos pour des messages courts ("ok", "merci", "continue")
❌ Compresser du code — jamais
❌ Compresser des nombres/métriques — jamais  
❌ Utiliser Logos-Lite sur GPT-4/Claude (moins efficace que v4 sans raison)
❌ Faire un /pack à chaque message (overhead > gain)
✅ PRC pour tout sauf sessions <5 tours
✅ Tree PACK pour les sessions debug avec hypothèses multiples
✅ Logos-Lite pour les modèles locaux < 13B
```
