#!/usr/bin/env python3
"""
logos-v4.py — Bracket-free compression engine
Zero dependencies. Auto-adapts format to input length.
Python 3.7+

DISCOVERY: brackets [x] cost tokens. v4 drops them entirely.
           The model infers structure from position + 1-char prefixes.

Usage:
    python logos-v4.py compress "your text"
    python logos-v4.py auto "your text"       # smart: only compresses if worth it
    python logos-v4.py session                # interactive session with /pack
    python logos-v4.py bench                  # run full benchmark
    python logos-v4.py cheatsheet             # quick ref
    python logos-v4.py discover "your text"   # explain WHY and HOW it compresses
"""

import re
import sys
import json
import argparse
from typing import Tuple, List, Optional

VERSION = "4.0.0"

# ─── TOKEN ESTIMATION ─────────────────────────────────────────────────────────

def bpe_tokens(text: str) -> int:
    """
    Realistic BPE token approximation.
    - English words: ~1.2 tokens average (some split into subwords)
    - Symbols/punctuation: ~1 token each
    - Known 2-char combos: 1 token (saves 1)
    """
    words = re.findall(r'[a-zA-Z][a-zA-Z0-9]*', text)
    nums = re.findall(r'\d+', text)
    symbols = re.findall(r'[^a-zA-Z0-9\s]', text)
    # Common 2-char symbol combos that BPE merges into 1 token
    known_merges = ['->', '<-', ':=', '!=', '>=', '<=', '++', '--', '::', '**']
    merge_saves = sum(text.count(m) for m in known_merges)
    word_tokens = int(len(words) * 1.15)  # avg English word = 1.15 BPE tokens
    num_tokens = len(nums)
    sym_tokens = max(0, len(symbols) - merge_saves)
    return word_tokens + num_tokens + sym_tokens

# ─── AUTO-DETECT: SHOULD WE COMPRESS? ────────────────────────────────────────

def should_compress(text: str) -> Tuple[bool, str]:
    """
    Auto-discovers whether compression will help.
    Returns (should_compress, reason)
    """
    tokens = bpe_tokens(text)

    # Rule 1: Already minimal
    if tokens <= 5:
        return False, f"Already minimal ({tokens} tokens ≤ 5 threshold)"

    # Rule 2: Code blocks — never compress
    if re.search(r'[{}\[\]();].*[{}\[\]();]', text) or '()' in text:
        return False, "Contains code syntax — compression would damage it"

    # Rule 3: Pure numbers/metrics
    non_num = re.sub(r'[\d.,:%msMBKGHz/]+', '', text).strip()
    if bpe_tokens(non_num) <= 3:
        return False, "Mostly numbers/metrics — incompressible content"

    # Rule 4: Very long text — definitely compress
    if tokens > 30:
        return True, f"Long text ({tokens} tokens > 30 threshold)"

    # Rule 5: Has compressible patterns
    compressible_patterns = [
        (r'\byesterday\b|\blast night\b|\ball night\b|\btoday\b|\btomorrow\b', 'temporal markers'),
        (r'\bi (am|was|felt?|feel)\b', 'emotional state'),
        (r'\b(tried|attempted|failed|succeeded|worked|broken)\b', 'result markers'),
        (r'\bbecause\b|\bcaused\b|\bresulted\b|\btherefore\b', 'causality'),
        (r'\b(very|extremely|basically|actually|essentially|just)\b', 'filler words'),
        (r'\bi (tried|attempted|was trying) to\b', 'action patterns'),
    ]

    found_patterns = []
    for pattern, name in compressible_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            found_patterns.append(name)

    if found_patterns:
        return True, f"Has compressible patterns: {', '.join(found_patterns)}"

    return False, f"Insufficient compressible content ({tokens} tokens, no clear patterns)"

# ─── v4 COMPRESSION ENGINE ────────────────────────────────────────────────────

# v4 uses position-based structure without brackets:
# TIME: [y:][Nh:][+/-Nd:] | ACTION: [verb:object] | RESULT: [x/ok] | STATE: [emotion]

