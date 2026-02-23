# MCP Manifold Tool Guide

**Server**: `manifold` — Structural Chaos Proxy  
**Protocol**: Model Context Protocol (MCP)  
**Tools**: 21

This is the single comprehensive reference for every tool provided by the Manifold MCP server. Each tool includes its purpose, parameters, expected output, and recommended usage context.

---

## Table of Contents

1. [Setup](#setup)
2. [Indexing & Monitoring](#1-indexing--monitoring)
3. [File Discovery & Search](#2-file-discovery--search)
4. [Chaos Analysis](#3-chaos-analysis)
5. [Git Integration](#4-git-integration)
6. [Dependency & Combined Risk](#5-dependency--combined-risk)
7. [Verification & Memory](#6-verification--memory)
8. [Workflows](#workflows)
9. [Interpreting Results](#interpreting-results)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)

---

## Setup

### Prerequisites

- **Valkey/Redis** running on `localhost:6379`
- **Python 3.10+** with dependencies installed (`pip install -e .`)
- **MCP-compatible client** (Kilo Code, Claude Desktop, Cursor)

### First-Time Initialization

```
1. ingest_repo  (root_dir=".", clear_first=true, compute_chaos=true)
2. get_index_stats
3. batch_chaos_scan  (pattern="*.py", max_files=30)
```

---

## 1. Indexing & Monitoring

### `ingest_repo`

Index the entire repository into Valkey with structural signatures and chaos metrics.

| Parameter | Default | Description |
|---|---|---|
| `root_dir` | `"."` | Directory to ingest relative to workspace |
| `clear_first` | `false` | Wipe existing index before ingesting |
| `compute_chaos` | `true` | Enable chaos/complexity scoring |
| `lite` | `false` | Skip chaos on tests/docs to save memory |
| `max_bytes_per_file` | `512000` | Max file size to index (bytes) |

**When to use**: First-time setup, after major codebase changes, after branch switches.

```
ingest_repo  (root_dir=".", clear_first=true, compute_chaos=true)
```

```
✅ Ingest complete in 0.9s
  Text files : 52
  Signatures : 46
  Errors     : 0
  Avg chaos  : 0.407
```

---

### `get_index_stats`

View real-time statistics about the indexed codebase.

**Parameters**: None.

**When to use**: Verify ingestion, check index health, monitor memory usage.

```
get_index_stats
```

```
📊 Codebase Index Stats
  Indexed documents  : 52
  Structural sigs   : 46
  Chaos profiles    : 46
  Valkey memory      : 1.55M
  Avg chaos score    : 0.407
  Encoder available  : True
```

---

### `start_watcher`

Start a background filesystem watcher that auto-ingests file changes.

| Parameter | Default | Description |
|---|---|---|
| `watch_dir` | `"."` | Directory to monitor |
| `max_bytes_per_file` | `512000` | Max file size to auto-ingest |

**When to use**: During active development for real-time index updates.

```
start_watcher  (watch_dir=".")
```

```
✅ Watcher started for /path/to/repo (cap 512000 bytes)
```

---

## 2. File Discovery & Search

### `list_indexed_files`

List all indexed files matching a glob pattern.

| Parameter | Default | Description |
|---|---|---|
| `pattern` | `"*"` | Glob pattern (e.g., `"*.py"`, `"src/*"`) |
| `max_results` | `200` | Maximum files to return |

```
list_indexed_files  (pattern="*.py")
```

```
Indexed files (29):
mcp_server.py
src/manifold/sidecar.py
src/manifold/router.py
...
```

---

### `get_file`

Read the full content of an indexed file with line numbers.

| Parameter | Default | Description |
|---|---|---|
| `path` | *(required)* | File path relative to repo root |

```
get_file  (path="src/manifold/verifier.py")
```

```
📄 src/manifold/verifier.py (17 lines, 537 chars):

    1 | """Helpers to inspect verification metrics."""
    2 |
    ...
```

---

### `search_code`

Search across all indexed files by keyword or regex with surrounding context.

| Parameter | Default | Description |
|---|---|---|
| `query` | *(required)* | Search string or Python regex |
| `file_pattern` | `"*"` | Glob to limit search scope |
| `max_results` | `20` | Maximum matching files to return |
| `case_sensitive` | `false` | Case-sensitive matching |

```
search_code  (query="def compute_.*score", file_pattern="*.py")
```

```
Found 3 file(s) matching 'def compute_.*score' (scanned 29):

📄 src/manifold/git_churn.py  (1 match)
      L414:     def compute_friction_score(
  >>> L415:         self, chaos_score: float, churn_score: float
      L416:     ) -> Tuple[float, str]:
...
```

**Regex examples**:
- `"def \w+_handler"` — find all handler functions
- `"class \w+Manager"` — find all Manager classes
- `"TODO|FIXME|HACK"` — find all pending work

---

### `get_file_signature`

Get the structural fingerprint for a specific file.

| Parameter | Default | Description |
|---|---|---|
| `path` | *(required)* | File path relative to repo root |

```
get_file_signature  (path="mcp_server.py")
```

```
📐 mcp_server.py → signature: c0.213_s0.000_e0.928
```

**Signature format**: `c{coherence}_s{stability}_e{entropy}`
- **c** (Coherence): Structural consistency (0–1)
- **s** (Stability): Rate of structural change (0–1)
- **e** (Entropy): Information density (0–1)

---

### `search_by_structure`

Find files with similar structural signatures.

| Parameter | Default | Description |
|---|---|---|
| `signature` | *(required)* | Target signature (e.g., `"c0.213_s0.000_e0.928"`) |
| `tolerance` | `0.05` | Max per-component deviation |
| `max_results` | `20` | Maximum results |
| `scope` | `"*"` | Glob to limit scope |

```
search_by_structure  (signature="c0.213_s0.000_e0.928", tolerance=0.1)
```

```
Files structurally similar to c0.213_s0.000_e0.928 (±0.1):
  c0.213_s0.000_e0.928  Δ=0.0000  mcp_server.py
  c0.212_s0.000_e0.928  Δ=0.0010  scripts/rag/bulk_valkey_ingest.py
  c0.211_s0.000_e0.927  Δ=0.0020  src/manifold/router.py
  ...
```

---

### `cluster_codebase_structure`

Automatically dump the mathematical "obscure file groupings" seen on the Coherence vs Entropy Heatmap (Chart 4) into discrete, physically clustered lists of files. 

| Parameter | Default | Description |
|---|---|---|
| `pattern` | `"*"` | Glob pattern to limit clustering scope |
| `n_clusters` | `5` | Maximum number of physical structural groups to form |

```
cluster_codebase_structure  (pattern="*.py", n_clusters=3)
```

```
🧠 Structural Codebase Clusters (k=3, files=45)
Matching pattern: '*.py'

=== Cluster 1: HIGH-CHAOS (Complex/Unstable) ===
  Size: 5 files | Avg Chaos: 0.395 | Centroid (C: 0.280, E: 0.910)
    0.412 | complex_router.py (c=0.210, e=0.950)
    ...

=== Cluster 2: HIGH-COHERENCE (Linear/Simple) ===
  Size: 25 files | Avg Chaos: 0.050 | Centroid (C: 0.750, E: 0.400)
    0.010 | simple_models.py (c=0.880, e=0.350)
    ...
```

---

## 3. Chaos Analysis

### `analyze_code_chaos`

Deep-dive chaos analysis of a specific file.

| Parameter | Default | Description |
|---|---|---|
| `path` | *(required)* | File path relative to repo root |

```
analyze_code_chaos  (path="mcp_server.py")
```

```
📈 Chaos Analysis for mcp_server.py
Chaos Score (fluctuation_persistence) : 0.386
Entropy                               : 0.914
Coherence                             : 0.441
Collapse Risk                         : HIGH
Windows analyzed                      : 10
```

**Metrics**:
- **Chaos Score**: Fraction of time spent in PERSISTENT_HIGH state (0–1)
- **Entropy**: Information density (closer to 1.0 = denser)
- **Coherence**: Structural consistency (lower = more variation)
- **Collapse Risk**: LOW / HIGH based on chaos threshold

---

### `batch_chaos_scan`

Rank all files in the repository by chaos score, highest risk first.

| Parameter | Default | Description |
|---|---|---|
| `pattern` | `"*.py"` | File pattern to scan |
| `max_files` | `50` | Top N files to return |
| `scope` | `"*"` | Glob to narrow scope |

```
batch_chaos_scan  (pattern="*.py", max_files=10)
```

```
🔍 Batch Chaos Scan (Top 10 highest risk files matching *.py):

  [HIGH] 0.427 | setup.py
  [HIGH] 0.423 | memory_benchmark.py
  [HIGH] 0.422 | scripts/rag/bulk_valkey_ingest.py
  ...
```

---

### `predict_structural_ejection`

Forecast when a file will become unmaintainable based on its chaos trajectory.

| Parameter | Default | Description |
|---|---|---|
| `path` | *(required)* | File path to analyze |
| `horizon_days` | `30` | Forecast window in days |

```
predict_structural_ejection  (path="mcp_server.py", horizon_days=90)
```

```
⚠️ WARNING: mcp_server.py is in PERSISTENT_HIGH state (score: 0.386).
Predicted structural ejection in ~13 days without refactoring.
```

---

### `visualize_manifold_trajectory`

Generate a 4-panel PNG dashboard visualizing chaos dynamics across a file's byte-stream.

| Parameter | Default | Description |
|---|---|---|
| `path` | *(required)* | File path to visualize |

**Panels**:
1. **Top-left**: Structural trajectory — byte offset vs coherence, colored by chaos
2. **Top-right**: Chaos vs LLE analog — entropy vs hazard scatter
3. **Bottom-left**: Time series — hazard, entropy, coherence per window
4. **Bottom-right**: Chaos Heatmap (Branches) — physical reality of branch hazard

```
visualize_manifold_trajectory  (path="mcp_server.py")
```

```
📊 4-Panel Manifold Dashboard saved to: reports/manifold_trajectory_mcp_server.py.png

  Windows analyzed    : 21
  Avg Chaos Score     : 0.394
  Collapse Risk       : HIGH
  Symbolic States:
    PERSISTENT_HIGH   : 21
```

---

## 4. Git Integration (NEW):
    • analyze_git_churn    – Git commit frequency and churn metrics

### `analyze_git_churn`

Analyze Git commit history for a specific file: commit frequency, lines changed, and churn score.

| Parameter | Default | Description |
|---|---|---|
| `path` | *(required)* | File path relative to repo root |
| `days_back` | `365` | Number of days of history to analyze |

```
analyze_git_churn  (path="mcp_server.py")
```

```
📈 Git Churn Analysis for mcp_server.py

Total Commits        : 9
Recent Commits (90d) : 9
Commits/Month        : 9.00
Lines Added (total)  : 2,465
Lines Deleted (total): 386
Churn Score          : 0.600
```

**Churn score interpretation**: >0.5 = actively modified, <0.2 = stable.



## 5. Dependency & Combined Risk

### `analyze_blast_radius`

Trace the import dependency tree for a file and calculate how many files would be impacted by a change.

| Parameter | Default | Description |
|---|---|---|
| `path` | *(required)* | File path relative to repo root |

```
analyze_blast_radius  (path="src/manifold/sidecar.py")
```

```
💥 Blast Radius Analysis for src/manifold/sidecar.py

Blast Radius     : 17 files
Dependency Depth : 2 levels
Is Core Module   : Yes
Direct Imports   : 9
Imported By      : 8

Dependency Tree (2 levels):
📦 src/manifold/sidecar.py
├── mcp_server.py
│   ├── COMPREHENSIVE_MCP_TEST.py
│   ├── scripts/tests/test_mcp_tools.py
│   └── ...
├── src/manifold/router.py
│   ├── scripts/rag/pair_programmer_agent.py
│   └── ...
└── tests/test_sidecar.py
```

| Blast Radius | Impact | Guidance |
|---|---|---|
| ≥20 files | VERY HIGH | System-wide, requires cross-team coordination |
| 10–19 files | HIGH | Important integration point |
| 5–9 files | MODERATE | Localized impact |
| <5 files | LOW | Relatively isolated |

---

### `compute_combined_risk`

The most comprehensive risk metric: `0.4×chaos + 0.3×blast + 0.3×churn`.

| Parameter | Default | Description |
|---|---|---|
| `path` | *(required)* | File path relative to repo root |

```
compute_combined_risk  (path="src/manifold/sidecar.py")
```

```
⚠️ Combined Risk Analysis for src/manifold/sidecar.py

Components:
  Chaos Score      : 0.408 (HIGH complexity)
  Blast Radius     : 17 files
  Churn Score      : 0.133

Combined Risk Score: 0.305
Risk Level         : HIGH

Formula:
  combined = 0.4 × 0.408 + 0.3 × 0.340 + 0.3 × 0.133 = 0.305
```

| Combined Risk | Level | Action |
|---|---|---|
| ≥0.40 | CRITICAL | Immediate refactoring |
| 0.30–0.39 | HIGH | Schedule within sprint |
| 0.20–0.29 | MODERATE | Monitor and consider |
| <0.20 | LOW | Acceptable |

---

### `scan_critical_files`

Repository-wide scan for the highest combined risk files.

| Parameter | Default | Description |
|---|---|---|
| `pattern` | `"*.py"` | Glob pattern to filter files |
| `min_combined_risk` | `0.30` | Minimum risk threshold |
| `max_files` | `20` | Maximum files to return |

```
scan_critical_files  (pattern="*.py", min_combined_risk=0.20)
```

```
⚠️ Critical Files (Top 7 with risk ≥0.20):

  [    HIGH] 0.370 | mcp_server.py
             chaos=0.386, blast= 6, churn=0.600
  [    HIGH] 0.342 | src/manifold/valkey_client.py
             chaos=0.395, blast=14, churn=0.333
  [    HIGH] 0.305 | src/manifold/sidecar.py
             chaos=0.408, blast=17, churn=0.133
  ...
```

---

## 6. Verification & Memory

### `compute_signature`

Compress arbitrary text into manifold signatures for analysis or comparison.

| Parameter | Default | Description |
|---|---|---|
| `text` | *(required)* | Raw text to compress |

```
compute_signature  (text="def hello():\n    print('world')\n...")
```

```
✅ Compressed 1,950 bytes → 36 manifold bytes
  Compression ratio  : 54.17×
  Unique signatures  : 4
  Hazard threshold   : 0.4324
```

---

### `verify_snippet`

Check if a code snippet structurally matches existing codebase patterns. Useful for validating AI-generated code before committing.

| Parameter | Default | Description |
|---|---|---|
| `snippet` | *(required)* | Text to verify (must be ≥512 bytes) |
| `coverage_threshold` | `0.5` | Minimum safe coverage ratio (0–1) |
| `scope` | `"*"` | Glob to constrain validation |

```
verify_snippet  (snippet="...", coverage_threshold=0.3, scope="*.py")
```

```
Status: ❌ FAILED
  Safe coverage   : 0.00%
  Raw match ratio : 25.00%
  Gated hits      : 0/4
  Matched docs    : mcp_server.py
```

- `✅ VERIFIED` — Code matches existing patterns above threshold
- `❌ FAILED` — Code doesn't match; potentially novel or unsafe

---

### `inject_fact`

Add a persistent fact to the Dynamic Semantic Codebook. Facts survive across sessions and inform all subsequent retrievals.

| Parameter | Default | Description |
|---|---|---|
| `fact_id` | *(required)* | Unique identifier (e.g., `"api_conventions"`) |
| `fact_text` | *(required)* | The factual text to store |

```
inject_fact  (fact_id="api_conventions", fact_text="All endpoints use snake_case naming.")
```

```
🚀 Fact 'api_conventions' injected into the Dynamic Semantic Codebook.
```

**Use cases**: Framework rules, naming conventions, security requirements, architecture constraints.

---

### `remove_fact`

Remove a previously injected fact from the codebook.

| Parameter | Default | Description |
|---|---|---|
| `fact_id` | *(required)* | The fact identifier to remove |

```
remove_fact  (fact_id="api_conventions")
```

```
🗑️ Fact 'api_conventions' removed from the Dynamic Semantic Codebook.
```

---

## Workflows

### New Repository Analysis

```
1. ingest_repo        (root_dir=".", clear_first=true, compute_chaos=true)
2. get_index_stats    (verify ingestion)
3. batch_chaos_scan   (pattern="*.py", max_files=30)
4. scan_critical_files (pattern="*.py", min_combined_risk=0.25)
5. For the top file:
   - analyze_code_chaos
   - analyze_blast_radius
   - visualize_manifold_trajectory
```

### Refactoring Decision

```
1. compute_combined_risk    (path="target.py")
2. analyze_blast_radius     (path="target.py")
3. predict_structural_ejection (path="target.py", horizon_days=30)
4. Decide: refactor now vs later based on risk + timeline
```

### Sprint Planning

```
1. scan_critical_files       (min_combined_risk=0.25)
2. For each candidate:
   - analyze_blast_radius (assess impact)
   - analyze_git_churn (assess team velocity)
3. Select 1–2 files that fit sprint capacity
```

### Finding Implementation Patterns

```
1. search_code         (query="class.*Handler", file_pattern="*.py")
2. get_file            (path="found_file.py")
3. get_file_signature  (path="found_file.py")
4. search_by_structure (signature="...", tolerance=0.05)
```

### AI Code Validation

```
1. Generate code with AI
2. verify_snippet  (snippet="...", coverage_threshold=0.5)
3. If VERIFIED → review and commit
4. If FAILED → revise to match existing patterns, re-verify
```

### Continuous Monitoring

```
1. start_watcher  (watch_dir=".")
2. Work normally — watcher auto-updates on save
3. Periodically: batch_chaos_scan + get_index_stats
```

---

## Interpreting Results

### Chaos Score Ranges

| Score | Level | Action |
|---|---|---|
| 0.00–0.34 | Normal | Monitor |
| 0.35–0.39 | Elevated | Review during next refactoring pass |
| 0.40–0.44 | **HIGH** | Plan refactoring |
| 0.45+ | Critical | Urgent attention |

### Symbolic States

Files transition between three structural states:

- **LOW_FLUCTUATION**: Stable, consistent structure
- **OSCILLATION**: Alternating between simple and complex regions
- **PERSISTENT_HIGH**: Continuously in high-complexity state (the danger zone)

### The Chaos Pipeline

1. Rolling variance of byte-stream "kinetic energy"
2. Log scaling + Delta-Sigma 1-bit quantization
3. Symbolic state machine (LOW / OSCILLATION / HIGH)
4. Chaos score = fraction of PERSISTENT_HIGH windows
5. Hazard gating for retrieval safety

---

## Best Practices

### Indexing
- Use `clear_first=true` after branch switches or major merges
- Use `lite=true` for large repos (>10K files) to skip chaos on tests/docs
- Verify with `get_index_stats` after every ingest

### Searching
- Start broad with `search_code`, then narrow with `file_pattern`
- Use `list_indexed_files` to discover paths before reading them
- Combine structural search (`search_by_structure`) with text search (`search_code`)

### Analysis
- Run `batch_chaos_scan` as the first analysis step
- Use `scan_critical_files` for comprehensive prioritization (chaos + blast + churn)
- Generate visualizations for files you plan to refactor

### Working Memory
- Use descriptive `fact_id` values (e.g., `"api_v2_conventions"`)
- Keep facts concise and actionable
- Remove outdated facts promptly

---

## Troubleshooting

### Valkey not reachable

```bash
valkey-server    # or: redis-server
redis-cli ping   # should return: PONG
```

### File not found in the index

```
list_indexed_files  (pattern="*filename*")
# If missing, re-ingest:
ingest_repo  (root_dir=".", clear_first=true)
```

### Could not compute chaos

File is too short (<512 bytes) or the native encoder is unavailable. Check `get_index_stats` for `Encoder available: True`.

### Not a valid Git repository

Git churn tools require a Git repo. Churn-dependent features degrade gracefully (churn_score = 0) without Git.

### High chaos scores everywhere

This is common for algorithmic or mathematical code. Focus on files **above the repo average** and prioritize by combined risk rather than chaos alone.

---

## Additional Resources

- **[README.md](README.md)** — Project overview and installation
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** — Command cheat sheet
- **[reports/react_validation_case_study.md](reports/react_validation_case_study.md)** — React 15.0 prediction study
- **[reports/true_validation_study.md](reports/true_validation_study.md)** — Langchain ROC analysis
- **[scripts/tests/test_mcp_tools.py](scripts/tests/test_mcp_tools.py)** — Automated test suite
