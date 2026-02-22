# Structural Manifold Compression MCP Server - Complete Guide

## Overview

The Manifold MCP server provides 16 powerful tools for structural code analysis, compression, and validation using manifold-based algorithms derived from three-body chaos dynamics. This server is now configured as a **global utility** available in all VS Code workspaces.

## Global Configuration Status

✅ **Configured Location**: `~/.config/Code/User/globalStorage/kilocode.kilo-code/settings/mcp_settings.json`
✅ **Server Name**: `manifold`
✅ **Status**: Active and available in all workspaces
✅ **Timeout**: 60 seconds
✅ **Auto-allowed tools**: All 16 tools pre-approved

## Tool Categories

### 1. Index Management Tools

#### `get_index_stats()`
**Purpose**: View current state of the Valkey codebase index
**Use Cases**:
- Monitor index health and memory usage
- Check last ingest timestamp
- View average chaos scores across codebase
- Determine high-risk file counts

**Example Output**:
```
📊 Codebase Index Stats
  Total Valkey keys  : 15497
  Indexed documents  : 5426
  File list entries  : 5426
  Structural sigs   : 4520
  Chaos profiles    : 4520
  Valkey memory      : 3.47G
  Last ingest        : 2026-02-22T05:44:16Z
  Avg chaos score    : 0.402
  High-risk files    : 4507
```

#### `ingest_repo(root_dir, clear_first, compute_chaos, max_bytes_per_file)`
**Purpose**: Index an entire directory into Valkey
**Parameters**:
- `root_dir` (default: "."): Directory to ingest
- `clear_first` (default: false): Wipe existing index first
- `compute_chaos` (default: true): Compute chaos profiles
- `max_bytes_per_file` (default: 512000): File size limit

**Use Cases**:
- Initial repository indexing
- Refresh stale index data
- Index new projects
- Bulk analysis setup

**Edge Cases Tested**:
- ⚠️ Large repos (>5000 files) may timeout with 60s limit
- ✅ Binary files are tracked but not fully indexed
- ✅ Can re-ingest without clearing (merges data)

#### `start_watcher(watch_dir, max_bytes_per_file)`
**Purpose**: Auto-ingest files on save events
**Parameters**:
- `watch_dir` (default: "."): Directory to monitor
- `max_bytes_per_file` (default: 512000): Size limit

**Use Cases**:
- Keep index fresh during active development
- Automatic chaos tracking on file changes
- Real-time codebase monitoring
- CI/CD integration potential

**How It Works**:
- Monitors filesystem for modifications/creations
- Automatically updates Valkey index
- Non-blocking background process
- Respects file size limits

### 2. Code Retrieval Tools

#### `list_indexed_files(pattern, max_results)`
**Purpose**: List files matching a glob pattern
**Parameters**:
- `pattern` (default: "*"): Glob pattern (e.g., "*.py", "src/**")
- `max_results` (default: 200): Maximum files to return

**Use Cases**:
- Explore available files in index
- Filter by file type or directory
- Audit indexed content
- Quick file discovery

**Pattern Examples**:
- `*.py` - All Python files
- `src/**/*.cpp` - All C++ files in src/ recursively
- `test_*.py` - All test files
- `**/*.md` - All markdown files

#### `get_file(path)`
**Purpose**: Retrieve full text content of indexed file
**Parameters**:
- `path`: File path relative to repo root

**Use Cases**:
- Read indexed file contents
- Verify file is properly indexed
- Extract code for analysis
- Code review assistance

**Edge Cases**:
- ❌ Returns error if file not in index
- ✅ Works with full absolute or relative paths
- ✅ Returns original text as stored during ingest

#### `search_code(query, file_pattern, case_sensitive, max_results)`
**Purpose**: Search indexed codebase by keyword or regex
**Parameters**:
- `query`: Search string or Python regex pattern
- `file_pattern` (default: "*"): Glob to filter files
- `case_sensitive` (default: false): Case sensitivity
- `max_results` (default: 20): Max matching files

**Use Cases**:
- Find function definitions across codebase
- Locate API usage patterns
- Search for TODO/FIXME comments
- Identify code patterns
- Security audit for sensitive patterns
- Dependency tracking

**Example Queries**:
- `def compute_signature` - Find function definition
- `import.*torch` - Find PyTorch imports (regex)
- `TODO|FIXME` - Find all todos (regex)
- `password.*=` - Security audit (regex)

### 3. Structural Signature Tools

#### `compute_signature(text)`
**Purpose**: Compress text into manifold signatures
**Parameters**:
- `text`: Raw text string (must be ≥512 bytes for full analysis)

