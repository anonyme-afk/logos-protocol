# Logos Benchmark Framework

> How to scientifically measure compression quality, faithfulness, and efficiency.

---

## The Three Metrics

Every Logos benchmark must measure three things:

### 1. Compression Ratio (CR)
```
CR = tokens(original) / tokens(logos)
```
Higher = better. Minimum useful CR: 1.5. Target: 3.0+

### 2. Faithfulness Score (FS)
```
FS = semantic_similarity(decompress(logos), original)
```
Range: 0.0 to 1.0. Minimum acceptable: 0.85. Target: 0.95+

Measured by:
- Ask the model to decompress the Logos block
- Compare decomposed meaning against original
- Rate on 5-point scale: 1=wrong, 2=major loss, 3=minor loss, 4=near-perfect, 5=perfect
- Normalize to 0.0–1.0

### 3. Logos Efficiency (η)
```
η = FS / CR_inverse = FS × CR / max_possible_CR
```
Combines both metrics. Range: 0.0 to 1.0.
A CR=5:1 with FS=0.6 is worse than CR=3:1 with FS=0.95.

---

## Benchmark Test Suite

### Category A: Single Sentences (n=20)

Test compression of standalone sentences across difficulty levels.

**A1 — Simple temporal (easy)**
```
Original: "Yesterday I worked on the auth module."
Target CR: ≥ 2.0 | Target FS: ≥ 0.95
Expected: [t:-1d][worked:auth_module]
```

**A2 — Complex causal chain (medium)**
```
Original: "The deployment failed because the CI pipeline timed out after we 
           pushed a large commit that included unoptimized database queries."
Target CR: ≥ 3.0 | Target FS: ≥ 0.90
Expected: [deploy:fail←ci:timeout←!commit:large+db_queries:unoptimized]
```

**A3 — High-precision technical (hard)**
```
Original: "The race condition occurs when two goroutines simultaneously 
           access the token refresh mutex without proper locking, causing 
           a deadlock on the users table at high concurrency."
Target CR: ≥ 2.5 | Target FS: ≥ 0.90
Expected: [!!race_cond:goroutines×2→mutex:token_refresh:!no_lock→deadlock:users_table@high_concurrency]
```

**A4 — Emotional/nuanced (hard)**
```
Original: "I'm frustrated but still hopeful — I feel like we're close to 
           the solution, even though we've been stuck for three days."
Target CR: ≥ 2.0 | Target FS: ≥ 0.85
Expected: [state:frustrated+hopeful][feel:close_to_solution≠stuck:3d]
```

---

### Category B: Conversation History (n=10)

Test compression of multi-turn conversation excerpts.

**B1 — 5-turn technical debug session**
Target CR: ≥ 5.0 | Target FS: ≥ 0.90

**B2 — 10-turn project planning session**
Target CR: ≥ 7.0 | Target FS: ≥ 0.85

**B3 — 20-turn research session**
Target CR: ≥ 10.0 | Target FS: ≥ 0.85

---

### Category C: Cross-Model Compliance (n=5 models)

Test that the model correctly decompresses Logos blocks.

```
Input:  [t:-1d, dur:~8h][!try→fix:machine.panne][result:fail][state:frustrated]
Expected decompression:
  "Yesterday, I spent approximately 8 hours trying to fix a critically 
   broken machine. I failed. I am frustrated."

Score: 1 point per correctly recovered element:
  - t:-1d → "yesterday" ✓
  - dur:~8h → "approximately 8 hours" ✓  
  - !try→fix → "trying to fix" (critical) ✓
  - machine.panne → "broken machine" ✓
  - result:fail → "failed" ✓
  - state:frustrated → "frustrated" ✓
  Max score: 6/6
```

---

### Category D: v2 Session Acceleration (n=5 sessions)

Measures the compression ratio acceleration effect over 30 turns.

```
Record CR at turns: 1, 3, 5, 10, 15, 20, 30
Plot the acceleration curve
Compare v1 vs v2 trajectory
```

Target: v2 CR at turn 20 ≥ 3× v1 CR at same turn.

---

## Running a Benchmark

### Manual Benchmark (no tools)

1. Select 5 texts from Category A
2. Compress each with Logos (manually or with the CLI tool)
3. Ask your target LLM to decompress each Logos block
4. Rate faithfulness 1-5 for each
5. Calculate CR and η
6. Report results in an Issue with tag `benchmark`

### Automated Benchmark (with API access)

```bash
python tools/logos-benchmark.py \
  --model claude-3-5-sonnet-20241022 \
  --category A \
  --api-key YOUR_KEY
```

---

## Reporting Format

When submitting benchmark results, use this format:

```
## Benchmark Report

**Date:** YYYY-MM-DD
**Model:** claude-3-5-sonnet / gpt-4o / gemini-1.5-pro / etc.
**Logos version:** v1 / v2
**Boot tokens used:** N

| Category | Test | CR | FS | η |
|----------|------|----|----|----|
| A1 | Simple temporal | 2.3 | 0.97 | 0.89 |
| A2 | Causal chain | 3.1 | 0.91 | 0.94 |
| A3 | High-precision | 2.7 | 0.88 | 0.88 |
| B1 | 5-turn session | 5.8 | 0.92 | 0.91 |

**Average η:** 0.91
**Notes:** [any observations]
```

---

## Current Benchmark Results

*(Community contributions welcome — open a PR to add yours)*

| Contributor | Model | Logos | Avg CR | Avg FS | Avg η | Date |
|-------------|-------|-------|--------|--------|--------|------|
| — | — | — | — | — | — | — |

---

## Leaderboard Goal

Target community benchmark covering:
- 5+ different LLMs
- 3 languages (EN, FR, ES minimum)
- v1 and v2 comparison
- 20+ conversation samples per language

**Help us fill this table.**

---

*Logos Benchmark Framework — MIT License*
