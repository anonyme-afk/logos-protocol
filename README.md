# LOGOS 🗜️
### Ultra-condensed language protocol for LLMs — no retraining needed

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-3.0-blue.svg)](spec/GRAMMAR_v3.md)
[![Honest](https://img.shields.io/badge/benchmarks-honest-green.svg)](spec/HONEST_BENCHMARKS.md)

> **Extend your effective Claude/GPT session length by 5-10×** by compressing session history — no model retraining needed.

---

## The Real Problem

When you talk to Claude or GPT-4 for a long session, **every message re-sends the full conversation history**. A 20-turn debug session = 3,000+ tokens of history sent on turn 20, most of it redundant.

Logos solves this by giving you a compact, model-native format for session history.

---

## Honest Benchmarks (Updated v3)

> We made a mistake in v1/v2: we claimed 8-20× ratios based on character counts, not token counts.
> Here are the real numbers.

| Use case | Real CR | Worth it? |
|----------|---------|-----------|
| Single sentence compression | 0.5-1.1× | ❌ No |
| Paragraph compression | 2-3× | 🟡 Marginal |
| Session history compression | **10-20×** | ✅ Yes |
| Repeated concepts (aliases) | **5-15× per reuse** | ✅ Yes |

**The real win**: compressing your session history pack, not individual messages.

---

## How It Works (30 Seconds)

LLMs were trained on JSON, code, math notation, ISO formats.
They already understand these "sub-languages" natively.
Logos assembles them into a compact context format.

```
Normal message (150 tokens):
"Yesterday I spent all night debugging the auth issue. I tried checking 
the JWT expiry first, that wasn't it. Then I checked the localStorage 
refresh token logic and found it wasn't being saved."

Logos PACK after 10 turns (15 tokens):
[t:-1d,dur:~8h][check:JWT.expiry→∅issue][find:localStorage∅save=!!root_cause]
```

---

## Quick Start

```bash
# Install (no dependencies)
git clone https://github.com/anonyme-afk/logos-protocol
cd logos-protocol

# Compress a sentence
python tools/logos-v3.py compress "Yesterday I spent all night fixing the auth bug"

# Interactive session with auto-compression
python tools/logos-v3.py session

# See the cheatsheet
python tools/logos-v3.py cheatsheet

# Run benchmarks
python tools/logos-v3.py bench

# Get compat check prompt for your model
python tools/logos-v3.py compat-check
```

---

## Boot Prompt (21 tokens)

Paste at the start of any conversation:

```
[LOGOS:v3] Decompress before responding. Build VOC as we go.
```

Then use `/pack` (or ask Claude "make a LOGOS_PACK") every 5-10 turns to compress history.

---

## Syntax Reference

```
TIME:           t:-1d=yesterday  t:0d=today  t:+1d=tomorrow  dur:~8h=~8hours
RESULT:         ∅x=failed/null   ✓x=succeeded  !x=critical  !!x=verbatim-preserve
CAUSALITY:      [A→B]=A causes B  [A←B]=A because B  [A+B]=A linked to B
STATE:          state:frustrated / stuck / blocked / confused / ?=unknown
COMPRESSION:    [L1:...]=lexical  [L2:...]=semantic  [L3:...]=episodic  [L4:...]=full-tree
ALIASES:        [VOC: @x=definition]  then use @x anywhere
SESSION PACK:   {∑}=compress all above  [SESSION:v3][HISTORY:T1:...,T2:...]
```

Full reference: [spec/GRAMMAR_v3.md](spec/GRAMMAR_v3.md)

---

## Example: Full Debug Session Pack

**Original 10-turn session** (~1,200 tokens):
> A full debugging session about a JWT authentication bug where localStorage wasn't saving the refresh token.

**Logos PACK** (~65 tokens):
```logos
[SESSION:v3]
[VOC:ANCHOR: @bug1=!!localStorage∅setItem:refresh_token]
[HISTORY:
  T1: [t:-1d,dur:~8h][hyp:JWT.expiry→∅issue]
  T2-T5: [explore:refresh_token_logic]
  T6: [find:@bug1=!!root_cause]
  T7-T9: [fix:add_setItem][test:3/3pass]
  T10: [✓auth.stable]
]
[STATS: 1200tok→65tok, CR:18.5×]
```

---

## File Structure

```
logos-protocol/
├── README.md                 ← you are here
├── spec/
│   ├── GRAMMAR_v3.md         ← full v3 specification (L1-L4, VOC, TREE)
│   ├── GRAMMAR_v2.md         ← v2 spec (backward compatible)
│   ├── GRAMMAR.md            ← v1 spec
│   ├── OPERATORS.md          ← quick reference card
│   ├── BENCHMARK.md          ← benchmark framework
│   └── HONEST_BENCHMARKS.md  ← real measured data (read this first)
├── research/
│   ├── PAROXYSM.md           ← theoretical foundations (v2)
│   └── PAROXYSM_v2.md        ← unsolved problems, now solved (v3)
├── examples/
│   ├── examples-by-domain.md ← 6 domains: dev, PM, research...
│   └── v2-full-session.md    ← complete session example
├── prompts/
│   └── system-prompts.md     ← copy-paste prompts for Claude/GPT
├── tools/
│   ├── logos-v3.py           ← v3 CLI (zero dependencies)
│   └── logos-v2.py           ← v2 CLI (API-powered)
└── tests/
    └── community_benchmarks.csv  ← submit your benchmarks here
```

---

## Model Compatibility

| Model | Level | Notes |
|-------|-------|-------|
| Claude 3+ (Sonnet/Opus) | Full v3 | Best performance |
| GPT-4+ | Full v3 | Excellent |
| Gemini 1.5+ | v2 | L3/L4 partial |
| Claude 2, GPT-3.5 | v1/v2 | Basic operators only |
| Mistral 7B+ | v1 | Simple syntax only |
| <7B models | ❌ | Use natural language |

Test your model: `python tools/logos-v3.py compat-check`

---

## Contributing

### Quickest contribution (10 minutes)
1. Pick any sentence you've sent to an AI this week
2. Compress it manually using the cheatsheet
3. Test decompression with your LLM
4. Add a row to `tests/community_benchmarks.csv`
5. Submit a PR

### Bigger contributions
- Test L3/L4 compression on real long sessions
- Add domain-specific aliases (medical, legal, finance, gaming)
- Build a browser extension that auto-packs sessions
- Port logos-v3.py to JavaScript/TypeScript

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

---

## Origins

Logos was invented in a single conversation trying to solve Claude's rate limits.
The insight: LLMs already speak dozens of "sub-languages" (JSON, math, ISO formats).
Logos is just those sub-languages assembled into a compression protocol.

The theoretical foundation is the "GIST tokens" paper (Mu et al., 2023) —
though Logos achieves similar goals without model retraining.

---

## License

MIT — do whatever you want with it.

*Built with rate limit frustration and too much coffee. ☕*