**Use Cases**:
- Compress large code snippets
- Analyze structural patterns
- Generate fingerprints for code
- Compare code similarity without storing full text
- Understand code complexity metrics

**Output Metrics**:
- **Compression ratio**: How much smaller the signature is
- **Unique signatures**: Number of distinct structural patterns
- **Total windows**: Number of 512-byte windows analyzed
- **Hazard threshold**: Chaos risk boundary

**Edge Cases Tested**:
- ✅ Small text (<512 bytes): Single window analysis
- ✅ Large text: Multiple windows with unique signatures
- ✅ Handles any text format (code, prose, data)

#### `get_file_signature(path)`
**Purpose**: Get cached signature for indexed file
**Parameters**:
- `path`: File path relative to repo root

**Use Cases**:
- Quick signature lookup without recomputation
- Compare file structures efficiently
- Track structural changes over time
- Identify similar code patterns

**Signature Format**: `c{coherence}_s{stability}_e{entropy}`
- **c (coherence)**: Structural consistency (0.0-1.0)
- **s (stability)**: Temporal stability (0.0-1.0)
- **e (entropy)**: Information density (0.0-1.0)

#### `search_by_structure(signature, tolerance, max_results)`
**Purpose**: Find files with similar structural signatures
**Parameters**:
- `signature`: Target signature (e.g., "c0.418_s0.760_e0.957")
- `tolerance` (default: 0.05): Max per-component deviation
- `max_results` (default: 20): Max similar files

**Use Cases**:
- Find structurally similar files
- Identify code duplication by structure
- Discover related modules
- Locate refactoring candidates
- Find architectural patterns

**How It Works**:
- Computes Euclidean distance in c-s-e space
- Returns files within tolerance sphere
- Sorted by structural similarity (Δ)

### 4. Chaos Analysis Tools

#### `analyze_code_chaos(path)`
**Purpose**: Compute full chaos analysis for a file
**Parameters**:
- `path`: File path relative to repo root

**Use Cases**:
- Assess code maintainability risk
- Identify refactoring priorities
- Track technical debt
- Predict maintenance burden
- Code quality metrics

**Output Metrics**:
- **Chaos Score**: Fluctuation persistence (0.0-1.0, higher = worse)
- **Entropy**: Information density
- **Coherence**: Structural consistency
- **Collapse Risk**: LOW/MEDIUM/HIGH assessment
- **Windows analyzed**: Granularity of analysis

**Risk Thresholds**:
- `< 0.25`: LOW risk - Stable, maintainable code
- `0.25-0.35`: MEDIUM risk - Monitor for growth
- `> 0.35`: HIGH risk - Refactoring recommended

#### `batch_chaos_scan(pattern, max_files)`
**Purpose**: Run chaos analysis across multiple files
**Parameters**:
- `pattern` (default: "*.py"): Glob pattern
- `max_files` (default: 50): Max highest-risk files to return

**Use Cases**:
- Find highest-risk files in codebase
- Prioritize refactoring efforts
- Generate technical debt reports
- Track code quality trends
- CI/CD quality gates

**Output**: Files ranked by chaos score (highest risk first)

**Strategic Applications**:
- Pre-merge quality checks
- Sprint planning (identify refactor targets)
- Onboarding (show complex areas to new devs)
- Architecture reviews

#### `predict_structural_ejection(path, horizon_days)`
**Purpose**: Predict when file becomes unmaintainable
**Parameters**:
- `path`: File path to analyze
- `horizon_days` (default: 30): Forecast window

**Use Cases**:
- Long-term maintenance planning
- Technical debt forecasting
- Budget allocation for refactoring
- Risk assessment for critical modules
- Proactive code health management

**How It Works**:
- Uses three-body dynamics correlation
- Maps chaos score to instability timeline
- PERSISTENT_HIGH state = ejection risk
- Based on published physics research

**Example Output**:
```
⚠️ WARNING: mcp_server.py is in PERSISTENT_HIGH state (score: 0.399).
Predicted structural ejection in ~10 days without refactoring.
```

#### `visualize_manifold_trajectory(path)`
**Purpose**: Generate 4-panel chaos analysis dashboard
**Parameters**:
- `path`: File path to visualize

**Use Cases**:
- Visualize code complexity patterns
- Present chaos metrics to stakeholders
- Deep dive into structural issues
- Research and publication figures
- Architecture documentation

**Dashboard Panels**:
1. **Structural Trajectory**: Byte offset vs coherence (colored by chaos)
2. **Chaos vs LLE Analog**: Entropy vs hazard scatter plot
3. **Time Series**: Hazard/entropy/coherence per window
4. **Symbolic State Distribution**: LOW/OSCILLATION/HIGH bar chart

