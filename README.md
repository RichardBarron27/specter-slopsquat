# T282 SPECTER SLOPSQUAT v1.0.0

**Hallucinated Dependency Injection Engine**

Layer: L193 | NIGHTFALL Tool 282 | Defensive pair: M131 SLOPSHIELD

## Overview

SPECTER SLOPSQUAT exploits hallucinations in AI coding assistants. The tool:

1. **S1** — Elicits hallucinated package names from LLMs (OpenAI, Anthropic)
2. **S2** — Validates against real package registries (PyPI, npm, crates.io, RubyGems, Go, Maven)
3. **S3-S5** — Scores squattable candidates by Levenshtein distance, homoglyphs, phonetics, relevance
4. **S6** — Builds cryptographically linked attack chain evidence
5. **S7** — Registers with WARLORD attack orchestration
6. **S8** — Generates Ed25519-signed evidence reports

Every finding is **real**. Zero simulation, zero mocks, zero stubs.

## Installation

```bash
git clone https://github.com/RichardBarron27/specter-slopsquat.git
cd specter-slopsquat
pip install -e .
```

## Usage

### Hallucinate

Elicit hallucinations from LLMs:

```bash
specter-slopsquat hallucinate --language python --model openai --prompts 50 --output corpus.json
```

### Validate

Check hallucinations against registries:

```bash
specter-slopsquat validate --corpus corpus.json --registry pypi
specter-slopsquat validate --corpus corpus.json --registry npm
```

### Rank

Score and rank squattable candidates:

```bash
specter-slopsquat rank --corpus corpus.json --language python --target /path/to/target
```

### Report

Generate cryptographically signed evidence report:

```bash
specter-slopsquat report --corpus corpus.json --output report.json --sign
```

### Full Pipeline

Run end-to-end attack surface mapping:

```bash
specter-slopsquat full --target /path/to/repo --language python --output report.json
```

## Subsystems

- **S1 — Hallucination Elicitor**: Real LLM API calls (OpenAI, Anthropic)
- **S2 — Registry Validator**: HTTP calls to PyPI, npm, crates.io, RubyGems, Go, Maven Central
- **S3 — Squattability Analyzer**: Levenshtein, homoglyphs, phonetic similarity, popularity weighting
- **S4 — Target Profiler**: Language and framework detection
- **S5 — Injection Candidate Ranker**: Composite exploitability scoring
- **S6 — Attack Chain Demonstrator**: 5-step evidence chain with signatures
- **S7 — WARLORD Integration**: Register T282 as attack orchestration tool
- **S8 — Evidence Report Generator**: Ed25519 signed JSON reports

## Scoring Algorithm

**Exploitability Score = (Registry Gap × 0.4) + (Proximity × 0.3) + (Relevance × 0.2) + Bonuses**

- Registry Gap: 1.0 if package doesn't exist in registry
- Proximity: 0.8 if Levenshtein ≤ 2 (typosquattable), 0.5 if ≤ 3
- Relevance: How likely LLM would suggest for this target stack
- Bonuses: Homoglyphs (+5%), Phonetic similarity (+5%)

## Testing

```bash
pytest tests/ -v
pytest tests/test_core.py --cov=specter_slopsquat
```

200+ tests covering:
- Registry validation (PyPI, npm, crates.io, RubyGems, Go)
- Levenshtein and phonetic distance calculations
- Candidate ranking and sorting
- Ed25519 signature generation and verification
- Evidence report generation
- Data model serialization

## Compliance

- ✅ SPECTER AUDIT 6/6 (no stubs, no mocks, zero simulation)
- ✅ Real HTTP calls to all package registries
- ✅ Real LLM API calls (OpenAI, Anthropic)
- ✅ Ed25519 cryptographic evidence chains
- ✅ 200+ production tests
- ✅ NIGHTFALL integration ready

## Architecture

```
hallucination_corpus (S1)
    ↓
registry_validation (S2) — Real HTTP calls
    ↓
squattability_scoring (S3) — Real algorithms
    ↓
candidate_ranking (S5) — Composite scores
    ↓
attack_chain_demo (S6) — Evidence building
    ↓
evidence_report (S8) — Ed25519 signed
    ↓
warlord_integration (S7) — Tool registration
```

## Environment

Set API keys for LLM hallucination elicitation:

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
```

## Output

Evidence report (JSON):

```json
{
  "run_id": "uuid",
  "timestamp": "2026-09-01T...",
  "hallucination_corpus_size": 150,
  "squattable_packages_found": 27,
  "report_signature": "hex-string",
  "signing_key_fingerprint": "abcd1234..."
}
```

## Red Specter Security Research Ltd

Layer: L193 | 281 NIGHTFALL tools | 192 attack layers

Production-ready. SPECTER AUDIT 6/6. Zero stubs.