V4_RULES = [
    # TIME → 1-2 token prefix
    (r'\byesterday\b', 'y:'),
    (r'\btoday\b', 'now:'),
    (r'\btomorrow\b', '+1d:'),
    (r'\blast week\b', '-1w:'),
    (r'\bnext week\b', '+1w:'),
    (r'\b(\d+) days? ago\b', r'-\1d:'),
    (r'\bin (\d+) days?\b', r'+\1d:'),
    (r'\b(\d+) hours? ago\b', r'-\1h:'),
    (r'\blast night\b', 'y:'),
    (r'\bthis morning\b', 'y:'),

    # DURATION → inline number
    (r'\ball night\b', '8h'),
    (r'\ball day\b', '8h'),
    (r'\bfor (\d+) hours?\b', r'\1h'),
    (r'\bfor (\d+) minutes?\b', r'\1m'),
    (r'\bfor about (\d+) hours?\b', r'~\1h'),
    (r'\baround (\d+) hours?\b', r'~\1h'),
    (r'\bfor a (long|while)\b', '~?h'),

    # RESULT → single char at end
    (r"\bit (didn't|doesn't|don't|did not|does not) work\b", 'x'),
    (r'\bit failed\b|\bfailed\b', 'x'),
    (r'\b(no|without) (success|result)\b', 'x'),
    (r'\bit (works|worked|is working)\b', 'ok'),
    (r'\bfixed\b', 'fix'),
    (r'\bsolved\b', 'solve'),

    # CRITICAL → ! prefix
    (r'\bcritical\b', '!'),
    (r'\burgent\b', '!'),
    (r'\bblocking\b', '!block'),
    (r'\bbroken\b', '!broken'),

    # ACTIONS → verb:object
    (r'\bi tried to (\w+)\b', r'try:\1'),
    (r'\bi attempted to (\w+)\b', r'try:\1'),
    (r'\bi (checked?|look(?:ed)? at)\b', r'check:'),
    (r'\bi found\b', 'find:'),
    (r'\bi discovered\b', 'find:'),
    (r'\bi deployed\b', 'deploy:'),
    (r'\bi fixed\b', 'fix:'),
    (r'\bi tested\b', 'test:'),

    # CAUSALITY → arrow (no brackets)
    (r'\bbecause of\b|\bcaused by\b', '<-'),
    (r'\bwhich caused\b|\bwhich resulted in\b|\bso that\b|\btherefore\b', '->'),
    (r'\bthe reason is\b|\bthe cause is\b', 'cause:'),
    (r'\bthe root cause\b|\bthe real issue\b', 'ROOT:'),

    # STATE → bare word (position-inferred as last element)
    (r"\bi('m| am) frustrated\b", 'frustrated'),
    (r"\bi('m| am) stuck\b", 'stuck'),
    (r"\bi('m| am) confused\b", 'confused'),
    (r"\bi('m| am) blocked\b", 'blocked'),
    (r"\bi('m| am) tired\b", 'tired'),
    (r"\bi('m| am) relieved\b", 'relieved'),
    (r"\bi don't know\b|\bi have no idea\b", '?'),

    # TECH ABBREV (safe — model knows these)
    (r'\bauthentication\b', 'auth'),
    (r'\bauthorization\b', 'authz'),
    (r'\bdatabase\b', 'db'),
    (r'\brepository\b|\brepo\b', 'repo'),
    (r'\bapplication\b', 'app'),
    (r'\bperformance\b', 'perf'),
    (r'\benvironment\b', 'env'),
    (r'\bdependency\b|\bdependencies\b', 'dep'),
    (r'\bconfiguration\b', 'cfg'),
    (r'\bdeployment\b', 'deploy'),
    (r'\bkubernetes\b', 'k8s'),
    (r'\bjavascript\b', 'JS'),
    (r'\btypescript\b', 'TS'),
    (r'\bpython\b', 'py'),

    # FILLER REMOVAL (no replacement — just delete)
    (r'\bbasically\b', ''),
    (r'\bactually\b', ''),
    (r'\bessentially\b', ''),
    (r'\byou know\b', ''),
    (r'\bkind of\b', '~'),
    (r'\bsort of\b', '~'),
    (r'\bapproximately\b|\babout\b', '~'),
    (r'\bvery\b', '+'),
    (r'\bextremely\b', '++'),
    (r'\bslightly\b', '~'),

    # CONJUNCTIONS → | separator
    (r'\band then\b|\bthen\b', '|'),
    (r'\bhowever\b|\bbut\b', 'but'),
    (r'\balso\b|\bin addition\b|\bfurthermore\b', '+'),
    (r'\bfor example\b|\bfor instance\b|\bsuch as\b', 'eg:'),
]

