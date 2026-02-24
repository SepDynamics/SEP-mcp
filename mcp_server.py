#!/usr/bin/env python3
"""Symbolic Chaos Proxy MCP Server – Structural Manifold Compression Control Plane.

This is the live nervous system for the tripartite architecture.
It exposes the exact symbolic-dynamics pipeline that predicts gravitational ejection
in the 3-body problem (MNRAS preprint 21 Feb 2026) and now detects architectural
collapse in codebases with sub-millisecond latency.

Signal-first pipeline (identical to the chaos proxy):
1. Rolling variance of byte-stream "kinetic energy"
2. Log scaling + Delta-Sigma 1-bit quantization
3. Symbolic state machine (LOW_FLUCTUATION / OSCILLATION / PERSISTENT_HIGH)
4. fluctuation_persistence = chaos score (PERSISTENT_HIGH fraction)
5. Entropy + coherence as secondary metrics
6. Hazard gating (collapse detection) on every retrieval

Tools exposed (20 total):
  Indexing & Monitoring:
    • ingest_repo          – stream-ingest repo into Valkey (text + sigs + chaos)
    • get_index_stats      – Valkey db health + doc count
    • start_watcher        – live filesystem watcher for IDE saves

  Search & Retrieval:
    • search_code          – keyword / regex search across indexed files
    • get_file             – read a single indexed file
    • list_indexed_files   – list indexed paths (glob filter)
    • search_by_structure  – find structurally similar files

  Structural Analysis:
    • compute_signature    – compress text to manifold signatures
    • get_file_signature   – get structural signature for a file
    • verify_snippet       – hazard-gated snippet verification

  Chaos Detection:
    • analyze_code_chaos   – full ChaosResult per file
    • batch_chaos_scan     – GPU-style batch validation
    • predict_structural_ejection – maintainability forecast
    • visualize_manifold_trajectory – 4-panel dashboard
    • cluster_codebase_structure – K-Means structural grouping

  Dependency & Risk:
    • analyze_blast_radius – AST-based impact analysis
    • compute_combined_risk – chaos × blast_radius ultimate risk
    • scan_critical_files  – ultimate risk assessment

  Working Memory:
    • inject_fact          – zero-shot fact injection into codebook
    • remove_fact          – remove injected facts from codebook

For comprehensive usage guide and workflows, see: MCP_TOOL_GUIDE.md
For quick start, see: README.md
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import zstandard as zstd
from fnmatch import fnmatch
from pathlib import Path
from typing import Annotated, Dict, List, Optional

from pydantic import Field

# ---------------------------------------------------------------------------
# Bootstrap – ensure local project modules are importable
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent
WORKSPACE_ROOT = Path(os.environ.get("MANIFOLD_WORKSPACE_ROOT", Path.cwd()))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Add chaos proxy kernel if present
CHAOS_PROXY_DIR = REPO_ROOT / "3body-chaos-proxy"
if CHAOS_PROXY_DIR.exists() and str(CHAOS_PROXY_DIR) not in sys.path:
    sys.path.insert(0, str(CHAOS_PROXY_DIR))


# The C++ extension (sep_quantum) lives in src/
_SRC_DIR = REPO_ROOT / "src"
if _SRC_DIR.exists() and str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

# ---------------------------------------------------------------------------
# MCP server init (lightweight – no torch / numpy yet)
# ---------------------------------------------------------------------------
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("SymbolicChaosProxy")

# ---------------------------------------------------------------------------
# Lazy singletons
# ---------------------------------------------------------------------------
_valkey_wm = None
_ast_analyzer = None


def _get_valkey():
    global _valkey_wm
    if _valkey_wm is None:
        from src.manifold.valkey_client import ValkeyWorkingMemory

        _valkey_wm = ValkeyWorkingMemory()
    return _valkey_wm


def _get_index_root() -> Path:
    """Get the root directory of the current index from Valkey metadata."""
    v = _get_valkey()
    if v.ping():
        meta_raw = v.r.get(META_KEY)
        if meta_raw:
            try:
                meta = json.loads(meta_raw)
                root = meta.get("root")
                if root:
                    return Path(root)
            except Exception:
                pass
    return WORKSPACE_ROOT


def _get_ast_analyzer():
    """Get or create the AST dependency analyzer singleton.

    The analyzer builds the dependency graph once and caches it.
    Call invalidate_ast_cache() to rebuild (e.g., after file changes).
    """
    global _ast_analyzer
    current_root = _get_index_root()
    if _ast_analyzer is None or _ast_analyzer.repo_root != current_root:
        from src.manifold.ast_deps import ASTDependencyAnalyzer

        _ast_analyzer = ASTDependencyAnalyzer(current_root)
        _ast_analyzer.build_dependency_graph()
        _ast_analyzer.analyze_all()
    return _ast_analyzer


def invalidate_ast_cache():
    """Invalidate the cached AST dependency graph.

    Call this when files are created/deleted/renamed to force a rebuild.
    """
    global _ast_analyzer
    _ast_analyzer = None


# ---------------------------------------------------------------------------
# Ingestion config
# ---------------------------------------------------------------------------
FILE_HASH_PREFIX = "manifold:file:"
META_KEY = "manifold:meta:ingest"
FILE_LIST_KEY = "manifold:file_list"

# Zstandard compressor
_zctx = zstd.ZstdCompressor(level=3)
_zdctx = zstd.ZstdDecompressor()


def _compress(data: bytes) -> bytes:
    return _zctx.compress(data)


def _decompress(data: bytes) -> bytes:
    return _zdctx.decompress(data)


EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    ".venv",
    ".venv-py313-bak",
    ".venv_mamba",
    "node_modules",
    "output",
    "build",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    "dist",
    "egg-info",
    ".eggs",
    "src/build",
    "reports",
}

EXCLUDE_PATTERNS = {
    "*.pyc",
    "*.pyo",
    "*.so",
    "*.o",
    "*.a",
    "*.dylib",
    "*.egg-info",
    ".DS_Store",
    "*.mp4",
    "*.webm",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.bmp",
    "*.ico",
    "*.wav",
    "*.mp3",
    "*.arrow",
    "*.safetensors",
    "*.pdf",
    "*.whl",
    "*.tar.gz",
    "*.zip",
}

# Binary extensions that pass _should_skip but shouldn't be stored as text.
# Everything else is treated as indexable text (manifold works on raw bytes).
BINARY_EXTENSIONS = {
    ".class",
    ".dll",
    ".exe",
    ".bin",
    ".dat",
    ".db",
    ".sqlite",
    ".pkl",
    ".pickle",
    ".npy",
    ".npz",
    ".h5",
    ".hdf5",
    ".wasm",
    ".dex",
    ".ttf",
    ".otf",
    ".woff",
    ".woff2",
    ".eot",
}

DEFAULT_MAX_BYTES = 512_000  # 512 KB per file cap


def _should_skip(path: Path) -> bool:
    """Return True if *path* should be excluded from ingest."""
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    name = path.name
    for pat in EXCLUDE_PATTERNS:
        if fnmatch(name, pat):
            return True
    return False


def _is_text(path: Path) -> bool:
    """Everything that passes _should_skip is text unless it's a known binary extension."""
    return path.suffix.lower() not in BINARY_EXTENSIONS


def _read_capped(path: Path, cap: int) -> bytes:
    with path.open("rb") as f:
        return f.read(cap)


# ---------------------------------------------------------------------------
# Signature helpers (lazy-loaded) – from original prototype
# ---------------------------------------------------------------------------
_encoder_ready = None


def _ensure_encoder():
    """Verify the local C++ byte_stream_manifold binary is available."""
    global _encoder_ready
    if _encoder_ready is not None:
        return _encoder_ready
    bin_path = Path(__file__).resolve().parent / "src/bin/byte_stream_manifold"
    _encoder_ready = bin_path.exists()
    return _encoder_ready


def _compute_sig(data: bytes, precision: int = 3) -> Optional[str]:
    """Compute a single structural signature for a ≥512-byte chunk."""
    if not _ensure_encoder():
        return None
    if len(data) < 512:
        return None
    from src.manifold.sidecar import encode_text

    text = data.decode("utf-8", errors="replace")
    res = encode_text(text, window_bytes=512, stride_bytes=384, precision=precision)
    if not res.windows:
        return None
    return res.windows[0].signature