**Output**: PNG saved to `reports/` directory

### 5. Advanced Validation Tools

#### `verify_snippet(snippet, coverage_threshold)`
**Purpose**: Verify code snippet against indexed codebase
**Parameters**:
- `snippet`: Text to verify (must be ≥512 bytes)
- `coverage_threshold` (default: 0.5): Min safe coverage ratio (0.0-1.0)

**Use Cases**:
- Validate AI-generated code
- Detect code plagiarism
- Ensure code aligns with project patterns
- Quality assurance for external code
- Compliance checking

**How It Works**:
- Computes manifold signature for snippet
- Compares against indexed signatures
- Checks if structural patterns match codebase
- Returns coverage ratio and matched documents

**Interpretation**:
- **Safe coverage ≥ threshold**: Code structurally aligns with codebase
- **Safe coverage < threshold**: Code may be foreign or novel patterns
- **Raw match ratio**: Direct structural similarity

#### `inject_fact(fact_id, fact_text)`
**Purpose**: Add knowledge to working memory (zero-shot learning)
**Parameters**:
- `fact_id`: Unique identifier for the fact
- `fact_text`: Factual text to assimilate

**Use Cases**:
- Teach AI about project-specific patterns
- Document architectural decisions
- Store coding guidelines
- Create institutional knowledge base
- Context injection for specialized tasks

**Examples**:
```python
inject_fact(
    "error_handling_standard",
    "All API functions must use try-except blocks with specific "
    "exception types. Never use bare except. Log errors with context."
)

inject_fact(
    "database_transaction_pattern",
    "Database transactions must use async context managers. "
    "Example: async with db.transaction() as txn: ..."
)
```

#### `remove_fact(fact_id)`
**Purpose**: Remove injected fact from working memory
**Parameters**:
- `fact_id`: Unique identifier to remove

**Use Cases**:
- Update outdated guidelines
- Remove temporary project facts
- Clean up deprecated patterns
- Manage memory usage

### 6. Edge Cases & Limitations

**Tested Edge Cases**:
1. ✅ Small snippets (<512 bytes): Single window analysis
2. ✅ Very large files: Multiple windows, may take time
3. ⚠️ Full repo ingest on large codebases: May timeout (60s limit)
4. ✅ Binary files: Tracked but not fully indexed
5. ✅ Re-ingesting without clearing: Data merges correctly
6. ✅ Missing files in get_file: Clear error message
7. ✅ Invalid signatures: Graceful error handling
8. ✅ Regex search: Full Python regex support
9. ✅ Glob patterns: Recursive and nested patterns work
10. ✅ Concurrent operations: Valkey handles concurrency

**Known Limitations**:
- 60-second timeout may be short for very large operations
- Binary file content not available via get_file
- Watcher doesn't detect deletions (only mods/creates)
- Signature requires minimum 512 bytes for meaningful analysis
- No incremental ingest_repo (all or nothing approach)

## Utility Maximization: When to Use Each Tool

### Daily Development Workflow

**Morning Routine**:
1. `start_watcher()` - Keep index fresh all day
2. `get_index_stats()` - Check index health

**During Coding**:
3. `search_code()` - Find similar implementations
4. `get_file()` - Read reference code
5. `compute_signature()` - Check your code's complexity

**Before Committing**:
6. `analyze_code_chaos()` - Check files you modified
7. `verify_snippet()` - Validate new code patterns

### Code Review Workflow

1. `batch_chaos_scan()` - Identify risky changes
2. `analyze_code_chaos()` - Deep dive on flagged files
3. `visualize_manifold_trajectory()` - Share complexity visualizations
4. `search_by_structure()` - Find similar code for comparison

### Refactoring Planning

1. `batch_chaos_scan()` - Find highest-risk files
2. `predict_structural_ejection()` - Prioritize by urgency
3. `visualize_manifold_trajectory()` - Understand complexity patterns
4. `search_by_structure()` - Find related files to refactor together

### Architecture Analysis

1. `list_indexed_files()` - Survey codebase structure
2. `get_file_signature()` - Get structural fingerprints
3. `search_by_structure()` - Identify architectural clusters
4. `batch_chaos_scan()` - Find architectural hot spots

### AI-Assisted Development

1. `inject_fact()` - Teach AI about project standards
2. `search_code()` - Find reference implementations
3. `verify_snippet()` - Validate AI-generated code
4. `compute_signature()` - Check if AI code matches project style

### Technical Debt Management

