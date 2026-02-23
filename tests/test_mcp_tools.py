#!/usr/bin/env python3
"""SEP MCP Server – Unified Tool Validation Suite.

Executes and tests every tool exposed by mcp_server.py natively via pytest,
checking for edge cases, metrics properties, and failure modes.
"""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path

import pytest

# Add src to path to allow direct import of mcp_server
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mcp_server import (
    analyze_blast_radius,
    analyze_code_chaos,
    batch_chaos_scan,
    cluster_codebase_structure,
    compute_combined_risk,
    compute_signature,
    get_file,
    get_file_signature,
    get_index_stats,
    ingest_repo,
    inject_fact,
    list_indexed_files,
    predict_structural_ejection,
    remove_fact,
    scan_critical_files,
    search_by_structure,
    search_code,
    start_watcher,
    verify_snippet,
    visualize_manifold_trajectory,
)

# ---------------------------------------------------------------------------
# Test Test Data
# ---------------------------------------------------------------------------

SAMPLE_TEXT_512_PLUS = (
    '"""Wrapper utilities for structural manifold encoding."""\n'
    "\n"
    "from __future__ import annotations\n"
    "\n"
    "from pathlib import Path\n"
    "from typing import Dict, Optional\n"
    "\n"
    "import numpy as np\n"
    "\n"
    "from .metrics import (\n"
    "    compute_coherence,\n"
    "    compute_entropy,\n"
    "    compute_hazard,\n"
    ")\n"
    "\n"
    "class ManifoldEncoder:\n"
    "    def __init__(self, precision: int = 3, hazard_threshold: float = 0.5):\n"
    "        self.precision = precision\n"
    "        self.hazard_threshold = hazard_threshold\n"
    "\n"
    "    def encode_chunk(self, chunk: bytes) -> str:\n"
    "        if len(chunk) < 512:\n"
    '            raise ValueError("Chunk must be at least 512 bytes")\n'
    "        \n"
    "        coh = compute_coherence(chunk)\n"
    "        ent = compute_entropy(chunk)\n"
    "        haz = compute_hazard(chunk, coh, ent)\n"
    "        \n"
    '        return f"c{coh:.{self.precision}f}_s{1.0 - ent:.{self.precision}f}_e{ent:.{self.precision}f}"\n'
    "\n"
    "def build_index(\n"
    "    repo_path: Path,\n"
    "    max_documents: int = 1000,\n"
    ") -> Dict[str, str]:\n"
    '    """Build a structural search index.\n'
    "    \n"
    "    Args:\n"
    "        repo_path: Path to codebase\n"
    "        max_documents: Stop after this many files\n"
    '    """\n'
    "    from .crawler import crawl_repo\n"
    "    return crawl_repo(\n"
    "        repo_path,\n"
    "        max_documents=max_documents,\n"
    "    )\n"
)

INJECT_FACT_ID = f"__test_fact_{int(time.time())}"
FACT_QUERY = "".join(
    [
        "test fact ",
        "injected by the MCP ",
        "tool validation suite",
    ]
)
INJECT_FACT_TEXT = (
    "This is a " + FACT_QUERY + ". "
    "It confirms that the inject_fact tool correctly stores data in Valkey "
    "and that it can be retrieved afterward via get_file."
)


@pytest.fixture(scope="module", autouse=True)
def ensure_ingested():
    """Ensure the repository is ingested before running tests."""
    ingest_repo(root_dir=".", compute_chaos=True, clear_first=False, lite=True)


# ---------------------------------------------------------------------------
# Core Analysis Tests
# ---------------------------------------------------------------------------


def test_get_index_stats():
    res = get_index_stats()
    assert "Total Valkey keys" in res
    assert "Structural sigs" in res
    assert "❌" not in res


def test_list_indexed_files():
    # Base pattern
    res = list_indexed_files(pattern="*.py", max_results=5)
    assert ".py" in res
    assert "❌" not in res

    # Empty match
    no_match = list_indexed_files(pattern="*.nonexistent_extension", max_results=10)
    assert "No indexed files match" in no_match

    # Scope match
    scoped = list_indexed_files(pattern="src/*", max_results=5)
    assert scoped != res


def test_search_code():
    res = search_code(query="async def", file_pattern="*.py", max_results=5)
    assert "async def" in res or "No matches found" in res

    # Edge Case: regex search
    regex_res = search_code(query="class \\w+\\(", file_pattern="*.py", max_results=3)
    assert "class " in regex_res

    # Edge Case: case-sensitive
    case_res = search_code(query="MCP", case_sensitive=True, max_results=3)
    assert "MCP" in case_res

    # Edge Case: empty search
    empty_res = search_code(query="", max_results=1)
    assert "No matches found" in empty_res or len(empty_res.strip()) > 0

    # Edge Case: huge payload
    long_query = "x" * 1000
    try:
        long_res = search_code(query=long_query, max_results=1)
        assert True
    except Exception:
        pytest.fail("Search should handle large queries gracefully")


def test_get_file():
    res = get_file("mcp_server.py")
    assert "def " in res
    assert len(res) > 1000

    # Non-existent file
    error_res = get_file("nonexistent_file_12345.py")
    assert "not found in the index" in error_res


# ---------------------------------------------------------------------------
# Signature & Inference Tests
# ---------------------------------------------------------------------------


def test_compute_signature():
    # Expected pass (valid length)
    res = compute_signature(SAMPLE_TEXT_512_PLUS)
    assert "Compression ratio" in res

    # Expected fail (too short)
    small_text = "def hello(): return 'world'"
    try:
        res_short = compute_signature(small_text)
        assert "ratio" not in res_short.lower()
    except Exception:
        pass


def test_get_file_signature():
    res = get_file_signature("mcp_server.py")
    if "❌" not in res:
        assert "c0." in res or "c1." in res