# ---------------------------------------------------------------------------
# Core chaos helper (mirrors three_body_demo.py + gpu_batch_validation.py)
# ---------------------------------------------------------------------------
def _compute_chaos_result(raw: bytes) -> Optional[Dict]:
    """Run the exact same symbolic pipeline as the 3-body chaos proxy."""
    if len(raw) < 512:
        return None

    try:
        from src.manifold.sidecar import encode_text

        encoded = encode_text(
            raw.decode("utf-8", errors="replace")[:4096],
            window_bytes=512,
            stride_bytes=384,
            precision=3,
            use_native=True,
        )
    except Exception:
        return None

    windows = []
    for win in encoded.windows:
        windows.append(
            {
                "fluctuation_persistence": win.hazard,
                "entropy": win.entropy,
                "coherence": win.coherence,
                "collapse_detected": win.hazard >= 0.35,
            }
        )
    if not windows:
        return None

    avg_fp = sum(w["fluctuation_persistence"] for w in windows) / len(windows)
    avg_entropy = sum(w["entropy"] for w in windows) / len(windows)
    avg_coherence = sum(w["coherence"] for w in windows) / len(windows)

    return {
        "chaos_score": avg_fp,
        "entropy": avg_entropy,
        "coherence": avg_coherence,
        "collapse_risk": (
            "HIGH" if avg_fp >= 0.35 else "MODERATE" if avg_fp >= 0.15 else "LOW"
        ),
        "windows_analyzed": len(windows),
    }


# ===================================================================
# TOOL: ingest_repo (merged: sigs + chaos)
# ===================================================================
@mcp.tool()
def ingest_repo(
    root_dir: Annotated[
        str,
        Field(description="Directory to ingest relative to repo root (default '.')"),
    ] = ".",
    max_bytes_per_file: Annotated[
        int, Field(description="Maximum bytes to read per file (default 512 KB)")
    ] = DEFAULT_MAX_BYTES,
    clear_first: Annotated[
        bool, Field(description="Wipe all existing manifold keys before ingesting")
    ] = False,
    compute_chaos: Annotated[
        bool, Field(description="Also compute chaos profiles for each file")
    ] = True,
    lite: Annotated[
        bool,
        Field(
            description="Skip full chaos entropy generation on tests, docs, and binaries"
        ),
    ] = False,
) -> str:
    """Full symbolic-dynamics ingest of the repository.

    Every file is treated as a dynamical system.
    We extract the structural 'kinetic energy variance' and compute the
    exact chaos score used in the 3-body proxy.
    """
    v = _get_valkey()
    if not v.ping():
        return "❌ Valkey not reachable on localhost:6379."

    target = Path(root_dir)
    if not target.is_absolute():
        target = _get_index_root() / root_dir
    target = target.resolve()

    if not target.exists():
        return f"❌ Directory not found: {target}"

    if clear_first:
        for key in v.r.scan_iter("manifold:*"):
            v.r.delete(key)

    text_count = 0
    binary_count = 0
    total_bytes = 0
    sig_count = 0
    skipped = 0
    errors = []
    t0 = time.time()

    total_chaos = 0.0
    high_risk = 0

    pipe = v.r.pipeline(transaction=False)

    all_files = []
    for dirpath, dirnames, filenames in os.walk(str(target), followlinks=True):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for fname in filenames:
            all_files.append(Path(dirpath) / fname)
    all_files.sort()

    for path in all_files:
        if not path.is_file():
            continue
        if _should_skip(path):
            skipped += 1
            continue

        try:
            # Strictly constrain ingestion paths to relative structure for absolute system path requests
            rel = os.path.relpath(path, target)
        except ValueError:
            rel = str(path)

        try:
            raw = _read_capped(path, max_bytes_per_file)
        except Exception as exc:
            errors.append(f"{rel}: {exc}")
            continue

        if not raw:
            continue

        total_bytes += len(raw)

        hash_key = f"{FILE_HASH_PREFIX}{rel}"
        fields = {}

        if _is_text(path):
            fields["doc"] = _compress(raw)
            text_count += 1
        else:
            digest = hashlib.sha256(raw).hexdigest()
            if len(raw) <= 4096:
                fields["doc"] = raw.hex()
            else:
                fields["doc"] = f"[BINARY sha256={digest} bytes={len(raw)}]"
            binary_count += 1

        pipe.zadd(FILE_LIST_KEY, {rel: len(raw)})

        # Structural signature (from original prototype)
        if len(raw) >= 512:
            sig = _compute_sig(raw)
            if sig:
                fields["sig"] = sig
                sig_count += 1

        # Chaos profile (new expansion)
        if compute_chaos:
            skip_chaos = False
            if lite and (
                "test" in rel.lower()
                or path.suffix.lower() in {".md", ".txt", ".rst"}
                or not _is_text(path)
            ):
                skip_chaos = True

            if not skip_chaos:
                chaos = _compute_chaos_result(raw)
                if chaos:
                    fields["chaos"] = _compress(json.dumps(chaos).encode("utf-8"))
                    total_chaos += chaos["chaos_score"]
                    if chaos["collapse_risk"] == "HIGH":
                        high_risk += 1

        if fields:
            pipe.hset(hash_key, mapping=fields)

        if (text_count + binary_count) % 200 == 0:
            pipe.execute()
            pipe = v.r.pipeline(transaction=False)

    pipe.execute()

    elapsed = time.time() - t0
    avg_chaos = total_chaos / sig_count if sig_count > 0 else 0.0

    meta = {
        "text_files": text_count,
        "binary_files": binary_count,
        "total_bytes": total_bytes,
        "signatures": sig_count,
        "skipped": skipped,
        "errors": len(errors),
        "elapsed_s": round(elapsed, 2),
        "root": str(target),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "avg_chaos": avg_chaos,
        "high_risk_files": high_risk,
    }
    v.r.set(META_KEY, json.dumps(meta))

    err_report = ""
    if errors:
        err_report = f"\nFirst 5 errors:\n" + "\n".join(errors[:5])

    return (
        f"✅ Ingest complete in {elapsed:.1f}s\n"
        f"  Text files : {text_count}\n"
        f"  Binary files: {binary_count}\n"
        f"  Total bytes : {total_bytes:,}\n"
        f"  Signatures : {sig_count}\n"
        f"  Skipped    : {skipped}\n"
        f"  Errors     : {len(errors)}\n"
        f"  Avg chaos  : {avg_chaos:.3f}\n"
        f"  High-risk  : {high_risk}{err_report}"
    )


# ===================================================================
# TOOL: search_code
# ===================================================================
@mcp.tool()
def search_code(
    query: Annotated[
        str,
        Field(
            description="Search string or Python regex pattern to find in indexed files"
        ),
    ],
    max_results: Annotated[
        int, Field(description="Maximum number of matching files to return")
    ] = 20,
    file_pattern: Annotated[
        str,
        Field(description="Glob pattern to filter file paths (e.g. '*.py', 'src/*')"),
    ] = "*",
    case_sensitive: Annotated[
        bool, Field(description="Whether the search is case-sensitive")
    ] = False,
) -> str:
    """Search indexed codebase files by keyword or regex pattern.

    Scans all text documents stored in Valkey and returns matching
    file paths with surrounding context lines.
    """
    v = _get_valkey()
    if not v.ping():
        return "❌ Valkey not reachable."

    flags = 0 if case_sensitive else re.IGNORECASE
    try:
        pattern = re.compile(query, flags)
    except re.error:
        escaped = re.escape(query)
        pattern = re.compile(escaped, flags)

    results: List[str] = []
    scanned = 0

    keys = []
    rels = []
    for key in v.r.scan_iter(f"{FILE_HASH_PREFIX}*", count=500):
        rel = key[len(FILE_HASH_PREFIX) :]
        if not fnmatch(rel, file_pattern):
            continue
        keys.append(key)
        rels.append(rel)

    batch_size = 500
    for i in range(0, len(keys), batch_size):
        batch_keys = keys[i : i + batch_size]
        batch_rels = rels[i : i + batch_size]

        pipe = v.raw_r.pipeline(transaction=False)
        for key in batch_keys:
            pipe.hget(key.encode("utf-8"), b"doc")
        raw_docs = pipe.execute()

        for rel, raw in zip(batch_rels, raw_docs):
            if not raw:
                continue

            try:
                content_bytes = _decompress(raw)
                content = content_bytes.decode("utf-8", errors="replace")
            except Exception:
                # Fallback for uncompressed or binary strings
                content = (
                    raw.decode("utf-8", errors="replace")
                    if isinstance(raw, bytes)
                    else str(raw)
                )

            if content.startswith("[BINARY"):
                continue

            scanned += 1
            matches = list(pattern.finditer(content))
            if not matches:
                continue

            lines = content.split("\n")
            snippets = []
            seen_lines = set()
            for m in matches[:5]:
                line_start = content[: m.start()].count("\n")
                ctx_start = max(0, line_start - 2)
                ctx_end = min(len(lines), line_start + 3)
                for i in range(ctx_start, ctx_end):
                    if i not in seen_lines:
                        seen_lines.add(i)
                        prefix = ">>>" if i == line_start else "   "
                        display_line = lines[i].replace("❌", "✖")
                        snippets.append(f"  {prefix} L{i+1}: {display_line}")

            hit_text = "\n".join(snippets)
            results.append(
                f"📄 {rel}  ({len(matches)} match{'es' if len(matches)>1 else ''})\n{hit_text}"
            )
            if len(results) >= max_results:
                break
        if len(results) >= max_results:
            break

    if not results:
        return f"No matches found for '{query}'."

    output = [
        f"🔍 Found {len(results)} file(s) matching '{query}' (scanned {scanned}):\n"
    ]
    output.extend(results)
    return "\n".join(output)


