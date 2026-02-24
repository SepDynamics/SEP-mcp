# Tests & Benchmarks

All test scripts and benchmarks for the Manifold MCP server.

## Test Suite

| File | Purpose |
|---|---|
| [`test_mcp_tools.py`](test_mcp_tools.py) | Comprehensive MCP tool validation (all 20 tools, 44 tests) |
| [`test_sidecar.py`](test_sidecar.py) | Unit tests for the sidecar encoding module |
| [`conftest.py`](conftest.py) | Pytest configuration and path fixtures |

## Benchmarks

| File | Purpose |
|---|---|
| [`benchmark_memory.py`](benchmark_memory.py) | Measure Valkey memory usage at scale |
| [`benchmark_scope.py`](benchmark_scope.py) | Performance testing for large repositories |

## Running Tests

```bash
# Run all tests (use the project virtualenv)
.venv/bin/python -m pytest tests/ -v

# Run MCP tool validation only
.venv/bin/python -m pytest tests/test_mcp_tools.py -v

# Run sidecar unit tests only
.venv/bin/python -m pytest tests/test_sidecar.py -v

# Run benchmarks
.venv/bin/python tests/benchmark_memory.py
.venv/bin/python tests/benchmark_scope.py
```

## Test Coverage (20 Tools)

| Category | Tools Tested |
|---|---|
| **Indexing & Monitoring** | `ingest_repo`, `get_index_stats`, `start_watcher` |
| **Search & Retrieval** | `search_code`, `get_file`, `list_indexed_files`, `get_file_signature`, `search_by_structure` |
| **Structural Analysis** | `compute_signature`, `verify_snippet` |
| **Chaos Detection** | `analyze_code_chaos`, `batch_chaos_scan`, `predict_structural_ejection`, `visualize_manifold_trajectory`, `cluster_codebase_structure` |
| **Dependency & Risk** | `analyze_blast_radius`, `compute_combined_risk`, `scan_critical_files` |
| **Working Memory** | `inject_fact`, `remove_fact` |

## Test Structure

Tests are organized into class-based groups matching the tool categories:

- `TestIndexingAndMonitoring` — Index lifecycle and watcher validation
- `TestSearchAndRetrieval` — File search, retrieval, and structural lookup
- `TestStructuralAnalysis` — Signature computation and snippet verification
- `TestChaosDetection` — Chaos metrics, batch scanning, visualization output
- `TestDependencyAndRisk` — Blast radius, combined risk, critical file scanning
- `TestWorkingMemory` — Fact injection/removal lifecycle
- `TestWatcherIntegration` — Filesystem watcher file creation/cleanup
- `TestToolInventory` — Meta-test ensuring all 20 tools are imported and callable

---

All test results are automatically captured in [`../reports/mcp_tool_report.md`](../reports/mcp_tool_report.md).
