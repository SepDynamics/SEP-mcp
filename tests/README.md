# Tests & Benchmarks

All test scripts and benchmarks for the Manifold MCP server.

## Test Suite

| File | Purpose |
|---|---|
| [`test_comprehensive.py`](test_comprehensive.py) | Comprehensive MCP tool validation (all 22 tools) |
| [`test_mcp_tools.py`](test_mcp_tools.py) | Automated test suite with assertions |
| [`test_zero_shot_injection.py`](test_zero_shot_injection.py) | Working memory fact injection tests |
| [`test_autonomous_agent.py`](test_autonomous_agent.py) | Autonomous agent workflow demonstration |
| [`test_sidecar.py`](test_sidecar.py) | Unit tests for the sidecar module |
| [`conftest.py`](conftest.py) | Pytest configuration and fixtures |

## Benchmarks

| File | Purpose |
|---|---|
| [`benchmark_memory.py`](benchmark_memory.py) | Measure Valkey memory usage at scale |
| [`benchmark_scope.py`](benchmark_scope.py) | Performance testing for large repositories |

## Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_mcp_tools.py

# Run comprehensive validation
python tests/test_comprehensive.py

# Run benchmarks
python tests/benchmark_memory.py
python tests/benchmark_scope.py
```

## Test Coverage

- **Indexing**: ingest, stats, file listing, watcher
- **Search**: keyword, regex, structural similarity
- **Chaos**: analysis, scanning, prediction, visualization
- **Git**: churn analysis, friction scoring
- **Dependencies**: blast radius, combined risk
- **Verification**: snippet validation, signature computation
- **Memory**: fact injection/removal

All tests automatically validated in [`../reports/mcp_tool_report.md`](../reports/mcp_tool_report.md).
