# Logos v2 — Adaptive Grammar Specification

> Logos v2 adds three things v1 lacked: **adaptive schemas**, **salience detection**, and **fidelity verification**.

---

## Core Additions vs v1

| Feature | v1 | v2 |
|---------|----|----|
| Grammar | Static | Adaptive (session schemas) |
| Boot cost | ~65 tokens | ~28 tokens |
| Compression ratio | ~3:1 to 8:1 | ~3:1 → 20:1 (accelerates) |
| Faithfulness check | None | Fidelity anchors |
| Critical content | No distinction | `!!` verbatim marker |
| Session aliases | None | `@alias` system |

---

## New Operators (v2 only)

| Symbol | Name | Meaning | Example |
|--------|------|---------|---------|
| `!!x` | Vital | Preserve verbatim — do not compress further | `!!root_cause:race_condition_token_refresh` |
| `??x` | Critical unknown | Must resolve — high priority uncertainty | `??blocking_bug_source` |
| `@name` | Alias | Refers to session schema definition | `@auth`, `@proj`, `@bug` |
| `[FA:x]` | Fidelity anchor | Check/correct model's understanding | `[FA:check]`, `[FA:correct]` |
| `ref:x` | Reference | Points to previous context or decision | `ref:decision[-2]` |
| `>N` | Depth marker | Indicates N levels of nested causality | `>3:bug→fix→deploy→fail` |

---

## The `[SCHEMA]` Block

Defines session-specific aliases. Must be placed at the start of a turn, after the boot sequence.

```
[SCHEMA:v2]
  @alias1 = full_concept_1
  @alias2 = full_concept_2
  @alias3 = @alias1→@alias2    ← aliases can reference other aliases
[/SCHEMA]
```

### Rules
- Alias names: `@` + 1-8 alphanumeric chars
- Definitions: any valid Logos expression or natural language fragment
- Aliases of aliases: allowed, max 2 levels deep
- Schema can be extended mid-session (just add a new `[SCHEMA]` block)
- Conflicts: later definition wins

### Example
```
[SCHEMA:v2]
  @proj  = ecommerce_backend_v2_python_fastapi
  @auth  = jwt_authentication_module
  @bug   = critical_production_bug_token_expiry
  @chain = @auth→@bug
[/SCHEMA]

[t:-3d][@chain:reported][t:-2d][tried:fix_v1→fail]
[t:-1d][tried:fix_v2→?partial][!!root_cause:unknown]
goal: resolve[!!root_cause]→fix[@bug]→deploy[@proj]
```

---

## The `!!` Verbatim Marker

Used when a concept is too precise or unique to safely compress.

```
!!x        → preserve x exactly as written
!!key:val  → preserve the key:value pair verbatim
```

The model must NOT paraphrase, alias, or summarize content marked `!!`.

**Use cases:**
- Exact error messages
- Precise technical identifiers
- Legal/contractual exact wording
- Mathematical formulas
- Root causes that are fragile to paraphrase

```
[bug:@auth][!!error_msg:"TypeError: 'NoneType' object is not subscriptable at line 247"]
[!!fix_constraint: must_not_modify_token_schema_backward_compat]
```

---

## The `[FA]` Fidelity Anchor System

Prevents semantic drift in long sessions.

### FA Check
```
[FA:check → topic]
```
Asks the model to state its current understanding of `topic`.
User verifies the response matches their intent.

### FA Correct
```
[FA:correct] @bug is race_condition NOT deadlock [/FA:correct]
```
Corrects the model's understanding. Model must acknowledge and update.

### FA Snapshot
```
[FA:snapshot]
```
Asks the model to output a full LOGOS_PACK of its current session understanding.
Use this at natural breakpoints (every 10-15 turns) to reset accumulated drift.

### FA Resume
```
[FA:resume → paste_previous_snapshot_here]
```
Resumes a session from a saved FA snapshot. Enables cross-session continuity.

---

## The `[L2]` Boot Sequence (28 tokens)

Minimal v2 bootstrap. One-time cost per session.

```
[L2] →=cause,+=link,≠=contrast,!!=vital,??=unknown,t:=time,dur:=duration,@=alias,[SCHEMA]=define,[FA]=verify [/L2]
```

