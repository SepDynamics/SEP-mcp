# SEP MCP Server – Tool Validation Report

**Generated:** 2026-02-22 01:05:05 UTC  
**Total Tools:** 15  
**Passed:** 15  
**Failed:** 0  
**Status:** ✅ ALL PASS

## Summary

| # | Tool | Status | Time (ms) | Assertions |
|---|------|--------|-----------|------------|
| 1 | `get_index_stats` | ✅ PASS | 4991.9 | 6/6 |
| 2 | `ingest_repo` | ✅ PASS | 635.5 | 6/6 |
| 3 | `list_indexed_files` | ✅ PASS | 0.4 | 4/4 |
| 4 | `search_code` | ✅ PASS | 7.5 | 5/5 |
| 5 | `get_file` | ✅ PASS | 0.1 | 6/6 |
| 6 | `get_file_signature` | ✅ PASS | 0.1 | 5/5 |
| 7 | `compute_signature` | ✅ PASS | 5.0 | 7/7 |
| 8 | `verify_snippet` | ✅ PASS | 4986.4 | 6/6 |
| 9 | `search_by_structure` | ✅ PASS | 0.7 | 5/5 |
| 10 | `inject_fact` | ✅ PASS | 0.1 | 9/9 |
| 11 | `start_watcher` | ✅ PASS | 245.0 | 6/6 |
| 12 | `analyze_code_chaos` | ✅ PASS | 76.2 | 8/8 |
| 13 | `batch_chaos_scan` | ✅ PASS | 2.7 | 6/6 |
| 14 | `predict_structural_ejection` | ✅ PASS | 0.0 | 5/5 |
| 15 | `visualize_manifold_trajectory` | ✅ PASS | 909.9 | 12/12 |

## Detailed Results

### 1. `get_index_stats` — ✅ PASS

**Execution time:** 4991.9ms

**Assertions:**

- ✅ returns string
- ✅ contains '📊'
- ✅ contains 'Indexed documents'
- ✅ contains 'Valkey memory'
- ✅ contains 'Encoder available'
- ✅ no error marker

**Response:**

```
📊 Codebase Index Stats
  Total Valkey keys  : 1347
  Indexed documents  : 115
  File list entries  : 114
  Structural sigs   : 101
  Chaos profiles    : 101
  Valkey memory      : 3.25G
  Last ingest        : 2026-02-22T01:04:23Z
  Last ingest root   : /sep/structural-manifold-compression/SEP-mcp
  Last text files    : 46
  Last binary files  : 4
  Last total bytes   : 2,984,410
  Last elapsed       : 0.63s
  Avg chaos score    : 0.406
  High-risk files    : 42
  Encoder available  : True
```

---

### 2. `ingest_repo` — ✅ PASS

**Execution time:** 635.5ms

**Assertions:**

- ✅ returns string
- ✅ contains '✅'
- ✅ contains 'Text files'
- ✅ contains 'Signatures'
- ✅ reports zero errors
- ✅ no error marker

**Response:**

```
✅ Ingest complete in 0.6s
  Text files : 46
  Binary files: 4
  Total bytes : 2,984,407
  Signatures : 42
  Skipped    : 3
  Errors     : 0
  Avg chaos  : 0.405
  High-risk  : 42
```

---

### 3. `list_indexed_files` — ✅ PASS

**Execution time:** 0.4ms

**Assertions:**

- ✅ returns string
- ✅ contains 'Indexed files'
- ✅ lists .py files
- ✅ no error marker

**Response:**

```
Indexed files (20):
scripts/__init__.py
scripts/experiments/build_causal_domain.py
scripts/experiments/build_hybrid_report.py
scripts/experiments/plot_curves.py
scripts/experiments/plot_fep_curves.py
scripts/experiments/plot_hebbian_convergence.py
scripts/rag/inject_5m_signatures.py
scripts/rag/stress_test_valkey.py
scripts/rag/synthesize_thalamic.py
scripts/rag/test_programmer.py
scripts/rag/verify_5m_latency.py
scripts/tests/build_codebook.py
src/manifold/__init__.py
src/manifold/encoder.py
src/manifold/verifier.py
test_wrapper.py
tests/conftest.py
tests/test_compression.py
tests/test_prepare_corpus.py
tests/test_sidecar.py
```

---

### 4. `search_code` — ✅ PASS

**Execution time:** 7.5ms

**Assertions:**

- ✅ returns string
- ✅ contains 'Found'
- ✅ shows match context
- ✅ mentions mcp_server.py
- ✅ no error marker

**Response:**