1. `batch_chaos_scan()` - Generate debt inventory
2. `predict_structural_ejection()` - Forecast maintenance burden
3. `visualize_manifold_trajectory()` - Document problem areas
4. `analyze_code_chaos()` - Track improvement over time

## Integration with Kilo Code Assistant

Since this MCP server is globally configured, I (Kilo Code) now have access to these tools in **every workspace**. This means:

### Automatic Capabilities

When you ask me to:
- "Find all files that do X" → I'll use `search_code()`
- "Check if this code is too complex" → I'll use `analyze_code_chaos()`
- "Show me similar files" → I'll use `search_by_structure()`
- "Is this AI code good?" → I'll use `verify_snippet()`
- "What's the state of the codebase?" → I'll use `get_index_stats()`

### Proactive Analysis

I can now automatically:
- Check chaos scores before suggesting changes
- Find structurally similar code for reference
- Verify patterns match your codebase
- Monitor complexity as you code (with watcher)
- Suggest refactoring based on ejection predictions

### Context Awareness

With `inject_fact()`, you can teach me about:
- Your coding standards
- Project-specific patterns
- Architectural decisions
- Team conventions
- Domain-specific requirements

## Performance Characteristics

**Fast Operations** (<1s):
- `get_index_stats()`
- `list_indexed_files()`
- `get_file()`
- `get_file_signature()`
- `search_by_structure()`

**Medium Operations** (1-5s):
- `search_code()` - Depends on index size
- `analyze_code_chaos()` - Depends on file size
- `compute_signature()` - Depends on text length
- `verify_snippet()` - Depends on snippet size

**Slow Operations** (5-60s):
- `batch_chaos_scan()` - Depends on file count
- `visualize_manifold_trajectory()` - Includes rendering
- `ingest_repo()` - May timeout on large repos
- `predict_structural_ejection()` - Compute-intensive

**Background Operations**:
- `start_watcher()` - Non-blocking, runs continuously

## Best Practices

### Index Management
1. Run `ingest_repo()` once on project setup
2. Use `start_watcher()` for ongoing updates
3. Check `get_index_stats()` periodically
4. Re-ingest if last_ingest timestamp is stale

### Performance Optimization
1. Use specific `file_pattern` in searches to reduce scope
2. Limit `max_results` for faster responses
3. Use `get_file_signature()` instead of recomputing
4. Batch operations during off-hours for large codebases

### Chaos Analysis Workflow
1. Start with `batch_chaos_scan()` for overview
2. Deep dive with `analyze_code_chaos()` on specific files
3. Use `visualize_manifold_trajectory()` for presentations
4. Track trends with `predict_structural_ejection()`

### Snippet Verification
1. Ensure snippets are ≥512 bytes for accurate verification
2. Use 0.5-0.7 coverage_threshold for validation
3. Lower threshold (0.3-0.5) for exploratory checks
4. Higher threshold (0.7-0.9) for strict compliance

### Fact Injection Strategy
1. Use clear, descriptive fact_ids (e.g., "error_handling_v2")
2. Keep facts focused and specific
3. Include examples in fact_text
4. Version fact_ids for updates (v1, v2, etc.)
5. Document injected facts externally

## Security Considerations

- All tools operate read-only on indexed data
- No write access to source files
- `inject_fact()` only affects working memory (Valkey)
- Valkey instance is local (not exposed externally)
- File size limits prevent memory exhaustion
- Timeout prevents infinite operations

## Maintenance

### Regular Tasks
- **Daily**: Monitor `get_index_stats()` for health
- **Weekly**: Review high chaos scores from `batch_chaos_scan()`
- **Monthly**: Re-ingest to catch any missed changes
- **Quarterly**: Review and clean up injected facts

### Troubleshooting
- **Tool timeout**: Reduce scope or increase timeout in config
- **Missing files**: Check if file was ingested
- **High memory usage**: Clear old indices, re-ingest
- **Stale data**: Restart watcher or re-ingest

## Conclusion

This MCP server provides a comprehensive suite of tools for structural code analysis based on manifold compression and three-body chaos dynamics. With 16 tools spanning indexing, retrieval, signature analysis, chaos detection, and validation, it enables deep insights into code quality, complexity, and maintainability.

The global configuration ensures these capabilities are available across all your VS Code projects, making sophisticated code analysis just a tool call away.

---

**Version**: 1.0.0  
**Last Updated**: 2026-02-22  
**MCP Server**: manifold  
**Total Tools**: 16  
**Configuration**: Global (~/.config/Code/User/globalStorage/kilocode.kilo-code/settings/mcp_settings.json)