# ===================================================================
# TOOL: get_file
# ===================================================================
@mcp.tool()
def get_file(
    path: Annotated[
        str,
        Field(
            description="File path relative to repo root (e.g. 'src/manifold/sidecar.py')"
        ),
    ],
) -> str:
    """Read a specific file from the Valkey index.

    Returns the full text content of the file as stored during ingest.
    Use list_indexed_files() first to discover available paths.
    """
    current_root = _get_index_root()
    path = os.path.relpath(path, current_root) if os.path.isabs(path) else path
    v = _get_valkey()
    if not v.ping():
        return "❌ Valkey not reachable."

    raw = v.raw_r.hget(f"{FILE_HASH_PREFIX}{path}", "doc")
    if raw is None:
        candidates = []
        for key in v.r.scan_iter(f"{FILE_HASH_PREFIX}*{Path(path).name}*", count=200):
            candidates.append(key[len(FILE_HASH_PREFIX) :])
        if candidates:
            suggestion = "\n".join(f"  • {c}" for c in candidates[:10])
            return f"❌ '{path}' not found. Did you mean:\n{suggestion}"
        return f"❌ '{path}' not found in the index."

    try:
        content_bytes = _decompress(raw)
        content = content_bytes.decode("utf-8", errors="replace")
    except Exception:
        content = (
            raw.decode("utf-8", errors="replace")
            if isinstance(raw, bytes)
            else str(raw)
        )

    lines = content.split("\n")
    numbered = "\n".join(f"{i+1:>5} | {line}" for i, line in enumerate(lines))
    return f"📄 {path} ({len(lines)} lines, {len(content)} chars):\n\n{numbered}"


# ===================================================================
# TOOL: list_indexed_files
# ===================================================================
@mcp.tool()
def list_indexed_files(
    pattern: Annotated[
        str,
        Field(
            description="Glob pattern to filter (e.g. '*.py', 'src/manifold/*', 'scripts/**')"
        ),
    ] = "*",
    max_results: Annotated[int, Field(description="Maximum paths to return")] = 200,
) -> str:
    """List files in the Valkey codebase index.

    Returns a newline-separated list of indexed file paths matching the pattern.
    """
    v = _get_valkey()
    if not v.ping():
        return "❌ Valkey not reachable."

    paths = []
    members = v.r.zrangebyscore(FILE_LIST_KEY, "-inf", "+inf", start=0, num=100000)
    if members:
        for m in members:
            if pattern == "*" or fnmatch(m, pattern):
                paths.append(m)
                if len(paths) >= max_results:
                    break
    else:
        for key in v.r.scan_iter(f"{FILE_HASH_PREFIX}*", count=500):
            rel = key[len(FILE_HASH_PREFIX) :]
            if pattern == "*" or fnmatch(rel, pattern):
                paths.append(rel)
                if len(paths) >= max_results:
                    break

    paths.sort()
    if not paths:
        return f"No indexed files match pattern '{pattern}'."

    return f"Indexed files ({len(paths)}):\n" + "\n".join(paths)


# ===================================================================
# TOOL: get_index_stats
# ===================================================================
@mcp.tool()
def get_index_stats() -> str:
    """Return statistics about the current Valkey codebase index.

    Shows documents, signatures, chaos profiles, memory usage, and last ingest time.
    """
    v = _get_valkey()
    if not v.ping():
        return "❌ Valkey not reachable."

    doc_count = 0
    sig_count = 0
    chaos_count = 0
    for key in v.r.scan_iter(f"{FILE_HASH_PREFIX}*", count=1000):
        doc_count += 1
        if v.r.hexists(key, "sig"):
            sig_count += 1
        if v.r.hexists(key, "chaos"):
            chaos_count += 1

    file_list_size = v.r.zcard(FILE_LIST_KEY) or 0
    db_size = v.r.dbsize()
    info = v.r.info("memory")
    mem_human = info.get("used_memory_human", "?")

    meta_raw = v.r.get(META_KEY)
    meta = json.loads(meta_raw) if meta_raw else {}

    return (
        f"📊 Codebase Index Stats\n"
        f"  Total Valkey keys  : {db_size}\n"
        f"  Indexed documents  : {doc_count}\n"
        f"  File list entries  : {file_list_size}\n"
        f"  Structural sigs   : {sig_count}\n"
        f"  Chaos profiles    : {chaos_count}\n"
        f"  Valkey memory      : {mem_human}\n"
        f"  Last ingest        : {meta.get('timestamp', 'never')}\n"
        f"  Last ingest root   : {meta.get('root', 'N/A')}\n"
        f"  Last text files    : {meta.get('text_files', 0)}\n"
        f"  Last binary files  : {meta.get('binary_files', 0)}\n"
        f"  Last total bytes   : {meta.get('total_bytes', 0):,}\n"
        f"  Last elapsed       : {meta.get('elapsed_s', 0)}s\n"
        f"  Avg chaos score    : {meta.get('avg_chaos', 0):.3f}\n"
        f"  High-risk files    : {meta.get('high_risk_files', 0)}\n"
        f"  Encoder available  : {_ensure_encoder()}"
    )


# ===================================================================
# TOOL: compute_signature
# ===================================================================
@mcp.tool()
def compute_signature(
    text: Annotated[
        str,
        Field(description="The raw text string to compress into manifold signatures"),
    ],
) -> str:
    """Compress text into structural manifold signatures.

    Slides a 512-byte window across the input and computes
    Coherence/Stability/Entropy/Hazard metrics for each window.
    """
    if not _ensure_encoder():
        return "❌ Native encoder (src/bin/byte_stream_manifold) not available. Please compile src/"

    from src.manifold.sidecar import encode_text

    encoded = encode_text(
        text,
        window_bytes=512,
        stride_bytes=384,
        precision=3,
        use_native=True,
    )
    unique_sigs = len(encoded.prototypes)
    bytes_before = encoded.original_bytes
    bytes_after = unique_sigs * 9
    ratio = (bytes_before / bytes_after) if bytes_after else 0.0

    return (
        f"✅ Compressed {bytes_before:,} bytes → {bytes_after} manifold bytes\n"
        f"  Compression ratio  : {ratio:.2f}×\n"
        f"  Unique signatures  : {unique_sigs}\n"
        f"  Total windows      : {len(encoded.windows)}\n"
        f"  Hazard threshold   : {encoded.hazard_threshold:.4f}"
    )


