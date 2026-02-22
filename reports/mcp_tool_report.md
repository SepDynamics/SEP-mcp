# SEP MCP Server – Tool Validation Report

**Generated:** 2026-02-22 22:24:15 UTC  
**Total Tools:** 16  
**Passed:** 16  
**Failed:** 0  
**Status:** ✅ ALL PASS

## Summary

| # | Tool | Status | Time (ms) | Assertions |
|---|------|--------|-----------|------------|
| 1 | `ingest_repo` | ✅ PASS | 143355.0 | 6/6 |
| 2 | `get_index_stats` | ✅ PASS | 284.7 | 6/6 |
| 3 | `list_indexed_files` | ✅ PASS | 5.7 | 4/4 |
| 4 | `search_code` | ✅ PASS | 355.6 | 5/5 |
| 5 | `get_file` | ✅ PASS | 0.4 | 6/6 |
| 6 | `get_file_signature` | ✅ PASS | 0.1 | 5/5 |
| 7 | `compute_signature` | ✅ PASS | 0.6 | 7/7 |
| 8 | `verify_snippet` | ✅ PASS | 125721.3 | 6/6 |
| 9 | `search_by_structure` | ✅ PASS | 2.7 | 5/5 |
| 10 | `inject_fact` | ✅ PASS | 1.6 | 5/5 |
| 11 | `remove_fact` | ✅ PASS | 0.3 | 3/3 |
| 12 | `start_watcher_and_cli_updates` | ✅ PASS | 377.1 | 3/3 |
| 13 | `analyze_code_chaos` | ✅ PASS | 2.7 | 8/8 |
| 14 | `batch_chaos_scan` | ✅ PASS | 30.9 | 6/6 |
| 15 | `predict_structural_ejection` | ✅ PASS | 0.2 | 5/5 |
| 16 | `visualize_manifold_trajectory` | ✅ PASS | 845.6 | 12/12 |

## Detailed Results

### 1. `ingest_repo` — ✅ PASS

**Execution time:** 143355.0ms

**Assertions:**

- ✅ returns string
- ✅ contains '✅'
- ✅ contains 'Text files'
- ✅ contains 'Signatures'
- ✅ reports zero errors
- ✅ no error marker

**Response:**

```
✅ Ingest complete in 143.2s
  Text files : 5479
  Binary files: 2
  Total bytes : 108,247,815
  Signatures : 4568
  Skipped    : 100
  Errors     : 0
  Avg chaos  : 0.402
  High-risk  : 4555
```

---

### 2. `get_index_stats` — ✅ PASS

**Execution time:** 284.7ms

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
  Total Valkey keys  : 5483
  Indexed documents  : 5481
  File list entries  : 5481
  Structural sigs   : 4568
  Chaos profiles    : 4568
  Valkey memory      : 33.14M
  Last ingest        : 2026-02-22T22:22:02Z
  Last ingest root   : /sep/structural-manifold-compression/SEP-mcp
  Last text files    : 5479
  Last binary files  : 2
  Last total bytes   : 108,247,815
  Last elapsed       : 143.15s
  Avg chaos score    : 0.402
  High-risk files    : 4555
  Encoder available  : True
```

---

### 3. `list_indexed_files` — ✅ PASS

**Execution time:** 5.7ms

**Assertions:**

- ✅ returns string
- ✅ contains 'Indexed files'
- ✅ lists .py files
- ✅ no error marker

**Response:**

```
Indexed files (20):
cpython/Lib/test/relimport.py
cpython/Lib/test/test_import/data/circular_imports/basic2.py
cpython/Lib/test/test_import/data/circular_imports/subpkg/util.py
cpython/Lib/test/test_import/data/circular_imports/util.py
cpython/Lib/test/test_import/data/lazy_imports/basic2.py
cpython/Lib/test/test_import/data/lazy_imports/lazy_try_except_from_star.py
cpython/Lib/test/test_import/data/lazy_imports/pkg/__init__.py
cpython/Lib/test/test_importlib/namespace_pkgs/module_and_namespace_package/a_test.py
cpython/Lib/test/test_importlib/namespace_pkgs/not_a_namespace_pkg/foo/one.py
cpython/Lib/test/test_importlib/namespace_pkgs/portion1/foo/one.py
cpython/Lib/test/test_importlib/namespace_pkgs/portion2/foo/two.py
cpython/Lib/test/test_importlib/namespace_pkgs/project1/parent/child/one.py
cpython/Lib/test/test_importlib/namespace_pkgs/project2/parent/child/two.py
cpython/Lib/test/tokenizedata/bad_coding.py
cpython/Lib/test/tokenizedata/badsyntax_pep3120.py
cpython/Lib/test/tokenizedata/coding20731.py
cpython/Lib/test/typinganndata/partialexecution/__init__.py
cpython/Tools/c-analyzer/c_common/__init__.py
cpython/Tools/freeze/hello.py
cpython/Tools/freeze/test/ok.py
```

---

### 4. `search_code` — ✅ PASS

**Execution time:** 355.6ms

**Assertions:**

- ✅ returns string
- ✅ contains 'Found'
- ✅ shows match context
- ✅ mentions mcp_server.py
- ✅ no error marker

**Response:**

```
Found 3 file(s) matching 'chaos_score' (scanned 2271):

