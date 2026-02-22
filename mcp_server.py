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

Tools exposed (merged from prototype + chaos expansion):
  • ingest_repo          – stream-ingest repo into Valkey (text + sigs + chaos)
  • search_code          – keyword / regex search across indexed files
  • get_file             – read a single indexed file
  • list_indexed_files   – list indexed paths (glob filter)
  • get_index_stats      – Valkey db health + doc count
  • compute_signature    – compress text to manifold signatures
  • verify_snippet       – hazard-gated snippet verification
  • get_file_signature   – get structural signature for a file
  • search_by_structure  – find structurally similar files
  • start_watcher        – live filesystem watcher for IDE saves
  • inject_fact          – zero-shot fact injection into codebook
  • analyze_code_chaos   – full ChaosResult per file
  • batch_chaos_scan     – GPU-style batch validation
  • predict_structural_ejection – maintainability forecast
  • visualize_manifold_trajectory – 4-panel dashboard
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
WORKSPACE_ROOT = Path.cwd().resolve()
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


def _get_valkey():
    global _valkey_wm
    if _valkey_wm is None:
        from src.manifold.valkey_client import ValkeyWorkingMemory

        _valkey_wm = ValkeyWorkingMemory()
    return _valkey_wm


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

TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
    ".ini",
    ".cfg",
    ".rst",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".cu",
    ".sh",
    ".bash",
    ".zsh",
    ".fish",
    ".makefile",
    ".cmake",
    ".tex",
    ".bib",
    ".bst",
    ".cls",
    ".sty",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".xml",
    ".csv",
    ".tsv",
    ".sql",
    ".r",
    ".R",
    ".go",
    ".rs",
    ".java",
    ".scala",
    ".kt",
    ".swift",
    ".rb",
    ".pl",
    ".pm",
    ".lua",
    ".zig",
    ".nim",
    ".gitignore",
    ".dockerignore",
    ".editorconfig",
    ".jsonl",
    ".ndjson",
    ".env",
    ".cff",
}