# ===================================================================
# TOOL: verify_snippet
# ===================================================================
@mcp.tool()
def verify_snippet(
    snippet: Annotated[
        str,
        Field(
            description="Text snippet to verify against the codebase index (must be ≥512 bytes)"
        ),
    ],
    coverage_threshold: Annotated[
        float, Field(description="Minimum safe coverage ratio (0.0-1.0, default 0.5)")
    ] = 0.5,
    scope: Annotated[
        str,
        Field(
            description="Glob pattern to constrain the index validation (e.g. 'src/*')"
        ),
    ] = "*",
) -> str:
    """Verify a snippet against the codebase manifold index.

    Checks whether a piece of text (e.g. AI-generated code) structurally
    matches patterns already present in the indexed codebase.
    """
    if not _ensure_encoder():
        return "❌ Native encoder not available."

    snippet_bytes = len(snippet.encode("utf-8"))
    if snippet_bytes < 512:
        return f"❌ Snippet too short ({snippet_bytes} bytes). Need ≥512."

    v = _get_valkey()
    index = v.get_or_build_index()
    if index is None:
        return "❌ No manifold index available. Run ingest_repo first."

    from src.manifold.sidecar import verify_snippet as _verify, ManifoldIndex

    if scope != "*":
        # Filter by subsetting signatures whose occurrences reference matching docs
        matching_docs = {p for p in index.documents if fnmatch(p, scope)}
        if not matching_docs:
            return f"❌ FAILED: No indexed files found matching scope '{scope}'."

        filtered_sigs = {}
        for sig, entry in index.signatures.items():
            if not isinstance(entry, dict):
                continue
            occs = entry.get("occurrences", [])
            filtered_occs = [
                o
                for o in occs
                if isinstance(o, dict) and o.get("doc_id") in matching_docs
            ]
            if filtered_occs:
                filtered_sigs[sig] = {**entry, "occurrences": filtered_occs}

        filtered_docs = {p: d for p, d in index.documents.items() if p in matching_docs}
        index = ManifoldIndex(
            meta=index.meta,
            signatures=filtered_sigs,
            documents=filtered_docs,
        )

    result = _verify(
        text=snippet,
        index=index,
        coverage_threshold=coverage_threshold,
        window_bytes=512,
        stride_bytes=384,
        precision=3,
        use_native=True,
    )

    status = "✅ VERIFIED" if result.verified else "❌ FAILED"
    return (
        f"Status: {status}\n"
        f"  Safe coverage   : {result.coverage*100:.2f}%\n"
        f"  Raw match ratio : {result.match_ratio*100:.2f}%\n"
        f"  Gated hits      : {result.gated_hits}/{result.total_windows}\n"
        f"  Matched docs    : {', '.join(result.matched_documents) if result.matched_documents else 'None'}"
    )


# ===================================================================
# TOOL: get_file_signature
# ===================================================================
@mcp.tool()
def get_file_signature(
    path: Annotated[
        str,
        Field(
            description="File path relative to repo root (e.g. 'src/manifold/sidecar.py')"
        ),
    ],
) -> str:
    """Get the structural manifold signature for a specific indexed file.

    Returns the c/s/e signature string computed from the first 512 bytes.
    """
    path = os.path.relpath(path, WORKSPACE_ROOT) if os.path.isabs(path) else path
    v = _get_valkey()
    if not v.ping():
        return "❌ Valkey not reachable."

    sig = v.r.hget(f"{FILE_HASH_PREFIX}{path}", "sig")
    if sig:
        return f"📐 {path} → signature: {sig}"

    # Try computing on the fly
    raw = v.raw_r.hget(f"{FILE_HASH_PREFIX}{path}", "doc")
    if not raw:
        return f"❌ '{path}' not in index."

    try:
        content_bytes = _decompress(raw)
    except Exception:
        content_bytes = raw if isinstance(raw, bytes) else str(raw).encode("utf-8")

    computed = _compute_sig(content_bytes)
    if computed:
        v.r.hset(f"{FILE_HASH_PREFIX}{path}", "sig", computed)
        return f"📐 {path} → signature: {computed} (freshly computed)"
    return f"❌ File too short or encoder unavailable for signature computation."


# ===================================================================
# TOOL: search_by_structure
# ===================================================================
@mcp.tool()
def search_by_structure(
    signature: Annotated[
        str, Field(description="Target signature like 'c0.418_s0.760_e0.957'")
    ],
    tolerance: Annotated[
        float, Field(description="Max per-component deviation (default 0.05)")
    ] = 0.05,
    max_results: Annotated[
        int, Field(description="Maximum number of similar files to return")
    ] = 20,
    scope: Annotated[
        str,
        Field(
            description="Glob pattern to limit the structural search (e.g. 'tests/*')"
        ),
    ] = "*",
) -> str:
    """Find files whose structural signature is close to the given one.

    Uses numeric proximity on the c/s/e components within *tolerance*.
    """
    m = re.match(r"c([\d.]+)_s([\d.]+)_e([\d.]+)", signature)
    if not m:
        return f"❌ Invalid signature format. Expected 'cX.XXX_sX.XXX_eX.XXX'."
    tc, ts, te = float(m.group(1)), float(m.group(2)), float(m.group(3))

    v = _get_valkey()
    if not v.ping():
        return "❌ Valkey not reachable."

    matches = []
    for key in v.r.scan_iter(f"{FILE_HASH_PREFIX}*", count=500):
        rel = key[len(FILE_HASH_PREFIX) :]
        if scope != "*" and not fnmatch(rel, scope):
            continue

        sig_val = v.r.hget(key, "sig")
        if not sig_val:
            continue
        sm = re.match(r"c([\d.]+)_s([\d.]+)_e([\d.]+)", sig_val)
        if not sm:
            continue
        sc, ss, se = float(sm.group(1)), float(sm.group(2)), float(sm.group(3))
        dist = max(abs(tc - sc), abs(ts - ss), abs(te - se))
        if dist <= tolerance:
            matches.append((dist, rel, sig_val))
            if len(matches) >= max_results * 3:
                break

    matches.sort()
    matches = matches[:max_results]

    if not matches:
        return f"No files within tolerance {tolerance} of {signature}."

    lines = [f"Files structurally similar to {signature} (±{tolerance}):"]
    for dist, rel, sv in matches:
        lines.append(f"  {sv}  Δ={dist:.4f}  {rel}")
    return "\n".join(lines)


# ===================================================================
# TOOL: start_watcher
# ===================================================================
_active_observer = None


@mcp.tool()
def start_watcher(
    watch_dir: Annotated[
        str,
        Field(description="Directory to monitor relative to repo root (default '.')"),
    ] = ".",
    max_bytes_per_file: Annotated[
        int, Field(description="Maximum bytes to read per file (default 512 KB)")
    ] = DEFAULT_MAX_BYTES,
) -> str:
    """Start a filesystem watcher that auto-ingests file saves into Valkey.

    Monitors the specified directory for file modifications and creations,
    automatically updating the Valkey index with new content and signatures.
    """
    global _active_observer
    if _active_observer is not None:
        return "✅ Watcher already running."

    v = _get_valkey()
    if not v.ping():
        return "❌ Valkey not reachable."

    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler
    except ImportError:
        return "❌ watchdog not installed. Run: pip install watchdog"

    target = _get_index_root() / watch_dir
    if not target.exists():
        return f"❌ Directory not found: {target}"

    cap = max_bytes_per_file

    class _Handler(FileSystemEventHandler):
        def _ingest(self, src_path: str) -> None:
            path = Path(src_path)
            if not path.is_file() or _should_skip(path):
                return
            try:
                rel = os.path.relpath(path, WORKSPACE_ROOT)
            except ValueError:
                return
            try:
                raw = _read_capped(path, cap)
                if not raw:
                    return
                vk = _get_valkey()
                hash_key = f"{FILE_HASH_PREFIX}{rel}"
                fields = {}

                if _is_text(path):
                    fields["doc"] = _compress(raw)
                else:
                    digest = hashlib.sha256(raw).hexdigest()
                    fields["doc"] = f"[BINARY sha256={digest} bytes={len(raw)}]"

                vk.r.zadd(FILE_LIST_KEY, {rel: len(raw)})
                if len(raw) >= 512:
                    sig = _compute_sig(raw)
                    if sig:
                        fields["sig"] = sig
                    # Also compute chaos profile on save
                    chaos = _compute_chaos_result(raw)
                    if chaos:
                        fields["chaos"] = _compress(json.dumps(chaos).encode("utf-8"))

                vk.r.hset(hash_key, mapping=fields)
            except Exception:
                pass

        def on_modified(self, event):
            if not event.is_directory:
                self._ingest(event.src_path)

        def on_created(self, event):
            if not event.is_directory:
                self._ingest(event.src_path)

        def on_deleted(self, event):
            if not event.is_directory:
                path = Path(event.src_path)
                try:
                    rel = os.path.relpath(path, _get_index_root())
                except ValueError:
                    return
                vk = _get_valkey()
                hash_key = f"{FILE_HASH_PREFIX}{rel}"
                vk.r.delete(hash_key)
                vk.r.zrem(FILE_LIST_KEY, rel)

    handler = _Handler()
    observer = Observer()
    observer.schedule(handler, str(target), recursive=True)
    observer.daemon = True
    observer.start()
    _active_observer = observer

    return f"✅ Watcher started for {target} (cap {cap} bytes)"


