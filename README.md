# Structural Manifold Compression MCP Server

**A Model Context Protocol (MCP) server that exposes the chaos-detection neural primitives from the 3-body gravitational ejection predictor (MNRAS preprint Feb 2026) for real-time codebase structural analysis.**

---

## Overview

This MCP server implements the exact symbolic-dynamics pipeline used to predict gravitational ejection in the 3-body problem, now adapted for detecting architectural collapse in software codebases with sub-millisecond latency.

The server provides a complete suite of tools for:
- **Structural analysis** of code through byte-stream manifold signatures
- **Chaos detection** using the same fluctuation persistence metrics that predict orbital instability
- **Real-time monitoring** of codebase health and maintainability
- **Zero-shot learning** through fact injection into working memory

## Core Signal Pipeline

The server implements a 6-stage signal-first pipeline identical to the chaos proxy:

1. **Rolling variance** of byte-stream "kinetic energy"
2. **Log scaling** + Delta-Sigma 1-bit quantization
3. **Symbolic state machine** (LOW_FLUCTUATION / OSCILLATION / PERSISTENT_HIGH)
4. **fluctuation_persistence** = chaos score (PERSISTENT_HIGH fraction)
5. **Entropy + coherence** as secondary metrics
6. **Hazard gating** (collapse detection) on every retrieval

---

## Installation

### Prerequisites

- Python 3.10+
- Valkey (or Redis) server running on `localhost:6379`
- C++ structural entropy engine (compiled from `src/`)

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/SepDynamics/structural-manifold-compression.git
   cd structural-manifold-compression
   ```

2. **Install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Build the C++ engine** (optional, pre-built binary included)
   ```bash
   cd src
   cmake -B build
   cmake --build build
   ```

4. **Start Valkey/Redis**
   ```bash
   valkey-server
   # Or: redis-server
   ```

5. **Configure MCP in your IDE**
   
   Add to your MCP settings (e.g., Claude Desktop, Cursor, or other MCP-compatible editors):
   
   ```json
   {
     "mcpServers": {
       "manifold": {
         "command": "python",
         "args": ["mcp_server.py"],
         "cwd": "/path/to/structural-manifold-compression"
       }
     }
   }
   ```

---

## MCP Tools

The server exposes 14 tools through the Model Context Protocol:

### Repository Management
- **`ingest_repo`** - Full symbolic-dynamics ingest of repository into Valkey
- **`get_index_stats`** - Statistics about the indexed codebase
- **`start_watcher`** - Live filesystem watcher for auto-ingestion on save

### Code Search & Retrieval
- **`search_code`** - Keyword/regex search across indexed files
- **`get_file`** - Read a specific indexed file
- **`list_indexed_files`** - List all indexed files with glob filtering

### Structural Analysis
- **`compute_signature`** - Compress text into manifold signatures
- **`get_file_signature`** - Get structural signature for a file
- **`search_by_structure`** - Find structurally similar files
- **`verify_snippet`** - Verify code snippet against codebase patterns

### Chaos Detection
- **`analyze_code_chaos`** - Full ChaosResult per file (identical to three_body_demo.py)
- **`batch_chaos_scan`** - GPU-style batch validation across repository
- **`predict_structural_ejection`** - Forecast when a file will become unmaintainable
- **`visualize_manifold_trajectory`** - Generate 4-panel chaos dashboard

### Zero-Shot Learning
- **`inject_fact`** - Inject new facts into working memory codebook

---

## Quick Start Example

Once configured in your MCP-compatible IDE:

```
# Index your codebase
> ingest_repo(root_dir=".", compute_chaos=True)

# Analyze a specific file for chaos
> analyze_code_chaos(path="src/manifold/sidecar.py")

# Find high-risk files
> batch_chaos_scan(pattern="*.py", max_files=50)