```
Found 3 file(s) matching 'chaos_score' (scanned 76):

📄 mcp_server.py  (5 matches)
      L226: 
      L227:     return {
  >>> L228:         "chaos_score": avg_fp,
      L229:         "entropy": avg_entropy,
      L230:         "coherence": avg_coherence,
      L336:             if chaos:
      L337:                 pipe.set(f"manifold:chaos:{rel}", json.dumps(chaos))
  >>> L338:                 total_chaos += chaos["chaos_score"]
      L339:                 if chaos["collapse_risk"] == "HIGH":
      L340:                     high_risk += 1
      L869: 
      L870:     return f"""📈 Chaos Analysis for {path}
  >>> L871: Chaos Score (fluctuation_persistence) : {result['chaos_score']:.3f}
      L872: Entropy                               : {result['entropy']:.3f}
      L873: Coherence                             : {result['coherence']:.3f}
      L900:             try:
      L901:                 chaos = json.loads(chaos_data)
  >>> L902:                 results.append((chaos["chaos_score"], rel, chaos))
      L903:             except json.JSONDecodeError:
      L904:                 pass
      L933: 
      L934:     chaos = json.loads(chaos_data)
  >>> L935:     score = chaos["chaos_score"]
      L936: 
      L937:     if score >= 0.35:

📄 scripts/tests/test_mcp_tools.py  (1 match)
      L159: 
      L160: def test_search_code() -> ToolTestResult:
  >>> L161:     r = run_tool("search_code", srv.search_code, query="chaos_score", file_pattern="*.py", max_results=5)
      L162:     r.assert_check("returns string", isinstance(r.response, str))
      L163:     r.assert_check("contains 'Found'", "Found" in r.response)

📄 scripts/rag/pair_programmer_agent.py  (2 matches)
      L65:             
      L66:             if chaos and chaos["collapse_risk"] == "HIGH":
  >>> L67:                 print(f"⚠️ WARNING: {filepath.name} is in PERSISTENT_HIGH state (score: {chaos['chaos_score']:.3f}).")
      L68:                 print(f"Impending structural ejection detected!")
      L69
... (truncated)
```

---

### 5. `get_file` — ✅ PASS

**Execution time:** 0.1ms

**Assertions:**

- ✅ returns string
- ✅ contains '📄'
- ✅ shows line numbers
- ✅ contains 'encoder.py'
- ✅ contains actual code
- ✅ no error marker

**Response:**

```
📄 src/manifold/encoder.py (31 lines, 887 chars):

    1 | """Wrapper utilities for structural manifold encoding."""
    2 | 
    3 | from __future__ import annotations
    4 | 
    5 | from pathlib import Path
    6 | from typing import Dict, Optional
    7 | 
    8 | from scripts.experiments.manifold_compression_eval import evaluate_manifold
    9 | 
   10 | 
   11 | def build_signature_index(
   12 |     text_root: Path,
   13 |     window_bytes: int = 512,
   14 |     stride_bytes: int = 384,
   15 |     precision: int = 3,
   16 |     tokenizer_name: str = "gpt2",
   17 |     tokenizer_trust_remote_code: bool = False,
   18 |     max_documents: Optional[int] = None,
   19 | ) -> Dict[str, object]:
   20 |     """Return the same summary dictionary exposed by benchmark_eval."""
   21 | 
   22 |     return evaluate_manifold(
   23 |         text_root=text_root,
   24 |         window_bytes=window_bytes,
   25 |         stride_bytes=stride_bytes,
   26 |         precision=precision,
   27 |         tokenizer_name=tokenizer_name,
   28 |         tokenizer_trust_remote_code=tokenizer_trust_remote_code,
   29 |         max_documents=max_documents,
   30 |     )
   31 | 
```

---

### 6. `get_file_signature` — ✅ PASS

**Execution time:** 0.1ms

**Assertions:**

- ✅ returns string
- ✅ contains '📐'
- ✅ contains signature format
- ✅ references mcp_server.py
- ✅ no error marker

**Response:**

```
📐 mcp_server.py → signature: c0.462_s0.8_e0.928
```

---

### 7. `compute_signature` — ✅ PASS

**Execution time:** 5.0ms

**Assertions:**

- ✅ returns string
- ✅ contains '✅'
- ✅ mentions compression ratio
- ✅ mentions unique signatures
- ✅ mentions total windows
- ✅ mentions hazard threshold
- ✅ no error marker

**Response:**

```
✅ Compressed 887 bytes → 9 manifold bytes
  Compression ratio  : 98.56×
  Unique signatures  : 1
  Total windows      : 1
  Hazard threshold   : 0.3932
```

---

### 8. `verify_snippet` — ✅ PASS

**Execution time:** 4986.4ms

**Assertions:**

- ✅ returns string
- ✅ contains VERIFIED or FAILED
- ✅ shows coverage
- ✅ shows match ratio
- ✅ shows gated hits
- ✅ no error marker

**Response:**

```
Status: ✅ VERIFIED
  Safe coverage   : 100.00%
  Raw match ratio : 100.00%
  Gated hits      : 1/1
  Matched docs    : src/manifold/encoder.py, tests/trading/test_gate_evaluation.py
```

---

### 9. `search_by_structure` — ✅ PASS

**Execution time:** 0.7ms

**Assertions:**

