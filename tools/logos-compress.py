#!/usr/bin/env python3
"""
logos-compress.py
-----------------
Experimental tool to compress natural language into Logos notation.
Uses simple heuristics + regex. For deep compression, use an LLM with the Logos prompt.

Usage:
    python logos-compress.py "Your text here"
    python logos-compress.py --file input.txt
    python logos-compress.py --interactive
    python logos-compress.py --session-pack conversation.txt
"""

import re
import sys
import argparse
from datetime import datetime, timedelta


# ─────────────────────────────────────────────
# TEMPORAL PATTERNS
# ─────────────────────────────────────────────

TEMPORAL_PATTERNS = [
    (r'\byesterday\b', 't:-1d'),
    (r'\blast night\b', 't:-1d+dur:~8h'),
    (r'\bthis morning\b', 't:today_am'),
    (r'\btoday\b', 't:today'),
    (r'\bright now\b|\bcurrently\b|\bat the moment\b', 't:now'),
    (r'\btomorrow\b', 't:+1d'),
    (r'\b(\d+)\s*hours?\s*ago\b', lambda m: f't:-{m.group(1)}h'),
    (r'\b(\d+)\s*minutes?\s*ago\b', lambda m: f't:-{m.group(1)}min'),
    (r'\blast week\b', 't:-1w'),
    (r'\bnext week\b', 't:+1w'),
    (r'\bin (\d+) hours?\b', lambda m: f't:+{m.group(1)}h'),
    (r'\bin (\d+) days?\b', lambda m: f't:+{m.group(1)}d'),
    # French
    (r'\bhier\b', 't:-1d'),
    (r'\baujourd\'hui\b', 't:today'),
    (r'\bmaintenant\b|\ben ce moment\b', 't:now'),
    (r'\bdemain\b', 't:+1d'),
    (r'\bla semaine dernière\b', 't:-1w'),
    (r'\bce matin\b', 't:today_am'),
    (r'\bcette nuit\b|\bla nuit dernière\b', 't:-1d+dur:~8h'),
    (r'\bil y a (\d+) heure', lambda m: f't:-{m.group(1)}h'),
    (r'\bil y a (\d+) minute', lambda m: f't:-{m.group(1)}min'),
]

DURATION_PATTERNS = [
    (r'\ball\s+night\b|\bthe whole night\b|\btoute la nuit\b', 'dur:~8h'),
    (r'\ball day\b|\btoute la journée\b', 'dur:~8h'),
    (r'\b(\d+)\s*hours?\b', lambda m: f'dur:{m.group(1)}h'),
    (r'\b(\d+)\s*minutes?\b', lambda m: f'dur:{m.group(1)}min'),
    (r'\babout (\d+)\s*hours?\b|\baround (\d+)\s*hours?\b', lambda m: f'dur:~{m.group(1) or m.group(2)}h'),
    (r'\benviron (\d+)\s*heure', lambda m: f'dur:~{m.group(1)}h'),
    (r'\bpendant (\d+)\s*heure', lambda m: f'dur:{m.group(1)}h'),
]

STATE_PATTERNS = [
    (r'\bfrustrat\w*\b', 'state:frustrated'),
    (r'\bstuck\b|\bblocked\b|\bbloqué\w*\b', 'state:blocked'),
    (r'\btired\b|\bexhausted\b|\bépuisé\w*\b', 'state:tired'),
    (r'\bconfused\b|\bperplexed\b|\bperdu\b', 'state:confused'),
    (r'\bpressured\b|\bunder pressure\b|\bstressé\w*\b', 'state:pressured'),
    (r'\boptimistic\b|\bconfident\b|\boptimiste\b', 'state:optimistic'),
    (r'\bworried\b|\banxious\b|\binquiet\w*\b', 'state:worried'),
]

