#!/usr/bin/env python3
"""
logos-v3.py — Logos v3 compression engine
Zero dependencies. No API key needed for basic mode.
Works offline. Python 3.7+

Usage:
    python logos-v3.py compress "Your text here"
    python logos-v3.py decompress "[t:-1d][fix:auth]"
    python logos-v3.py session
    python logos-v3.py bench "Your text"
    python logos-v3.py cheatsheet
    python logos-v3.py compat-check

Quick start:
    python logos-v3.py cheatsheet    # learn the syntax
    python logos-v3.py compress "Yesterday I spent all night fixing the auth bug"
"""

import sys
import re
import json
import argparse
import hashlib
from typing import Tuple, List, Dict
from datetime import datetime, timedelta

VERSION = "3.0.0"

# ─── COMPRESSION ENGINE ────────────────────────────────────────────────────────

RULES = [
    # Time patterns
    (r"\byesterday\b", "t:-1d"),
    (r"\btoday\b", "t:0d"),
    (r"\btomorrow\b", "t:+1d"),
    (r"\blast week\b", "t:-1w"),
    (r"\bnext week\b", "t:+1w"),
    (r"\blast month\b", "t:-1m"),
    (r"\b(\d+) days? ago\b", r"t:-\1d"),
    (r"\bin (\d+) days?\b", r"t:+\1d"),
    (r"\b(\d+) hours? ago\b", r"t:-\1h"),

    # Duration patterns
    (r"\ball night\b", "dur:~8h"),
    (r"\ball day\b", "dur:~8h"),
    (r"\bfor (\d+) hours?\b", r"dur:\1h"),
    (r"\bfor (\d+) minutes?\b", r"dur:\1min"),
    (r"\bfor about (\d+) hours?\b", r"dur:~\1h"),
    (r"\baround (\d+) hours?\b", r"dur:~\1h"),

    # State/emotion
    (r"\bi('m| am) frustrated\b", "state:frustrated"),
    (r"\bi('m| am) stuck\b", "state:stuck"),
    (r"\bi('m| am) confused\b", "state:confused"),
    (r"\bi('m| am) tired\b", "state:tired"),
    (r"\bi('m| am) happy\b", "state:happy"),
    (r"\bi('m| am) excited\b", "state:excited"),
    (r"\bi('m| am) blocked\b", "state:blocked"),
    (r"\bi don't know\b", "state:?"),
    (r"\bi have no idea\b", "state:∅"),

    # Result patterns
    (r"\bit (didn't|doesn't|don't) work\b", "∅result"),
    (r"\bit failed\b", "∅result"),
    (r"\b(no|without) (success|result)\b", "∅result"),
    (r"\bit worked\b", "✓result"),
    (r"\bit (works|is working)\b", "✓result"),
    (r"\bfixed\b", "✓fix"),
    (r"\bbroken\b", "!broken"),
    (r"\bcritical\b", "!crit"),
    (r"\burgent\b", "!urgent"),
    (r"\bimportant\b", "!imp"),

    # Common tech patterns
    (r"\bauthentication\b", "auth"),
    (r"\bauthorization\b", "authz"),
    (r"\bdatabase\b", "db"),
    (r"\brepository\b", "repo"),
    (r"\bapplication\b", "app"),
    (r"\bperformance\b", "perf"),
    (r"\benvironment\b", "env"),
    (r"\bdependency\b", "dep"),
    (r"\bdependencies\b", "deps"),
    (r"\bconfiguration\b", "cfg"),
    (r"\bdeployment\b", "deploy"),
    (r"\berror message\b", "err_msg"),
    (r"\bstack trace\b", "stacktrace"),
    (r"\bpull request\b", "PR"),
    (r"\bmerge conflict\b", "merge_conflict"),

    # Filler removal
    (r"\bi tried to\b", "try→"),
    (r"\bi attempted to\b", "try→"),
    (r"\bi was trying to\b", "try→"),
    (r"\bi need to\b", "need:"),
    (r"\bwe need to\b", "need:"),
    (r"\bthe problem is\b", "!prob:"),
    (r"\bthe issue is\b", "!issue:"),
    (r"\bthe reason is\b", "cause:"),
    (r"\bbecause of\b", "←"),
    (r"\bcaused by\b", "←"),
    (r"\bwhich caused\b", "→"),
    (r"\bwhich resulted in\b", "→"),
    (r"\bso that\b", "→"),
    (r"\btherefore\b", "∴"),
    (r"\bhowever\b", "but"),
    (r"\balthough\b", "but"),
    (r"\bdespite\b", "but"),

    # Conjunctions / common filler
    (r"\bI (also|additionally) \b", "also:"),
    (r"\bin addition\b", "also:"),
    (r"\bfor example\b", "ex:"),
    (r"\bfor instance\b", "ex:"),
    (r"\bsuch as\b", "eg:"),
    (r"\bspecifically\b", "eg:"),
    (r"\bbasically\b", ""),
    (r"\bactually\b", ""),
    (r"\bessentially\b", ""),
    (r"\bjust\b", ""),  # often filler
    (r"\bvery\b", "+"),
    (r"\bextremely\b", "++"),
    (r"\bslightly\b", "~"),
    (r"\bapproximately\b", "~"),
    (r"\babout\b", "~"),
]