📄 mcp_server.py  (5 matches)
      L258: 
      L259:     return {
  >>> L260:         "chaos_score": avg_fp,
      L261:         "entropy": avg_entropy,
      L262:         "coherence": avg_coherence,
      L392:                 if chaos:
      L393:                     fields["chaos"] = _compress(json.dumps(chaos).encode("utf-8"))
  >>> L394:                     total_chaos += chaos["chaos_score"]
      L395:                     if chaos["collapse_risk"] == "HIGH":
      L396:                         high_risk += 1
      L1123: 
      L1124:     return f"""📈 Chaos Analysis for {path}
  >>> L1125: Chaos Score (fluctuation_persistence) : {result['chaos_score']:.3f}
      L1126: Entropy                               : {result['entropy']:.3f}
      L1127: Coherence                             : {result['coherence']:.3f}
      L1187:                         )
      L1188:                     chaos = json.loads(js)
  >>> L1189:                     results.append((chaos["chaos_score"], rel, chaos))
      L1190:                 except json.JSONDecodeError:
      L1191:                     pass
      L1243:         return f"✖ Failed to parse chaos profile for {path}."
      L1244: 
  >>> L1245:     score = chaos["chaos_score"]
      L1246: 
      L1247:     if score >= 0.35:

📄 scripts/tests/test_mcp_tools.py  (1 match)
      L180:         "search_code",
      L181:         srv.search_code,
  >>> L182:         query="chaos_score",
      L183:         file_pattern="*.py",
      L184:         max_results=5,

📄 scripts/rag/pair_programmer_agent.py  (2 matches)
      L65:             
      L66:             if chaos and chaos["collapse_risk"] == "HIGH":
  >>> L67:                 print(f"⚠️ WARNING: {filepath.name} is in PERSISTENT_HIGH state (score: {chaos['chaos_score']:.3f}).")
      L68:                 print(f"Impending structural ejection detected!")
      L69:             elif chaos:
  >>> L70:                 prin
... (truncated)
```

---

### 5. `get_file` — ✅ PASS

**Execution time:** 0.4ms

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
📐 mcp_server.py → signature: c0.213_s0.000_e0.928
```

---

### 7. `compute_signature` — ✅ PASS

**Execution time:** 0.6ms

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

**Execution time:** 125721.3ms

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
  Matched docs    : cpython/Doc/_static/tachyon-example-heatmap.html, cpython/Doc/howto/curses.rst, cpython/Doc/howto/functional.rst, cpython/Doc/library/functions.rst, cpython/Doc/library/multiprocessing.rst, cpython/Doc/library/ssl.rst, cpython/Doc/library/sys.rst, cpython/Doc/library/typing.rst, cpython/Doc/using/cmdline.rst, cpython/Doc/using/windows.rst, cpython/Doc/whatsnew/2.3.rst, cpython/Doc/whatsnew/3.10.rst, cpython/Lib/_pyrepl/_module_completer.py, cpython/Lib/asyncio/unix_events.py, cpython/Lib/idlelib/format.py, cpython/Lib/inspect.py, cpython/Lib/posixpath.py, cpython/Lib/profiling/sampling/heatmap_collector.py, cpython/Lib/test/pythoninfo.py, cpython/Lib/test/test_ast/test_ast.py, cpython/Lib/test/test_logging.py, cpython/Lib/test/test_long.py, cpython/Lib/test/test_profiling/test_sampling_profiler/test_async.py, cpython/Lib/turtledemo/__main__.py, cpython/Lib/typing.py, cpython/Misc/NEWS.d/3.10.0a1.rst, cpython/Misc/mypy/_pyrepl/_module_completer.py, cpython/Modules/_testcapi/pyatomic.c, cpython/Modules/cjkcodecs/mappings_jp.h, cpython/Modules/clinic/_testclinic.c.h, cpython/Objects/bytesobject.c, cpython/Python/flowgraph.c, cpython/Python/thread_pthread_stubs.h, cpython/Tools/gdb/libpython.py, cpython/Tools/i18n/pygettext.py, cpython/Tools/jit/_optimizers.py, src/manifold/encoder.py, wikitext-103/wiki.valid.tokens
```

---

### 9. `search_by_structure` — ✅ PASS

**Execution time:** 2.7ms

**Assertions:**

- ✅ returns string
- ✅ contains 'structurally similar'
- ✅ shows delta values
- ✅ lists file paths
- ✅ no error marker

**Response:**

```
Files structurally similar to c0.213_s0.000_e0.928 (±0.05):
  c0.212_s0.000_e0.927  Δ=0.0010  cpython/Tools/peg_generator/pegen/__main__.py
  c0.221_s0.000_e0.932  Δ=0.0080  cpython/PCbuild/_overlapped.vcxproj.filters
  c0.224_s0.000_e0.918  Δ=0.0110  cpython/Include/internal/pycore_instruction_sequence.h
  c0.214_s0.000_e0.916  Δ=0.0120  cpython/Modules/_tracemalloc.c
  c0.225_s0.000_e0.926  Δ=0.0120  cpython/PCbuild/pyexpat.vcxproj.filters
```

---

### 10. `inject_fact` — ✅ PASS

**Execution time:** 1.6ms

**Assertions:**

- ✅ returns string
- ✅ contains '🚀'
- ✅ no error marker
- ✅ fact retrievable via get_file
- ✅ visible in search_code

**Response:**

```
🚀 Fact '__test_fact_1771798779' injected into the Dynamic Semantic Codebook.
```

---

### 11. `remove_fact` — ✅ PASS

**Execution time:** 0.3ms

**Assertions:**

- ✅ returns string
- ✅ contains '🗑️'
- ✅ erased from search_code

**Response:**

```
🗑️ Fact '__test_fact_1771798779' removed from the Dynamic Semantic Codebook.
```

---

### 12. `start_watcher_and_cli_updates` — ✅ PASS

**Execution time:** 377.1ms

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

**Execution time:** 2.7ms

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
Chaos Score (fluctuation_persistence) : 0.399
Entropy                               : 0.903
Coherence                             : 0.360
Collapse Risk                         : HIGH
Windows analyzed                      : 10

```

---

### 14. `batch_chaos_scan` — ✅ PASS

**Execution time:** 30.9ms

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

  [HIGH] 0.439 | cpython/Lib/test/mp_preload_sysargv.py
  [HIGH] 0.439 | cpython/Lib/test/test_dataclasses/dataclass_module_1.py
  [HIGH] 0.438 | cpython/Lib/test/_test_monitoring_shutdown.py
  [HIGH] 0.438 | cpython/Lib/test/test_dataclasses/dataclass_module_2.py
  [HIGH] 0.438 | cpython/Lib/test/test_codecmaps_tw.py
```

---

### 15. `predict_structural_ejection` — ✅ PASS

**Execution time:** 0.2ms

**Assertions:**

- ✅ returns string
- ✅ mentions state
- ✅ mentions file path
- ✅ includes score
- ✅ no error marker

**Response:**

```
⚠️ WARNING: mcp_server.py is in PERSISTENT_HIGH state (score: 0.399).
Predicted structural ejection in ~10 days without refactoring.
```

---

### 16. `visualize_manifold_trajectory` — ✅ PASS

**Execution time:** 845.6ms

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
  Avg Chaos Score     : 0.399
  Max Chaos Score     : 0.437
  Avg Entropy         : 0.908
  Avg Coherence       : 0.365
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
