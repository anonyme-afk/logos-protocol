# Logos v3 — System Prompts

> Copy-paste ready prompts for Claude, GPT-4, and Gemini.

---

## Boot Prompt — Ultra Short (21 tokens)

```
[LOGOS:v3] Decompress before responding. Build VOC as we go.
```

Use this. That's it. The model infers the rest from context.

---

## Boot Prompt — Standard (60 tokens)

```
[LOGOS:v3]
Operators: t:-1d=yesterday, dur:~8h=allnight, ∅x=failed, ✓x=ok, !x=critical, 
!!x=verbatim, [A→B]=A_causes_B, state:x=emotion, @x=alias
Decompress blocks before responding. Add @aliases to [VOC] as concepts repeat.
```

---

## Boot Prompt — Full (120 tokens, use once then switch to short)

```
[LOGOS:v3] — Token compression protocol. Rules:
- Decompress ALL Logos blocks before reasoning
- t:±N{d|h|w} = time delta. dur:Nh = duration. state:x = emotional state
- ∅x = null/failed. ✓x = success. !x = critical. !!x = preserve verbatim
- [A→B] = A causes B. [A←B] = A because B. [A+B] = linked
- @alias = reference to [VOC] definition. Build VOC as concepts repeat
- [L1]...[L4] = compression levels (L4 = full thought tree)
- When I say {∑} = compress all prior context into a LOGOS_PACK
- When I say /pack = generate compressed session summary I can paste next message
```

---

## The PACK Command

Ask the model this at turn 5, 10, 15, etc:

```
/pack
```

Or more explicitly:

```
Generate a LOGOS_PACK of our entire conversation so far. 
Include [VOC:ANCHOR] for all key concepts. 
Keep it under 100 tokens. I will paste it at the start of my next message.
```

---

## Starting a New Session with Pack

When you have a pack from a previous session:

```
[LOGOS:v3]
[PACK:
  [VOC:ANCHOR: @bug1=!!auth_refresh_token_localStorage_miss]
  [HISTORY: T1-T10: debug:@bug1 → ✓fix:add_setItem]
  [CONTEXT: proj=logos_protocol, goal=push_paroxysm, state:focused]
]
Continue from here. New question: [...]
```

---

## Domain Prompts

### For coding sessions

```
[LOGOS:v3][domain:code]
Extra aliases auto-build: @err=last_error, @fn=current_function, @fix=proposed_fix
[VOC: @stack=current_tech_stack, @goal=current_coding_goal]
```

### For research sessions

```
[LOGOS:v3][domain:research]
Extra: hyp:x=hypothesis_x, find:x=finding_x, ∅hyp:x=hypothesis_x_rejected
[VOC: @q=main_research_question]
```

### For project management

```
[LOGOS:v3][domain:PM]
Extra: @T=ticket, @M=milestone, @B=blocker, due:t=deadline
[VOC: @sprint=current_sprint_goal]
```

---

## Anti-patterns (what not to do)

❌ Don't use Logos for single sentences — overhead costs more than it saves.

❌ Don't compress critical information without `!!` prefix.

❌ Don't use Logos with models smaller than 7B — they can't parse it.

✅ Do use Logos for session history packs.

✅ Do build `[VOC:ANCHOR]` for concepts that repeat every message.

✅ Do request `/pack` every 5-10 turns.
