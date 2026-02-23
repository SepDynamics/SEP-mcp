# MCP Manifold Tool Usage Guide

**Last Updated:** 2026-02-23  
**Repository:** `/sep/structural-manifold-compression/SEP-mcp`  
**MCP Server:** `manifold` (Symbolic Chaos Proxy)

This guide provides comprehensive instructions for using the Manifold MCP server tools for codebase analysis, structural validation, and chaos detection.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Tool Reference](#tool-reference)
3. [Workflow Patterns](#workflow-patterns)
4. [Chaos Score Interpretation](#chaos-score-interpretation)
5. [Best Practices](#best-practices)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

- **Valkey/Redis Server**: Must be running on `localhost:6379`
- **Python 3.10+** with dependencies installed (`pip install -e .`)
- **MCP-compatible IDE**: Claude Desktop, Cursor, or any MCP client

### Initial Setup Verification

```bash
# Start Valkey server
valkey-server

# Verify the MCP server can connect
python mcp_server.py
```

### First-Time Index

When starting with a new workspace or after major changes:

1. **Clear and ingest** the repository:
   ```
   mcp--manifold--ingest_repo
     root_dir: "."
     clear_first: true
     compute_chaos: true
     lite: false
   ```

2. **Verify indexing** succeeded:
   ```
   mcp--manifold--get_index_stats
   ```

3. **Scan for high-risk files**:
   ```
   mcp--manifold--batch_chaos_scan
     pattern: "*.py"
     max_files: 30
   ```

---

## Tool Reference

### 1. Repository Indexing & Management

#### `ingest_repo`
**Purpose**: Index the entire repository into Valkey with structural signatures and chaos metrics.

**Parameters**:
- `root_dir` (default: `"."`): Directory to ingest (relative to workspace)
- `clear_first` (default: `false`): Clear existing index before ingesting
- `compute_chaos` (default: `true`): Enable chaos/complexity scoring
- `lite` (default: `false`): Skip chaos on tests/docs to save memory
- `max_bytes_per_file` (default: `512000`): Max file size to index (512 KB)

**When to use**:
- First-time setup
- After major codebase changes
- When index statistics show stale data

**Example**:
```
mcp--manifold--ingest_repo
  root_dir: "."
  clear_first: true
  compute_chaos: true
  lite: false
```

**Expected output**:
```
✅ Ingest complete in 1.5s
  Text files : 47
  Binary files: 0
  Total bytes : 768,182
  Signatures : 41
  Skipped    : 4
  Errors     : 0
  Avg chaos  : 0.408
  High-risk  : 41
```

---

#### `get_index_stats`
**Purpose**: View real-time statistics about the indexed codebase.

**Parameters**: None

**When to use**:
- Verify successful ingestion
- Check index health
- Monitor memory usage

**Example**:
```
mcp--manifold--get_index_stats
```

**Expected output**:
```
📊 Codebase Index Stats
  Total Valkey keys  : 49
  Indexed documents  : 47
  File list entries  : 47
  Structural sigs   : 41
  Chaos profiles    : 41
  Valkey memory      : 1.51M
  Last ingest        : 2026-02-23T00:53:09Z
  Last ingest root   : /sep/structural-manifold-compression/SEP-mcp
  Last text files    : 47
  Last binary files  : 0
  Last total bytes   : 768,182
  Last elapsed       : 1.53s
  Avg chaos score    : 0.408
  High-risk files    : 41
  Encoder available  : True
```

**What to check**:
- `Last ingest root` matches your workspace directory
- `Indexed documents` is non-zero
- `Encoder available` is `True`

---

#### `start_watcher`
**Purpose**: Start a filesystem watcher that auto-ingests file changes.

**Parameters**:
- `watch_dir` (default: `"."`): Directory to monitor
- `max_bytes_per_file` (default: `512000`): Max file size to auto-ingest

**When to use**:
- During active development
- When you want real-time index updates
- For continuous monitoring scenarios

**Example**:
```
mcp--manifold--start_watcher
  watch_dir: "."
  max_bytes_per_file: 512000
```

**Expected output**:
```
✅ Watcher started for /sep/structural-manifold-compression/SEP-mcp (cap 512000 bytes)
```

**Note**: The watcher runs in the background and automatically updates the index on file save/create/delete events.

---

### 2. File Discovery & Retrieval

#### `list_indexed_files`
**Purpose**: List all indexed files matching a glob pattern.

**Parameters**:
- `pattern` (default: `"*"`): Glob pattern to filter files (e.g., `"*.py"`, `"src/*"`)
- `max_results` (default: `200`): Maximum files to return

**When to use**:
- Discover what files are indexed
- Find files by pattern before reading them
- Explore directory structure

**Example**:
```
mcp--manifold--list_indexed_files
  pattern: "*.py"
  max_results: 50
```

**Expected output**:
```
Indexed files (26):
setup.py
memory_benchmark.py
scripts/rag/bulk_valkey_ingest.py
mcp_server.py
...
```

---

#### `get_file`
**Purpose**: Read the full content of an indexed file with line numbers.

**Parameters**:
- `path` (required): File path relative to repo root (e.g., `"src/manifold/sidecar.py"`)

**When to use**:
- After identifying interesting files via search or chaos scan
- To read complete file context
- When you need to see the actual code

**Example**:
```
mcp--manifold--get_file
  path: "src/manifold/sidecar.py"
```

**Expected output**:
```
📄 src/manifold/sidecar.py (682 lines, 24039 chars):

    1 | """Structural manifold sidecar for compression + verification..."""
    2 | 
    3 | from __future__ import annotations
    4 | 
    5 | import json
    ...
```

**Troubleshooting**:
- If file not found, use `list_indexed_files` to discover the exact path
- The tool suggests similar filenames if the exact path doesn't exist

---

### 3. Code Search

#### `search_code`
**Purpose**: Search for code patterns across all indexed files using keyword or regex.

**Parameters**:
- `query` (required): Search string or Python regex pattern
- `file_pattern` (default: `"*"`): Glob to limit search scope (e.g., `"*.py"`)
- `max_results` (default: `20`): Maximum matching files to return
- `case_sensitive` (default: `false`): Whether search is case-sensitive

**When to use**:
- Find specific function/class definitions
- Locate where a variable or import is used
- Search for TODO comments or specific patterns

**Example**:
```
mcp--manifold--search_code
  query: "class PortfolioManager"
  file_pattern: "*.py"
  max_results: 10
```

**Example output**:
```
Found 3 file(s) matching 'chaos_score' (scanned 27):

📄 mcp_server.py  (5 matches)
      L258: 
      L259:     return {
  >>> L260:         "chaos_score": avg_fp,
      L261:         "entropy": avg_entropy,
      L262:         "coherence": avg_coherence,
...
```

**Regex patterns**:
- `"def \w+_handler"` - Find all handlers
- `"@mcp\.tool\(\)"` - Find MCP tool definitions
- `"class \w+Manager"` - Find all Manager classes
- `"TODO|FIXME"` - Find all pending work

---

#### `search_by_structure`
**Purpose**: Find files with similar structural signatures.

**Parameters**:
- `signature` (required): Target signature (e.g., `"c0.418_s0.760_e0.957"`)
- `tolerance` (default: `0.05`): Max per-component deviation
- `max_results` (default: `20`): Maximum similar files to return
- `scope` (default: `"*"`): Glob pattern to limit search

**When to use**:
- Find structurally similar files (e.g., all config files)
- Discover files with similar complexity profiles
- Group files by architectural pattern

**Example**:
```
mcp--manifold--search_by_structure
  signature: "c0.418_s0.760_e0.957"
  tolerance: 0.05
  max_results: 10
```

**Expected output**:
```
Files structurally similar to c0.418_s0.760_e0.957 (±0.05):
  c0.420_s0.755_e0.960  Δ=0.0050  src/manifold/sidecar.py
  c0.415_s0.765_e0.955  Δ=0.0070  scripts/rag/bulk_valkey_ingest.py
...
```

---

### 4. Structural Analysis

#### `get_file_signature`
**Purpose**: Get the structural signature for a specific file.

**Parameters**:
- `path` (required): File path relative to repo root

**When to use**:
- Quick structural fingerprint of a file
- Before using `search_by_structure`
- To understand file complexity at a glance

**Example**:
```
mcp--manifold--get_file_signature
  path: "mcp_server.py"
```

**Expected output**:
```
📐 mcp_server.py → signature: c0.213_s0.000_e0.928
```

**Signature format**: `c{coherence}_s{stability}_e{entropy}`
- **Coherence** (`c`): Structural consistency (0.0-1.0)
- **Stability** (`s`): Rate of change in structure (0.0-1.0)
- **Entropy** (`e`): Information density/complexity (0.0-1.0)

---

#### `compute_signature`
**Purpose**: Compress arbitrary text into manifold signatures.

**Parameters**:
- `text` (required): The raw text to compress

**When to use**:
- Analyze text snippets or AI-generated code
- Test structural similarity before committing
- Research/experimentation with compression ratios

**Example**:
```
mcp--manifold--compute_signature
  text: "def hello():\n    print('world')"
```

**Expected output**:
```
✅ Compressed 887 bytes → 9 manifold bytes
  Compression ratio  : 98.56×
  Unique signatures  : 1
  Total windows      : 1
  Hazard threshold   : 0.3932
```

---

### 5. Chaos Analysis & Risk Detection

#### `analyze_code_chaos`
**Purpose**: Deep-dive chaos analysis of a specific file.

**Parameters**:
- `path` (required): File path relative to repo root

**When to use**:
- Detailed analysis of a suspected complex file
- Before refactoring to understand structural issues
- To quantify maintainability risk

**Example**:
```
mcp--manifold--analyze_code_chaos
  path: "mcp_server.py"
```

**Expected output**:
```
📈 Chaos Analysis for mcp_server.py
Chaos Score (fluctuation_persistence) : 0.399
Entropy                               : 0.903
Coherence                             : 0.360
Collapse Risk                         : HIGH
Windows analyzed                      : 10
```

**Current Repo Insights**:
- **Highest chaos**: [`setup.py`](setup.py:1) (0.427)
- **Average chaos**: 0.408 across 41 files
- **High-risk files**: 41/47 files are flagged as HIGH

---

#### `batch_chaos_scan`
**Purpose**: Scan the entire repository and rank files by chaos score.

**Parameters**:
- `pattern` (default: `"*.py"`): File pattern to scan (e.g., `"*.cpp"`, `"src/*"`)
- `max_files` (default: `50`): Top N highest-risk files to return
- `scope` (default: `"*"`): Glob to narrow scope (e.g., `"core/*"`)

**When to use**:
- **First step** after ingestion to identify complexity hotspots
- Regular health checks of codebase
- Prioritize refactoring efforts

**Example**:
```
mcp--manifold--batch_chaos_scan
  pattern: "*.py"
  scope: "*"
  max_files: 30
```

**Expected output**:
```
🔍 Batch Chaos Scan (Top 26 highest risk files matching *.py):

  [HIGH] 0.427 | setup.py
  [HIGH] 0.423 | memory_benchmark.py
  [HIGH] 0.422 | scripts/rag/bulk_valkey_ingest.py
  [HIGH] 0.419 | scripts/rag/prepare_corpus.py
  [HIGH] 0.419 | tests/test_sidecar.py
  [HIGH] 0.414 | scripts/rag/verify_snippet.py
  [HIGH] 0.408 | scripts/rag/verify_llm_saturation.py
  [HIGH] 0.408 | src/manifold/sidecar.py
  [HIGH] 0.407 | scripts/rag/active_watcher.py
  ...
```

**Current Repo Findings**:
The chaos scan reveals this codebase has uniformly high complexity across files, with the top files including:
- [`setup.py`](setup.py:1) (0.427) - Build configuration
- [`memory_benchmark.py`](memory_benchmark.py:1) (0.423) - Performance testing
- [`scripts/rag/bulk_valkey_ingest.py`](scripts/rag/bulk_valkey_ingest.py:1) (0.422) - Bulk ingestion logic

---

#### `predict_structural_ejection`
**Purpose**: Forecast when a file will become unmaintainable.

**Parameters**:
- `path` (required): File path to analyze
- `horizon_days` (default: `30`): Forecast window in days

**When to use**:
- Planning refactoring timelines
- Risk assessment for critical files
- Understanding technical debt accumulation

**Example**:
```
mcp--manifold--predict_structural_ejection
  path: "mcp_server.py"
  horizon_days: 30
```

**Expected output**:
```
⚠️ WARNING: mcp_server.py is in PERSISTENT_HIGH state (score: 0.399).
Predicted structural ejection in ~10 days without refactoring.
```

**Interpretation**:
- **PERSISTENT_HIGH**: File is continuously in high-chaos state
- **Ejection forecast**: Time until the file becomes unmaintainable
- **Action**: Consider refactoring before the predicted date

---

#### `visualize_manifold_trajectory`
**Purpose**: Generate a 4-panel dashboard visualizing file chaos dynamics.

**Parameters**:
- `path` (required): File path to visualize

**When to use**:
- Visual inspection of chaos patterns
- Documentation/reporting
- Understanding chaos evolution over file structure

**Example**:
```
mcp--manifold--visualize_manifold_trajectory
  path: "mcp_server.py"
```

**Expected output**:
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

**Dashboard panels**:
1. **Top-left**: Physical trajectory - byte position vs coherence
2. **Top-right**: Chaos vs LLE analog - entropy vs hazard scatter
3. **Bottom-left**: Time series - hazard/entropy/coherence evolution
4. **Bottom-right**: Symbolic state distribution bar chart

**Current examples**:
- [`reports/manifold_trajectory_mcp_server.py.png`](reports/manifold_trajectory_mcp_server.py.png)
- [`reports/manifold_trajectory_src_manifold_router.py.png`](reports/manifold_trajectory_src_manifold_router.py.png)

---

### 6. Working Memory (Zero-Shot Learning)

#### `inject_fact`
**Purpose**: Add a fact/rule permanently to the semantic codebook.

**Parameters**:
- `fact_id` (required): Unique identifier (e.g., `"project_architecture_v2"`)
- `fact_text` (required): The factual text to remember

**When to use**:
- Store project conventions permanently
- Add architectural guidelines for the AI
- Create a persistent knowledge base

**Example**:
```
mcp--manifold--inject_fact
  fact_id: "api_rate_limits"
  fact_text: "All API endpoints must implement rate limiting at 100 req/min using the @rate_limit decorator."
```

**Expected output**:
```
🚀 Fact 'api_rate_limits' injected into the Dynamic Semantic Codebook.
```

**Use cases**:
- Framework-specific patterns
- API design rules
- Security requirements
- Naming conventions

---

#### `remove_fact`
**Purpose**: Remove a previously injected fact.

**Parameters**:
- `fact_id` (required): The fact identifier to remove

**When to use**:
- Clean up outdated guidelines
- Remove temporary rules
- Maintain codebook hygiene

**Example**:
```
mcp--manifold--remove_fact
  fact_id: "api_rate_limits"
```

**Expected output**:
```
🗑️ Fact 'api_rate_limits' removed from the Dynamic Semantic Codebook.
```

---

### 7. Code Verification

#### `verify_snippet`
**Purpose**: Verify AI-generated code against the indexed codebase.

**Parameters**:
- `snippet` (required): Text to verify (must be ≥512 bytes)
- `coverage_threshold` (default: `0.5`): Minimum safe coverage ratio (0.0-1.0)
- `scope` (default: `"*"`): Glob to constrain validation

**When to use**:
- Validate AI-generated code before committing
- Check if code matches existing patterns
- Detect hallucinated or unsafe code

**Example**:
```
mcp--manifold--verify_snippet
  snippet: "def process_data(items):\n    return [x*2 for x in items]"
  coverage_threshold: 0.5
  scope: "*"
```

**Expected output**:
```
Status: ✅ VERIFIED
  Safe coverage   : 85.00%
  Raw match ratio : 90.00%
  Gated hits      : 17/20
  Matched docs    : src/manifold/sidecar.py, mcp_server.py, ...
```

**Status meanings**:
- `✅ VERIFIED`: Code matches existing patterns above threshold
- `❌ FAILED`: Code doesn't match codebase or is potentially unsafe

---

## Workflow Patterns

### Pattern 1: Initial Repository Analysis

**Goal**: Get a complete picture of a new codebase.

```
1. mcp--manifold--ingest_repo (root_dir=".", clear_first=true, compute_chaos=true)
2. mcp--manifold--get_index_stats (verify ingestion)
3. mcp--manifold--batch_chaos_scan (pattern="*.py", max_files=30)
4. For each high-risk file:
   a. mcp--manifold--analyze_code_chaos (path="{file}")
   b. mcp--manifold--get_file (path="{file}")
   c. mcp--manifold--visualize_manifold_trajectory (path="{file}")
```

**Current repository results**:
- **47 files** indexed (768 KB)
- **Average chaos**: 0.408 (HIGH)
- **Top risks**: [`setup.py`](setup.py:1), [`memory_benchmark.py`](memory_benchmark.py:1), [`bulk_valkey_ingest.py`](scripts/rag/bulk_valkey_ingest.py:1)

---

### Pattern 2: Finding Implementation Patterns

**Goal**: Locate how a specific pattern is implemented.

```
1. mcp--manifold--search_code (query="class.*Manager", file_pattern="*.py")
2. mcp--manifold--get_file (path="{found_file}")
3. mcp--manifold--get_file_signature (path="{found_file}")
4. mcp--manifold--search_by_structure (signature="{sig}", tolerance=0.05)
```

---

### Pattern 3: Refactoring Decision Support

**Goal**: Decide if/when to refactor a complex file.

```
1. mcp--manifold--analyze_code_chaos (path="{target_file}")
2. mcp--manifold--predict_structural_ejection (path="{target_file}", horizon_days=30)
3. mcp--manifold--visualize_manifold_trajectory (path="{target_file}")
4. Review dashboard and decide based on:
   - Chaos score (>0.40 = urgent)
   - Ejection timeline (<14 days = critical)
   - Symbolic states (PERSISTENT_HIGH = bad)
```

---

### Pattern 4: AI Code Validation

**Goal**: Verify AI-generated code before committing.

```
1. Generate code with AI
2. mcp--manifold--verify_snippet (snippet="{generated_code}", coverage_threshold=0.5)
3. If VERIFIED:
   - mcp--manifold--search_by_structure (find similar implementations)
   - Review and commit
4. If FAILED:
   - Revise code to match existing patterns
   - Re-verify
```

---

### Pattern 5: Continuous Monitoring

**Goal**: Keep index up-to-date during development.

```
1. mcp--manifold--start_watcher (watch_dir=".", max_bytes_per_file=512000)
2. Work normally (watcher auto-updates index on saves)
3. Periodically:
   - mcp--manifold--get_index_stats (check health)
   - mcp--manifold--batch_chaos_scan (spot-check for new risks)
```

---

## Chaos Score Interpretation

### Score Ranges

| Range | Level | Description | Action |
|-------|-------|-------------|--------|
| 0.00-0.34 | **NORMAL** | Well-structured, maintainable code | Monitor |
| 0.35-0.39 | **ELEVATED** | Moderate complexity, common in algorithms | Review |
| 0.40-0.44 | **HIGH** | High complexity, refactoring candidate | Plan refactoring |
| 0.45+ | **CRITICAL** | Very high complexity, urgent attention | Immediate action |

### Current Repository Profile

Based on the chaos scan of this repository:

- **Average chaos score**: 0.408 (HIGH)
- **Distribution**: 41 of 47 files (87%) are HIGH risk
- **Highest**: 0.427 ([`setup.py`](setup.py:1))
- **Lowest**: 0.389 ([`verify_latency.py`](scripts/rag/verify_latency.py:1), [`verifier.py`](src/manifold/verifier.py:1))

**Interpretation**: This codebase operates at a consistently high complexity level, likely due to:
1. Advanced algorithms (manifold compression, chaos computation)
2. Heavy use of mathematical operations
3. Dense integration logic across modules

**Recommendations**:
- Focus refactoring on files >0.42 chaos score
- Break down monolithic files like [`mcp_server.py`](mcp_server.py:1) (1382 lines)
- Add inline documentation to reduce cognitive load
- Consider extracting pure functions from complex classes

### Chaos Metrics Explained

1. **Chaos Score** (fluctuation_persistence):
   - Fraction of time the file spends in PERSISTENT_HIGH state
   - Based on byte-stream kinetic energy variance
   - **0.399**: File is in high-chaos state 39.9% of the time

2. **Entropy**:
   - Information density/complexity measure
   - **0.903**: Very high information density (close to maximum)

3. **Coherence**:
   - Structural consistency across the file
   - **0.360**: Lower coherence = more structural variation

4. **Collapse Risk**:
   - Overall maintainability assessment
   - **HIGH**: File is at risk of becoming unmaintainable

### Symbolic States

Files transition between three states:

1. **LOW_FLUCTUATION**: Stable, consistent structure
2. **OSCILLATION**: Alternating between simple and complex
3. **PERSISTENT_HIGH**: Continuously in high-complexity state

**Current repo state**: Most files show `PERSISTENT_HIGH` dominance, indicating sustained complexity throughout.

---

## Best Practices

### 1. Index Management

**DO**:
- ✅ Use `clear_first=true` when switching branches or after major merges
- ✅ Run `get_index_stats` regularly to verify index health
- ✅ Use `lite=true` for very large repos to save memory on test files
- ✅ Set `max_bytes_per_file` appropriately (default 512 KB is usually good)

**DON'T**:
- ❌ Don't ingest without checking Valkey is running first
- ❌ Don't forget to re-ingest after pulling major changes
- ❌ Don't ignore "stale data" warnings from index stats

---

### 2. Search Strategy

**DO**:
- ✅ Start broad with `search_code`, then narrow with `file_pattern`
- ✅ Use `list_indexed_files` first to understand what's available
- ✅ Combine structural (`search_by_structure`) and text (`search_code`) searches
- ✅ Use regex for complex patterns (e.g., `"def \w+_handler"`)

**DON'T**:
- ❌ Don't search for non-indexed files (check with `list_indexed_files` first)
- ❌ Don't forget to escape regex special characters
- ❌ Don't use overly broad patterns that match everything

---

### 3. Chaos Analysis

**DO**:
- ✅ Always run `batch_chaos_scan` as your first analysis step
- ✅ Prioritize files with chaos >0.40 for refactoring
- ✅ Use `visualize_manifold_trajectory` for deep investigation
- ✅ Compare chaos before/after refactoring to measure improvement
- ✅ Track `predict_structural_ejection` timelines for critical files

**DON'T**:
- ❌ Don't panic at high chaos scores - they indicate density, not necessarily bad code
- ❌ Don't ignore PERSISTENT_HIGH files - they need attention
- ❌ Don't refactor without understanding the trajectory first

---

### 4. File Path Handling

**DO**:
- ✅ Use relative paths from repo root (e.g., `"src/manifold/sidecar.py"`)
- ✅ Check path suggestions if a file isn't found
- ✅ Use `list_indexed_files` with glob patterns to discover paths

**DON'T**:
- ❌ Don't use absolute paths
- ❌ Don't assume paths - always verify with `list_indexed_files`
- ❌ Don't forget that indexed paths may include prefixes like `../../`

---

### 5. Working Memory

**DO**:
- ✅ Use descriptive `fact_id` values (e.g., `"api_v2_conventions"`)
- ✅ Keep facts concise and actionable
- ✅ Remove outdated facts promptly with `remove_fact`
- ✅ Document injected facts in your project README

**DON'T**:
- ❌ Don't inject sensitive information (facts are stored in Valkey)
- ❌ Don't create duplicate facts with different IDs
- ❌ Don't let the codebook grow unbounded

---

### 6. Performance Optimization

**When to use `lite` mode**:
- Large repos (>10,000 files)
- When focusing only on core source files
- Memory-constrained environments

**When to skip watcher**:
- Read-only analysis
- Batch processing scenarios
- When using external file monitors

**Batching**:
- The MCP server automatically batches Valkey operations
- Use `max_files` and `max_results` to limit output size
- Process large repos in stages (e.g., by directory scope)

---

## Troubleshooting

### Common Issues

#### 1. "Valkey not reachable"

**Cause**: Valkey/Redis server is not running or not accessible.

**Solution**:
```bash
# Start Valkey server
valkey-server

# Or use Redis
redis-server

# Check if running
redis-cli ping
# Should return: PONG
```

---

#### 2. "File not found in the index"

**Cause**: File hasn't been indexed or path is incorrect.

**Solution**:
```
# List all indexed files
mcp--manifold--list_indexed_files
  pattern: "*filename*"

# If not found, re-ingest
mcp--manifold--ingest_repo
  root_dir: "."
  clear_first: true
```

---

#### 3. High chaos scores everywhere

**Cause**: Could be legitimate complexity or analysis calibration.

**Context from current repo**:
- This codebase averages 0.408 chaos (HIGH)
- Complex algorithms naturally score higher
- Not necessarily "bad" code

**Interpretation**:
- **>0.42**: Focus here first (e.g., [`setup.py`](setup.py:1) at 0.427)
- **0.40-0.42**: Monitor for growth
- **<0.40**: Acceptable for complex algorithms

---

#### 4. "Could not compute chaos"

**Cause**: File too short (<512 bytes) or native encoder unavailable.

**Solution**:
```bash
# Verify native encoder is built
pip install -e .

# Check encoder availability
mcp--manifold--get_index_stats
# Look for: "Encoder available : True"
```

---

#### 5. Slow ingestion

**Possible causes**:
- Very large repository
- Slow disk I/O
- Chaos computation on every file

**Solutions**:
```
# Use lite mode to skip tests/docs
mcp--manifold--ingest_repo
  root_dir: "."
  lite: true

# Reduce max file size
mcp--manifold--ingest_repo
  max_bytes_per_file: 256000

# Narrow scope
mcp--manifold--ingest_repo
  root_dir: "src"  # Just src directory
```

---

#### 6. Memory usage too high

**Current repo**: 1.51 MB for 47 files (very efficient)

**For larger repos**:
```
# Use lite mode
mcp--manifold--ingest_repo
  lite: true

# This skips chaos on:
  - test files
  - documentation
  - binary files

# Can reduce memory by >99% (e.g., cpython: 3.4 GB → 28 MB)
```

---

## Advanced Topics

### Understanding Structural Signatures

Signatures encode files into three dimensions:

```
c{coherence}_s{stability}_e{entropy}
```

**Example**: `c0.418_s0.760_e0.957`
- `c0.418`: 41.8% coherence (moderate structural consistency)
- `s0.760`: 76.0% stability (fairly stable structure)
- `e0.957`: 95.7% entropy (very high information density)

**Use cases**:
1. **Clone detection**: Find structurally identical files
2. **Refactoring impact**: Compare signatures before/after
3. **Architectural grouping**: Cluster files by structural similarity

---

### The Three-Body Chaos Proxy

This MCP server implements the exact chaos detection algorithm from the 3-body gravitational ejection predictor (MNRAS preprint, Feb 2026).

**Pipeline**:
1. **Rolling variance** of byte-stream "kinetic energy"
2. **Log scaling** + Delta-Sigma 1-bit quantization
3. **Symbolic state machine** (LOW/OSC/HIGH)
4. **Chaos score** = PERSISTENT_HIGH fraction
5. **Hazard gating** for retrieval safety

**Why it works for code**:
- Source code is a continuous byte-stream
- Structural complexity manifests as "kinetic variance"
- Unmaintainable code shows "gravitational instability"

---

### Validation Studies

The chaos detection has been empirically validated:

1. **React 15.0 Case Study**: 
   - Predicted exact files deleted in React Fiber rewrite
   - No semantic understanding required
   - [Read the study](reports/react_validation_case_study.md)

2. **Langchain ROC Analysis**:
   - Chaos score ≥0.396 optimally predicts ejection
   - ROC AUC: 0.575
   - ~91% of semantic AST parser power at O(1) speed
   - [Read the study](reports/true_validation_study.md)

3. **Memory Optimization**:
   - zstd compression reduces index size >99%
   - cpython: 3.4 GB → 28 MB
   - Zero loss in retrieval accuracy

---

## Additional Resources

- **Main README**: [`README.md`](README.md)
- **RAG Scripts Guide**: [`scripts/rag/README.md`](scripts/rag/README.md)
- **Test Suite**: [`scripts/tests/test_mcp_tools.py`](scripts/tests/test_mcp_tools.py)
- **Validation Report**: [`reports/mcp_tool_report.md`](reports/mcp_tool_report.md)
- **React Case Study**: [`reports/react_validation_case_study.md`](reports/react_validation_case_study.md)
- **True Validation**: [`reports/true_validation_study.md`](reports/true_validation_study.md)

---

## Revision History

| Date | Changes |
|------|---------|
| 2026-02-23 | Initial comprehensive guide created from repository analysis |

---

## New Features: Git Integration & Blast Radius Analysis

**Added**: 2026-02-23 (6 new tools)

### Git Churn Analysis

Track how frequently files are modified to identify high-maintenance areas.

#### `analyze_git_churn`
**Purpose**: Analyze Git commit history for a specific file.

**Parameters**:
- `path` (required): File path relative to repo root
- `days_back` (default: `365`): Number of days to analyze

**When to use**:
- Identify frequently modified files
- Understand file stability
- Assess maintenance burden

**Example**:
```
mcp--manifold--analyze_git_churn
  path: "mcp_server.py"
  days_back: 365
```

**Expected output**:
```
📈 Git Churn Analysis for mcp_server.py

Total Commits        : 47
Recent Commits (90d) : 12
Commits/Month        : 3.42
Unique Authors       : 2
Lines Added (total)  : 2,451
Lines Deleted (total): 1,103
File Age (days)      : 413
Days Since Modified  : 2
Churn Score          : 0.643

Interpretation:
  - Churn score combines recent activity with commit frequency
  - Higher churn (>0.5) = actively modified file
  - Lower churn (<0.2) = stable file
```

---

#### `compute_friction_score`
**Purpose**: Compute friction score = chaos × churn.

High friction identifies files that are **both complex AND frequently modified** - the ultimate maintenance burden.

**Parameters**:
- `path` (required): File path relative to repo root

**When to use**:
- Prioritize refactoring efforts
- Identify developer pain points
- Assess technical debt hotspots

**Example**:
```
mcp--manifold--compute_friction_score
  path: "mcp_server.py"
```

**Expected output**:
```
🔥 Friction Analysis for mcp_server.py

Chaos Score  : 0.399
Churn Score  : 0.643
Friction     : 0.257
Risk Level   : HIGH

Components:
  • Chaos  : Structural complexity (HIGH risk)
  • Churn  : 12 commits in last 90 days
  • Friction: chaos × churn = 0.257

Interpretation:
  [CRITICAL] ≥0.30 : Urgent attention needed
  [HIGH]     ≥0.20 : Should refactor soon
  [MODERATE] ≥0.10 : Monitor closely
  [LOW]      <0.10 : Acceptable risk

Recommendation:
  This file combines moderate-to-high complexity with active churn.
  Priority: HIGH. Schedule refactoring in next sprint.
```

**Friction Score Interpretation**:
- **≥0.30**: CRITICAL - Both complex AND highly active
- **0.20-0.29**: HIGH - Significant maintenance burden
- **0.10-0.19**: MODERATE - Monitor for trends
- **<0.10**: LOW - Either simple, stable, or both

---

#### `scan_high_friction_files`
**Purpose**: Scan entire repository for high-friction files.

**Parameters**:
- `pattern` (default: `"*.py"`): Glob pattern to filter files
- `min_friction` (default: `0.20`): Minimum friction threshold
- `max_files` (default: `30`): Maximum files to return

**When to use**:
- Sprint planning (identify refactoring candidates)
- Technical debt assessment
- Developer onboarding (show pain points)

**Example**:
```
mcp--manifold--scan_high_friction_files
  pattern: "*.py"
  min_friction: 0.20
  max_files: 30
```

**Expected output**:
```
🔥 High-Friction Files (Top 5 with friction ≥0.20):

  [    HIGH] 0.271 | scripts/rag/bulk_valkey_ingest.py  (chaos=0.422, churn=0.643)
  [    HIGH] 0.257 | mcp_server.py  (chaos=0.399, churn=0.643)
  [    HIGH] 0.234 | src/manifold/sidecar.py  (chaos=0.408, churn=0.574)
  [    HIGH] 0.220 | scripts/rag/active_watcher.py  (chaos=0.407, churn=0.541)
  [    HIGH] 0.209 | scripts/tests/test_mcp_tools.py  (chaos=0.402, churn=0.520)
```

---

### Blast Radius Analysis

Use AST parsing to trace dependencies and understand impact of changes.

#### `analyze_blast_radius`
**Purpose**: Calculate how many files would be impacted if a file changes.

**Parameters**:
- `path` (required): File path relative to repo root

**When to use**:
- Before refactoring (assess impact)
- Identify core modules
- Plan breaking changes
- Architecture review

**Example**:
```
mcp--manifold--analyze_blast_radius
  path: "src/manifold/sidecar.py"
```

**Expected output**:
```
💥 Blast Radius Analysis for src/manifold/sidecar.py

Blast Radius     : 8 files
Dependency Depth : 2 levels
Is Core Module   : Yes
Direct Imports   : 5
Imported By      : 8

Impact Assessment:
  MODERATE IMPACT (8 files). Localized but not isolated.
  Changes will affect several files.
  Standard testing procedures apply.

Dependency Tree (2 levels):
📦 src/manifold/sidecar.py
├── mcp_server.py
│   └── (end of tree)
├── scripts/rag/build_manifold_index.py
├── scripts/rag/bulk_valkey_ingest.py
├── scripts/rag/verify_snippet.py
└── scripts/tests/test_mcp_tools.py

Imports:
  ast, dataclasses, json, pathlib, subprocess, typing

Imported By:
  mcp_server.py, scripts/rag/build_manifold_index.py, scripts/rag/bulk_valkey_ingest.py, ...
```

**Blast Radius Interpretation**:
- **≥20 files**: VERY HIGH - Core module, system-wide impact
- **10-19 files**: HIGH - Important integration point
- **5-9 files**: MODERATE - Localized impact
- **<5 files**: LOW - Relatively isolated

---

#### `compute_combined_risk`
**Purpose**: Compute ultimate risk score = chaos × blast_radius × churn.

This is the **most comprehensive risk metric**, combining:
1. **Chaos**: Structural complexity
2. **Blast Radius**: Impact scope
3. **Churn**: Modification frequency

**Parameters**:
- `path` (required): File path relative to repo root

**When to use**:
- Ultimate refactoring prioritization
- Critical path analysis
- Risk assessment for releases
- Technical debt quantification

**Example**:
```
mcp--manifold--compute_combined_risk
  path: "mcp_server.py"
```

**Expected output**:
```
⚠️ Combined Risk Analysis for mcp_server.py

Components:
  Chaos Score      : 0.399 (HIGH complexity)
  Blast Radius     : 15 files
  Churn Score      : 0.643

Combined Risk Score: 0.399
Risk Level         : CRITICAL

Formula:
  combined = 0.4 × chaos + 0.3 × blast + 0.3 × churn
  combined = 0.4 × 0.399 + 0.3 × 0.300 + 0.3 × 0.643
  combined = 0.399

Risk Levels:
  [CRITICAL] ≥0.40 : Immediate refactoring required
  [HIGH]     ≥0.30 : Schedule refactoring within sprint
  [MODERATE] ≥0.20 : Monitor and consider refactoring
  [LOW]      <0.20 : Acceptable risk

Recommendation:
  HIGH RISK. This file needs attention soon.
  • Complexity: 0.40, Blast radius: 15, Churn: 0.64
  Action: Schedule refactoring in current/next sprint.
  Consider: Add comprehensive tests before refactoring.
```

**Combined Risk Formula**:
```
combined_risk = 0.4 × chaos + 0.3 × (blast_radius/50) + 0.3 × churn
```

**Why this weighting?**
- **40% Chaos**: Complexity is the primary concern
- **30% Blast**: Impact scope matters for coordination
- **30% Churn**: Active modification indicates pain points

---

#### `scan_critical_files`
**Purpose**: Scan entire repository for critical files using combined risk.

**Parameters**:
- `pattern` (default: `"*.py"`): Glob pattern to filter files
- `min_combined_risk` (default: `0.30`): Minimum risk threshold
- `max_files` (default: `20`): Maximum files to return

**When to use**:
- Strategic refactoring planning
- Quarterly technical debt review
- Risk assessment before major releases
- Team capacity planning

**Example**:
```
mcp--manifold--scan_critical_files
  pattern: "*.py"
  min_combined_risk: 0.30
  max_files: 20
```

**Expected output**:
```
⚠️ Critical Files (Top 3 with risk ≥0.30):

  [CRITICAL] 0.423 | mcp_server.py
             chaos=0.399, blast=15, churn=0.643
  [    HIGH] 0.387 | src/manifold/sidecar.py
             chaos=0.408, blast= 8, churn=0.574
  [    HIGH] 0.352 | scripts/rag/bulk_valkey_ingest.py
             chaos=0.422, blast= 3, churn=0.643
```

---

### Workflow: Comprehensive Risk Assessment

**Goal**: Identify the single most critical file to refactor.

```
1. mcp--manifold--ingest_repo (full indexing)
2. mcp--manifold--scan_critical_files (pattern="*.py", min_combined_risk=0.30)
3. For top file:
   a. mcp--manifold--compute_combined_risk (path="{file}")
   b. mcp--manifold--analyze_blast_radius (path="{file}")
   c. mcp--manifold--compute_friction_score (path="{file}")
   d. mcp--manifold--visualize_manifold_trajectory (path="{file}")
4. Decision: Refactor now vs later
```

---

### Workflow: Sprint Planning

**Goal**: Identify refactoring candidates for the next sprint.

```
1. mcp--manifold--scan_high_friction_files (min_friction=0.20, max_files=30)
2. For each high-friction file:
   - Check blast radius (is it a core module?)
   - Check combined risk (is it critical?)
   - Estimate refactoring effort (LOC, complexity)
3. Select 1-2 files that fit sprint capacity
4. Create refactoring tasks with context
```

---

### Workflow: Pre-Refactoring Assessment

**Goal**: Understand impact before refactoring a specific file.

```
1. mcp--manifold--compute_combined_risk (path="{target_file}")
2. mcp--manifold--analyze_blast_radius (path="{target_file}")
3. Review dependency tree (which files will be affected?)
4. mcp--manifold--analyze_git_churn (path="{target_file}")
5. Check if other developers are actively working on it
6. Decision: Safe to refactor? Need coordination?
```

---

### Workflow: Technical Debt Quantification

**Goal**: Create a technical debt report for stakeholders.

```
1. mcp--manifold--ingest_repo
2. mcp--manifold--batch_chaos_scan (all files)
3. mcp--manifold--scan_critical_files (combined risk report)
4. mcp--manifold--scan_high_friction_files (maintenance burden)
5. Generate summary:
   - Total files with HIGH/CRITICAL risk
   - Estimated refactoring effort (story points)
   - Priority ranking
   - ROI analysis (friction reduction)
```

---

## Integration Examples

### Example 1: Combined Friction + Chaos Analysis

```python
# Pseudocode workflow
files = scan_high_friction_files(pattern="src/**/*.py", min_friction=0.15)

for file_path, friction, risk_level in files:
    if friction >= 0.25:
        # High friction - analyze further
        chaos_data = analyze_code_chaos(file_path)
        blast_data = analyze_blast_radius(file_path)
        
        print(f"REFACTOR CANDIDATE: {file_path}")
        print(f"  Friction: {friction} (chaos={chaos_data['chaos_score']}, churn high)")
        print(f"  Blast radius: {blast_data['blast_radius']} files")
        print(f"  Action: {'URGENT' if friction >= 0.30 else 'Schedule next sprint'}")
```

---

### Example 2: Architecture Review

```python
# Find core modules (high blast radius)
blast_analyzer = ASTDependencyAnalyzer(repo_root)
blast_analyzer.build_dependency_graph()
core_modules = blast_analyzer.get_high_impact_files(min_blast_radius=10)

for file_path, dep_info in core_modules:
    print(f"CORE MODULE: {file_path}")
    print(f"  Impacts {dep_info.blast_radius} files")
    print(f"  Depth: {dep_info.depth} levels")
    
    # Check if it's also complex
    chaos = get_chaos_score(file_path)
    if chaos > 0.40:
        print(f"  WARNING: High complexity ({chaos}) + High impact")
        print(f"  Recommendation: Requires architectural review")
```

---

## Best Practices for New Features

### Git Churn Analysis

**DO**:
- ✅ Use churn to contextualize chaos scores
- ✅ Consider recent commits (90d) vs total history
- ✅ Check churn before starting refactoring
- ✅ Track churn trends over time

**DON'T**:
- ❌ Don't assume high churn = bad (could be active development)
- ❌ Don't ignore low-churn but high-chaos files (time bombs)
- ❌ Don't refactor high-churn files without team coordination

### Friction Score

**DO**:
- ✅ Prioritize friction >0.25 for refactoring
- ✅ Use friction for sprint planning
- ✅ Track friction reduction as a metric
- ✅ Consider friction when assigning tasks

**DON'T**:
- ❌ Don't refactor solely based on friction (check blast radius too)
- ❌ Don't ignore developer feedback (friction is quantitative, pain is qualitative)

### Blast Radius

**DO**:
- ✅ Always check blast radius before major refactoring
- ✅ Use blast radius for impact assessment
- ✅ Coordinate with teams affected by high blast radius changes
- ✅ Add extra test coverage for high-blast files

**DON'T**:
- ❌ Don't fear high blast radius (core modules need refactoring too)
- ❌ Don't refactor high-blast files without comprehensive tests
- ❌ Don't ignore dependency tree visualization

### Combined Risk

**DO**:
- ✅ Use combined risk for ultimate prioritization
- ✅ Review top 10 critical files quarterly
- ✅ Track combined risk trends over releases
- ✅ Set combined risk thresholds for CI/CD gates

**DON'T**:
- ❌ Don't use combined risk alone (context matters)
- ❌ Don't let combined risk paralyze decision-making
- ❌ Don't ignore files just below threshold

---

## Troubleshooting New Features

### "Not a valid Git repository"

**Cause**: Git churn analysis requires a Git repo.

**Solution**:
- Ensure you're running inside a Git repository
- Check `.git` directory exists
- Some features gracefully degrade without Git (churn_score = 0)

---

### "No Git history found for file"

**Cause**: File is not tracked by Git or was just added.

**Solution**:
- Check if file is in `.gitignore`
- Ensure file has been committed at least once
- New files will have churn_score = 0

---

### "Error analyzing dependencies"

**Cause**: AST parsing failed (syntax error, encoding issue).

**Solution**:
- Check file has valid Python syntax
- Ensure file encoding is UTF-8
- Binary files are automatically skipped

---

### High combined risk but low chaos

**Cause**: File has high blast radius or high churn but moderate chaos.

**Interpretation**:
- **High blast + moderate chaos**: Core integration point, needs careful handling
- **High churn + moderate chaos**: Active development, may stabilize
- **Action**: Consider context before refactoring

---

## Performance Notes

### Git Churn Analysis
- **Single file**: ~50-200ms (depends on commit history)
- **Repo scan**: ~2-10s for 50 files
- **Optimization**: Uses batch Git commands

### Blast Radius Analysis
- **Single file**: ~100-500ms (depends on repo size)
- **Repo scan**: ~5-30s for 50 files
- **First run**: Slower (builds AST cache)
- **Subsequent runs**: Faster (uses cached graph)

### Combined Operations
- **Single file (all metrics)**: ~500ms-1s
- **Critical files scan**: ~10-30s for 50 files
- **Optimization**: Tools cache intermediate results

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2026-02-23 | 2.0 | Added Git churn, blast radius, and combined risk analysis (6 new tools) |
| 2026-02-23 | 1.0 | Initial comprehensive guide (16 original tools) |

---

**End of Guide**