TEXT_FILENAMES = {
    "Makefile",
    "Dockerfile",
    "LICENSE",
    "Procfile",
    "Gemfile",
    "Rakefile",
    "Vagrantfile",
    ".gitignore",
    ".dockerignore",
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
    if path.name in TEXT_FILENAMES:
        return True
    return path.suffix.lower() in TEXT_EXTENSIONS


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

    target = WORKSPACE_ROOT / root_dir
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
            rel = str(path.resolve().relative_to(WORKSPACE_ROOT))
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

    for key in v.r.scan_iter(f"{FILE_HASH_PREFIX}*", count=500):
        rel = key[len(FILE_HASH_PREFIX) :]
        if not fnmatch(rel, file_pattern):
            continue

        raw = v.raw_r.hget(key, "doc")
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
                    snippets.append(f"  {prefix} L{i+1}: {lines[i]}")

        hit_text = "\n".join(snippets)
        results.append(
            f"📄 {rel}  ({len(matches)} match{'es' if len(matches)>1 else ''})\n{hit_text}"
        )
        if len(results) >= max_results:
            break

    if not results:
        return f"No matches found for '{query}' (scanned {scanned} files, pattern='{file_pattern}')."

    header = f"Found {len(results)} file(s) matching '{query}' (scanned {scanned}):\n\n"
    return header + "\n\n".join(results)


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
    path = path.replace(str(WORKSPACE_ROOT) + "/", "").lstrip("/")
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

    from src.manifold.sidecar import verify_snippet as _verify

    docs = index.documents
    if scope != "*":
        filtered_docs = {}
        for path, doc_content in docs.items():
            if fnmatch(path, scope):
                filtered_docs[path] = doc_content

        if not filtered_docs:
            return f"❌ FAILED: No indexed files found matching scope '{scope}'."

        from src.manifold.sidecar import build_index

        index = build_index(filtered_docs)

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
    path = path.replace(str(WORKSPACE_ROOT) + "/", "").lstrip("/")
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

    target = WORKSPACE_ROOT / watch_dir
    if not target.exists():
        return f"❌ Directory not found: {target}"

    cap = max_bytes_per_file

    class _Handler(FileSystemEventHandler):
        def _ingest(self, src_path: str) -> None:
            path = Path(src_path)
            if not path.is_file() or _should_skip(path):
                return
            try:
                rel = str(path.relative_to(WORKSPACE_ROOT))
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
                    rel = str(path.relative_to(WORKSPACE_ROOT))
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

    v.add_document(fact_id, fact_text)
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

    v.remove_document(fact_id)
    return f"🗑️ Fact '{fact_id}' removed from the Dynamic Semantic Codebook."


# ===================================================================
# CHAOS EXPANSION TOOLS (new in this version)
# ===================================================================
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
    path = path.replace(str(WORKSPACE_ROOT) + "/", "").lstrip("/")
    v = _get_valkey()
    raw = v.raw_r.hget(f"{FILE_HASH_PREFIX}{path}", "doc")
    if not raw:
        return "❌ File not indexed."

    try:
        content_bytes = _decompress(raw)
        content = content_bytes.decode("utf-8", errors="replace")
    except Exception:
        content = (
            raw.decode("utf-8", errors="replace")
            if isinstance(raw, bytes)
            else str(raw)
        )

    raw_bytes = content.encode("utf-8", errors="replace")
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
    for key in v.r.scan_iter(f"{FILE_HASH_PREFIX}*", count=500):
        rel = key[len(FILE_HASH_PREFIX) :]
        if pattern != "*" and not fnmatch(rel, pattern):
            continue
        if scope != "*" and not fnmatch(rel, scope):
            continue

        chaos_data = v.raw_r.hget(key, "chaos")
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
    path = path.replace(str(WORKSPACE_ROOT) + "/", "").lstrip("/")
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

    if score >= 0.35:
        days = max(1, int((0.5 - score) * 100))
        return f"⚠️ WARNING: {path} is in PERSISTENT_HIGH state (score: {score:.3f}).\nPredicted structural ejection in ~{days} days without refactoring."
    elif score >= 0.15:
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
    path = path.replace(str(WORKSPACE_ROOT) + "/", "").lstrip("/")
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
    indices = np.arange(n)
    hazards = np.array([w.hazard for w in encoded.windows])
    entropies = np.array([w.entropy for w in encoded.windows])
    coherences = np.array([w.coherence for w in encoded.windows])
    byte_starts = np.array([w.byte_start for w in encoded.windows])

    # Classify symbolic states
    states = []
    for h in hazards:
        if h >= 0.35:
            states.append("PERSISTENT_HIGH")
        elif h >= 0.15:
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
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        f"Structural Manifold Trajectory — {path}\n"
        f"(Windows={n}, Avg Chaos={avg_hazard:.3f}, "
        f"Avg Entropy={avg_entropy:.3f}, Avg Coherence={avg_coherence:.3f})",
        fontsize=13,
        fontweight="bold",
    )

    # Color map for chaos
    cmap = plt.cm.RdYlGn_r  # Red = high chaos, Green = low

    # Panel 1 (top-left): Structural trajectory – byte position vs coherence
    ax1 = axes[0, 0]
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
    ax1.set_title("Physical Reality (colored by chaos score)", fontsize=11)
    ax1.axhline(
        y=np.mean(coherences),
        color="gray",
        linestyle="--",
        alpha=0.5,
        label=f"mean={avg_coherence:.3f}",
    )
    ax1.legend(fontsize=8)
    fig.colorbar(sc1, ax=ax1, label="Hazard (Chaos Score)")

    # Panel 2 (top-right): Chaos vs LLE analog – entropy vs hazard
    ax2 = axes[0, 1]
    sc2 = ax2.scatter(
        entropies,
        hazards,
        c=coherences,
        cmap="viridis",
        s=60,
        edgecolors="k",
        linewidth=0.5,
    )
    ax2.set_xlabel("Entropy", fontsize=10)
    ax2.set_ylabel("Hazard (Chaos Score)", fontsize=10)
    ax2.set_title("Scatter vs LLE Analog", fontsize=11)
    ax2.axhline(
        y=0.35,
        color="red",
        linestyle="--",
        alpha=0.7,
        label="PERSISTENT_HIGH threshold",
    )
    ax2.axhline(
        y=0.15, color="orange", linestyle="--", alpha=0.7, label="OSCILLATION threshold"
    )
    ax2.legend(fontsize=8)
    fig.colorbar(sc2, ax=ax2, label="Coherence")

    # Panel 3 (bottom-left): Time series – all three metrics
    ax3 = axes[1, 0]
    ax3.plot(
        indices, hazards, "r-o", markersize=4, linewidth=1.5, label="Hazard (Chaos)"
    )
    ax3.plot(indices, entropies, "b-s", markersize=4, linewidth=1.5, label="Entropy")
    ax3.plot(indices, coherences, "g-^", markersize=4, linewidth=1.5, label="Coherence")
    ax3.axhline(y=0.35, color="red", linestyle=":", alpha=0.5)
    ax3.set_xlabel("Window Index", fontsize=10)
    ax3.set_ylabel("Metric Value", fontsize=10)
    ax3.set_title("Time Series (per window)", fontsize=11)
    ax3.legend(fontsize=8)
    ax3.set_ylim(-0.05, 1.05)

    # Panel 4 (bottom-right): Symbolic state distribution
    ax4 = axes[1, 1]
    state_labels = ["LOW_FLUCTUATION", "OSCILLATION", "PERSISTENT_HIGH"]
    state_colors = ["#2ecc71", "#f39c12", "#e74c3c"]
    state_vals = [state_counts[s] for s in state_labels]
    bars = ax4.bar(
        state_labels, state_vals, color=state_colors, edgecolor="k", linewidth=0.5
    )
    ax4.set_ylabel("Window Count", fontsize=10)
    ax4.set_title("Symbolic State Distribution", fontsize=11)
    for bar, val in zip(bars, state_vals):
        if val > 0:
            ax4.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.2,
                str(val),
                ha="center",
                va="bottom",
                fontweight="bold",
            )
    ax4.set_xticks(range(len(state_labels)))
    ax4.set_xticklabels(["LOW", "OSCILLATION", "PERSISTENT\nHIGH"], fontsize=9)

    plt.tight_layout(rect=[0, 0, 1, 0.93])

    # Save to reports/
    report_dir = WORKSPACE_ROOT / "reports"
    report_dir.mkdir(exist_ok=True)
    safe_name = re.sub(r"[^\w.]", "_", path)
    out_path = report_dir / f"manifold_trajectory_{safe_name}.png"
    fig.savefig(str(out_path), dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Build text summary
    collapse_risk = (
        "HIGH" if avg_hazard >= 0.35 else "MODERATE" if avg_hazard >= 0.15 else "LOW"
    )

    return (
        f"📊 4-Panel Manifold Dashboard saved to: {out_path.relative_to(WORKSPACE_ROOT)}\n\n"
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
        f"    1. Structural trajectory (byte offset vs coherence, colored by chaos)\n"
        f"    2. Chaos vs LLE analog (entropy vs hazard scatter)\n"
        f"    3. Time series (hazard/entropy/coherence per window)\n"
        f"    4. Symbolic state distribution (LOW/OSCILLATION/HIGH bar chart)"
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
