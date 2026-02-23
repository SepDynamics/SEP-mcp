# Quick Reference — Manifold MCP Server

All 22 tools at a glance. Full documentation: [MCP_TOOL_GUIDE.md](MCP_TOOL_GUIDE.md).

---

## Indexing & Monitoring

```
ingest_repo           root_dir="."  clear_first=true  compute_chaos=true  lite=false
get_index_stats
start_watcher         watch_dir="."
```

## File Discovery & Search

```
list_indexed_files    pattern="*.py"  max_results=200
get_file              path="src/manifold/sidecar.py"
search_code           query="chaos_score"  file_pattern="*.py"  case_sensitive=false
get_file_signature    path="mcp_server.py"
search_by_structure   signature="c0.213_s0.000_e0.928"  tolerance=0.05
```

## Chaos Analysis

```
analyze_code_chaos             path="mcp_server.py"
batch_chaos_scan               pattern="*.py"  max_files=50
predict_structural_ejection    path="mcp_server.py"  horizon_days=30
visualize_manifold_trajectory  path="mcp_server.py"
```

## Git Integration

```
analyze_git_churn         path="mcp_server.py"  days_back=365
compute_friction_score    path="mcp_server.py"
scan_high_friction_files  pattern="*.py"  min_friction=0.20  max_files=30
```

## Dependency & Combined Risk

```
analyze_blast_radius    path="src/manifold/sidecar.py"
compute_combined_risk   path="src/manifold/sidecar.py"
scan_critical_files     pattern="*.py"  min_combined_risk=0.30  max_files=20
```

## Verification & Memory

```
compute_signature    text="def hello(): ..."
verify_snippet       snippet="..."  coverage_threshold=0.5  scope="*.py"
inject_fact          fact_id="api_rules"  fact_text="All endpoints use snake_case."
remove_fact          fact_id="api_rules"
```

---

## Common Workflows

### New Project
```
1. ingest_repo  (clear_first=true)
2. get_index_stats
3. batch_chaos_scan
4. scan_critical_files
```

### Refactoring Decision
```
1. compute_combined_risk  (path)
2. analyze_blast_radius   (path)
3. predict_structural_ejection  (path)
4. visualize_manifold_trajectory  (path)
```

### Sprint Planning
```
1. scan_high_friction_files  (min_friction=0.15)
2. scan_critical_files  (min_combined_risk=0.25)
3. analyze_blast_radius for each candidate
```

### Find Code
```
1. search_code  (query, file_pattern)
2. get_file  (path)
3. search_by_structure  (signature)
```

---

## Chaos Score Ranges

| Score | Level | Action |
|---|---|---|
| 0.00–0.34 | Normal | Monitor |
| 0.35–0.39 | Elevated | Review |
| 0.40–0.44 | **HIGH** | Plan refactor |
| 0.45+ | Critical | Urgent |

## Risk Score Ranges

| Score | Level | Action |
|---|---|---|
| ≥0.40 | CRITICAL | Immediate refactoring |
| 0.30–0.39 | HIGH | Schedule within sprint |
| 0.20–0.29 | MODERATE | Monitor |
| <0.20 | LOW | Acceptable |

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Valkey not reachable | `valkey-server` or `redis-server` |
| File not found | `list_indexed_files  (pattern="*name*")` then re-ingest |
| Cannot compute chaos | File <512 bytes or encoder unavailable |
| No Git history | Ensure `.git` exists; churn degrades gracefully to 0 |

---

**Full documentation**: [MCP_TOOL_GUIDE.md](MCP_TOOL_GUIDE.md) · **Project overview**: [README.md](README.md)
