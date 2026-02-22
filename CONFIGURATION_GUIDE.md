# Manifold MCP Server - Configuration Guide

## Current Global Configuration

The Manifold MCP server is configured as a **global utility** available in all VS Code workspaces.

### Configuration Location

**Global Settings Path**:
```
~/.config/Code/User/globalStorage/kilocode.kilo-code/settings/mcp_settings.json
```

### Current Configuration

```json
{
  "mcpServers": {
    "manifold": {
      "command": ".venv/bin/python",
      "args": ["mcp_server.py"],
      "cwd": "/sep/structural-manifold-compression/SEP-mcp",
      "env": {
        "PYTHONPATH": "."
      },
      "alwaysAllow": [
        "search_code",
        "get_file",
        "list_indexed_files",
        "get_index_stats",
        "compute_signature",
        "get_file_signature",
        "search_by_structure",
        "ingest_repo",
        "verify_snippet",
        "start_watcher",
        "inject_fact",
        "remove_fact",
        "analyze_code_chaos",
        "batch_chaos_scan",
        "predict_structural_ejection",
        "visualize_manifold_trajectory"
      ],
      "disabled": false,
      "timeout": 60
    }
  }
}
```

## Configuration Components

### Server Identity
- **Name**: `manifold`
- **Type**: Local (stdio-based)
- **Status**: Enabled (`disabled: false`)

### Execution Environment
- **Command**: `.venv/bin/python` - Uses project's virtual environment
- **Script**: `mcp_server.py` - Main server entry point
- **Working Directory**: `/sep/structural-manifold-compression/SEP-mcp`
- **Python Path**: Project root (`.`) for imports

### Tool Permissions
All 16 tools are pre-approved in `alwaysAllow`:
1. `search_code` - Code pattern search
2. `get_file` - File retrieval
3. `list_indexed_files` - File listing
4. `get_index_stats` - Index statistics
5. `compute_signature` - Signature computation
6. `get_file_signature` - Cached signature retrieval
7. `search_by_structure` - Structural similarity search
8. `ingest_repo` - Repository indexing
9. `verify_snippet` - Code validation
10. `start_watcher` - Auto-indexing watcher
11. `inject_fact` - Knowledge injection
12. `remove_fact` - Fact removal
13. `analyze_code_chaos` - Chaos analysis
14. `batch_chaos_scan` - Batch chaos scan
15. `predict_structural_ejection` - Ejection prediction
16. `visualize_manifold_trajectory` - Trajectory visualization

### Timeout
- **Value**: 60 seconds
- **Recommendation**: Increase to 120-180s for large repos

## Local vs Global Configuration

### Current Setup: Global
- **Location**: `~/.config/Code/User/globalStorage/kilocode.kilo-code/settings/mcp_settings.json`
- **Scope**: All VS Code workspaces
- **Benefit**: Available everywhere without per-project setup

### Alternative: Local (Per-Project)
- **Location**: `.kilocode/mcp.json` in project root
- **Scope**: Only in that workspace
- **When to use**: Project-specific MCP servers or configurations

### Verification
Both locations currently have the configuration, but **global takes precedence** for cross-workspace availability.

## Dependencies

### System Requirements
1. **Valkey/Redis**: Running on localhost (default port)
2. **Python 3.11+**: With virtual environment
3. **VS Code**: With Kilo Code extension

### Python Dependencies
See [`requirements.txt`](./requirements.txt):
```
mcp>=1.3.2
Pillow>=11.0.0
matplotlib>=3.10.0
watchdog>=6.0.0
valkey>=6.0.2
numpy>=2.2.3
```

### Installation
```bash
# Create virtual environment
python -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python mcp_server.py --version  # If available
```

## Valkey Configuration

### Default Valkey Setup
The server expects Valkey running at:
- **Host**: `localhost`
- **Port**: 6379 (default)
- **DB**: 0