RESULT_PATTERNS = [
    (r'\bfailed\b|\bdid not work\b|\bn\'a pas fonctionné\b|\bécho[uéer]\w*\b', 'result:fail'),
    (r'\bsucceeded\b|\bworked\b|\bfonctionne\b|\bréussi\b', 'result:success'),
    (r'\bpartially\b|\bpartial\b|\bpartiellement\b', 'result:partial'),
    (r'\bunclear\b|\bunknown\b|\bincertain\b|\bpas sûr\b', 'result:?'),
]

URGENCY_PATTERNS = [
    (r'\burgent\b|\bcritical\b|\bcritique\b|\burgent\b', '!'),
    (r'\bdeadline\b|\béchéance\b|\bdate limite\b', '!deadline'),
]


# ─────────────────────────────────────────────
# CORE COMPRESSION FUNCTIONS
# ─────────────────────────────────────────────

def extract_temporal(text: str) -> list[str]:
    """Extract temporal markers from text."""
    found = []
    text_lower = text.lower()
    for pattern, replacement in TEMPORAL_PATTERNS:
        if callable(replacement):
            match = re.search(pattern, text_lower)
            if match:
                found.append(replacement(match))
        else:
            if re.search(pattern, text_lower):
                found.append(replacement)
    return list(dict.fromkeys(found))  # deduplicate preserving order


def extract_duration(text: str) -> list[str]:
    """Extract duration markers from text."""
    found = []
    text_lower = text.lower()
    for pattern, replacement in DURATION_PATTERNS:
        if callable(replacement):
            match = re.search(pattern, text_lower)
            if match:
                found.append(replacement(match))
        else:
            if re.search(pattern, text_lower):
                found.append(replacement)
    return list(dict.fromkeys(found))


def extract_states(text: str) -> list[str]:
    found = []
    text_lower = text.lower()
    for pattern, state in STATE_PATTERNS:
        if re.search(pattern, text_lower):
            found.append(state)
    return found


def extract_results(text: str) -> list[str]:
    found = []
    text_lower = text.lower()
    for pattern, result in RESULT_PATTERNS:
        if re.search(pattern, text_lower):
            found.append(result)
    return found


def extract_key_nouns(text: str) -> list[str]:
    """Very basic noun extraction — prefer LLM for quality."""
    technical_terms = re.findall(
        r'\b(?:bug|error|crash|fix|deploy|auth|api|database|server|'
        r'machine|bug|panne|réparation|repair|issue|problem|feature|'
        r'module|component|service|token|session|cache|memory)\b',
        text.lower()
    )
    return list(dict.fromkeys(technical_terms))


def compress_sentence(text: str) -> str:
    """
    Compress a natural language sentence to Logos notation.
    This is a heuristic approach — for best results, use an LLM.
    """
    parts = []

    # Temporal + duration
    temporals = extract_temporal(text)
    durations = extract_duration(text)
    if temporals or durations:
        temporal_str = ', '.join(temporals + durations)
        parts.append(f"[{temporal_str}]")

    # Key nouns/concepts
    nouns = extract_key_nouns(text)
    if nouns:
        main_topic = '+'.join(nouns[:3])  # max 3 nouns
        # Check for failure
        results = extract_results(text)
        if results:
            parts.append(f"[try→{main_topic}][{results[0]}]")
        else:
            parts.append(f"[{main_topic}]")

    # States
    states = extract_states(text)
    for state in states:
        parts.append(f"[{state}]")

    if not parts:
        # Fallback: return a warning
        return f"[?logos_compress_failed: use LLM for this input]"

    return ' '.join(parts)