- ✅ returns string
- ✅ contains 'structurally similar'
- ✅ shows delta values
- ✅ lists file paths
- ✅ no error marker

**Response:**

```
Files structurally similar to c0.462_s0.8_e0.928 (±0.05):
  c0.463_s0.802_e0.927  Δ=0.0020  scripts/data/prepare_causal_dataset.py
  c0.463_s0.802_e0.928  Δ=0.0020  scripts/experiments/prototype_cache.py
  c0.461_s0.797_e0.93  Δ=0.0030  README.md
  c0.462_s0.797_e0.924  Δ=0.0040  scripts/inference/dual_stream_inference.py
  c0.461_s0.801_e0.933  Δ=0.0050  scripts/data/download_finemath.py
```

---

### 10. `inject_fact` — ✅ PASS

**Execution time:** 0.1ms

**Assertions:**

- ✅ returns string
- ✅ contains '🚀'
- ✅ mentions fact_id
- ✅ mentions codebook
- ✅ no error marker
- ✅ fact retrievable via get_file
- ✅ retrieved fact is not an error
- ✅ fact stored correctly in Valkey
- ✅ index invalidated after injection

**Response:**

```
🚀 Fact '__test_fact_1771722293' injected into the Dynamic Semantic Codebook.
```

---

### 11. `start_watcher` — ✅ PASS

**Execution time:** 245.0ms

**Assertions:**

- ✅ returns string
- ✅ contains '✅'
- ✅ mentions watcher started or already running
- ✅ no error marker
- ✅ observer is active
- ✅ idempotent – already running

**Response:**

```
✅ Watcher started for /sep/structural-manifold-compression/SEP-mcp (cap 512000 bytes)
```

---

### 12. `analyze_code_chaos` — ✅ PASS

**Execution time:** 76.2ms

**Assertions:**

- ✅ returns string
- ✅ contains '📈'
- ✅ shows chaos score
- ✅ shows entropy
- ✅ shows coherence
- ✅ shows collapse risk
- ✅ shows windows analyzed
- ✅ no error marker

**Response:**

```
📈 Chaos Analysis for mcp_server.py
Chaos Score (fluctuation_persistence) : 0.401
Entropy                               : 0.906
Coherence                             : 0.352
Collapse Risk                         : HIGH
Windows analyzed                      : 10

```

---

### 13. `batch_chaos_scan` — ✅ PASS

**Execution time:** 2.7ms

**Assertions:**

- ✅ returns string
- ✅ contains '🔍'
- ✅ shows risk levels
- ✅ shows scores
- ✅ shows file paths
- ✅ no error marker

**Response:**

```
🔍 Batch Chaos Scan (Top 5 highest risk files matching *.py):

  [HIGH] 0.426 | test_wrapper.py
  [HIGH] 0.425 | scripts/experiments/eval_math_dataset.py
  [HIGH] 0.424 | scripts/rag/synthesize_thalamic.py
  [HIGH] 0.422 | scripts/rag/bulk_valkey_ingest.py
  [HIGH] 0.421 | scripts/rag/stress_test_valkey.py
```

---

### 14. `predict_structural_ejection` — ✅ PASS

**Execution time:** 0.0ms

**Assertions:**

- ✅ returns string
- ✅ mentions state
- ✅ mentions file path
- ✅ includes score
- ✅ no error marker

**Response:**

```
⚠️ WARNING: mcp_server.py is in PERSISTENT_HIGH state (score: 0.401).
Predicted structural ejection in ~9 days without refactoring.
```

---

### 15. `visualize_manifold_trajectory` — ✅ PASS

**Execution time:** 909.9ms

**Assertions:**

- ✅ returns string
- ✅ contains '📊'
- ✅ mentions dashboard
- ✅ references the file
- ✅ reports windows analyzed
- ✅ reports chaos score
- ✅ reports symbolic states
- ✅ reports collapse risk
- ✅ PNG saved
- ✅ no error marker
- ✅ PNG file exists on disk
- ✅ PNG file has content

**Response:**

```
📊 4-Panel Manifold Dashboard saved to: reports/manifold_trajectory_mcp_server.py.png

  File                : mcp_server.py
  Windows analyzed    : 21
  Avg Chaos Score     : 0.400
  Max Chaos Score     : 0.439
  Avg Entropy         : 0.907
  Avg Coherence       : 0.362
  Collapse Risk       : HIGH

  Symbolic States:
    LOW_FLUCTUATION   : 0
    OSCILLATION       : 0
    PERSISTENT_HIGH   : 21

  Dashboard panels:
    1. Structural trajectory (byte offset vs coherence, colored by chaos)
    2. Chaos vs LLE analog (entropy vs hazard scatter)
    3. Time series (hazard/entropy/coherence per window)
    4. Symbolic state distribution (LOW/OSCILLATION/HIGH bar chart)
```

**Generated Dashboard:**

![Manifold Trajectory Dashboard](reports/manifold_trajectory_mcp_server.py.png)

---