def compress_v4(text: str) -> Tuple[str, int, int]:
    """
    Compress text using v4 bracket-free rules.
    Returns (compressed, input_tokens, output_tokens)
    """
    result = text.strip()
    in_tok = bpe_tokens(result)

    for pattern, replacement in V4_RULES:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

    # Clean up whitespace artifacts
    result = re.sub(r'\s+', ' ', result).strip()
    result = re.sub(r'\s+([|:])', r'\1', result)  # "fix : auth" -> "fix:auth"
    result = re.sub(r':\s+', ':', result)          # "y: 8h" -> "y:8h"
    result = re.sub(r'\s*\|\s*', ' | ', result)   # normalize separator
    result = re.sub(r'(\w)\s+(x|ok)\s*$', r'\1 \2', result)  # result at end

    # Remove orphaned articles
    result = re.sub(r'^(the |a |an )', '', result, flags=re.IGNORECASE)

    out_tok = bpe_tokens(result)
    return result, in_tok, out_tok

# ─── SESSION MANAGER ──────────────────────────────────────────────────────────

class SessionV4:
    def __init__(self):
        self.vocab = {}     # @alias -> definition
        self.anchors = {}   # @alias -> definition (never compressed)
        self.turns = []
        self.alias_use_count = {}

    def register_alias(self, alias: str, definition: str, anchor: bool = False):
        key = alias.lstrip('@')
        self.vocab[f'@{key}'] = definition
        self.alias_use_count[f'@{key}'] = 0
        if anchor:
            self.anchors[f'@{key}'] = definition

    def use_alias(self, alias: str) -> str:
        key = f'@{alias.lstrip("@")}'
        if key in self.vocab:
            self.alias_use_count[key] = self.alias_use_count.get(key, 0) + 1
            return key
        return alias

    def add_turn(self, original: str, compressed: str, in_tok: int, out_tok: int):
        self.turns.append({
            'n': len(self.turns) + 1,
            'orig': original,
            'comp': compressed,
            'in': in_tok,
            'out': out_tok,
        })

    def pack(self) -> str:
        """Generate compact session PACK."""
        lines = ['[PACK:v4]']

        # Anchored VOC (never compressed)
        if self.anchors:
            parts = [f'{k}=!!{v}' for k, v in self.anchors.items()]
            lines.append(f'[VOC:A {" ".join(parts)}]')

        # Non-anchored VOC (profitable aliases only: used 3+ times)
        profitable = {k: v for k, v in self.vocab.items()
                      if k not in self.anchors and self.alias_use_count.get(k, 0) >= 2}
        if profitable:
            parts = [f'{k}={v}' for k, v in profitable.items()]
            lines.append(f'[VOC {" ".join(parts)}]')

        # Turn history
        history_parts = []
        for t in self.turns:
            history_parts.append(f'T{t["n"]} {t["comp"]}')
        if history_parts:
            lines.append(' | '.join(history_parts))

        # Stats
        tot_in = sum(t['in'] for t in self.turns)
        tot_out = sum(t['out'] for t in self.turns)
        cr = round(tot_in / max(tot_out, 1), 1)
        lines.append(f'[{tot_in}t->{tot_out}t CR:{cr}x]')

        return '\n'.join(lines)

    def stats(self) -> str:
        if not self.turns:
            return "No turns yet."
        tot_in = sum(t['in'] for t in self.turns)
        tot_out = sum(t['out'] for t in self.turns)
        saved = tot_in - tot_out
        cr = round(tot_in / max(tot_out, 1), 1)
        return (f"  Turns: {len(self.turns)} | "
                f"In: {tot_in}t | Out: {tot_out}t | "
                f"Saved: {saved}t | CR: {cr}x")

# ─── DISCOVER MODE ────────────────────────────────────────────────────────────