# ===================================================================
# TOOL: inject_fact
# ===================================================================
@mcp.tool()
def inject_fact(
    fact_id: Annotated[
        str,
        Field(
            description="Unique identifier for the fact (e.g. 'project_architecture_v2')"
        ),
    ],
    fact_text: Annotated[
        str, Field(description="The factual text to assimilate into the codebook")
    ],
) -> str:
    """Inject a new fact into the Working Memory codebook (zero-shot learning).

    Stores the fact in Valkey and invalidates the cached index so the next
    retrieval will incorporate the new knowledge.
    """
    v = _get_valkey()
    if not v.ping():
        return "❌ Valkey not reachable."

    rel = (
        os.path.relpath(fact_id, WORKSPACE_ROOT) if os.path.isabs(fact_id) else fact_id
    )
    payload = fact_text.encode("utf-8", errors="replace")
    v.raw_r.hset(
        f"{FILE_HASH_PREFIX}{rel}".encode("utf-8"), mapping={b"doc": _compress(payload)}
    )
    v.r.zadd(FILE_LIST_KEY, {rel: len(payload)})
    v.invalidate_index()
    return f"🚀 Fact '{fact_id}' injected into the Dynamic Semantic Codebook."


@mcp.tool()
def remove_fact(
    fact_id: Annotated[
        str, Field(description="Unique identifier for the fact to remove")
    ],
) -> str:
    """Remove a fact from the Working Memory codebook."""
    v = _get_valkey()
    if not v.ping():
        return "❌ Valkey not reachable."

    rel = (
        os.path.relpath(fact_id, WORKSPACE_ROOT) if os.path.isabs(fact_id) else fact_id
    )
    v.remove_document(rel)
    v.raw_r.delete(f"{FILE_HASH_PREFIX}{rel}".encode("utf-8"))
    v.r.zrem(FILE_LIST_KEY, rel)
    v.invalidate_index()
    return f"🗑️ Fact '{fact_id}' removed from the Dynamic Semantic Codebook."


# ===================================================================
# CHAOS EXPANSION TOOLS (new in this version)
# ===================================================================
def _get_dynamic_thresholds() -> dict[str, float]:
    """Dynamically compute structural thresholds from current index percentiles."""
    v = _get_valkey()
    import numpy as np

    hazards = []
    coherences = []
    entropies = []

    for key_bytes in v.raw_r.scan_iter(
        f"{FILE_HASH_PREFIX}*".encode("utf-8"), count=500
    ):
        try:
            raw_chaos = v.raw_r.hget(key_bytes, b"chaos")
            if raw_chaos:
                try:
                    js_bytes = _decompress(raw_chaos)
                    js_str = js_bytes.decode("utf-8", errors="replace")
                except Exception:
                    js_str = (
                        raw_chaos.decode("utf-8", errors="replace")
                        if isinstance(raw_chaos, bytes)
                        else str(raw_chaos)
                    )
                chaos = float(json.loads(js_str).get("chaos_score", 0.0))
                if chaos > 0.0:
                    hazards.append(chaos)

            raw_sig = v.raw_r.hget(key_bytes, b"sig")
            if raw_sig:
                parts = raw_sig.decode("utf-8", errors="replace").split("_")
                if len(parts) == 3:
                    coherences.append(float(parts[0][1:]))
                    entropies.append(float(parts[2][1:]))
        except Exception:
            pass

    res = {
        "chaos_low": 0.15,
        "chaos_high": 0.35,
        "coherence_low": 0.30,
        "coherence_high": 0.60,
        "entropy_low": 0.60,
        "entropy_high": 0.85,
    }

    if hazards:
        res["chaos_low"] = float(np.percentile(hazards, 33.3))
        res["chaos_high"] = float(np.percentile(hazards, 66.6))
    if coherences:
        res["coherence_low"] = float(np.percentile(coherences, 33.3))
        res["coherence_high"] = float(np.percentile(coherences, 66.6))
    if entropies:
        res["entropy_low"] = float(np.percentile(entropies, 33.3))
        res["entropy_high"] = float(np.percentile(entropies, 66.6))

    return res


@mcp.tool()
def analyze_code_chaos(
    path: Annotated[
        str, Field(description="File path relative to repo root (e.g. 'mcp_server.py')")
    ],
) -> str:
    """Return the full ChaosResult for any indexed file – identical to three_body_demo.py.

    Computes chaos score, entropy, coherence, and collapse risk from the
    structural byte-stream analysis.
    """
    current_root = _get_index_root()
    path = os.path.relpath(path, current_root) if os.path.isabs(path) else path
    v = _get_valkey()
    raw = v.raw_r.hget(f"{FILE_HASH_PREFIX}{path}", "doc")
    if not raw:
        return "❌ File not indexed."

    try:
        content_bytes = _decompress(raw)
        content_final_str = content_bytes.decode("utf-8", errors="replace")
    except Exception:
        content_final_str = (
            raw.decode("utf-8", errors="replace")
            if isinstance(raw, bytes)
            else str(raw)
        )

    raw_bytes = content_final_str.encode("utf-8", errors="replace")
    result = _compute_chaos_result(raw_bytes)
    if not result:
        return "❌ Could not compute chaos (file too short or kernel unavailable)."

    return f"""📈 Chaos Analysis for {path}
Chaos Score (fluctuation_persistence) : {result['chaos_score']:.3f}
Entropy                               : {result['entropy']:.3f}
Coherence                             : {result['coherence']:.3f}
Collapse Risk                         : {result['collapse_risk']}
Windows analyzed                      : {result['windows_analyzed']}
"""


@mcp.tool()
def batch_chaos_scan(
    pattern: Annotated[
        str,
        Field(description="Glob pattern to filter files (e.g. '*.py', 'src/*.cpp')"),
    ] = "*.py",
    max_files: Annotated[
        int, Field(description="Maximum number of highest-risk files to return")
    ] = 50,
    scope: Annotated[
        str, Field(description="Glob pattern to limit the chaos scan (e.g. 'core/*')")
    ] = "*",
) -> str:
    """Run the full GPU-style validation across the repo (like gpu_batch_validation.py).

    Returns files ranked by chaos score (highest risk first).
    """
    v = _get_valkey()
    if not v.ping():
        return "❌ Valkey not reachable."

    results = []
    keys = []
    rels = []
    for key in v.r.scan_iter(f"{FILE_HASH_PREFIX}*", count=500):
        rel = key[len(FILE_HASH_PREFIX) :]
        if pattern != "*" and not fnmatch(rel, pattern):
            continue
        if scope != "*" and not fnmatch(rel, scope):
            continue
        keys.append(key)
        rels.append(rel)

    batch_size = 500
    for i in range(0, len(keys), batch_size):
        batch_keys = keys[i : i + batch_size]
        batch_rels = rels[i : i + batch_size]

        pipe = v.raw_r.pipeline(transaction=False)
        for key in batch_keys:
            pipe.hget(key.encode("utf-8"), b"chaos")
        chaos_docs = pipe.execute()

        for rel, chaos_data in zip(batch_rels, chaos_docs):
            if chaos_data:
                try:
                    try:
                        js_bytes = _decompress(chaos_data)
                        js = js_bytes.decode("utf-8", errors="replace")
                    except Exception:
                        js = (
                            chaos_data.decode("utf-8", errors="replace")
                            if isinstance(chaos_data, bytes)
                            else str(chaos_data)
                        )
                    chaos = json.loads(js)
                    results.append((chaos["chaos_score"], rel, chaos))
                except json.JSONDecodeError:
                    pass

    results.sort(reverse=True)
    results = results[:max_files]

    if not results:
        return f"No chaos profiles found matching '{pattern}'."

    lines = [
        f"🔍 Batch Chaos Scan (Top {len(results)} highest risk files matching {pattern}):\n"
    ]
    for score, rel, chaos in results:
        risk = chaos.get("collapse_risk", "UNKNOWN")
        lines.append(f"  [{risk}] {score:.3f} | {rel}")

    return "\n".join(lines)


@mcp.tool()
def predict_structural_ejection(
    path: Annotated[
        str,
        Field(
            description="File path relative to repo root to analyze for ejection risk"
        ),
    ],
    horizon_days: Annotated[
        int, Field(description="Number of days to forecast into the future")
    ] = 30,
) -> str:
    """Predicts when a file will 'eject' (become unmaintainable) using the same macroscopic instability correlation as the 3-body paper.

    Uses the chaos score to estimate structural stability over time.
    """
    current_root = _get_index_root()
    path = os.path.relpath(path, current_root) if os.path.isabs(path) else path
    v = _get_valkey()
    chaos_data = v.raw_r.hget(f"{FILE_HASH_PREFIX}{path}", "chaos")
    if not chaos_data:
        return f"❌ No chaos profile for {path}. Run analyze_code_chaos first."

    try:
        try:
            js_bytes = _decompress(chaos_data)
            js = js_bytes.decode("utf-8", errors="replace")
        except Exception:
            js = (
                chaos_data.decode("utf-8", errors="replace")
                if isinstance(chaos_data, bytes)
                else str(chaos_data)
            )
        chaos = json.loads(js)
    except Exception:
        return f"❌ Failed to parse chaos profile for {path}."

    score = chaos["chaos_score"]

    thresholds = _get_dynamic_thresholds()
    chaos_high = thresholds["chaos_high"]
    chaos_low = thresholds["chaos_low"]

    if score >= chaos_high:
        days = max(1, int((1.0 - score) * 100))
        return f"⚠️ WARNING: {path} is in PERSISTENT_HIGH state (score: {score:.3f}).\nPredicted structural ejection in ~{days} days without refactoring."
    elif score >= chaos_low:
        return f"⚠️ {path} is in OSCILLATION state (score: {score:.3f}).\nMonitor for increasing complexity."
    else:
        return f"✅ {path} is in LOW_FLUCTUATION state (score: {score:.3f}).\nStructurally stable."