### Custom Valkey Configuration
Modify in [`mcp_server.py`](./mcp_server.py):
```python
# Around line 19
router = ValkeyRouter()

# For custom connection
router = ValkeyRouter(
    host='custom-host',
    port=6380,
    db=1
)
```

### Valkey Memory Management
- Monitor with `get_index_stats()` → `Valkey memory` field
- Current usage: ~3.47GB with CPython indexed
- Clear old data: Restart Valkey or use `ingest_repo(clear_first=True)`

## Troubleshooting Configuration

### Issue: Server Not Available
**Symptoms**: Tools don't appear in Kilo Code
**Solutions**:
1. Check VS Code output panel for MCP errors
2. Verify Python virtual environment exists: `ls .venv/bin/python`
3. Test server manually: `.venv/bin/python mcp_server.py`
4. Restart VS Code
5. Check Kilo Code extension is enabled

### Issue: Timeout Errors
**Symptoms**: Operations fail with "Request timed out"
**Solutions**:
1. Increase timeout in config: `"timeout": 120`
2. Reduce operation scope (e.g., fewer files in batch_chaos_scan)
3. Run operations during low-activity periods
4. Consider splitting large operations

### Issue: Import Errors
**Symptoms**: Server fails to start with Python import errors
**Solutions**:
1. Verify PYTHONPATH includes project root
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Check virtual environment activation
4. Ensure all submodules are present

### Issue: Valkey Connection Refused
**Symptoms**: "Connection refused" or "Could not connect to Valkey"
**Solutions**:
1. Start Valkey: `valkey-server` or `redis-server`
2. Check Valkey is running: `valkey-cli ping` (should return PONG)
3. Verify port not blocked by firewall
4. Check Valkey bind address allows localhost

### Issue: Stale Configuration
**Symptoms**: Changes to mcp.json not reflected
**Solutions**:
1. Restart VS Code (Cmd/Ctrl + Q, reopen)
2. Reload window (Cmd/Ctrl + R)
3. Check file saved properly
4. Verify JSON syntax is valid

## Advanced Configuration

### Multiple Valkey Instances
For isolated projects:
```json
{
  "mcpServers": {
    "manifold-project-a": {
      "command": ".venv/bin/python",
      "args": ["mcp_server.py", "--db", "0"],
      "cwd": "/path/to/project-a/SEP-mcp",
      ...
    },
    "manifold-project-b": {
      "command": ".venv/bin/python",
      "args": ["mcp_server.py", "--db", "1"],
      "cwd": "/path/to/project-b/SEP-mcp",
      ...
    }
  }
}
```

### Custom Timeout Per Tool
Not directly supported, but can modify server code:
```python
# In mcp_server.py
@mcp.tool(timeout=180)  # 3 minutes
def ingest_repo(...):
    ...
```

### Environment Variables
Add to `env` section:
```json
"env": {
  "PYTHONPATH": ".",
  "VALKEY_HOST": "localhost",
  "VALKEY_PORT": "6379",
  "LOG_LEVEL": "INFO"
}
```

### Logging Configuration
For debugging, add to environment:
```json
"env": {
  "PYTHONPATH": ".",
  "MCP_LOG_LEVEL": "DEBUG"
}
```

## Backup and Migration

### Backup Configuration
```bash
# Backup global settings
cp ~/.config/Code/User/globalStorage/kilocode.kilo-code/settings/mcp_settings.json \
   ~/mcp_settings_backup.json

# Backup Valkey data
valkey-cli SAVE  # Creates dump.rdb
cp /var/lib/valkey/dump.rdb ~/valkey_backup_$(date +%Y%m%d).rdb
```

### Restore Configuration
```bash
# Restore global settings
cp ~/mcp_settings_backup.json \
   ~/.config/Code/User/globalStorage/kilocode.kilo-code/settings/mcp_settings.json

# Restore Valkey data
valkey-cli SHUTDOWN
cp ~/valkey_backup_20260222.rdb /var/lib/valkey/dump.rdb
valkey-server &
```

