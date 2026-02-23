# MCP Manifold Quick Reference

**Quick command reference for the Manifold MCP server. For detailed documentation, see [MCP_TOOL_GUIDE.md](MCP_TOOL_GUIDE.md).**

---

## Essential Commands

### 1. Initial Setup (First-Time Use)

```
# Clear and index repository
mcp--manifold--ingest_repo
  root_dir: "."
  clear_first: true
  compute_chaos: true
  lite: false

# Verify successful indexing
mcp--manifold--get_index_stats
```

**Expected Stats** (this repo):
- **47 files** indexed (768 KB)
- **Average chaos**: 0.408 (HIGH)
- **High-risk files**: 41/47

---

### 2. Find High-Risk Files

```
mcp--manifold--batch_chaos_scan
  pattern: "*.py"
  scope: "*"
  max_files: 30
```

**Top risks in this repo**:
- [`setup.py`](setup.py:1) - 0.427
- [`memory_benchmark.py`](memory_benchmark.py:1) - 0.423
- [`scripts/rag/bulk_valkey_ingest.py`](scripts/rag/bulk_valkey_ingest.py:1) - 0.422

---

### 3. Search for Code

```
# Keyword search
mcp--manifold--search_code
  query: "chaos_score"
  file_pattern: "*.py"
  max_results: 10

# Regex search for patterns
mcp--manifold--search_code
  query: "class \w+Manager"
  file_pattern: "*.py"
```

---

### 4. Analyze Specific File

```
# Deep chaos analysis
mcp--manifold--analyze_code_chaos
  path: "mcp_server.py"

# Visual dashboard
mcp--manifold--visualize_manifold_trajectory
  path: "mcp_server.py"

# Read full content
mcp--manifold--get_file
  path: "mcp_server.py"
```

---

### 5. Structural Search

```
# Get file's signature
mcp--manifold--get_file_signature
  path: "mcp_server.py"

# Find similar files
mcp--manifold--search_by_structure
  signature: "c0.213_s0.000_e0.928"
  tolerance: 0.05
```

---

### 6. Code Validation

```
mcp--manifold--verify_snippet
  snippet: "def my_function():\n    pass"
  coverage_threshold: 0.5
  scope: "*"
```

---

### 7. Working Memory

```
# Add persistent fact
mcp--manifold--inject_fact
  fact_id: "api_conventions"
  fact_text: "All API endpoints must use snake_case naming."

# Remove fact
mcp--manifold--remove_fact
  fact_id: "api_conventions"
```

---

## Chaos Score Ranges

| Score | Level | Action |
|-------|-------|--------|
| 0.00-0.34 | Normal | Monitor |
| 0.35-0.39 | Elevated | Review |
| 0.40-0.44 | **HIGH** | Plan refactor |
| 0.45+ | Critical | Urgent action |

**This repo average**: 0.408 (HIGH) - typical for complex algorithmic code.

---

## Common Workflows

### New Project Analysis
```
1. ingest_repo (clear_first=true)
2. get_index_stats (verify)
3. batch_chaos_scan (find hotspots)
4. analyze_code_chaos (deep dive on top files)
```

### Find Implementation
```
1. search_code (find pattern)
2. get_file (read full content)
3. get_file_signature (get structure)
4. search_by_structure (find similar)
```

### Refactoring Decision
```
1. analyze_code_chaos (get metrics)
2. predict_structural_ejection (get timeline)
3. visualize_manifold_trajectory (visual inspection)
```

### Continuous Monitoring
```
1. start_watcher (auto-update on save)
2. Periodic: batch_chaos_scan
```

---

## Tips

✅ **DO**:
- Use `clear_first=true` after major changes
- Run `batch_chaos_scan` first to prioritize
- Use regex in `search_code` for patterns
- Check `get_index_stats` regularly

❌ **DON'T**:
- Don't forget to start Valkey server first
- Don't panic at high chaos scores (context matters)
- Don't assume paths - use `list_indexed_files`
- Don't over-index (use `lite=true` for large repos)

---

## Troubleshooting

**"Valkey not reachable"**
```bash
valkey-server  # or: redis-server
```

**"File not found"**
```
mcp--manifold--list_indexed_files
  pattern: "*filename*"
```

**High memory usage**
```
mcp--manifold--ingest_repo
  lite: true  # Skip chaos on tests/docs
```

---

**For comprehensive documentation**: [MCP_TOOL_GUIDE.md](MCP_TOOL_GUIDE.md)  
**For project overview**: [README.md](README.md)