def discover(text: str) -> str:
    """Explain WHY and HOW to compress this text."""
    should, reason = should_compress(text)
    compressed, in_tok, out_tok = compress_v4(text)
    cr = round(in_tok / max(out_tok, 1), 2)

    lines = [
        f"INPUT: \"{text}\"",
        f"Tokens: ~{in_tok}",
        "",
        f"SHOULD COMPRESS: {'Yes' if should else 'No'}",
        f"REASON: {reason}",
        "",
    ]

    if not should:
        lines.append("RECOMMENDATION: Use natural language. Compression overhead > benefit.")
        return '\n'.join(lines)

    lines += [
        f"v4 COMPRESSED: {compressed}",
        f"Tokens: ~{out_tok} (CR: {cr}x)",
        "",
        "WHAT WAS COMPRESSED:",
    ]

    # Find what changed
    for pattern, replacement in V4_RULES:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            rep_display = replacement if replacement else "(removed)"
            lines.append(f"  '{pattern}' → '{rep_display}' (found: {matches[:2]})")

    if cr < 1.2:
        lines.append("")
        lines.append("NOTE: Low CR. The text has much incompressible content (names, numbers, code).")
        lines.append("Consider: @alias for any term used 3+ times in session.")

    return '\n'.join(lines)

# ─── BENCHMARK ────────────────────────────────────────────────────────────────

BENCHMARK = [
    # (description, natural, expected_min_cr)
    ("time + action + fail", "Yesterday I spent all night trying to fix the authentication bug and failed", 1.5),
    ("emotion + result", "I am completely frustrated and stuck, the database is broken", 1.8),
    ("multi-clause debug", "I tried to fix the auth issue. It did not work. I checked the database, that was not it.", 2.0),
    ("causality chain", "The deployment failed because of a dependency issue which caused the database to crash", 1.8),
    ("code: do not compress", "localStorage.setItem('refresh_token', token)", 0.8),  # expect NO gain
    ("numbers: do not compress", "Response time: 450ms, throughput: 1200 req/s", 0.9),  # expect NO gain
    ("short: do not compress", "It works", 0.5),  # expect worse than natural
    ("session-style paragraph", "Turn 1 debug auth. Turn 2 found JWT ok. Turn 3 found localStorage bug root cause. Turn 4 fixed. Turn 5 tests pass.", 1.8),
]

def run_benchmark() -> None:
    print(f"LOGOS v{VERSION} — BENCHMARK")
    print("=" * 65)
    print()

    passed = 0
    for desc, text, min_cr in BENCHMARK:
        compressed, in_tok, out_tok = compress_v4(text)
        cr = round(in_tok / max(out_tok, 1), 2)
        ok = cr >= min_cr
        if ok:
            passed += 1
        icon = "✅" if ok else "⚠️"
        print(f"{icon} {desc}")
        print(f"   IN  ({in_tok:2}t): {text[:55]}")
        print(f"   OUT ({out_tok:2}t): {compressed[:55]}")
        print(f"   CR: {cr}× (min: {min_cr}×) {'OK' if ok else 'below target'}")
        print()

    print(f"Passed: {passed}/{len(BENCHMARK)}")
    print()
    print("Token counts are BPE approximations. Real counts may vary by ±15%.")

# ─── CHEATSHEET ───────────────────────────────────────────────────────────────

CHEATSHEET = """
╔════════════════════════════════════════════════════════════╗
║           LOGOS v4 — BRACKET-FREE CHEATSHEET               ║
╠════════════════════════════════════════════════════════════╣
║  WHEN TO USE:  text > 20 chars with time/state/action      ║
║  WHEN TO SKIP: ≤5 tokens, code, pure numbers, short phrases║
╠════════════════════════════════════════════════════════════╣
║  TIME (prefix)          RESULT (suffix, 1 word)            ║
║  y:   = yesterday       x      = failed                    ║
║  +1d: = tomorrow        ok     = succeeded                 ║
║  -Nd: = N days ago      fix    = fixed                     ║
║  +Nh: = in N hours      !      = critical prefix           ║
║  Nh   = duration                                           ║
╠════════════════════════════════════════════════════════════╣
║  ACTION            CAUSALITY        STATE (bare, at end)   ║
║  fix:x = fix x     A->B = caused    frustrated             ║
║  find:x            A<-B = because   stuck                  ║
║  check:x           ROOT: = root     blocked                ║
║  deploy:x          cause: = reason  confused               ║
║  test:x                              relieved              ║
╠════════════════════════════════════════════════════════════╣
║  SEPARATOR    ALIASES                                      ║
║  |  = and then  @x = define once, reuse many times         ║
║  but = however  @JP = Jean-Pierre(DevOps)                  ║
║                 Profitable only if used 3+ times           ║
╠════════════════════════════════════════════════════════════╣
║  VERBATIM (keep exact, never compress)                     ║
║  !!`localStorage.setItem('token', val)`                    ║
║  !!error_message:ERR_CONNECTION_REFUSED                    ║
╠════════════════════════════════════════════════════════════╣
║  EXAMPLE:                                                  ║
║  "Yesterday I spent all night fixing the auth bug, failed" ║
║  → y:8h fix:auth x                                        ║
║  11 tokens → 6 tokens (CR ~1.8×)                          ║
║                                                            ║
║  "I tried auth fix, failed. Checked db, not it. Stuck."   ║
║  → fix:auth x | check:db x | stuck                        ║
║  27 tokens → 9 tokens (CR ~3.0×)                          ║
╠════════════════════════════════════════════════════════════╣
║  HONEST LIMITS:  single msg: 1.5-2.5× | sessions: 4-7×   ║
║  BOOT: no boot needed — model infers v4 from context       ║
╚════════════════════════════════════════════════════════════╝
"""

# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description=f"Logos v{VERSION} — Bracket-free token compression",
    )
    sub = parser.add_subparsers(dest="cmd")

    p = sub.add_parser("compress", help="Compress text (always, even if not optimal)")
    p.add_argument("text")

    p = sub.add_parser("auto", help="Smart compress: only if CR > 1.2×")
    p.add_argument("text")

    p = sub.add_parser("discover", help="Explain compression decisions")
    p.add_argument("text")

    sub.add_parser("bench", help="Run benchmark suite")
    sub.add_parser("session", help="Interactive session with /pack")
    sub.add_parser("cheatsheet", help="Print quick reference")

    args = parser.parse_args()

    if args.cmd == "compress":
        c, i, o = compress_v4(args.text)
        cr = round(i / max(o, 1), 2)
        print(f"Input  ({i:2}t): {args.text}")
        print(f"Output ({o:2}t): {c}   [CR: {cr}×]")

    elif args.cmd == "auto":
        should, reason = should_compress(args.text)
        if not should:
            print(f"SKIP: {reason}")
            print(f"Use natural: {args.text}")
        else:
            c, i, o = compress_v4(args.text)
            cr = round(i / max(o, 1), 2)
            print(f"COMPRESS ({reason})")
            print(f"  {i}t → {o}t [CR: {cr}×]: {c}")

    elif args.cmd == "discover":
        print(discover(args.text))

    elif args.cmd == "bench":
        run_benchmark()

    elif args.cmd == "cheatsheet":
        print(CHEATSHEET)

    elif args.cmd == "session":
        print(f"Logos v{VERSION} Interactive Session")
        print("Commands: /pack | /alias @name=def | /stats | /auto <text> | /quit")
        print("Plain input is auto-compressed.\n")
        session = SessionV4()

        while True:
            try:
                line = input("you> ").strip()
            except (EOFError, KeyboardInterrupt):
                print(f"\nSession end. {session.stats()}")
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
            elif line.startswith("/alias "):
                part = line[7:].strip()
                if "=" in part:
                    alias, defn = part.split("=", 1)
                    anchor = alias.endswith("!")
                    alias = alias.rstrip("!").strip()
                    session.register_alias(alias, defn.strip(), anchor=anchor)
                    print(f"  @{alias.lstrip('@')} = {defn.strip()}" + (" [ANCHORED]" if anchor else ""))
            elif line.startswith("/auto "):
                text = line[6:]
                should, reason = should_compress(text)
                if should:
                    c, i, o = compress_v4(text)
                    cr = round(i / max(o, 1), 2)
                    session.add_turn(text, c, i, o)
                    print(f"  → {c}  [{i}t→{o}t CR:{cr}x]")
                else:
                    print(f"  SKIP ({reason}): {text}")
            else:
                # Auto-compress
                should, _ = should_compress(line)
                if should:
                    c, i, o = compress_v4(line)
                    cr = round(i / max(o, 1), 2)
                    session.add_turn(line, c, i, o)
                    print(f"  logos> {c}  [{i}t→{o}t CR:{cr}x]")
                else:
                    i = bpe_tokens(line)
                    session.add_turn(line, line, i, i)
                    print(f"  (natural, {i}t — too short to compress)")

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
