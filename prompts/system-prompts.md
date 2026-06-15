# Logos System Prompts

Copy-paste ready prompts to activate Logos in your LLM sessions.

---

## 🇫🇷 French — Minimal (recommended)

```
[LOGOS_PROTO_V1]
Protocole de compression actif. Règles d'interprétation :
- [A→B] = A a causé / mené à B
- [A+B] = A lié à B
- [A≠B] = A contraste avec B
- t: = temps (t:-1d=hier, t:-2h=il y a 2h, t:now=maintenant, t:+1d=demain)
- dur: = durée (~=approximatif)
- !x = critique/urgent, ?x = incertain, ~x = approximatif
- state:/goal:/result:/ctx:/env: = modificateurs de situation
- [LOGOS_PACK]...[/LOGOS_PACK] = bloc de contexte compressé
Décompresse tous les blocs LOGOS avant de répondre.
[/LOGOS_PROTO_V1]
```
**Token cost: ~65**

---

## 🇬🇧 English — Minimal (recommended)

```
[LOGOS_PROTO_V1]
Compression protocol active. Parsing rules:
- [A→B] = A caused / led to B
- [A+B] = A linked with B
- [A≠B] = A contrasts with B
- t: = time (t:-1d=yesterday, t:-2h=2h ago, t:now=now, t:+1d=tomorrow)
- dur: = duration (~=approximate)
- !x = critical/urgent, ?x = uncertain, ~x = approximate
- state:/goal:/result:/ctx:/env: = situation modifiers
- [LOGOS_PACK]...[/LOGOS_PACK] = compressed context block
Decompress all LOGOS blocks before responding.
[/LOGOS_PROTO_V1]
```
**Token cost: ~62**

---

## 🇫🇷 French — Extended (with examples, more reliable)

```
[LOGOS_PROTO_V1]
Protocole Logos actif. Règles :
- [A→B] = A a causé B
- [A+B] = A et B liés
- [A≠B] = A contraste avec B
- t:-1d = hier | t:-2h = il y a 2h | t:now = maintenant | t:+1d = demain
- dur:~3h = environ 3h
- !x = critique | ?x = incertain | ~x = approximatif
- state: état | goal: objectif | result: résultat | ctx: contexte | env: environnement

Exemples de décompression :
[t:-1d, dur:~8h][!try→fix:machine.panne][result:fail][state:frustrated]
→ "Hier j'ai passé ~8h à essayer réparer ma machine en panne, j'ai échoué, je suis frustré."

[LOGOS_PACK]
  prior: [bug:auth][tried:fix_v1→fail][tried:fix_v2→?partial]
  now: t:today
  goal: ?root_cause
[/LOGOS_PACK]
→ "Contexte : bug auth, deux tentatives de fix (1 échec, 1 partiel). Aujourd'hui : trouver la cause racine."

Décompresse tous les blocs LOGOS avant de répondre.
[/LOGOS_PROTO_V1]
```
**Token cost: ~130**

---

## 🇬🇧 English — Extended (with examples, more reliable)

```
[LOGOS_PROTO_V1]
Logos protocol active. Rules:
- [A→B] = A caused B
- [A+B] = A and B are linked
- [A≠B] = A contrasts with B
- t:-1d = yesterday | t:-2h = 2h ago | t:now = now | t:+1d = tomorrow
- dur:~3h = approximately 3 hours
- !x = critical | ?x = uncertain | ~x = approximate
- state: situation | goal: objective | result: outcome | ctx: background | env: environment

Decompression examples:
[t:-1d, dur:~8h][!try→fix:machine.failure][result:fail][state:frustrated]
→ "Yesterday I spent ~8h trying to fix a broken machine, failed, feeling frustrated."

[LOGOS_PACK]
  prior: [bug:auth][tried:fix_v1→fail][tried:fix_v2→?partial]
  now: t:today
  goal: ?root_cause
[/LOGOS_PACK]
→ "Context: auth bug, two fix attempts (1 failed, 1 partial). Today: find root cause."

Decompress all LOGOS blocks before responding.
[/LOGOS_PROTO_V1]
```
**Token cost: ~128**

---

## Usage Tips

1. **Use the minimal version** for experienced users / short sessions
2. **Use the extended version** when reliability matters or with smaller models
3. **Add domain-specific shortcuts** after the protocol block:
   ```
   [LOGOS_PROTO_V1]
   [... standard rules ...]
   Domain shortcuts: stack=react+fastapi+postgres, proj=ecommerce_app
   [/LOGOS_PROTO_V1]
   ```
4. **Refresh mid-session** if the model starts ignoring Logos (long sessions can drift):
   ```
   [LOGOS_REFRESH] Re-apply Logos protocol from session start.
   ```