Extended boot (more reliable with smaller models, ~45 tokens):
```
[L2_EXT]
→=cause | +=link | ≠=contrast
!!=verbatim_preserve | ??=critical_unknown
t:=time(t:-1d=yesterday,t:now=now) | dur:=duration
@=session_alias | [SCHEMA]=define_aliases
[FA:check]=verify_understanding | [FA:correct]=fix_drift
Decompress all [L2] blocks before responding.
[/L2_EXT]
```

---

## Progressive Schema Densification

The key v2 innovation: schemas get denser as sessions deepen.

```
Turn 1-3: No schema yet. Standard v1 operators.
           [t:-1d][!bug:jwt_auth_token_expiry][result:fail]
           ~12 tokens

Turn 5:   [SCHEMA] @auth=jwt_auth_token_expiry, @bug=current_blocker [/SCHEMA]
           [t:-1d][!@bug:@auth][result:fail]
           ~8 tokens

Turn 12:  [SCHEMA] @b=@bug, @a=@auth [/SCHEMA] (compression of aliases)
           [t:-1d][!@b:@a][result:fail]
           ~6 tokens

Turn 20:  [SCHEMA] @x=!@b:@a→fail [/SCHEMA] (entire pattern aliased)
           [t:-1d][@x]
           ~4 tokens
```

**Same information. 12 → 4 tokens. 3:1 → 3:1 improvement over already-compressed v1.**

---

## Full v2 Session Example

```
── SESSION START ──────────────────────────────────────

[L2] →=cause,+=link,≠=contrast,!!=vital,??=unknown,t:=time,dur:=duration,@=alias,[SCHEMA]=define,[FA]=verify [/L2]

[SCHEMA:v2]
  @proj = ecommerce_python_fastapi_postgres
  @auth = jwt_token_refresh_module
  @bug  = critical_production_issue
  @ci   = github_actions_pipeline
[/SCHEMA]

── TURN 1 ──────────────────────────────────────────────

[t:-3d][@bug:reported_by:users][symptom:logout_random]
[t:-2d][diagnosed:@auth][!!root_suspect:race_condition_concurrent_refresh]
[t:-1d][tried:fix_v1→@ci:pass][result:prod_still_failing≠staging]
[t:now][state:blocked+frustrated][??actual_root_cause]
goal: ??root_cause → permanent_fix

── TURN 5 (schema densifying) ──────────────────────────

[SCHEMA:v2:extend]
  @rc = race_condition_concurrent_token_refresh
  @env_gap = prod≠staging_discrepancy
[/SCHEMA]

[t:-4h][reproduced:@rc][env:prod_only][!!error:"deadlock on row 247 users table"]
[hypothesis:@env_gap→db_connection_pool_size_diff]
[checked:staging:pool=5, prod:pool=50][??this_causes_@rc]

── TURN 10 (fidelity check) ────────────────────────────

[FA:check → @bug root cause and current hypothesis]

── MODEL RESPONSE TO FA:check ──────────────────────────
Current understanding:
- @bug = random logouts in production
- Root cause suspect: race condition in JWT token refresh under high concurrency
- Key finding: deadlock on users table row 247
- Current hypothesis: prod/staging difference in DB connection pool size (50 vs 5) causes the race condition
- Status: unconfirmed, needs test

── TURN 11 (confirming + continuing) ───────────────────

[FA:confirm → correct]
[t:-1h][test:pool_size:prod→5][result:@bug:gone→72h_monitoring]
[!!fix_confirmed: reduce_prod_db_pool_5_with_connection_queuing]
[next:deploy_permanent_fix+@ci+monitoring]
goal: deploy → monitor → close[@bug]
```

---

## Compression Ratio Trajectory (v2 vs v1)

```
Session turn:    1    3    5   10   15   20   30
────────────────────────────────────────────────
v1 ratio:       2.5  3.0  3.2  3.5  3.5  3.5  3.5   (plateaus)
v2 ratio:       2.0  3.0  4.5  7.0  10.0 15.0 20.0  (accelerates)
```

**v2 is worse than v1 at turn 1** (schema overhead), but overtakes by turn 3
and pulls dramatically ahead by turn 10.

For long research sessions (30+ turns), v2 achieves **20:1 compression** —
the theoretical paroxysm within our formula's bounds.

---

## Backwards Compatibility

Logos v2 is fully backwards compatible with v1:
- All v1 operators work unchanged
- v1 sessions can be upgraded mid-session by adding `[L2]` boot
- v1 LOGOS_PACKs are valid in v2 sessions
- v2 schemas are ignored by systems running only v1

---

*Logos v2 — MIT License*