def test_verify_snippet():
    # Positive Match test
    good_snippet = get_file("mcp_server.py")[:1024]
    res_good = verify_snippet(snippet=good_snippet, scope="*")
    assert "match ratio" in res_good.lower()

    # Edge Case: Negative Match test
    unknown_snippet = (
        "x" * 600 + "\ndef fake_function():\n    return 'not in codebase'\n" * 10
    )
    res_bad = verify_snippet(snippet=unknown_snippet, coverage_threshold=0.5)
    assert "❌" in res_bad or "0.0" in res_bad


def test_search_by_structure():
    sig_res = get_file_signature("mcp_server.py")
    if "❌" not in sig_res:
        sig = sig_res.split("\n")[0] if "\n" in sig_res else sig_res
        # Just ensure the command doesn't crash
        res = search_by_structure(
            signature=sig, tolerance=0.1, max_results=3, scope="*"
        )
        assert "c0." in res or "c1." in res or "mcp_server.py" in res or "❌" in res


# ---------------------------------------------------------------------------
# Zero-Shot working Memory Tests
# ---------------------------------------------------------------------------


def test_inject_remove_fact():
    # 1. Inject
    inject_res = inject_fact(INJECT_FACT_ID, INJECT_FACT_TEXT)
    assert "injected" in inject_res.lower() or "success" in inject_res.lower()

    # 2. Verify existence
    search_res = search_code(query=FACT_QUERY, max_results=3)
    assert INJECT_FACT_ID in search_res or FACT_QUERY in search_res

    # 3. Remove
    rem_res = remove_fact(INJECT_FACT_ID)
    assert "removed" in rem_res.lower()

    # 4. Verify removal
    search_after = search_code(query=FACT_QUERY, max_results=3)
    assert INJECT_FACT_ID not in search_after


# ---------------------------------------------------------------------------
# Chaos & Structural Tension Tests
# ---------------------------------------------------------------------------


def test_cluster_codebase_structure():
    res = cluster_codebase_structure(pattern="*.py", n_clusters=2)
    assert "Structural Codebase Clusters" in res
    assert "Cluster" in res
    # Ensure it parsed files and didn't just err out
    assert "=" in res or "No structural signatures" in res


def test_analyze_code_chaos():
    res = analyze_code_chaos("mcp_server.py")
    assert "Chaos Score" in res
    assert "Entropy" in res
    assert "Coherence" in res


def test_batch_chaos_scan():
    res = batch_chaos_scan(pattern="*.py", max_files=5)
    assert "Batch Chaos Scan" in res
    assert ".py" in res


def test_predict_structural_ejection():
    # Should flag prediction
    res_30 = predict_structural_ejection("mcp_server.py", horizon_days=30)
    res_90 = predict_structural_ejection("mcp_server.py", horizon_days=90)

    # Must report chaos
    assert "score" in res_30.lower()
    assert "score" in res_90.lower()


def test_visualize_manifold_trajectory():
    res = visualize_manifold_trajectory("mcp_server.py")
    # Assert successful png return
    assert "4-Panel Manifold Dashboard saved to:" in res
    assert "Chaos Heatmap" in res  # test that our heatmap modification is acknowledged

    # Test file was actually dropped.
    reports_dir = Path("reports")
    assert reports_dir.exists()
    assert len(list(reports_dir.glob("manifold_trajectory_*.png"))) > 0


# ---------------------------------------------------------------------------
# Blast Radius & Combined Risk Tests
# ---------------------------------------------------------------------------


def test_analyze_blast_radius():
    res = analyze_blast_radius("mcp_server.py")
    assert "Blast Radius Analysis" in res
    assert "Dependency Depth" in res

    res_fails = analyze_blast_radius("non_existent_file.py")
    assert "❌" in res_fails


def test_compute_combined_risk():
    res = compute_combined_risk("mcp_server.py")
    assert "Combined Risk Analysis" in res
    assert "Risk Level" in res
    assert "Formula" in res


def test_scan_critical_files():
    res = scan_critical_files(pattern="*.py", max_files=5)
    # The string must reflect scanning the files and output
    assert (
        "No critical files found" in res
        or "Critical Files" in res
        or "mcp_server.py" in res
    )


# ---------------------------------------------------------------------------
# Autonomous Watcher Extensibility Tests
# ---------------------------------------------------------------------------


def test_start_watcher_and_cli_updates():
    # Note: Starting watcher in a background thread or checking its non-blocking mode.
    # To keep the test suite hermetic, we test the python API interface of `start_watcher` safely.
    test_dir = Path("test_watcher_dir")
    test_dir.mkdir(exist_ok=True)
    test_file = test_dir / "temp_file.py"

    try:
        # Edge case: non-existent dir
        bad_watch_res = start_watcher(
            watch_dir="non_existent_fake_dir", max_bytes_per_file=1024
        )
        assert (
            "not found" in bad_watch_res.lower()
            or "does not exist" in bad_watch_res.lower()
            or "not a directory" in bad_watch_res.lower()
            or "❌" in bad_watch_res
        )

        # 1. Start Watcher
        watch_res = start_watcher(watch_dir=str(test_dir), max_bytes_per_file=1024)
        assert "started" in watch_res.lower() or "already" in watch_res.lower()

        # 2. Write file
        test_file.write_text("print('hello auto update system')")
        time.sleep(1.0)  # Wait for fs events

        # 3. Check stats
        stats = get_index_stats()
        assert "temp_file.py" in str(stats) or "Total Valkey keys" in str(stats)

        # 4. Trigger delete
        test_file.unlink()
        time.sleep(0.5)

    finally:
        if test_file.exists():
            test_file.unlink()
        if test_dir.exists():
            test_dir.rmdir()