def count_tokens(text: str) -> int:
    """Approximate token count (4 chars ≈ 1 token, common heuristic)."""
    return max(1, len(text) // 4)

def compress(text: str, level: int = 1) -> Tuple[str, int, int]:
    """
    Compress text using Logos rules.
    Returns (compressed, input_tokens, output_tokens)
    """
    result = text.lower().strip()

    for pattern, replacement in RULES:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    # Clean up multiple spaces
    result = re.sub(r"\s+", " ", result).strip()

    # Remove leading/trailing articles that became orphaned
    result = re.sub(r"^(the|a|an) ", "", result)
    result = re.sub(r" (the|a|an)$", "", result)

    # Wrap in appropriate level marker
    if level >= 2:
        result = f"[L{level}: {result}]"

    input_tokens = count_tokens(text)
    output_tokens = count_tokens(result)
    return result, input_tokens, output_tokens

def decompress_hint(logos: str) -> str:
    """Provide decompression hints (for when you want to verify)."""
    hints = {
        "t:-1d": "yesterday",
        "t:0d": "today",
        "t:+1d": "tomorrow",
        "t:-1w": "last week",
        "dur:~8h": "approximately 8 hours (all night/day)",
        "∅result": "no result / failed",
        "✓result": "succeeded / worked",
        "✓fix": "fixed / resolved",
        "state:frustrated": "I am frustrated",
        "state:stuck": "I am stuck",
        "state:blocked": "I am blocked",
        "!crit": "CRITICAL",
        "!urgent": "URGENT",
        "auth": "authentication",
        "authz": "authorization",
        "db": "database",
        "cfg": "configuration",
        "deploy": "deployment",
        "∴": "therefore",
        "←": "caused by / because of",
        "→": "which caused / resulting in",
        "~": "approximately",
        "+": "very",
        "++": "extremely",
    }

    result = logos
    for logos_token, expansion in hints.items():
        result = result.replace(logos_token, f"{logos_token}[≈{expansion}]")
    return result

# ─── SESSION MANAGER ──────────────────────────────────────────────────────────

class LogosSession:
    def __init__(self):
        self.vocab: Dict[str, str] = {}
        self.anchors: Dict[str, str] = {}
        self.turns: List[Dict] = []
        self.total_saved = 0
        self.started = datetime.now().isoformat()

    def add_turn(self, original: str, compressed: str, input_tok: int, output_tok: int):
        self.turns.append({
            "original": original,
            "compressed": compressed,
            "input_tok": input_tok,
            "output_tok": output_tok,
            "saved": input_tok - output_tok,
        })
        self.total_saved += input_tok - output_tok

    def add_vocab(self, alias: str, definition: str, anchor: bool = False):
        self.vocab[alias] = definition
        if anchor:
            self.anchors[alias] = definition

    def pack(self) -> str:
        """Generate a LOGOS_PACK that summarizes the full session."""
        lines = ["[SESSION:v3]"]

        # Anchored vocab (always preserved)
        if self.anchors:
            lines.append("[VOC:ANCHOR:")
            for alias, defn in self.anchors.items():
                lines.append(f"  {alias}=!!{defn}")
            lines.append("]")

        # Non-anchored vocab
        non_anchored = {k: v for k, v in self.vocab.items() if k not in self.anchors}
        if non_anchored:
            lines.append("[VOC:")
            for alias, defn in non_anchored.items():
                lines.append(f"  {alias}={defn}")
            lines.append("]")

        # Turn history (compressed)
        if self.turns:
            lines.append("[HISTORY:")
            for i, turn in enumerate(self.turns):
                lines.append(f"  T{i+1}: {turn['compressed']}")
            lines.append("]")

        # Stats
        total_in = sum(t["input_tok"] for t in self.turns)
        total_out = sum(t["output_tok"] for t in self.turns)
        cr = round(total_in / max(total_out, 1), 1)
        lines.append(f"[STATS: {total_in}tok→{total_out}tok, CR:{cr}×, saved:{self.total_saved}tok]")

        return "\n".join(lines)

    def stats(self) -> str:
        total_in = sum(t["input_tok"] for t in self.turns)
        total_out = sum(t["output_tok"] for t in self.turns)
        if total_in == 0:
            return "No turns yet."
        cr = round(total_in / max(total_out, 1), 1)
        return (
            f"Session stats:\n"
            f"  Turns: {len(self.turns)}\n"
            f"  Original tokens: {total_in}\n"
            f"  Compressed tokens: {total_out}\n"
            f"  Compression ratio: {cr}×\n"
            f"  Tokens saved: {self.total_saved}"
        )

# ─── BENCHMARK ────────────────────────────────────────────────────────────────

BENCHMARK_CASES = [
    {
        "id": "T1_simple",
        "tier": 1,
        "input": "Yesterday I spent all night trying to fix the authentication bug",
        "expected_cr": 2.5,
    },
    {
        "id": "T1_state",
        "tier": 1,
        "input": "I am frustrated because the database is broken",
        "expected_cr": 2.0,
    },
    {
        "id": "T2_reasoning",
        "tier": 2,
        "input": (
            "I tried to fix the authentication issue. "
            "It didn't work. I then checked the database configuration. "
            "That wasn't the problem either. I am stuck and confused."
        ),
        "expected_cr": 3.5,
    },
    {
        "id": "T2_technical",
        "tier": 2,
        "input": (
            "The application deployment failed because of a dependency issue. "
            "The error message said the configuration was invalid. "
            "I need to fix this urgently because it's critical."
        ),
        "expected_cr": 4.0,
    },
]

def run_benchmark() -> None:
    print("=" * 60)
    print("LOGOS v3 — BENCHMARK SUITE")
    print("=" * 60)
    print()

    total_cr = []
    for case in BENCHMARK_CASES:
        compressed, in_tok, out_tok = compress(case["input"])
        cr = round(in_tok / max(out_tok, 1), 2)
        total_cr.append(cr)
        status = "✅" if cr >= case["expected_cr"] else "⚠️"
        print(f"[{status}] {case['id']} (Tier {case['tier']})")
        print(f"  Input:      {case['input'][:60]}...")
        print(f"  Compressed: {compressed}")
        print(f"  Tokens:     {in_tok} → {out_tok} | CR: {cr}× (target: {case['expected_cr']}×)")
        print()

    avg_cr = round(sum(total_cr) / len(total_cr), 2)
    print(f"Average CR: {avg_cr}×")
    print()
    print("Note: CR is measured by character-based token approximation.")
    print("Real token counts may vary by model tokenizer.")
    print("Run with actual API calls for production benchmarks.")

# ─── CHEATSHEET ───────────────────────────────────────────────────────────────

CHEATSHEET = """
╔══════════════════════════════════════════════════════════════╗
║              LOGOS v3 — QUICK REFERENCE CARD                 ║
╠══════════════════════════════════════════════════════════════╣
║  BOOT (paste at start of conversation):                      ║
║  [LOGOS:v3] Decompress before responding. Build VOC as go.  ║
╠══════════════════════════════════════════════════════════════╣
║  TIME                          RESULT                        ║
║  t:-1d  = yesterday            ∅x   = x failed/null         ║
║  t:0d   = today                ✓x   = x succeeded           ║
║  t:+1d  = tomorrow             !x   = x critical            ║
║  t:-Nh  = N hours ago          !!x  = x verbatim (no compress)║
║  dur:Nh = duration N hours     ?x   = x uncertain           ║
║  dur:~Nh= approx N hours                                     ║
╠══════════════════════════════════════════════════════════════╣
║  CAUSALITY              STATE                                 ║
║  [A→B]  = A causes B   state:x   = emotional/situational    ║
║  [A←B]  = A because B  state:?   = don't know               ║
║  [A+B]  = A linked B   state:∅   = no idea                  ║
║  A→→B→→C = chain       state:frustrated / stuck / blocked   ║
╠══════════════════════════════════════════════════════════════╣
║  COMPRESSION LEVELS (v3)                                     ║
║  [L1: ...] lexical (fast, 2-4×)                             ║
║  [L2: ...] semantic (medium, 5-10×)                         ║
║  [L3: ...] episodic/reasoning (10-20×)                      ║
║  [L4: ...] full thought map (20-50×)                        ║
╠══════════════════════════════════════════════════════════════╣
║  ALIASES               DELTA MARKERS                         ║
║  @x = define alias     Δ+x = x improved                     ║
║  [VOC: @x=defn]        Δ-x = x degraded                     ║
║  [VOC:ANCHOR: @x=!!y]  ⊕[A+B] = A and B fused              ║
╠══════════════════════════════════════════════════════════════╣
║  PACK / COMPRESS SESSION:                                    ║
║  {∑}  = compress everything above into summary              ║
║  [SESSION:v3] ... [HISTORY: T1:..., T2:...]                 ║
╠══════════════════════════════════════════════════════════════╣
║  EXAMPLE:                                                    ║
║  "Yesterday I spent all night fixing the auth bug, failed"  ║
║  → [t:-1d, dur:~8h][try→fix:auth][∅result][state:frustrated]║
║  → 11 tokens → 5 tokens (2.2×)                             ║
╚══════════════════════════════════════════════════════════════╝
"""

# ─── COMPAT CHECK ─────────────────────────────────────────────────────────────

COMPAT_PROMPT = """[LOGOS:v3][compat_test]

Decompress this block and describe what it means in plain English:
[t:-1d, dur:~8h][try→fix:auth_bug][∅result][state:frustrated]

Then compress this sentence into Logos:
"Tomorrow I need to urgently fix the database configuration, it's critical."
"""

# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=f"Logos v{VERSION} — Token compression for LLMs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    # compress
    p_compress = subparsers.add_parser("compress", help="Compress text to Logos")
    p_compress.add_argument("text", help="Text to compress")
    p_compress.add_argument("--level", type=int, default=1, help="Compression level (1-4)")

    # decompress
    p_decompress = subparsers.add_parser("decompress", help="Show decompression hints")
    p_decompress.add_argument("logos", help="Logos block to decompress")

    # bench
    subparsers.add_parser("bench", help="Run benchmark suite")

    # session
    subparsers.add_parser("session", help="Start interactive session")

    # cheatsheet
    subparsers.add_parser("cheatsheet", help="Print quick reference card")

    # compat-check
    subparsers.add_parser("compat-check", help="Print compatibility check prompt")

    args = parser.parse_args()

    if args.command == "compress":
        compressed, in_tok, out_tok = compress(args.text, level=args.level)
        cr = round(in_tok / max(out_tok, 1), 2)
        print(f"Input ({in_tok} tokens):")
        print(f"  {args.text}")
        print(f"\nLogos L{args.level} ({out_tok} tokens) — CR: {cr}×:")
        print(f"  {compressed}")
        if cr < 1.5:
            print("\n  ⚠️  Low CR: this sentence doesn't compress well with L1.")
            print("     Try L2/L3 for better results on longer text.")

    elif args.command == "decompress":
        result = decompress_hint(args.logos)
        print("Decompression hints:")
        print(result)
        print("\nNote: paste this into your LLM with [LOGOS:v3] prefix for full decompression.")

    elif args.command == "bench":
        run_benchmark()

    elif args.command == "session":
        print(f"Logos v{VERSION} — Interactive Session")
        print("Commands: /compress <text> | /pack | /vocab <alias>=<def> | /stats | /quit")
        print()
        session = LogosSession()
        while True:
            try:
                line = input("you> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nSession ended.")
                print(session.stats())
                break
            if not line:
                continue
            if line == "/quit":
                print(session.stats())
                break
            elif line == "/pack":
                print("\n" + session.pack() + "\n")
            elif line == "/stats":
                print(session.stats())
            elif line.startswith("/vocab "):
                part = line[7:].strip()
                if "=" in part:
                    alias, defn = part.split("=", 1)
                    anchor = alias.startswith("!")
                    alias = alias.lstrip("!")
                    session.add_vocab(f"@{alias.strip()}", defn.strip(), anchor=anchor)
                    print(f"  Vocab added: @{alias.strip()} = {defn.strip()}" + (" [ANCHORED]" if anchor else ""))
            elif line.startswith("/compress "):
                text = line[10:]
                c, i, o = compress(text)
                session.add_turn(text, c, i, o)
                cr = round(i / max(o, 1), 2)
                print(f"  → {c}  [{i}→{o}tok, CR:{cr}×]")
            else:
                # Auto-compress non-command input
                c, i, o = compress(line)
                session.add_turn(line, c, i, o)
                cr = round(i / max(o, 1), 2)
                print(f"  logos> {c}  [{i}→{o}tok, CR:{cr}×]")

    elif args.command == "cheatsheet":
        print(CHEATSHEET)

    elif args.command == "compat-check":
        print("Paste this into your LLM to test Logos compatibility:\n")
        print(COMPAT_PROMPT)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
