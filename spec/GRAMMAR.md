# Logos Grammar — Formal Specification v1.0

## Overview

Logos is a semantic compression notation for LLM interactions. It is designed to be parseable by any modern LLM without retraining, by reusing notation already present in training data (JSON, logic, ISO 8601, code conventions).

---

## BNF-like Grammar

```
logos_document   ::= (logos_block | natural_text)*
logos_block      ::= session_block | pack_block | inline_block
session_block    ::= "[SESSION:" identifier "]" logos_block*
pack_block       ::= "[LOGOS_PACK]" pack_content "[/LOGOS_PACK]"
pack_content     ::= prior_line? now_line? goal_line?
prior_line       ::= "prior:" compressed_chain
now_line         ::= "now:" compressed_expr
goal_line        ::= "goal:" compressed_expr
inline_block     ::= "[" compressed_expr ("," compressed_expr)* "]"
compressed_chain ::= compressed_expr ("→" compressed_expr)*
compressed_expr  ::= modifier? atom (operator atom)*
modifier         ::= "!" | "?" | "~"
operator         ::= "→" | "+" | "≠" | ":"
atom             ::= identifier | key_value | temporal | duration
key_value        ::= identifier ":" value
temporal         ::= "t:" time_ref
duration         ::= "dur:" "~"? number time_unit
time_ref         ::= "-" number time_unit | "now" | "today"
time_unit        ::= "min" | "h" | "d" | "w" | "m" | "y"
identifier       ::= [a-zA-Z_][a-zA-Z0-9_.-]*
value            ::= identifier | quoted_string | number
number           ::= [0-9]+
quoted_string    ::= '"' [^"]* '"'
```

---

## Operator Semantics

### Causal chain `→`
Encodes a sequence of causes and effects.

```
[A→B→C]  =  "A led to B which led to C"
```

Examples:
```
[debug→fix:auth→deploy]           # debug led to auth fix led to deployment
[miscommunication→delay→!crisis]  # communication issue caused a critical crisis
```

### Conjunction `+`
Encodes co-occurring, related, or combined concepts.

```
[A+B]  =  "A and B are linked / happen together"
```

Examples:
```
[tired+motivated]     # simultaneously tired and motivated
[react+fastapi]       # tech stack combining both
[state:stuck+blocked] # two states co-occurring
```

### Contrast `≠`
Encodes opposition, mismatch, or contradiction.

```
[A≠B]  =  "A contrasts with or contradicts B"
```

Examples:
```
[expected≠actual]        # mismatch between expectation and reality
[dev_env≠prod_env]       # environments differ (typical bug source)
[theory≠practice]        # conceptual vs real-world gap
```

### Definition `:`
Encodes attribution or property assignment.

```
key:value  =  "key is defined as / equals value"
```

Examples:
```
state:frustrated    # emotional state is frustration
goal:fix_auth       # objective is to fix authentication
result:partial      # outcome was partial
env:linux+py3.11    # environment is Linux with Python 3.11
```

---

## Modifier Semantics

### Critical `!`
Marks urgency, criticality, or high priority.

```
!bug        # critical bug
!deadline   # urgent deadline
```

### Uncertain `?`
Marks uncertainty about the element.

```
?solution   # uncertain whether this is the solution
?result     # outcome unclear
result:?    # same: result is unknown
```

### Approximate `~`
Marks approximation on numeric or temporal values.

```
dur:~3h     # approximately 3 hours
~50%        # roughly 50%
```

---

## Temporal Syntax

All temporal expressions use the `t:` prefix with a relative or absolute reference.

```
t:-1d      # yesterday (1 day ago)
t:-2h      # 2 hours ago
t:-30min   # 30 minutes ago
t:-1w      # last week
t:now      # present moment
t:today    # current day
t:+1d      # tomorrow (scheduled/future)
t:+2h      # in 2 hours (deadline/scheduled)
```

Duration uses `dur:` with optional approximation:

```
dur:3h       # exactly 3 hours
dur:~3h      # approximately 3 hours
dur:30min    # 30 minutes
dur:~1w      # about a week
```

---

## Structural Blocks

### LOGOS_PACK — Context summary block

Used to compress conversation history. Should be placed at the start of a message.

```
[LOGOS_PACK]
  prior: [previous context chain]
  now:   [current situation]
  goal:  [what this message aims to achieve]
[/LOGOS_PACK]
```

All three fields are optional. Use only what is relevant.

### SESSION — Session initialization

Marks the start of a session and optionally names it.

```
[SESSION:logos_v1]
[ctx:backend_project, env:linux+py3.11]
```

---

## Nesting Rules

Blocks can be nested to a maximum depth of 3. Deeper nesting reduces readability without compression benefit.

```
✅ [t:-1d][!try→fix:machine.panne][result:fail]
✅ [[t:-1d][bug:auth]]→[fix:v2→?partial]
❌ [[[t:-1d][a[b[c]]]]→x]   # too deep, break into separate blocks
```

---

## Compression Guidelines

### When to use Logos
- Recapping previous conversation turns
- Sending technical context (env, stack, prior attempts)
- Status updates with temporal markers
- Structured situation reports

### When NOT to use Logos
- Nuanced emotional content (prefer natural language)
- First-time explanations of new concepts
- Questions requiring precise natural language framing
- Creative writing, opinions, subjective content

### Mixed mode (recommended)

```
[LOGOS_PACK]
  prior: [t:-1h][discuss:auth_bug][found:jwt_mismatch]
  now: implement fix
[/LOGOS_PACK]

Can you review this implementation and flag any edge cases 
I might have missed regarding token refresh cycles?
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024 | Initial specification. Core operators: →, +, ≠, :, !, ?, ~. Temporal syntax. LOGOS_PACK block. |

---

*Logos Protocol — MIT License*
