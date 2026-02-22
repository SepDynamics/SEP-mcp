# SEP MCP Server – Tool Validation Report

**Generated:** 2026-02-22 01:56:23 UTC  
**Total Tools:** 16  
**Passed:** 16  
**Failed:** 0  
**Status:** ✅ ALL PASS

## Summary

| # | Tool | Status | Time (ms) | Assertions |
|---|------|--------|-----------|------------|
| 1 | `ingest_repo` | ✅ PASS | 5459.7 | 6/6 |
| 2 | `get_index_stats` | ✅ PASS | 1.6 | 6/6 |
| 3 | `list_indexed_files` | ✅ PASS | 0.5 | 4/4 |
| 4 | `search_code` | ✅ PASS | 6.3 | 5/5 |
| 5 | `get_file` | ✅ PASS | 0.1 | 6/6 |
| 6 | `get_file_signature` | ✅ PASS | 0.1 | 5/5 |
| 7 | `compute_signature` | ✅ PASS | 6.3 | 7/7 |
| 8 | `verify_snippet` | ✅ PASS | 24471.5 | 6/6 |
| 9 | `search_by_structure` | ✅ PASS | 1.0 | 5/5 |
| 10 | `inject_fact` | ✅ PASS | 0.5 | 5/5 |
| 11 | `remove_fact` | ✅ PASS | 0.2 | 3/3 |
| 12 | `start_watcher_and_cli_updates` | ✅ PASS | 364.6 | 3/3 |
| 13 | `analyze_code_chaos` | ✅ PASS | 19.2 | 8/8 |
| 14 | `batch_chaos_scan` | ✅ PASS | 3.9 | 6/6 |
| 15 | `predict_structural_ejection` | ✅ PASS | 0.1 | 5/5 |
| 16 | `visualize_manifold_trajectory` | ✅ PASS | 872.6 | 12/12 |

## Detailed Results

### 1. `ingest_repo` — ✅ PASS

**Execution time:** 5459.7ms

**Assertions:**

- ✅ returns string
- ✅ contains '✅'
- ✅ contains 'Text files'
- ✅ contains 'Signatures'
- ✅ reports zero errors
- ✅ no error marker

**Response:**

```
✅ Ingest complete in 5.4s
  Text files : 46
  Binary files: 4
  Total bytes : 2,990,407
  Signatures : 42
  Skipped    : 3
  Errors     : 0
  Avg chaos  : 0.406
  High-risk  : 42
```

---

### 2. `get_index_stats` — ✅ PASS

**Execution time:** 1.6ms

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
  Total Valkey keys  : 1899
  Indexed documents  : 337
  File list entries  : 337
  Structural sigs   : 266
  Chaos profiles    : 266
  Valkey memory      : 3.26G
  Last ingest        : 2026-02-22T01:55:54Z
  Last ingest root   : /sep/structural-manifold-compression/SEP-mcp
  Last text files    : 46
  Last binary files  : 4
  Last total bytes   : 2,990,407
  Last elapsed       : 5.44s
  Avg chaos score    : 0.406
  High-risk files    : 42
  Encoder available  : True
```

---

### 3. `list_indexed_files` — ✅ PASS

**Execution time:** 0.5ms

**Assertions:**

- ✅ returns string
- ✅ contains 'Indexed files'
- ✅ lists .py files
- ✅ no error marker

**Response:**

```
Indexed files (20):
3body-chaos-proxy/setup.py
SEP-mcp/scripts/__init__.py
SEP-mcp/src/manifold/__init__.py
SEP-mcp/src/manifold/encoder.py
SEP-mcp/src/manifold/verifier.py
SEP-mcp/tests/conftest.py
manim/__init__.py
manim/scenes/__init__.py
scripts/__init__.py
scripts/experiments/build_causal_domain.py
scripts/rag/synthesize_thalamic.py
scripts/rag/test_programmer.py
scripts/utils/setup_quantum.py
src/manifold/__init__.py
src/manifold/encoder.py
src/manifold/verifier.py
tests/conftest.py
tests/test_compression.py
tests/test_prepare_corpus.py
verify_workspace.py
```

---

### 4. `search_code` — ✅ PASS

**Execution time:** 6.3ms

**Assertions:**

- ✅ returns string
- ✅ contains 'Found'
- ✅ shows match context
- ✅ mentions mcp_server.py
- ✅ no error marker

**Response:**

```
Found 5 file(s) matching 'chaos_score' (scanned 67):