### Migration to New Machine
1. Copy project directory with `.venv`
2. Copy global MCP settings file
3. Install Valkey on new machine
4. Optionally: Copy Valkey dump.rdb or re-ingest

## Performance Tuning

### Increase Timeout for Large Repos
```json
"timeout": 180  // 3 minutes
```

### Optimize Valkey
```bash
# Edit /etc/valkey/valkey.conf
maxmemory 8gb
maxmemory-policy allkeys-lru
save ""  # Disable RDB if pure cache
```

### Reduce Index Scope
```python
# Only index source code, not tests
ingest_repo(root_dir="src", compute_chaos=True)
```

### Parallel Processing
Not currently supported, but could be added:
```python
# Feature request: Parallel chaos computation
batch_chaos_scan(pattern="*.py", workers=4)
```

## Security Considerations

### File Access
- Server runs with user's permissions
- Can read any file user can read
- No write access to source files (read-only indexing)
- Valkey writes to DB only

### Network Security
- Valkey on localhost (not exposed externally)
- No remote MCP connections
- All operations local to machine

### Data Privacy
- Code indexed in local Valkey instance
- No external API calls for core functionality
- Visualizations saved locally to `reports/`

## Maintenance Schedule

### Daily
- Monitor `get_index_stats()` for health
- Check Valkey memory usage

### Weekly
- Review chaos scores with `batch_chaos_scan()`
- Clean up temporary facts if needed

### Monthly
- Re-ingest codebase for consistency: `ingest_repo(clear_first=True)`
- Backup Valkey data
- Update dependencies: `pip install -U -r requirements.txt`

### Quarterly
- Review and update configuration
- Audit injected facts
- Clean up old visualization files

## Kilo Code Integration

### How Kilo Code Uses This Server

When you interact with me (Kilo Code), I automatically:

1. **Check index status** on workspace open
2. **Search code** when you ask about implementations
3. **Verify complexity** before suggesting changes
4. **Validate patterns** in AI-generated code
5. **Find examples** of similar code structures

### Teaching Kilo Code About Your Project

Use `inject_fact()` to teach me:
```python
inject_fact(
    "project_architecture",
    "This is a microservices architecture with 5 services: "
    "API Gateway, Auth Service, User Service, Payment Service, "
    "and Notification Service. All communication uses gRPC."
)

inject_fact(
    "coding_standard_error_handling",
    "Always use custom exception classes derived from AppError. "
    "Include context in exception messages. Log at ERROR level."
)
```

I'll remember these facts across sessions and apply them when helping you code.

## Verification Checklist

- [ ] Valkey running: `valkey-cli ping`
- [ ] Python venv exists: `ls .venv/bin/python`
- [ ] Dependencies installed: `pip list | grep mcp`
- [ ] Global config exists: `cat ~/.config/Code/User/globalStorage/kilocode.kilo-code/settings/mcp_settings.json`
- [ ] Server starts: `.venv/bin/python mcp_server.py` (if CLI mode exists)
- [ ] Tools visible in Kilo Code
- [ ] Index populated: Use `get_index_stats()`
- [ ] Watcher running: Use `start_watcher()`

## Support and Resources

### Documentation
- [`MCP_TOOL_GUIDE.md`](./MCP_TOOL_GUIDE.md) - Complete tool reference
- [`QUICK_REFERENCE.md`](./QUICK_REFERENCE.md) - Quick usage guide
- [`README.md`](./README.md) - Project overview

### Code References
- [`mcp_server.py`](./mcp_server.py) - Server implementation
- [`src/manifold/router.py`](./src/manifold/router.py) - Valkey integration
- [`src/manifold/sidecar.py`](./src/manifold/sidecar.py) - Chaos computation

### Testing
- [`scripts/tests/test_mcp_tools.py`](./scripts/tests/test_mcp_tools.py) - Tool tests
- Run tests: `pytest scripts/tests/`

---

**Status**: ✅ Configured globally and operational  
**Last Verified**: 2026-02-22  
**Next Review**: 2026-03-22
