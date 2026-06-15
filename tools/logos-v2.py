#!/usr/bin/env python3
"""
logos-v2.py
-----------
Logos v2 adaptive compression engine.

Adds over v1:
  - Session schema management (@aliases)
  - Salience detection (!! markers)
  - Fidelity anchor system ([FA])
  - LLM-powered compression (via API)
  - Session persistence (save/load)
  - Benchmark runner

Usage:
    python logos-v2.py compress "Your text here"
    python logos-v2.py session --new
    python logos-v2.py session --load my_session.json
    python logos-v2.py schema --add "@auth=jwt_module"
    python logos-v2.py bench --text "Your text" --model claude
    python logos-v2.py pack --turns conversation.txt
"""

import re
import sys
import json
import argparse
import hashlib
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


# ─────────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────────

@dataclass
class SessionSchema:
    """Manages session-specific @aliases."""
    aliases: dict[str, str] = field(default_factory=dict)
    version: int = 1

    def add(self, alias: str, definition: str):
        """Add or update an alias."""
        clean = alias.lstrip('@')
        self.aliases[clean] = definition
        self.version += 1

    def apply(self, text: str) -> str:
        """Replace definitions with @aliases in text."""
        result = text
        # Sort by length descending to avoid partial replacements
        for alias, definition in sorted(self.aliases.items(), key=lambda x: -len(x[1])):
            if definition in result:
                result = result.replace(definition, f'@{alias}')
        return result

    def expand(self, text: str) -> str:
        """Expand @aliases to full definitions."""
        result = text
        for alias, definition in self.aliases.items():
            result = result.replace(f'@{alias}', definition)
        return result

    def to_logos_block(self) -> str:
        if not self.aliases:
            return ""
        lines = [f"  @{alias} = {defn}" for alias, defn in self.aliases.items()]
        return "[SCHEMA:v2]\n" + "\n".join(lines) + "\n[/SCHEMA]"

    def token_cost(self) -> int:
        """Estimate token cost of schema block."""
        return max(0, len(self.to_logos_block()) // 4)

    def savings_per_use(self, alias: str) -> int:
        """Tokens saved each time alias is used instead of full definition."""
        if alias not in self.aliases:
            return 0
        full = len(self.aliases[alias]) // 4
        short = (len(alias) + 1) // 4  # +1 for @
        return max(0, full - short)

    def break_even_uses(self, alias: str) -> int:
        """How many uses needed to amortize schema definition cost."""
        savings = self.savings_per_use(alias)
        if savings <= 0:
            return float('inf')
        cost = (len(alias) + len(self.aliases.get(alias, '')) + 5) // 4
        return max(1, cost // savings)


@dataclass
class FidelityAnchor:
    """Represents a fidelity check point in the session."""
    turn: int
    topic: str
    expected: str
    actual: Optional[str] = None
    score: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Session:
    """Full Logos v2 session state."""
    name: str = "unnamed_session"
    schema: SessionSchema = field(default_factory=SessionSchema)
    turns: list[dict] = field(default_factory=list)
    fidelity_anchors: list[FidelityAnchor] = field(default_factory=list)
    turn_count: int = 0
    total_original_tokens: int = 0
    total_logos_tokens: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def compression_ratio(self) -> float:
        if self.total_logos_tokens == 0:
            return 0.0
        return round(self.total_original_tokens / self.total_logos_tokens, 2)

    def add_turn(self, original: str, logos: str):
        orig_tokens = count_tokens(original)
        logos_tokens = count_tokens(logos)
        self.turns.append({
            'turn': self.turn_count + 1,
            'original': original,
            'logos': logos,
            'original_tokens': orig_tokens,
            'logos_tokens': logos_tokens,
            'ratio': round(orig_tokens / max(1, logos_tokens), 2)
        })
        self.total_original_tokens += orig_tokens
        self.total_logos_tokens += logos_tokens
        self.turn_count += 1

    def save(self, path: str):
        data = {
            'name': self.name,
            'schema': asdict(self.schema),
            'turns': self.turns,
            'turn_count': self.turn_count,
            'total_original_tokens': self.total_original_tokens,
            'total_logos_tokens': self.total_logos_tokens,
            'created_at': self.created_at,
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: str) -> 'Session':
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        s = cls(name=data['name'])
        s.schema = SessionSchema(**data['schema'])
        s.turns = data['turns']
        s.turn_count = data['turn_count']
        s.total_original_tokens = data['total_original_tokens']
        s.total_logos_tokens = data['total_logos_tokens']
        s.created_at = data['created_at']
        return s

    def generate_pack(self) -> str:
        """Generate a LOGOS_PACK summarizing all turns."""
        if not self.turns:
            return "[LOGOS_PACK]\n  prior: [empty]\n[/LOGOS_PACK]"
        compressed = []
        for turn in self.turns[-10:]:  # last 10 turns
            compressed.append(turn['logos'])
        prior = '\n    '.join(compressed)
        return f"""[LOGOS_PACK]
  prior:
    {prior}
  now: [t:now]
  turns: {self.turn_count} | ratio: {self.compression_ratio}:1
[/LOGOS_PACK]"""

    def stats(self) -> str:
        lines = [
            f"Session: {self.name}",
            f"Turns: {self.turn_count}",
            f"Original tokens: ~{self.total_original_tokens}",
            f"Logos tokens: ~{self.total_logos_tokens}",
            f"Compression ratio: {self.compression_ratio}:1",
            f"Schema aliases: {len(self.schema.aliases)}",
            f"Tokens saved: ~{self.total_original_tokens - self.total_logos_tokens}",
        ]
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────
# UTILITY FUNCTIONS
# ─────────────────────────────────────────────────────────────────

def count_tokens(text: str) -> int:
    """Approximate token count (4 chars ≈ 1 token)."""
    return max(1, len(text) // 4)


def detect_salience(text: str, context_keywords: list[str] = None) -> str:
    """
    Detect which parts of text are high-salience (new, critical).
    Returns modified text with !! markers on high-salience segments.
    """
    if context_keywords is None:
        context_keywords = []

    # Patterns that suggest high-salience content
    high_salience_patterns = [
        r'error[:\s]+["\']?(.{10,80})["\']?',
        r'exception[:\s]+["\']?(.{10,80})["\']?',
        r'must\s+not\s+(.{5,50})',
        r'critical[:\s]+(.{5,50})',
        r'exactly[:\s]+(.{5,80})',
        r'line \d+',
        r'TypeError|ValueError|KeyError|RuntimeError',
        r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IP addresses
        r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}',    # UUIDs
    ]

    marked = text
    for pattern in high_salience_patterns:
        def add_vital(m):
            return f"!![{m.group(0)}]"
        marked = re.sub(pattern, add_vital, marked, flags=re.IGNORECASE)

    return marked


def compress_with_heuristics(text: str, schema: SessionSchema = None) -> str:
    """Heuristic-based Logos v2 compression."""
    from tools_logos_compress import compress_text  # type: ignore
    # Fallback to v1 compressor + apply schema
    result = text

    # Apply temporal patterns
    result = re.sub(r'\byesterday\b', 't:-1d', result, flags=re.IGNORECASE)
    result = re.sub(r'\btoday\b', 't:today', result, flags=re.IGNORECASE)
    result = re.sub(r'\bright now\b|\bcurrently\b', 't:now', result, flags=re.IGNORECASE)
    result = re.sub(r'\btomorrow\b', 't:+1d', result, flags=re.IGNORECASE)
    result = re.sub(r'\ball night\b|\btoute la nuit\b', 'dur:~8h', result, flags=re.IGNORECASE)
    result = re.sub(r'\bhier\b', 't:-1d', result, flags=re.IGNORECASE)

    # Apply state patterns
    result = re.sub(r'\bfrustrat\w*\b', 'state:frustrated', result, flags=re.IGNORECASE)
    result = re.sub(r'\bblocked\b|\bstuck\b', 'state:blocked', result, flags=re.IGNORECASE)
    result = re.sub(r'\bfailed\b|\bdid not work\b', 'result:fail', result, flags=re.IGNORECASE)

    # Apply schema aliases
    if schema:
        result = schema.apply(result)

    return f"[{result.strip()}]"


def generate_llm_compression_prompt(text: str, schema: SessionSchema = None,
                                     version: str = 'v2') -> str:
    """Generate an optimal prompt for LLM-powered compression."""
    schema_block = schema.to_logos_block() if schema else ""

    return f"""Compress the following text into Logos {version} notation.

RULES:
- [A→B] = A caused B | [A+B] = A linked with B | [A≠B] = A contrasts B
- t:-1d=yesterday | t:now=now | t:+1d=tomorrow | dur:~3h≈3hours
- !=critical | ?=uncertain | ~=approximate
- !!=VERBATIM (never compress, exact wording required)
- state:/goal:/result:/ctx:/env: = situation modifiers
{"- @alias = use session aliases from schema below" if schema and schema.aliases else ""}

{"ACTIVE SESSION SCHEMA:\n" + schema_block if schema and schema.aliases else ""}

COMPRESSION RULES:
1. Remove grammatical overhead (articles, politeness markers, filler)
2. Compress repeated context aggressively
3. Mark critical technical details with !!
4. Preserve ALL semantic meaning — nothing important should be lost
5. Output ONLY the Logos notation, no explanation

TEXT TO COMPRESS:
\"\"\"{text}\"\"\"

LOGOS OUTPUT:"""


# ─────────────────────────────────────────────────────────────────
# LLM API INTEGRATION
# ─────────────────────────────────────────────────────────────────

def compress_with_llm(text: str, schema: SessionSchema = None,
                      api_key: str = None, model: str = "claude") -> dict:
    """
    Use an LLM to compress text to Logos v2.
    Returns dict with 'logos', 'original_tokens', 'logos_tokens', 'ratio'.
    """
    prompt = generate_llm_compression_prompt(text, schema)

    if model.startswith("claude"):
        return _compress_claude(prompt, text, api_key)
    elif model.startswith("gpt"):
        return _compress_openai(prompt, text, api_key)
    else:
        print(f"Model '{model}' not supported for API compression. Using heuristics.")
        logos = compress_with_heuristics(text, schema)
        return {
            'logos': logos,
            'original_tokens': count_tokens(text),
            'logos_tokens': count_tokens(logos),
            'ratio': round(count_tokens(text) / max(1, count_tokens(logos)), 2)
        }


def _compress_claude(prompt: str, original: str, api_key: str) -> dict:
    """Compress using Anthropic Claude API."""
    try:
        import urllib.request
        import urllib.error

        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not provided")

        payload = json.dumps({
            "model": "claude-sonnet-4-6",
            "max_tokens": 500,
            "messages": [{"role": "user", "content": prompt}]
        }).encode('utf-8')

        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=payload,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            logos = data['content'][0]['text'].strip()
            return {
                'logos': logos,
                'original_tokens': count_tokens(original),
                'logos_tokens': count_tokens(logos),
                'ratio': round(count_tokens(original) / max(1, count_tokens(logos)), 2),
                'model': 'claude-sonnet-4-6'
            }
    except Exception as e:
        print(f"Claude API error: {e}. Falling back to heuristics.")
        logos = compress_with_heuristics(original)
        return {'logos': logos, 'original_tokens': count_tokens(original),
                'logos_tokens': count_tokens(logos), 'ratio': 1.0, 'model': 'heuristic'}


def _compress_openai(prompt: str, original: str, api_key: str) -> dict:
    """Compress using OpenAI API."""
    try:
        import urllib.request
        payload = json.dumps({
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 500,
            "temperature": 0
        }).encode('utf-8')
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            logos = data['choices'][0]['message']['content'].strip()
            return {
                'logos': logos,
                'original_tokens': count_tokens(original),
                'logos_tokens': count_tokens(logos),
                'ratio': round(count_tokens(original) / max(1, count_tokens(logos)), 2),
                'model': 'gpt-4o'
            }
    except Exception as e:
        print(f"OpenAI API error: {e}. Falling back to heuristics.")
        logos = compress_with_heuristics(original)
        return {'logos': logos, 'original_tokens': count_tokens(original),
                'logos_tokens': count_tokens(logos), 'ratio': 1.0, 'model': 'heuristic'}


# ─────────────────────────────────────────────────────────────────
# BENCHMARK RUNNER
# ─────────────────────────────────────────────────────────────────

BENCHMARK_SUITE = [
    {
        "id": "A1",
        "category": "Single sentence - temporal",
        "text": "Yesterday I worked on the authentication module.",
        "target_cr": 2.0,
        "target_fs": 0.95
    },
    {
        "id": "A2",
        "category": "Single sentence - causal chain",
        "text": "The deployment failed because the CI pipeline timed out after we pushed a large commit.",
        "target_cr": 3.0,
        "target_fs": 0.90
    },
    {
        "id": "A3",
        "category": "Single sentence - high precision",
        "text": "The race condition occurs when two goroutines simultaneously access the token refresh mutex without proper locking.",
        "target_cr": 2.5,
        "target_fs": 0.90
    },
    {
        "id": "A4",
        "category": "Single sentence - emotional nuance",
        "text": "I'm frustrated but still hopeful — I feel like we're close to the solution, even though we've been stuck for three days.",
        "target_cr": 2.0,
        "target_fs": 0.85
    },
    {
        "id": "A5",
        "category": "French - simple",
        "text": "Hier j'ai passé toute la nuit à essayer de réparer ma machine en panne. J'ai échoué et je suis frustré.",
        "target_cr": 2.5,
        "target_fs": 0.90
    },
]


def run_benchmark(model: str = "heuristic", api_key: str = None,
                  logos_version: str = "v2") -> dict:
    """Run the benchmark suite and return results."""
    results = []
    schema = SessionSchema()

    print(f"\nRunning Logos {logos_version} Benchmark — Model: {model}")
    print("─" * 60)

    for test in BENCHMARK_SUITE:
        if api_key and model != "heuristic":
            result = compress_with_llm(test['text'], schema, api_key, model)
        else:
            logos = compress_with_heuristics(test['text'], schema)
            result = {
                'logos': logos,
                'original_tokens': count_tokens(test['text']),
                'logos_tokens': count_tokens(logos),
                'ratio': round(count_tokens(test['text']) / max(1, count_tokens(logos)), 2)
            }

        cr = result['ratio']
        cr_ok = "✅" if cr >= test['target_cr'] else "⚠️"

        results.append({
            'id': test['id'],
            'category': test['category'],
            'original': test['text'],
            'logos': result['logos'],
            'cr': cr,
            'target_cr': test['target_cr'],
            'cr_ok': cr >= test['target_cr'],
            'fs_note': "Manual verification needed",
        })

        print(f"{test['id']} [{test['category'][:35]:<35}]")
        print(f"   CR: {cr:.1f}:1 (target: {test['target_cr']}:1) {cr_ok}")
        print(f"   Logos: {result['logos'][:70]}...")
        print()

    avg_cr = sum(r['cr'] for r in results) / len(results)
    print(f"Average CR: {avg_cr:.2f}:1")
    print("─" * 60)
    print("Faithfulness score (FS) requires manual verification.")
    print("See spec/BENCHMARK.md for scoring methodology.")

    return {
        'model': model,
        'logos_version': logos_version,
        'date': datetime.now().isoformat(),
        'results': results,
        'avg_cr': round(avg_cr, 2)
    }


# ─────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────

def cmd_compress(args):
    schema = SessionSchema()
    if args.session and Path(args.session).exists():
        session = Session.load(args.session)
        schema = session.schema
    else:
        session = None

    if args.api_key:
        result = compress_with_llm(args.text, schema, args.api_key, args.model)
    else:
        logos = compress_with_heuristics(args.text, schema)
        result = {
            'logos': logos,
            'original_tokens': count_tokens(args.text),
            'logos_tokens': count_tokens(logos),
            'ratio': round(count_tokens(args.text) / max(1, count_tokens(logos)), 2)
        }

    print("\n" + "─" * 55)
    print("ORIGINAL:")
    print(f"  {args.text}")
    print(f"\nLOGOS v2:")
    print(f"  {result['logos']}")
    print(f"\nSTATS:")
    print(f"  Original  : ~{result['original_tokens']} tokens")
    print(f"  Compressed: ~{result['logos_tokens']} tokens")
    print(f"  Ratio     : {result['ratio']}:1")
    print("─" * 55)

    if session:
        session.add_turn(args.text, result['logos'])
        session.save(args.session)
        print(f"\nSession saved. Total ratio: {session.compression_ratio}:1")


def cmd_session(args):
    if args.new:
        name = args.name or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        s = Session(name=name)
        path = f"{name}.logos.json"
        s.save(path)
        print(f"New session created: {path}")
        print(f"\nBoot sequence (paste at start of conversation):")
        print("\n[L2] →=cause,+=link,≠=contrast,!!=vital,??=unknown,t:=time,dur:=duration,@=alias,[SCHEMA]=define,[FA]=verify [/L2]\n")

    elif args.load:
        s = Session.load(args.load)
        print(s.stats())
        if args.pack:
            print("\nGenerated LOGOS_PACK:")
            print(s.generate_pack())

    elif args.pack and args.load:
        s = Session.load(args.load)
        print(s.generate_pack())


def cmd_schema(args):
    session_file = args.session or "current.logos.json"
    if Path(session_file).exists():
        s = Session.load(session_file)
    else:
        s = Session()

    if args.add:
        # Parse "@alias=definition"
        match = re.match(r'@?(\w+)\s*=\s*(.+)', args.add)
        if match:
            alias, definition = match.group(1), match.group(2).strip()
            s.schema.add(alias, definition)
            savings = s.schema.savings_per_use(alias)
            break_even = s.schema.break_even_uses(alias)
            s.save(session_file)
            print(f"Added: @{alias} = {definition}")
            print(f"Saves {savings} tokens/use. Break-even after {break_even} uses.")
        else:
            print("Format: --add '@alias=definition'")

    elif args.list:
        if not s.schema.aliases:
            print("No aliases defined yet.")
        else:
            print("\nActive Schema:")
            print(s.schema.to_logos_block())

    elif args.export:
        print(s.schema.to_logos_block())


def cmd_bench(args):
    results = run_benchmark(
        model=args.model or "heuristic",
        api_key=args.api_key,
        logos_version="v2"
    )
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {args.output}")


def main():
    parser = argparse.ArgumentParser(
        description="Logos v2 — Adaptive LLM Compression Protocol",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest='command')

    # compress
    p_comp = sub.add_parser('compress', help='Compress text to Logos v2')
    p_comp.add_argument('text', help='Text to compress')
    p_comp.add_argument('--session', '-s', help='Session file to use for schema context')
    p_comp.add_argument('--api-key', '-k', help='LLM API key for high-quality compression')
    p_comp.add_argument('--model', '-m', default='claude', help='Model: claude, gpt-4o, heuristic')

    # session
    p_sess = sub.add_parser('session', help='Manage sessions')
    p_sess.add_argument('--new', action='store_true', help='Create new session')
    p_sess.add_argument('--load', help='Load existing session file')
    p_sess.add_argument('--name', help='Session name')
    p_sess.add_argument('--pack', action='store_true', help='Generate LOGOS_PACK')

    # schema
    p_schema = sub.add_parser('schema', help='Manage session schema aliases')
    p_schema.add_argument('--add', help='Add alias: "@name=definition"')
    p_schema.add_argument('--list', action='store_true', help='List all aliases')
    p_schema.add_argument('--export', action='store_true', help='Export schema block')
    p_schema.add_argument('--session', help='Session file')

    # bench
    p_bench = sub.add_parser('bench', help='Run benchmark suite')
    p_bench.add_argument('--model', default='heuristic', help='Model to test')
    p_bench.add_argument('--api-key', help='API key')
    p_bench.add_argument('--output', '-o', help='Save results to JSON file')

    args = parser.parse_args()

    if args.command == 'compress':
        cmd_compress(args)
    elif args.command == 'session':
        cmd_session(args)
    elif args.command == 'schema':
        cmd_schema(args)
    elif args.command == 'bench':
        cmd_bench(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
