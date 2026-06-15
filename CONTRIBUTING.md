# Contributing to Logos Protocol

Thank you for your interest! Logos is a community-driven project.

## Ways to Contribute

### 1. 🧪 Benchmarks (most needed)
Run compression tests and share results:
- Pick 10+ real conversation excerpts
- Compress with Logos
- Count tokens before/after (use tiktoken or similar)
- Share the ratio + which model you tested with
- Open an issue with tag `benchmark`

### 2. ➕ New Operators
Propose new operators:
- Open an issue with tag `new-operator`
- Explain what it encodes, why existing operators don't cover it
- Provide 3+ examples of usage
- Community votes before merging

Current priority gaps:
- Logical quantifiers (`∀`, `∃`)  
- Probability / confidence levels
- Hierarchical relationships (parent/child)
- Domain-specific shortcuts (medical, legal, finance)

### 3. 🌍 Domain Packs
Create a `domain-packs/` file for a specific field:
```
domain-packs/
  medical.md       # clinical notes compression
  legal.md         # contract/case context
  finance.md       # trading/reporting context
  devops.md        # infrastructure/incident context
```

### 4. 🔧 Tools
Improve `tools/logos-compress.py` or add new tools:
- Better heuristic extraction
- Integration with the OpenAI / Anthropic APIs
- VS Code extension
- Browser extension for Claude.ai / ChatGPT

### 5. 🐛 Bug Reports
If Logos produces wrong decompression with a specific model:
- Open an issue with tag `decompression-error`
- Include: model name, Logos input, expected output, actual output

---

## Pull Request Process

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Make changes
4. Test with at least one LLM
5. Update relevant docs
6. Open a PR with description of changes + test results

---

## Code Style (for Python tools)

- Python 3.10+
- Type hints on all functions
- Docstrings on public functions
- No external dependencies in core files (stdlib only)
- External dependencies go in `requirements.txt`

---

## License

By contributing, you agree your contributions will be licensed under MIT.