# Visualize the structural trajectory
> visualize_manifold_trajectory(path="mcp_server.py")
```

---

## Architecture

### Components

- **[`mcp_server.py`](mcp_server.py)** - Main MCP server with 14 exposed tools
- **`src/manifold/`** - Python modules for encoding, verification, and Valkey integration
  - [`sidecar.py`](src/manifold/sidecar.py) - Core encoding and chaos analysis
  - [`valkey_client.py`](src/manifold/valkey_client.py) - Working memory interface
  - [`encoder.py`](src/manifold/encoder.py) - Signature computation
  - [`router.py`](src/manifold/router.py) - Spatial routing logic
  - [`verifier.py`](src/manifold/verifier.py) - Snippet verification
- **`src/core/`** - C++ structural entropy engine
  - [`structural_entropy.cpp`](src/core/structural_entropy.cpp) - Core physics calculations
  - [`byte_stream_manifold.cpp`](src/core/byte_stream_manifold.cpp) - Byte stream processing
- **`scripts/rag/`** - Supporting RAG utilities and examples
- **`scripts/tests/`** - MCP tool tests

### Dependencies

Core dependencies (see [`requirements.txt`](requirements.txt)):
- `mcp[server]` - Model Context Protocol server framework
- `valkey` / `redis` - Working memory backend
- `pydantic` - Data validation
- `watchdog` - Filesystem monitoring (optional)

---

## Testing

Run the MCP tool test suite:

```bash
python scripts/tests/test_mcp_tools.py
```

Test zero-shot fact injection:

```bash
python scripts/tests/test_zero_shot_injection.py
```

---

## Use Cases

### For AI Assistants
- Real-time detection of code that violates established patterns
- Structural similarity search for finding related code
- Chaos-based file ranking for maintenance prioritization
- Verification of AI-generated code against codebase norms

### For Development Teams
- Continuous monitoring of codebase health metrics
- Early warning system for files approaching unmaintainability
- Structural refactoring guidance through similarity analysis
- Automated architectural alignment checks

### For Research
- Applying gravitational chaos theory to software engineering
- Studying code evolution through structural manifold trajectories
- Zero-shot learning experiments in working memory

---

## Project Structure

```
.
├── mcp_server.py              # Main MCP server (14 tools)
├── src/
│   ├── manifold/              # Python modules
│   │   ├── sidecar.py        # Core encoding & chaos
│   │   ├── valkey_client.py  # Working memory
│   │   ├── encoder.py        # Signature computation
│   │   ├── router.py         # Spatial routing
│   │   └── verifier.py       # Verification
│   ├── core/                  # C++ engine
│   │   ├── structural_entropy.cpp
│   │   └── byte_stream_manifold.cpp
│   └── bin/                   # Compiled binaries
├── scripts/
│   ├── rag/                   # RAG utilities
│   └── tests/                 # Test scripts
├── tests/                     # Unit tests
├── reports/                   # Generated analysis reports
└── README.md                  # This file
```

---

## Scientific Background

This MCP server is based on research that applies the same mathematical framework used to predict chaotic orbital ejection in 3-body gravitational systems to software architecture analysis.

**Key insight**: Just as fluctuation persistence in orbital kinetic energy predicts ejection events, fluctuation persistence in code byte-stream entropy predicts maintainability collapse.

For the full mathematical treatment and validation on gravitational systems, see the MNRAS preprint (Feb 2026).

---

## License & Citation

This project is released under the [MIT License](LICENSE).

```bibtex
@misc{nagy2026manifold,
  author       = {Alexander Nagy},
  title        = {Structural Manifold Compression MCP Server},
  year         = {2026},
  howpublished = {\url{https://github.com/SepDynamics/structural-manifold-compression}}
}
```

---

## Related Tools

- **Valkey Working Memory**: [`scripts/rag/bulk_valkey_ingest.py`](scripts/rag/bulk_valkey_ingest.py) - Standalone indexing
- **Pair Programmer Agent**: [`scripts/rag/pair_programmer_agent.py`](scripts/rag/pair_programmer_agent.py) - Autonomous watcher demo
- **RAG CLI**: [`scripts/rag/tripartite_cli.py`](scripts/rag/tripartite_cli.py) - Command-line interface

---

## Support

For issues, questions, or contributions, please open an issue on GitHub.

**Repository**: https://github.com/SepDynamics/structural-manifold-compression