📄 scripts/rag/pair_programmer_agent.py  (2 matches)
      L65:             
      L66:             if chaos and chaos["collapse_risk"] == "HIGH":
  >>> L67:                 print(f"⚠️ WARNING: {filepath.name} is in PERSISTENT_HIGH state (score: {chaos['chaos_score']:.3f}).")
      L68:                 print(f"Impending structural ejection detected!")
      L69:             elif chaos:
  >>> L70:                 print(f"✅ {filepath.name} chaos score: {chaos['chaos_score']:.3f} ({chaos['collapse_risk']})")
      L71: 
      L72:             verified, response, coverage, _ = self.router.process_query(

📄 3body-chaos-proxy/gpu_batch_validation.py  (6 matches)
      L238:     print("Running C++ Symbolic Chaos Kernel over batch...")
      L239:     # Pre-allocate
  >>> L240:     chaos_score_all = np.zeros_like(K_all_cpu)
      L241:     window_size = 200
      L242: 
      L260:         results = chaos_proxy.analyze_window_batch(windows_to_process)
      L261:         for i, res in enumerate(results):
  >>> L262:             chaos_score_all[i, b] = res.fluctuation_persistence
      L263: 
      L264:     print(f"C++ mapping took {time.time() - t_compile_start:.2f} sec")
      L270:     mis = []
      L271:     survival_times = []
  >>> L272:     mean_chaos_scores = []
      L273: 
      L274:     for b in valid_batch_indices:
      L290: 
      L291:         l_valid = l_smoothed[start_idx:][final_mask]
  >>> L292:         c_valid = chaos_score_all[start_idx:, b][final_mask]
      L293: 
      L294:         if len(l_valid) < 50 or np.var(l_valid) < 1e-10 or np.var(c_valid) < 1e-10:
      L314:             survival_step = num_steps
      L315:         survival_times.append(survival_step * DT)
  >>> L316:         mean_chaos_scores.append(float(np.mean(c_valid)))
      L317: 
      L318:     print("\n--- Massive GPU Validation Summary ---")

📄 3body-chaos-proxy/three_body_demo.py  (10 matches)
      L123: 
      L124: prin
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

**Execution time:** 6.3ms

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

**Execution time:** 24471.5ms

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
  Matched docs    : SEP-mcp/src/manifold/encoder.py, src/manifold/encoder.py, tests/trading/test_gate_evaluation.py
```

---

### 9. `search_by_structure` — ✅ PASS

**Execution time:** 1.0ms

**Assertions:**

- ✅ returns string
- ✅ contains 'structurally similar'
- ✅ shows delta values
- ✅ lists file paths
- ✅ no error marker

**Response:**

```
Files structurally similar to c0.462_s0.8_e0.928 (±0.05):
  c0.463_s0.802_e0.928  Δ=0.0020  scripts/experiments/prototype_cache.py
  c0.465_s0.803_e0.923  Δ=0.0050  SEP-mcp/README.md
  c0.46_s0.792_e0.931  Δ=0.0080  scripts/experiments/run_optical_inference.py
  c0.461_s0.804_e0.937  Δ=0.0090  SEP-mcp/scripts/rag/prepare_corpus.py
  c0.461_s0.804_e0.937  Δ=0.0090  scripts/rag/prepare_corpus.py
```

---

### 10. `inject_fact` — ✅ PASS

**Execution time:** 0.5ms

**Assertions:**

- ✅ returns string
- ✅ contains '🚀'
- ✅ no error marker
- ✅ fact retrievable via get_file
- ✅ visible in search_code

**Response:**

```
🚀 Fact '__test_fact_1771725348' injected into the Dynamic Semantic Codebook.
```

---

### 11. `remove_fact` — ✅ PASS

**Execution time:** 0.2ms

**Assertions:**

- ✅ returns string
- ✅ contains '🗑️'
- ✅ erased from search_code

**Response:**

```
🗑️ Fact '__test_fact_1771725348' removed from the Dynamic Semantic Codebook.
```

---

### 12. `start_watcher_and_cli_updates` — ✅ PASS

**Execution time:** 364.6ms

**Assertions:**

- ✅ watcher starts
- ✅ cli creation indexed dynamically
- ✅ cli deletion unindexed dynamically

**Response:**

```
✅ Watcher started for /sep/structural-manifold-compression/SEP-mcp (cap 512000 bytes)
```

---

### 13. `analyze_code_chaos` — ✅ PASS

**Execution time:** 19.2ms

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
Chaos Score (fluctuation_persistence) : 0.404
Entropy                               : 0.905
Coherence                             : 0.339
Collapse Risk                         : HIGH
Windows analyzed                      : 10

```

---

### 14. `batch_chaos_scan` — ✅ PASS

**Execution time:** 3.9ms

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

  [HIGH] 0.425 | scripts/experiments/eval_math_dataset.py
  [HIGH] 0.424 | scripts/rag/synthesize_thalamic.py
  [HIGH] 0.422 | scripts/rag/bulk_valkey_ingest.py
  [HIGH] 0.422 | SEP-mcp/scripts/rag/bulk_valkey_ingest.py
  [HIGH] 0.421 | scripts/rag/stress_test_valkey.py
```

---

### 15. `predict_structural_ejection` — ✅ PASS

**Execution time:** 0.1ms

**Assertions:**

- ✅ returns string
- ✅ mentions state
- ✅ mentions file path
- ✅ includes score
- ✅ no error marker

**Response:**

```
⚠️ WARNING: mcp_server.py is in PERSISTENT_HIGH state (score: 0.404).
Predicted structural ejection in ~9 days without refactoring.
```

---

### 16. `visualize_manifold_trajectory` — ✅ PASS

**Execution time:** 872.6ms

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
  Avg Chaos Score     : 0.395
  Max Chaos Score     : 0.437
  Avg Entropy         : 0.899
  Avg Coherence       : 0.371
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