def count_tokens_approx(text: str) -> int:
    """Rough token estimate: ~4 chars per token."""
    return max(1, len(text) // 4)


def compress_text(text: str, verbose: bool = False) -> dict:
    """Main compression function."""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    compressed_parts = []

    for sentence in sentences:
        if sentence.strip():
            compressed_parts.append(compress_sentence(sentence.strip()))

    compressed = ' '.join(compressed_parts)

    original_tokens = count_tokens_approx(text)
    compressed_tokens = count_tokens_approx(compressed)
    ratio = original_tokens / max(1, compressed_tokens)

    return {
        'original': text,
        'compressed': compressed,
        'original_tokens_approx': original_tokens,
        'compressed_tokens_approx': compressed_tokens,
        'ratio': round(ratio, 2),
    }


def generate_logos_pack(conversation_turns: list[str]) -> str:
    """
    Generate a LOGOS_PACK from a list of conversation turns.
    Each turn should be a string.
    """
    compressed_turns = []
    for i, turn in enumerate(conversation_turns):
        compressed = compress_sentence(turn)
        compressed_turns.append(compressed)

    prior_chain = '\n    '.join(compressed_turns)

    return f"""[LOGOS_PACK]
  prior:
    {prior_chain}
  now: [t:now]
  goal: ?continue
[/LOGOS_PACK]"""


def generate_llm_prompt(text: str) -> str:
    """
    Generate a prompt to send to an LLM for high-quality Logos compression.
    Use this when heuristic compression is not accurate enough.
    """
    return f"""Compress the following text into Logos notation. 
Use these rules:
- [A→B] = A caused B
- [A+B] = A linked with B  
- [A≠B] = A contrasts with B
- t: for time (t:-1d = yesterday, t:-2h = 2h ago)
- dur: for duration (~= approximate)
- !x = critical, ?x = uncertain
- state:/goal:/result:/ctx: for modifiers
- Be as compact as possible while preserving all key information

Text to compress:
\"\"\"{text}\"\"\"

Output only the Logos notation, nothing else."""


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def print_result(result: dict):
    print("\n" + "─" * 50)
    print("ORIGINAL:")
    print(f"  {result['original']}")
    print(f"\nLOGOS:")
    print(f"  {result['compressed']}")
    print(f"\nSTATS:")
    print(f"  Original  : ~{result['original_tokens_approx']} tokens")
    print(f"  Compressed: ~{result['compressed_tokens_approx']} tokens")
    print(f"  Ratio     : {result['ratio']}:1")
    print("─" * 50)


def interactive_mode():
    print("Logos Compressor — Interactive Mode")
    print("Type text and press Enter. Type 'quit' to exit.")
    print("─" * 50)
    while True:
        try:
            text = input("\n> ").strip()
            if text.lower() in ('quit', 'exit', 'q'):
                break
            if not text:
                continue
            result = compress_text(text)
            print_result(result)
        except (KeyboardInterrupt, EOFError):
            break
    print("\nBye!")


def session_pack_mode(filepath: str):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        pack = generate_logos_pack(lines)
        print("\nGenerated LOGOS_PACK:")
        print("─" * 50)
        print(pack)
        print("─" * 50)
        original_tokens = sum(count_tokens_approx(l) for l in lines)
        pack_tokens = count_tokens_approx(pack)
        print(f"\nOriginal: ~{original_tokens} tokens → Pack: ~{pack_tokens} tokens")
        print(f"Ratio: {round(original_tokens / max(1, pack_tokens), 2)}:1")
    except FileNotFoundError:
        print(f"Error: file '{filepath}' not found.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Logos Protocol — Natural language compressor for LLMs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python logos-compress.py "I spent all night trying to fix a broken machine"
  python logos-compress.py --file context.txt
  python logos-compress.py --interactive
  python logos-compress.py --session-pack conversation.txt
  python logos-compress.py --llm-prompt "My text here"
        """
    )
    parser.add_argument('text', nargs='?', help='Text to compress')
    parser.add_argument('--file', '-f', help='File to compress')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--session-pack', '-s', help='Generate LOGOS_PACK from conversation file')
    parser.add_argument('--llm-prompt', '-l', help='Generate LLM prompt for compression')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    args = parser.parse_args()

    if args.interactive:
        interactive_mode()
    elif args.session_pack:
        session_pack_mode(args.session_pack)
    elif args.llm_prompt:
        print(generate_llm_prompt(args.llm_prompt))
    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()
            result = compress_text(text, verbose=args.verbose)
            print_result(result)
        except FileNotFoundError:
            print(f"Error: file '{args.file}' not found.")
            sys.exit(1)
    elif args.text:
        result = compress_text(args.text, verbose=args.verbose)
        print_result(result)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
