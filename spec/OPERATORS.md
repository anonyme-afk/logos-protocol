# Logos Operators — Quick Reference

## Core Operators

| Operator | Name | Meaning | Example |
|----------|------|---------|---------|
| `→` | Causal chain | A caused / led to B | `[bug→crash→rollback]` |
| `+` | Conjunction | A and B are linked | `[react+typescript]` |
| `≠` | Contrast | A contradicts B | `[expected≠actual]` |
| `:` | Definition | key is value | `goal:fix_auth` |
| `!` | Critical | urgent / high priority | `!deadline` |
| `?` | Uncertain | unknown / to determine | `?solution` |
| `~` | Approximate | roughly / about | `dur:~3h` |

## Temporal Operators

| Operator | Meaning | Example |
|----------|---------|---------|
| `t:-1d` | Yesterday | `[t:-1d][worked_on:api]` |
| `t:-Nh` | N hours ago | `[t:-2h][meeting:done]` |
| `t:-Nmin` | N minutes ago | `[t:-30min][pushed:fix]` |
| `t:-1w` | Last week | `[t:-1w][sprint:finished]` |
| `t:now` | Right now | `[t:now][state:blocked]` |
| `t:today` | Current day | `[t:today][focus:auth]` |
| `t:+1d` | Tomorrow | `[t:+1d][deadline:demo]` |
| `t:+Nh` | In N hours | `[t:+2h][!meeting:client]` |
| `dur:Nh` | Duration N hours | `[dur:8h][worked_on:bug]` |
| `dur:~Nh` | Approx N hours | `[dur:~3h][debug:network]` |

## Situation Modifiers

| Modifier | Meaning | Example |
|----------|---------|---------|
| `state:x` | Emotional / situational state | `state:frustrated` |
| `goal:x` | Current objective | `goal:deploy_v2` |
| `result:x` | Outcome of action | `result:partial` |
| `ctx:x` | Background context | `ctx:startup_env` |
| `env:x` | Technical environment | `env:linux+py3.11` |
| `stack:x` | Tech stack | `stack:react+fastapi` |
| `blocker:x` | What is blocking progress | `!blocker:infra` |

## Structural Blocks

```
[SESSION:name]          → start a named session
[ctx:x, env:y]          → session-level context

[LOGOS_PACK]            → context summary block
  prior: [...]          → compressed history
  now:   [...]          → current situation  
  goal:  [...]          → message objective
[/LOGOS_PACK]
```

## Common Patterns

### Situation report
```
[t:-Nh, dur:~Xh][!action:target][result:x][state:y]
```

### Failed attempt chain
```
[tried:fix_v1→fail][tried:fix_v2→?partial][state:stuck]
```

### Context dump for long sessions
```
[LOGOS_PACK]
  prior: [t:-Xh][topic:y][explored:a+b+c][conclusion:z]
  now:   next_step
  goal:  ?solution
[/LOGOS_PACK]
```

### Technical bug report
```
[ctx:project, env:stack]
[t:x][!bug:description][repro:steps][result:error_type]
goal: fix → explain
```

### Progress update
```
[sprint:N][done:a+b+c][in_progress:d][!blocker:e][t:+deadline]
```

## Nesting Depth Guide

```
Depth 1 ✅  [state:blocked]
Depth 2 ✅  [t:-1d][!bug→result:crash]
Depth 3 ✅  [[ctx:prod][!bug:auth]]→[fix:v2→?partial]
Depth 4 ❌  Too complex — split into multiple blocks
```

## Compression Ratio Reference

| Content type | Typical ratio |
|-------------|--------------|
| Single sentence | 1.5:1 — 2.5:1 |
| Situation paragraph | 3:1 — 5:1 |
| Full conversation history | 8:1 — 12:1 |
| Technical context dump | 5:1 — 8:1 |

---

*Print this page and keep it nearby during Logos sessions.*