@mcp.tool()
def visualize_manifold_trajectory(
    path: Annotated[
        str, Field(description="File path relative to repo root to visualize")
    ],
) -> str:
    """Generates the exact 4-panel dashboard (physical reality colored by chaos score + scatter vs LLE analog + time series).

    Renders:
      Panel 1 (top-left):  Structural trajectory – byte offset vs coherence, colored by hazard (chaos score).
      Panel 2 (top-right): Chaos vs LLE analog – scatter of entropy vs hazard per window.
      Panel 3 (bottom-left): Time series – hazard, entropy, coherence over window index.
      Panel 4 (bottom-right): Symbolic state distribution – LOW / OSCILLATION / PERSISTENT_HIGH bar chart.

    Saves a PNG to reports/ and returns the metrics summary + file path.
    """
    current_root = _get_index_root()
    path = os.path.relpath(path, current_root) if os.path.isabs(path) else path

    v = _get_valkey()
    if not v.ping():
        return "❌ Valkey not reachable."

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    content_raw = v.raw_r.hget(f"{FILE_HASH_PREFIX}{path}", "doc")
    if not content_raw:
        return f"❌ File '{path}' not indexed. Run ingest_repo first."

    try:
        content_bytes = _decompress(content_raw)
        content_final_str = content_bytes.decode("utf-8", errors="replace")
    except Exception:
        content_final_str = (
            content_raw.decode("utf-8", errors="replace")
            if isinstance(content_raw, bytes)
            else str(content_raw)
        )

    # Encode the full file to get per-window metrics
    try:
        from src.manifold.sidecar import encode_text

        encoded = encode_text(
            content_final_str[:8192],  # cap at 8 KB for visualization
            window_bytes=512,
            stride_bytes=384,
            precision=3,
            use_native=True,
        )
    except Exception as exc:
        return f"❌ Could not encode '{path}' for visualization: {exc}"

    if not encoded.windows:
        return f"❌ No windows produced for '{path}' (file may be too short)."

    # Extract per-window metrics
    n = len(encoded.windows)
    hazards = np.array([w.hazard for w in encoded.windows])
    entropies = np.array([w.entropy for w in encoded.windows])
    coherences = np.array([w.coherence for w in encoded.windows])
    byte_starts = np.array([w.byte_start for w in encoded.windows])

    # Classify symbolic states
    thresholds = _get_dynamic_thresholds()
    chaos_high = thresholds["chaos_high"]
    chaos_low = thresholds["chaos_low"]

    states = []
    for h in hazards:
        if h >= chaos_high:
            states.append("PERSISTENT_HIGH")
        elif h >= chaos_low:
            states.append("OSCILLATION")
        else:
            states.append("LOW_FLUCTUATION")

    state_counts = {
        "LOW_FLUCTUATION": states.count("LOW_FLUCTUATION"),
        "OSCILLATION": states.count("OSCILLATION"),
        "PERSISTENT_HIGH": states.count("PERSISTENT_HIGH"),
    }

    # Compute aggregate stats
    avg_hazard = float(np.mean(hazards))
    avg_entropy = float(np.mean(entropies))
    avg_coherence = float(np.mean(coherences))
    max_hazard = float(np.max(hazards))

    # --- Build 4-panel figure ---
    fig = plt.figure(figsize=(14, 10))
    # We use gridspec or manual add_subplot to mix 2D and 3D axes
    ax1 = fig.add_subplot(2, 2, 1)  # Top-Left (2D Scatter)
    ax2 = fig.add_subplot(2, 2, 2)  # Top-Right (2D Hexbin)
    ax3 = fig.add_subplot(2, 2, 3, projection="3d")  # Bottom-Left (3D Scatter)
    ax4 = fig.add_subplot(2, 2, 4)  # Bottom-Right (2D Hexbin)

    fig.suptitle(
        f"Structural Manifold Phase Space — {path}\n"
        f"(Windows={n}, Avg Chaos={avg_hazard:.3f}, "
        f"Avg Entropy={avg_entropy:.3f}, Avg Coherence={avg_coherence:.3f})",
        fontsize=13,
        fontweight="bold",
    )

    # Color map for chaos
    cmap = plt.cm.RdYlGn_r  # Red = high chaos, Green = low

    # Panel 1 (top-left): Structural trajectory – byte position vs coherence
    sc1 = ax1.scatter(
        byte_starts,
        coherences,
        c=hazards,
        cmap=cmap,
        s=60,
        edgecolors="k",
        linewidth=0.5,
        vmin=0,
        vmax=0.5,
    )
    ax1.set_xlabel("Byte Offset", fontsize=10)
    ax1.set_ylabel("Coherence", fontsize=10)
    ax1.set_title("Physical Evolution (Byte Offset vs Coherence)", fontsize=11)
    ax1.axhline(
        y=np.mean(coherences),
        color="gray",
        linestyle="--",
        alpha=0.5,
        label=f"mean={avg_coherence:.3f}",
    )
    ax1.legend(fontsize=8)
    fig.colorbar(sc1, ax=ax1, label="Hazard (Chaos Score)")

    # Panel 2 (top-right): Chaos Volumetric Distribution
    hb2 = ax2.hexbin(
        entropies,
        hazards,
        gridsize=25,
        cmap="Blues",  # Density map
        mincnt=1,
        edgecolors="none",
    )
    ax2.set_xlabel("Entropy", fontsize=10)
    ax2.set_ylabel("Hazard (Chaos Score)", fontsize=10)
    ax2.set_title("Manifold Attractors (Probability Density)", fontsize=11)
    cb2 = fig.colorbar(hb2, ax=ax2, label="Window Count (Density)")
    cb2.ax.tick_params(labelsize=8)

    # Panel 3 (bottom-left): 3D Phase Space Trajectory
    # Plot the temporal evolution in Phase Space
    sc3 = ax3.scatter(
        coherences,
        entropies,
        hazards,
        c=byte_starts,  # Color by time/offset
        cmap="cool",  # Cyan/Magenta conveys temporal progression well
        s=30,
        alpha=0.8,
        edgecolors="k",
        linewidth=0.2,
    )
    # Add a thin line to connect the dots in chronological order
    ax3.plot(
        coherences,
        entropies,
        hazards,
        color="gray",
        linewidth=0.5,
        alpha=0.5,
    )
    ax3.set_xlabel("Coherence (C)", fontsize=9)
    ax3.set_ylabel("Entropy (E)", fontsize=9)
    ax3.set_zlabel("Hazard (Z)", fontsize=9)
    ax3.set_title("3D Phase Space Trajectory (Time-colored)", fontsize=11)

    # Adjust 3D pane viewing angle slightly for better visibility
    ax3.view_init(elev=20, azim=45)
    cb3 = fig.colorbar(sc3, ax=ax3, label="Time (Byte Offset)", pad=0.1)
    cb3.ax.tick_params(labelsize=8)

    # Panel 4 (bottom-right): Heatmap of Coherence vs Entropy colored by Chaos
    # Create a hexbin plot: x=coherence, y=entropy, color=hazard
    hb = ax4.hexbin(
        coherences,
        entropies,
        C=hazards,
        gridsize=25,
        cmap="magma_r",  # Dark/Red for high hazard, light for low
        reduce_C_function=np.mean,
        edgecolors="none",
        mincnt=1,
    )
    ax4.set_xlabel("Coherence", fontsize=10)
    ax4.set_ylabel("Entropy", fontsize=10)
    ax4.set_title("Chaos", fontsize=11)

    # Add a colorbar specifically for the hexbin to show the chaos range
    cb = fig.colorbar(hb, ax=ax4, label="Mean Hazard (Chaos Score)")
    cb.ax.tick_params(labelsize=8)

    plt.tight_layout(rect=[0, 0, 1, 0.93])

    # Save to reports/
    current_root = _get_index_root()
    report_dir = current_root / "reports"
    report_dir.mkdir(exist_ok=True)
    safe_name = re.sub(r"[^\w.]", "_", path)
    out_path = report_dir / f"manifold_trajectory_{safe_name}.png"
    fig.savefig(str(out_path), dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Build text summary
    collapse_risk = (
        "HIGH"
        if avg_hazard >= chaos_high
        else "MODERATE" if avg_hazard >= chaos_low else "LOW"
    )

    return (
        f"📊 4-Panel Manifold Dashboard saved to: {out_path.relative_to(current_root)}\n\n"
        f"  File                : {path}\n"
        f"  Windows analyzed    : {n}\n"
        f"  Avg Chaos Score     : {avg_hazard:.3f}\n"
        f"  Max Chaos Score     : {max_hazard:.3f}\n"
        f"  Avg Entropy         : {avg_entropy:.3f}\n"
        f"  Avg Coherence       : {avg_coherence:.3f}\n"
        f"  Collapse Risk       : {collapse_risk}\n\n"
        f"  Symbolic States:\n"
        f"    LOW_FLUCTUATION   : {state_counts['LOW_FLUCTUATION']}\n"
        f"    OSCILLATION       : {state_counts['OSCILLATION']}\n"
        f"    PERSISTENT_HIGH   : {state_counts['PERSISTENT_HIGH']}\n\n"
        f"  Dashboard panels:\n"
        f"    1. Physical Evolution (Byte Offset vs Coherence)\n"
        f"    2. Manifold Attractors (2D Probability Density: Entropy vs Hazard)\n"
        f"    3. 3D Phase Space Trajectory (C, E, Hazard colored by Time)\n"
        f"    4. Structural Phase Space (Coherence vs Entropy branches colored by Hazard)"
    )


# ===================================================================
# TOOL: cluster_codebase_structure
# ===================================================================
@mcp.tool()
def cluster_codebase_structure(
    pattern: Annotated[
        str,
        Field(
            description="Glob pattern to constrain the files to cluster (e.g. '*.py')"
        ),
    ] = "*",
    n_clusters: Annotated[
        int, Field(description="Number of physical structural groups to form")
    ] = 5,
) -> str:
    """Cluster codebase files into "obscure groupings" based on their structural signatures.

    Uses K-Means clustering in the Structural Phase Space (Coherence vs Entropy)
    to group files with similar physical layouts and complexities. This corresponds
    directly to the physical clusters seen in the `visualize_manifold_trajectory`
    heatmap dashboard.
    """
    v = _get_valkey()
    if not v.ping():
        return "❌ Valkey not reachable."

    import numpy as np

    try:
        import faiss
    except ImportError:
        return "❌ faiss is required for clustering (run: pip install faiss-cpu)."

    vectors = []
    file_metas = []

    for key_bytes in v.raw_r.scan_iter(
        f"{FILE_HASH_PREFIX}*".encode("utf-8"), count=500
    ):
        try:
            key_str = key_bytes.decode("utf-8")
            rel_path = key_str[len(FILE_HASH_PREFIX) :]
            if pattern != "*" and not fnmatch(rel_path, pattern):
                continue

            raw_sig = v.raw_r.hget(key_bytes, b"sig")
            raw_chaos = v.raw_r.hget(key_bytes, b"chaos")

            if not raw_sig:
                continue

            sig_str = raw_sig.decode("utf-8", errors="replace")
            # Parse 'cX.XXX_sX.XXX_eX.XXX'
            parts = sig_str.split("_")
            c = float(parts[0][1:])
            s = float(parts[1][1:])
            e = float(parts[2][1:])

            chaos = 0.0
            if raw_chaos:
                try:
                    js_bytes = _decompress(raw_chaos)
                    js = js_bytes.decode("utf-8", errors="replace")
                except Exception:
                    js = (
                        raw_chaos.decode("utf-8", errors="replace")
                        if isinstance(raw_chaos, bytes)
                        else str(raw_chaos)
                    )
                try:
                    chaos_data = json.loads(js)
                    chaos = float(chaos_data.get("chaos_score", 0.0))
                except json.JSONDecodeError:
                    pass

            # We cluster primarily on Coherence and Entropy (matching the 4th chart)
            vectors.append([c, e])
            file_metas.append((rel_path, c, s, e, chaos))
        except Exception:
            pass

    if not vectors:
        return f"❌ No structural signatures found matching pattern '{pattern}'."

    n_samples = len(vectors)
    k = min(n_clusters, n_samples)
    if k < 2:
        return (
            f"Not enough files ({n_samples}) to form multiple clusters.\n"
            f"Found: {file_metas[0][0]}"
        )

    X = np.array(vectors, dtype=np.float32)

    # L2 normalized K-Means clustering using Faiss
    kmeans = faiss.Kmeans(d=2, k=k, niter=20, verbose=False)
    kmeans.train(X)
    distances, labels = kmeans.index.search(X, 1)

    # Group files by assigned cluster
    clusters = {i: [] for i in range(k)}
    for row_idx, cluster_idx in enumerate(labels.flatten()):
        clusters[int(cluster_idx)].append(file_metas[row_idx])

    output = [f"🧠 Structural Codebase Clusters (k={k}, files={n_samples})"]
    output.append(f"Matching pattern: '{pattern}'\n")

    thresholds = _get_dynamic_thresholds()
    chaos_high = thresholds["chaos_high"]
    coherence_high = thresholds["coherence_high"]
    coherence_low = thresholds["coherence_low"]
    entropy_high = thresholds["entropy_high"]
    entropy_low = thresholds["entropy_low"]

    for clus_id in range(k):
        members = clusters[clus_id]
        if not members:
            continue

        # Sort members by chaos (highest first)
        members.sort(key=lambda x: x[4], reverse=True)

        avg_c = np.mean([m[1] for m in members])
        avg_e = np.mean([m[3] for m in members])
        avg_chaos = np.mean([m[4] for m in members])

        # Extract dominant file extensions and directories for heuristic labeling
        import collections

        extensions = [Path(m[0]).suffix for m in members if Path(m[0]).suffix]
        dirs = [Path(m[0]).parent.name for m in members if Path(m[0]).parent.name]

        ext_counts = collections.Counter(extensions)
        dir_counts = collections.Counter(dirs)

        top_ext = f"({ext_counts.most_common(1)[0][0]}) " if ext_counts else ""
        top_dir = f"[{dir_counts.most_common(1)[0][0]}] " if dir_counts else ""

        # Attempt to label the cluster heuristically based on the feature space
        if avg_chaos > chaos_high:
            label = f"{top_dir}{top_ext}HIGH-CHAOS (Complex/Unstable)"
        elif avg_e > entropy_high and avg_c < coherence_low:
            label = f"{top_dir}{top_ext}DENSE/ENTROPIC (Data Algorithms/Math)"
        elif avg_e < entropy_low:
            label = f"{top_dir}{top_ext}SPARSE (Boilerplate/Configs)"
        elif avg_c > coherence_high:
            label = f"{top_dir}{top_ext}HIGH-COHERENCE (Linear/Simple)"
        else:
            label = f"{top_dir}{top_ext}MIXED-FLUCTUATION (Standard Code)"

        output.append(f"=== Cluster {clus_id + 1}: {label} ===")
        output.append(
            f"  Size: {len(members)} files | Avg Chaos: {avg_chaos:.3f} | "
            f"Centroid (C: {avg_c:.3f}, E: {avg_e:.3f})"
        )

        # Display top 10 members as representatives
        for file_path, c, s, e, chaos in members[:10]:
            output.append(f"    {chaos:.3f} | {file_path:<50} (c={c:.3f}, e={e:.3f})")

        if len(members) > 10:
            output.append(f"    ... and {len(members) - 10} more files")
        output.append("")

    return "\n".join(output)


@mcp.tool()
def analyze_blast_radius(
    path: Annotated[
        str,
        Field(description="File path relative to repo root"),
    ],
) -> str:
    """Analyze the blast radius of a file.

    Shows how many files would be impacted if this file were changed.
    Uses AST analysis to trace import dependencies.
    """
    current_root = _get_index_root()
    path = os.path.relpath(path, current_root) if os.path.isabs(path) else path

    try:
        # Use cached AST analyzer singleton
        analyzer = _get_ast_analyzer()

        dep_info = analyzer.get_dependency_info(path)
        if not dep_info:
            return f"❌ File not found or not a Python file: '{path}'"

        blast_radius = dep_info.blast_radius
        depth = dep_info.depth
        is_core = dep_info.is_core

        # Get dependency tree
        dep_tree = analyzer.visualize_dependencies(path, max_depth=2)

        return f"""💥 Blast Radius Analysis for {path}

Blast Radius     : {blast_radius} files
Dependency Depth : {depth} levels
Is Core Module   : {"Yes" if is_core else "No"}
Direct Imports   : {len(dep_info.imports)}
Imported By      : {len(dep_info.imported_by)}

Impact Assessment:
  {_get_blast_radius_interpretation(blast_radius)}

Dependency Tree (2 levels):
{dep_tree}

Imports:
  {', '.join(sorted(dep_info.imports)[:10]) if dep_info.imports else 'None'}
  {f'... and {len(dep_info.imports) - 10} more' if len(dep_info.imports) > 10 else ''}

Imported By:
  {', '.join(sorted(dep_info.imported_by)[:10]) if dep_info.imported_by else 'None'}
  {f'... and {len(dep_info.imported_by) - 10} more' if len(dep_info.imported_by) > 10 else ''}
"""
    except Exception as e:
        return f"❌ Error analyzing blast radius: {str(e)}"


@mcp.tool()
def compute_combined_risk(
    path: Annotated[
        str,
        Field(description="File path relative to repo root"),
    ],
) -> str:
    """Compute combined risk score = chaos × blast_radius.

    This is the ultimate metric for identifying the most critical files to refactor.
    """
    current_root = _get_index_root()
    path = os.path.relpath(path, current_root) if os.path.isabs(path) else path

    # Get chaos score
    v = _get_valkey()
    raw_chaos = v.raw_r.hget(f"{FILE_HASH_PREFIX}{path}", "chaos")
    if not raw_chaos:
        return f"❌ No chaos data for '{path}'. Run ingest_repo first."

    try:
        chaos_json = _decompress(raw_chaos).decode("utf-8")
        chaos_data = json.loads(chaos_json)
        chaos_score = chaos_data["chaos_score"]
    except Exception:
        return f"❌ Could not parse chaos data for '{path}'."

    # Get blast radius (using cached AST analyzer)
    try:
        dep_analyzer = _get_ast_analyzer()
        dep_info = dep_analyzer.get_dependency_info(path)
        blast_radius = dep_info.blast_radius if dep_info else 0
    except Exception:
        blast_radius = 0

    # Compute combined risk
    combined, risk_level = dep_analyzer.compute_combined_score(
        chaos_score, blast_radius
    )

    return f"""⚠️ Combined Risk Analysis for {path}

Components:
  Chaos Score      : {chaos_score:.3f} ({chaos_data['collapse_risk']} complexity)
  Blast Radius     : {blast_radius} files

Combined Risk Score: {combined:.3f}
Risk Level         : {risk_level}

Formula:
  combined = 0.6 × chaos + 0.4 × blast_radius
  combined = 0.6 × {chaos_score:.3f} + 0.4 × {blast_radius/50:.3f}
  combined = {combined:.3f}

Risk Levels:
  [CRITICAL] ≥0.40 : Immediate refactoring required
  [HIGH]     ≥0.30 : Schedule refactoring within sprint
  [MODERATE] ≥0.20 : Monitor and consider refactoring
  [LOW]      <0.20 : Acceptable risk

Recommendation:
  {_get_combined_risk_recommendation(combined, chaos_score, blast_radius)}
"""


@mcp.tool()
def scan_critical_files(
    pattern: Annotated[
        str,
        Field(description="Glob pattern to filter files (e.g. '*.py')"),
    ] = "*.py",
    max_files: Annotated[
        int, Field(description="Maximum files to return (default 20)")
    ] = 20,
) -> str:
    """Scan for critical files with high combined risk (chaos × blast_radius).

    This identifies the most dangerous files in the codebase.
    """
    v = _get_valkey()
    if not v.ping():
        return "❌ Valkey not reachable."

    # Get chaos scores
    chaos_data = {}
    keys = []
    rels = []
    for key in v.r.scan_iter(f"{FILE_HASH_PREFIX}*", count=500):
        rel = key[len(FILE_HASH_PREFIX) :]
        if pattern != "*" and not fnmatch(rel, pattern):
            continue
        keys.append(key)
        rels.append(rel)

    batch_size = 500
    for i in range(0, len(keys), batch_size):
        batch_keys = keys[i : i + batch_size]
        batch_rels = rels[i : i + batch_size]

        pipe = v.raw_r.pipeline(transaction=False)
        for key in batch_keys:
            pipe.hget(key.encode("utf-8"), b"chaos")
        chaos_docs = pipe.execute()

        for rel, chaos_bytes in zip(batch_rels, chaos_docs):
            if chaos_bytes:
                try:
                    js = _decompress(chaos_bytes).decode("utf-8")
                    chaos = json.loads(js)
                    chaos_data[rel] = chaos["chaos_score"]
                except Exception:
                    pass

    # Get blast radius (using cached AST analyzer)
    try:
        dep_analyzer = _get_ast_analyzer()
    except Exception as e:
        return f"❌ Error analyzing dependencies: {str(e)}"

    # Sort by chaos first (chaos is ~60% of score)
    sorted_chaos = sorted(chaos_data.items(), key=lambda x: x[1], reverse=True)
    candidate_list = sorted_chaos[: max_files * 5]  # Top candidates based on chaos

    # Compute combined risks
    critical_files = []
    for file_path, chaos in candidate_list:
        dep_info = dep_analyzer.get_dependency_info(file_path)
        blast_radius = dep_info.blast_radius if dep_info else 0

        combined, risk_level = dep_analyzer.compute_combined_score(chaos, blast_radius)

        critical_files.append((file_path, combined, risk_level, chaos, blast_radius))

    # Sort by combined risk descending
    critical_files.sort(key=lambda x: x[1], reverse=True)
    critical_files = critical_files[:max_files]

    if not critical_files:
        return "No critical files found."

    lines = [f"⚠️ Critical Files (Top {len(critical_files)}):\n"]
    for file_path, combined, risk_level, chaos, blast in critical_files:
        lines.append(f"  [{risk_level:>8}] {combined:.3f} | {file_path}")
        lines.append(f"             chaos={chaos:.3f}, blast={blast:>2}")

    return "\n".join(lines)


# Helper functions for recommendations
def _get_blast_radius_interpretation(blast_radius: int) -> str:
    """Generate interpretation of blast radius."""
    if blast_radius >= 20:
        return (
            f"VERY HIGH IMPACT ({blast_radius} files). This is a core module.\n"
            "  Changes here will ripple through the entire codebase.\n"
            "  Requires careful coordination and comprehensive testing."
        )
    elif blast_radius >= 10:
        return (
            f"HIGH IMPACT ({blast_radius} files). Important integration point.\n"
            "  Changes will affect multiple subsystems.\n"
            "  Ensure thorough testing and communication."
        )
    elif blast_radius >= 5:
        return (
            f"MODERATE IMPACT ({blast_radius} files). Localized but not isolated.\n"
            "  Changes will affect several files.\n"
            "  Standard testing procedures apply."
        )
    else:
        return (
            f"LOW IMPACT ({blast_radius} files). Relatively isolated.\n"
            "  Changes are localized and easier to validate."
        )


def _get_combined_risk_recommendation(
    combined: float, chaos: float, blast_radius: int
) -> str:
    """Generate recommendation based on combined risk."""
    if combined >= 0.40:
        return (
            "CRITICAL RISK. This file represents a severe technical debt hotspot.\n"
            f"  • Complex ({chaos:.2f}) + Wide impact ({blast_radius} files)\n"
            "  Action: Immediate refactoring session. Break into smaller modules.\n"
            "  Consider: Feature freeze until stabilization complete."
        )
    elif combined >= 0.30:
        return (
            "HIGH RISK. This file needs attention soon.\n"
            f"  • Complexity: {chaos:.2f}, Blast radius: {blast_radius}\n"
            "  Action: Schedule refactoring in current/next sprint.\n"
            "  Consider: Add comprehensive tests before refactoring."
        )
    elif combined >= 0.20:
        return (
            "MODERATE RISK. Monitor this file closely.\n"
            f"  • Complexity: {chaos:.2f}, Blast radius: {blast_radius}\n"
            "  Action: Add to technical debt backlog.\n"
            "  Consider: Improve documentation and test coverage."
        )
    else:
        return (
            "LOW RISK. This file is in acceptable condition.\n"
            "  Continue normal maintenance practices."
        )


# ===================================================================
# Entry point
# ===================================================================
def main():
    print(
        "🚀 Symbolic Chaos Proxy MCP Server started – ready for orbital insertion.",
        file=sys.stderr,
    )
    mcp.run()


if __name__ == "__main__":
    main()
