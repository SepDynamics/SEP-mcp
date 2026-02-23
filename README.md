# Manifold Engine MCP Server

A Model Context Protocol server that gives AI coding assistants high-speed, structural codebase analysis and dynamic context management. Instead of reading code token-by-token, it maps repositories *structurally* — treating source files as continuous byte-streams, computing structural signatures, and detecting architectural chaos in O(1) time.

---

## Core Capabilities

| Capability | Description |
|---|---|
| **Structural Indexing** | Scans every file into a Valkey-backed grid with compressed signatures and chaos profiles. Sub-millisecond retrieval. |
| **Chaos Detection** | Calculates a `chaos_score` per file using a 3-body gravitational ejection proxy. Predicts which files will become unmaintainable. |
| **Dependency & Risk Analysis** | Traces import graphs via AST parsing, measures blast radius, combines chaos × blast into a single risk score. |
| **Working Memory** | Inject persistent facts (project conventions, architecture rules) into a Dynamic Semantic Codebook for zero-shot learning. |
| **Real-Time Sync** | Filesystem watcher auto-ingests file saves in milliseconds, keeping the index current without manual re-scans. |

---

## Installation

### Prerequisites

- Python 3.10+
- Valkey (or Redis) running on `localhost:6379`
- C++20 compiler (for building the native structural engine)
- `faiss-cpu` (required for running the `cluster_codebase_structure` tool)

### Setup

```bash
# 1. Start the Valkey backend
valkey-server

# 2. Install the manifold engine
pip install -e .

# 3. Configure your MCP client (Kilo Code, Claude Desktop, Cursor, etc.)
```

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "manifold": {
      "command": "path/to/virtualenv/bin/python",
      "args": ["path/to/SEP-mcp/mcp_server.py"],
      "cwd": "path/to/SEP-mcp"
    }
  }
}
```

---

## Quick Start

```
# 1. Index the repository
ingest_repo  (root_dir=".", clear_first=true, compute_chaos=true)

# 2. Verify
get_index_stats

# 3. Find complexity hotspots
batch_chaos_scan  (pattern="*.py", max_files=30)

# 4. Deep-dive a specific file
analyze_code_chaos      (path="target_file.py")
analyze_blast_radius    (path="target_file.py")
compute_combined_risk   (path="target_file.py")
```

---

## Tool Reference (21 Tools)

All tools are documented with parameters, examples, and workflows in **[MCP_TOOL_GUIDE.md](MCP_TOOL_GUIDE.md)**. Quick command reference in **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)**.

### Indexing & Monitoring
| Tool | Purpose |
|---|---|
| `ingest_repo` | Full repository scan into Valkey with signatures and chaos profiles |
| `get_index_stats` | Real-time index health: document count, memory, chaos averages |
| `start_watcher` | Background filesystem observer — auto-ingests on file save/delete |

### File Discovery & Search
| Tool | Purpose |
|---|---|
| `list_indexed_files` | Browse indexed files by glob pattern |
| `get_file` | Read full file content from the Valkey index |
| `search_code` | Keyword or regex search across all indexed files with context |
| `get_file_signature` | Structural fingerprint (coherence/stability/entropy) for a file |
| `search_by_structure` | Find files with similar structural signatures |
| `cluster_codebase_structure` | Cluster the codebase using Coherence/Entropy structural groupings |

### Chaos Analysis
| Tool | Purpose |
|---|---|
| `analyze_code_chaos` | Per-file chaos score, entropy, coherence, collapse risk |
| `batch_chaos_scan` | Rank all files by chaos score (highest risk first) |
| `predict_structural_ejection` | Forecast when a file becomes unmaintainable |
| `visualize_manifold_trajectory` | Generate a 4-panel PNG dashboard of chaos dynamics (incl. 3D Phase Space) |
| `visualize_manifold_3d.py` | Generate an interactive 3D probability volume scatter plot (C, E, Chaos) |

### Dependency & Combined Risk
| Tool | Purpose |
|---|---|
| `analyze_blast_radius` | Import dependency tree and impact file count |
| `compute_combined_risk` | Combined risk = 0.6×chaos + 0.4×blast |
| `scan_critical_files` | Repository-wide scan for highest combined risk |

### Verification & Memory
| Tool | Purpose |
|---|---|
| `compute_signature` | Compress arbitrary text into manifold signatures |
| `verify_snippet` | Check if code structurally matches existing codebase patterns |
| `inject_fact` | Add persistent knowledge to the Dynamic Semantic Codebook |
| `remove_fact` | Remove a previously injected fact |

---

## Empirical Validation

### React 15.0 Case Study
The structural engine flagged the exact files (`ReactReconcileTransaction.js`, `ReactInstanceHandles.js`) that the React core team subsequently deleted and rewrote as React Fiber — without any semantic understanding of JavaScript.
→ [Read the study](reports/react_validation_case_study.md)

### Langchain ROC Analysis
A blind forward-prediction study on `langchain v0.0.300` proved that a chaos score threshold of **0.396** optimally predicts architectural ejection, achieving ~91% of the predictive power of expensive AST-parsing tools at O(1) speed.
→ [Read the study](reports/true_validation_study.md)

### Memory Optimization
Zstandard compression reduced the cpython index from **3.4 GB to 28 MB** (>99% reduction) with zero loss in retrieval accuracy.

---

## Documentation

| Document | Purpose |
|---|---|
| [MCP_TOOL_GUIDE.md](MCP_TOOL_GUIDE.md) | Comprehensive tool reference, workflows, best practices |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | Command cheat sheet |
| [reports/](reports/) | Validation studies and generated reports |

---

## License

MIT — see [LICENSE](LICENSE)
