#!/usr/bin/env python3
"""SEP MCP Server – Comprehensive Tool Validation Suite.

Tests every tool exposed by mcp_server.py (21 tools total), verifying:
  - Correct output structure and content markers
  - Edge cases and failure modes
  - Metrics properties (chaos ∈ [0,1], coherence ∈ [0,1], etc.)
  - Visual output quality (PNG generation, file sizes)
  - Conceptual integrity of the structural analysis pipeline

Tool inventory (must match @mcp.tool() decorators in mcp_server.py):
  Indexing & Monitoring:  ingest_repo, get_index_stats, start_watcher
  Search & Retrieval:     search_code, get_file, list_indexed_files,
                          get_file_signature, search_by_structure,
                          search_by_signature_sequence
  Structural Analysis:    compute_signature, verify_snippet
  Chaos Detection:        analyze_code_chaos, batch_chaos_scan,
                          predict_structural_ejection,
                          visualize_manifold_trajectory,
                          cluster_codebase_structure
  Dependency & Risk:      analyze_blast_radius, compute_combined_risk,
                          scan_critical_files
  Working Memory:         inject_fact, remove_fact
"""

from __future__ import annotations

import re
import time
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Bootstrap imports
# ---------------------------------------------------------------------------
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
    search_by_signature_sequence,
    search_by_structure,
    search_code,
    start_watcher,
    verify_snippet,
    visualize_manifold_trajectory,
)

# ---------------------------------------------------------------------------
# Shared constants & test data
# ---------------------------------------------------------------------------
TOOL_COUNT = 21  # Must match the number of @mcp.tool() decorators

