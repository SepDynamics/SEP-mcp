# Manifold MCP Tools - Quick Reference Card

## 🚀 Setup (One-Time)
```bash
# Already configured globally at:
~/.config/Code/User/globalStorage/kilocode.kilo-code/settings/mcp_settings.json

# Start the watcher for auto-indexing
start_watcher()
```

## 📊 Essential Tools (Most Used)

| Tool | Purpose | Example |
|------|---------|---------|
| `search_code(query)` | Find code patterns | `search_code("def compute")` |
| `analyze_code_chaos(path)` | Check file complexity | `analyze_code_chaos("mcp_server.py")` |
| `get_index_stats()` | View index health | `get_index_stats()` |
| `list_indexed_files(pattern)` | List files by pattern | `list_indexed_files("*.py")` |
| `batch_chaos_scan(pattern)` | Find risky files | `batch_chaos_scan("src/**/*.py", 10)` |

## 🔍 By Use Case

### Finding Code
```
search_code("pattern", file_pattern="*.py")
list_indexed_files("src/**/*.cpp")
get_file("path/to/file.py")
```

### Quality Analysis
```
analyze_code_chaos("file.py")              # Single file
batch_chaos_scan("*.py", max_files=20)     # Multiple files
predict_structural_ejection("file.py", 30) # Forecast
```

### Structural Analysis
```
get_file_signature("file.py")                # Get signature
compute_signature(code_text)                  # Compute new
search_by_structure("c0.4_s0.7_e0.9", 0.05)  # Find similar
```

### Validation
```
verify_snippet(code_snippet, coverage_threshold=0.5)
```

### Knowledge Management
```
inject_fact("fact_id", "knowledge text")
remove_fact("fact_id")
```

### Visualization
```
visualize_manifold_trajectory("file.py")
# Outputs PNG to reports/
```

## 💡 Quick Patterns

### Pre-Commit Check
```python
# Check all modified files
files = ["src/module.py", "tests/test_module.py"]
for f in files:
    analyze_code_chaos(f)
```

### Find Technical Debt
```python
# Get top 10 riskiest files
batch_chaos_scan("**/*.py", max_files=10)
```

### Code Review
```python
# Analyze PR changes
analyze_code_chaos("modified_file.py")
visualize_manifold_trajectory("modified_file.py")
```

### Validate AI Code
```python
# Check if AI-generated code matches project
verify_snippet(ai_generated_code, coverage_threshold=0.6)
```

### Find Similar Files
```python
# Get signature of file you like
sig = get_file_signature("good_example.py")
# Find similar ones
search_by_structure(sig, tolerance=0.1)
```

## ⚡ Performance Tips

- Use `file_pattern` to narrow searches
- Limit `max_results` for faster responses
- Run `start_watcher()` once per session
- Use cached signatures with `get_file_signature()`
- Batch operations during low-activity periods

## 🎯 Risk Thresholds

| Chaos Score | Risk Level | Action |
|-------------|-----------|---------|
| < 0.25 | LOW | Maintain current quality |
| 0.25-0.35 | MEDIUM | Monitor, plan refactor |
| > 0.35 | HIGH | Refactor recommended |

## 📈 Signature Interpretation

**Format**: `c{coherence}_s{stability}_e{entropy}`

- **Coherence** (c): Higher = more consistent structure
- **Stability** (s): Higher = more stable patterns
- **Entropy** (e): Higher = more information density

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| File not found | Run `ingest_repo()` or check path |
| Timeout | Reduce scope or increase timeout |
| Stale data | Run `start_watcher()` or re-ingest |
| High memory | Clear Valkey and re-ingest |

## 📚 Full Documentation

See [`MCP_TOOL_GUIDE.md`](./MCP_TOOL_GUIDE.md) for complete documentation including:
- Detailed parameter descriptions
- Edge cases and limitations
- Advanced use cases
- Integration patterns
- Best practices

---

**Quick Tip**: This server is globally available in all VS Code workspaces!