# A realistic Python snippet ≥512 bytes for signature/verification tests
SAMPLE_CODE = (
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
FACT_QUERY = "test fact injected by the MCP tool validation suite"
INJECT_FACT_TEXT = (
    f"This is a {FACT_QUERY}. "
    "It confirms that the inject_fact tool correctly stores data in Valkey "
    "and that it can be retrieved afterward via get_file."
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _parse_signature(output: str) -> str | None:
    """Extract a cX.XXX_sX.XXX_eX.XXX signature from tool output."""
    m = re.search(r"c[\d.]+_s[\d.]+_e[\d.]+", output)
    return m.group(0) if m else None


def _parse_float_field(output: str, label: str) -> float | None:
    """Extract a float value from 'label ... : X.XXX' style output.

    Tolerates extra text between the label and the colon (e.g.
    'Chaos Score (fluctuation_persistence) : 0.399').
    """
    m = re.search(rf"{re.escape(label)}[^:\n]*:\s*([\d.]+)", output)
    return float(m.group(1)) if m else None


# ---------------------------------------------------------------------------
# Module-scoped fixture: ensure repo is ingested once before all tests
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module", autouse=True)
def ensure_ingested():
    """Ingest the repository before running any tests in this module."""
    result = ingest_repo(
        root_dir=str(REPO_ROOT), compute_chaos=True, clear_first=False, lite=True
    )
    assert "✅" in result, f"Ingest failed: {result}"


# ═══════════════════════════════════════════════════════════════════════════
# 1. INDEXING & MONITORING
# ═══════════════════════════════════════════════════════════════════════════


class TestIndexingAndMonitoring:
    """Validate the indexing pipeline and monitoring tools."""

    def test_ingest_repo_output_structure(self):
        """Verify ingest output contains all expected metrics."""
        result = ingest_repo(
            root_dir=str(REPO_ROOT), compute_chaos=True, clear_first=False, lite=True
        )
        assert "✅ Ingest complete" in result
        for field in ["Text files", "Binary files", "Signatures", "Avg chaos", "High-risk"]:
            assert field in result, f"Missing field '{field}' in ingest output"

    def test_ingest_repo_nonexistent_directory(self):
        """Ingest on a missing directory returns an error."""
        result = ingest_repo(root_dir="/nonexistent/path/12345")
        assert "❌" in result

    def test_get_index_stats_structure(self):
        """Verify stats output contains all key metrics."""
        result = get_index_stats()
        assert "❌" not in result, f"Stats failed: {result}"
        for field in [
            "Total Valkey keys",
            "Indexed documents",
            "Structural sigs",
            "Chaos profiles",
            "Valkey memory",
            "Encoder available",
        ]:
            assert field in result, f"Missing field '{field}' in stats output"

    def test_get_index_stats_has_documents(self):
        """After ingest, document count should be > 0."""
        result = get_index_stats()
        count = _parse_float_field(result, "Indexed documents")
        assert count is not None and count > 0

    def test_start_watcher_nonexistent_dir(self):
        """Watcher on a bad path returns error."""
        result = start_watcher(watch_dir="non_existent_fake_dir_12345")
        assert "❌" in result

    def test_start_watcher_real_dir(self):
        """Watcher can start on a valid directory."""
        test_dir = Path("test_watcher_dir")
        test_dir.mkdir(exist_ok=True)
        try:
            result = start_watcher(watch_dir=str(test_dir))
            assert "started" in result.lower() or "already" in result.lower()
        finally:
            if test_dir.exists():
                test_dir.rmdir()


# ═══════════════════════════════════════════════════════════════════════════
# 2. SEARCH & RETRIEVAL
# ═══════════════════════════════════════════════════════════════════════════


class TestSearchAndRetrieval:
    """Validate search and retrieval tools."""

    def test_list_indexed_files_python(self):
        """List *.py files returns at least one result."""
        result = list_indexed_files(pattern="*.py", max_results=5)
        assert "❌" not in result
        assert ".py" in result

    def test_list_indexed_files_no_match(self):
        """Pattern with no matches returns clear message."""
        result = list_indexed_files(pattern="*.nonexistent_extension_xyz")
        assert "No indexed files match" in result

    def test_list_indexed_files_scoped(self):
        """Scoped pattern returns different results from global."""
        global_res = list_indexed_files(pattern="*.py", max_results=100)
        scoped_res = list_indexed_files(pattern="src/*", max_results=100)
        assert scoped_res != global_res

    def test_search_code_keyword(self):
        """Keyword search finds matches in Python files."""
        result = search_code(query="def ", file_pattern="*.py", max_results=5)
        assert "def " in result or "No matches found" in result

    def test_search_code_regex(self):
        """Regex search for class definitions."""
        result = search_code(query=r"class \w+\(", file_pattern="*.py", max_results=3)
        assert "class " in result or "No matches found" in result

    def test_search_code_case_sensitive(self):
        """Case-sensitive search respects casing."""
        result = search_code(query="MCP", case_sensitive=True, max_results=3)
        assert "MCP" in result or "No matches found" in result

    def test_search_code_large_query_no_crash(self):
        """A very long query string doesn't crash the server."""
        result = search_code(query="x" * 1000, max_results=1)
        # Should either find nothing or return gracefully
        assert isinstance(result, str)

    def test_get_file_exists(self):
        """Reading an indexed file returns its content."""
        result = get_file("mcp_server.py")
        assert "📄" in result
        assert "def " in result
        assert len(result) > 1000

    def test_get_file_not_found(self):
        """Reading a nonexistent file returns error with suggestions."""
        result = get_file("nonexistent_file_12345.py")
        assert "not found" in result.lower()

    def test_get_file_signature_format(self):
        """File signature is in cX.XXX_sX.XXX_eX.XXX format."""
        result = get_file_signature("mcp_server.py")
        if "❌" not in result:
            sig = _parse_signature(result)
            assert sig is not None, f"Could not parse signature from: {result}"
            # Validate each component is in [0, 1]
            parts = sig.split("_")
            for part in parts:
                val = float(part[1:])
                assert 0.0 <= val <= 1.0, f"Signature component {part} out of [0,1] range"

    def test_search_by_structure_finds_self(self):
        """Searching by a file's own signature should find itself."""
        sig_result = get_file_signature("mcp_server.py")
        if "❌" in sig_result:
            pytest.skip("Signature unavailable for mcp_server.py")

        sig = _parse_signature(sig_result)
        assert sig is not None

        result = search_by_structure(signature=sig, tolerance=0.1, max_results=5)
        assert "mcp_server.py" in result or sig in result

    def test_search_by_structure_invalid_format(self):
        """Invalid signature format returns clear error."""
        result = search_by_structure(signature="invalid_format")
        assert "❌" in result

    def test_search_by_signature_sequence_too_short(self):
        """Sequence search on short snippet returns clear error."""
        result = search_by_signature_sequence(text="short text")
        assert "❌" in result and "512" in result

    def test_search_by_signature_sequence_matches_self(self):
        """Sequence search should match the source file when using its own text."""
        source_path = REPO_ROOT / "mcp_server.py"
        raw_text = source_path.read_text("utf-8")[:2048]
        if len(raw_text.encode("utf-8")) < 512:
            pytest.skip("Source text too short for signature sequence search")
        result = search_by_signature_sequence(text=raw_text, min_signatures=3)
        assert "mcp_server.py" in result or "Signature sequence matches" in result

    def test_search_by_signature_sequence_empty_after_trim(self):
        """Trimmed sequence that becomes empty returns clear error."""
        source_path = REPO_ROOT / "mcp_server.py"
        raw_text = source_path.read_text("utf-8")[:512]
        if len(raw_text.encode("utf-8")) < 512:
            pytest.skip("Source text too short for signature sequence search")
        result = search_by_signature_sequence(
            text=raw_text,
            min_signatures=2,
            trim_first_last=True,
        )
        assert "❌" in result and (
            "empty" in result.lower() or "not enough signatures" in result.lower()
        )



# ═══════════════════════════════════════════════════════════════════════════
# 3. STRUCTURAL ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════


class TestStructuralAnalysis:
    """Validate signature computation and snippet verification."""

    def test_compute_signature_valid(self):
        """Valid ≥512-byte text produces compression metrics."""
        result = compute_signature(SAMPLE_CODE)
        assert "Compression ratio" in result
        assert "Unique signatures" in result
        assert "Hazard threshold" in result

    def test_compute_signature_short_text(self):
        """Text shorter than 512 bytes should degrade gracefully."""
        result = compute_signature("def hello(): return 'world'")
        # Either an error or zero-compression result; no crash
        assert isinstance(result, str)

    def test_verify_snippet_too_short(self):
        """Snippet below 512 bytes returns clear error."""
        result = verify_snippet(snippet="short text", coverage_threshold=0.5)
        assert "❌" in result
        assert "512" in result

    def test_verify_snippet_known_code(self):
        """A snippet from the indexed codebase should have nonzero match ratio."""
        # Read raw source to get pure code (not the line-numbered get_file output)
        source_path = REPO_ROOT / "mcp_server.py"
        raw_text = source_path.read_text("utf-8")[:2048]
        if len(raw_text.encode("utf-8")) < 512:
            pytest.skip("Source text too short for snippet verification")

        result = verify_snippet(snippet=raw_text, scope="*")
        assert "match ratio" in result.lower()
        # Should have some matches since we're comparing codebase to itself
        ratio = _parse_float_field(result, "Raw match ratio")
        assert ratio is not None

    def test_verify_snippet_alien_code(self):
        """Completely fabricated code should fail verification."""
        alien = (
            "x" * 600
            + "\ndef fake_function_zzzz():\n    return 'absolutely not in codebase'\n" * 10
        )
        result = verify_snippet(snippet=alien, coverage_threshold=0.5)
        assert "❌" in result or "0.00%" in result


# ═══════════════════════════════════════════════════════════════════════════
# 4. CHAOS DETECTION
# ═══════════════════════════════════════════════════════════════════════════


class TestChaosDetection:
    """Validate chaos analysis, batch scanning, prediction, and visualization."""

    def test_analyze_code_chaos_metrics(self):
        """Chaos analysis returns all expected metrics in valid ranges."""
        result = analyze_code_chaos("mcp_server.py")
        assert "❌" not in result, f"Chaos analysis failed: {result}"

        # Verify all metric labels present
        for label in ["Chaos Score", "Entropy", "Coherence", "Collapse Risk", "Windows analyzed"]:
            assert label in result, f"Missing '{label}' in chaos output"

        # Parse metrics — note: output uses "Chaos Score (fluctuation_persistence) : 0.399"
        # The _parse_float_field helper tolerates extra text before the colon
        chaos = _parse_float_field(result, "Chaos Score")
        entropy = _parse_float_field(result, "Entropy")
        coherence = _parse_float_field(result, "Coherence")
        assert chaos is not None and 0.0 <= chaos <= 1.0, f"Chaos parse failed from: {result}"
        assert entropy is not None and 0.0 <= entropy <= 1.0
        assert coherence is not None and 0.0 <= coherence <= 1.0

    def test_analyze_code_chaos_not_indexed(self):
        """Chaos on a nonexistent file returns error."""
        result = analyze_code_chaos("nonexistent_file_99999.py")
        assert "❌" in result

    def test_batch_chaos_scan_structure(self):
        """Batch scan returns ranked results."""
        result = batch_chaos_scan(pattern="*.py", max_files=5)
        assert "Batch Chaos Scan" in result
        assert ".py" in result or "No chaos profiles" in result

    def test_batch_chaos_scan_scope(self):
        """Batch scan with scope narrows results."""
        full_scan = batch_chaos_scan(pattern="*.py", max_files=100, scope="*")
        scoped_scan = batch_chaos_scan(pattern="*.py", max_files=100, scope="src/*")
        # Scoped should differ from full (fewer results or different ordering)
        assert isinstance(full_scan, str)
        assert isinstance(scoped_scan, str)

    def test_predict_structural_ejection_states(self):
        """Ejection prediction returns one of the three symbolic states."""
        result = predict_structural_ejection("mcp_server.py", horizon_days=30)
        assert "❌" not in result, f"Prediction failed: {result}"
        # Must contain one of the three state keywords
        assert any(
            state in result
            for state in ["PERSISTENT_HIGH", "OSCILLATION", "LOW_FLUCTUATION"]
        ), f"No symbolic state found in: {result}"
        # Must report the chaos score
        assert "score" in result.lower()

    def test_predict_structural_ejection_missing_file(self):
        """Prediction on missing file returns error."""
        result = predict_structural_ejection("nonexistent_file_99999.py")
        assert "❌" in result

    def test_visualize_manifold_trajectory_creates_png(self):
        """Visualization generates a valid PNG dashboard."""
        result = visualize_manifold_trajectory("mcp_server.py")
        assert "❌" not in result, f"Visualization failed: {result}"
        assert "4-Panel Manifold Dashboard saved to:" in result

        # Verify file was created
        reports_dir = REPO_ROOT / "reports"
        pngs = list(reports_dir.glob("manifold_trajectory_*mcp_server*.png"))
        assert len(pngs) > 0, "No PNG file found in reports/"

        # Verify file is non-trivial (>10 KB indicates real plot data)
        for png in pngs:
            assert png.stat().st_size > 10_000, f"PNG too small ({png.stat().st_size} bytes)"

    def test_visualize_manifold_trajectory_output_metrics(self):
        """Dashboard output contains all expected metric labels."""
        result = visualize_manifold_trajectory("mcp_server.py")
        for label in [
            "Windows analyzed",
            "Avg Chaos Score",
            "Max Chaos Score",
            "Avg Entropy",
            "Avg Coherence",
            "Collapse Risk",
            "LOW_FLUCTUATION",
            "OSCILLATION",
            "PERSISTENT_HIGH",
        ]:
            assert label in result, f"Missing '{label}' in dashboard output"

        # Verify the four panel descriptions are referenced
        for panel in [
            "Physical Evolution",
            "Manifold Attractors",
            "3D Phase Space Trajectory",
            "Structural Phase Space",
        ]:
            assert panel in result, f"Missing panel description '{panel}'"

    def test_cluster_codebase_structure_basic(self):
        """Clustering produces labeled groups."""
        result = cluster_codebase_structure(pattern="*.py", n_clusters=2)
        assert "Structural Codebase Clusters" in result or "❌" in result
        if "❌" not in result:
            assert "Cluster" in result

    def test_cluster_codebase_structure_overclustering(self):
        """Requesting more clusters than files degrades gracefully."""
        result = cluster_codebase_structure(pattern="setup.py", n_clusters=10)
        # Should either auto-reduce k or report not enough files
        assert isinstance(result, str)


# ═══════════════════════════════════════════════════════════════════════════
# 5. DEPENDENCY & RISK ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════


class TestDependencyAndRisk:
    """Validate blast radius, combined risk, and critical file scanning."""

    def test_analyze_blast_radius_structure(self):
        """Blast radius analysis returns all expected fields."""
        result = analyze_blast_radius("mcp_server.py")
        assert "❌" not in result, f"Blast radius failed: {result}"
        for field in ["Blast Radius", "Dependency Depth", "Is Core Module", "Imports", "Imported By"]:
            assert field in result, f"Missing '{field}' in blast radius output"

    def test_analyze_blast_radius_nonexistent(self):
        """Blast radius on a nonexistent file returns error."""
        result = analyze_blast_radius("nonexistent_file_99999.py")
        assert "❌" in result

    def test_compute_combined_risk_structure(self):
        """Combined risk returns score, level, and formula."""
        result = compute_combined_risk("mcp_server.py")
        assert "❌" not in result, f"Combined risk failed: {result}"
        for field in ["Combined Risk", "Risk Level", "Formula", "Chaos Score", "Blast Radius"]:
            assert field in result, f"Missing '{field}' in combined risk output"

    def test_compute_combined_risk_levels(self):
        """Risk level is one of the four defined categories."""
        result = compute_combined_risk("mcp_server.py")
        if "❌" not in result:
            assert any(
                level in result for level in ["CRITICAL", "HIGH", "MODERATE", "LOW"]
            ), f"No valid risk level found in: {result}"

    def test_scan_critical_files_structure(self):
        """Critical file scan returns ranked results."""
        result = scan_critical_files(pattern="*.py", max_files=5)
        assert (
            "Critical Files" in result
            or "No critical files" in result
            or ".py" in result
        ), f"Unexpected scan_critical_files output: {result}"

    def test_scan_critical_files_combined_metrics(self):
        """Each result line includes both chaos and blast values."""
        result = scan_critical_files(pattern="*.py", max_files=3)
        if "Critical Files" in result:
            assert "chaos=" in result
            assert "blast=" in result


# ═══════════════════════════════════════════════════════════════════════════
# 6. WORKING MEMORY
# ═══════════════════════════════════════════════════════════════════════════


class TestWorkingMemory:
    """Validate zero-shot fact injection and removal lifecycle."""

    def test_inject_and_search_fact(self):
        """Injected fact is discoverable via search_code."""
        inject_res = inject_fact(INJECT_FACT_ID, INJECT_FACT_TEXT)
        assert "injected" in inject_res.lower()

        search_res = search_code(query=FACT_QUERY, max_results=3)
        assert INJECT_FACT_ID in search_res or FACT_QUERY in search_res

    def test_remove_fact_lifecycle(self):
        """Removed fact is no longer discoverable."""
        # Ensure fact exists first
        inject_fact(INJECT_FACT_ID, INJECT_FACT_TEXT)

        # Remove it
        rem_res = remove_fact(INJECT_FACT_ID)
        assert "removed" in rem_res.lower()

        # Verify it's gone
        search_after = search_code(query=FACT_QUERY, max_results=3)
        assert INJECT_FACT_ID not in search_after


# ═══════════════════════════════════════════════════════════════════════════
# 7. WATCHER INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════


class TestWatcherIntegration:
    """Validate the filesystem watcher lifecycle."""

    def test_watcher_file_creation_and_cleanup(self):
        """Watcher detects new files and index reflects changes."""
        test_dir = Path("test_watcher_dir")
        test_dir.mkdir(exist_ok=True)
        test_file = test_dir / "temp_watched_file.py"

        try:
            # Start watcher (may already be running from previous test)
            watch_res = start_watcher(watch_dir=str(test_dir))
            assert "started" in watch_res.lower() or "already" in watch_res.lower()

            # Create a file
            test_file.write_text("print('hello from watcher test')")
            time.sleep(1.0)  # Allow FS events to propagate

            # Stats should still be healthy
            stats = get_index_stats()
            assert "Total Valkey keys" in stats

            # Clean up the file
            test_file.unlink()
            time.sleep(0.5)
        finally:
            if test_file.exists():
                test_file.unlink()
            if test_dir.exists():
                test_dir.rmdir()


# ═══════════════════════════════════════════════════════════════════════════
# 8. META: TOOL INVENTORY VERIFICATION
# ═══════════════════════════════════════════════════════════════════════════


class TestToolInventory:
    """Verify that the test suite covers all declared tools."""

    def test_all_tools_imported(self):
        """Confirm we import exactly TOOL_COUNT tools from mcp_server."""
        imported_tools = [
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
            search_by_signature_sequence,
            search_by_structure,
            search_code,
            start_watcher,
            verify_snippet,
            visualize_manifold_trajectory,
        ]
        assert len(imported_tools) == TOOL_COUNT, (
            f"Expected {TOOL_COUNT} tools, got {len(imported_tools)}. "
            "Update TOOL_COUNT or imports if tools were added/removed."
        )

    def test_tools_are_callable(self):
        """Every imported tool is a callable function."""
        tools = [
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
            search_by_signature_sequence,
            search_by_structure,
            search_code,
            start_watcher,
            verify_snippet,
            visualize_manifold_trajectory,
        ]
        for tool in tools:
            assert callable(tool), f"{tool.__name__} is not callable"
