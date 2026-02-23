#!/usr/bin/env python3
"""SEP MCP Server – Full Tool Validation Suite.

Executes every tool exposed by mcp_server.py, validates responses,
and writes a comprehensive markdown report to `reports/mcp_tool_report.md`.

Usage:
    python scripts/tests/test_mcp_tools.py
"""

from __future__ import annotations

import re
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Bootstrap – ensure repo root is on sys.path
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Import the tool functions directly from the MCP server module
import mcp_server as srv

# ---------------------------------------------------------------------------
# Report output directory
# ---------------------------------------------------------------------------
REPORT_DIR = REPO_ROOT / "reports"
REPORT_DIR.mkdir(exist_ok=True)
REPORT_PATH = REPORT_DIR / "mcp_tool_report.md"

# ---------------------------------------------------------------------------
# Test sample data
# ---------------------------------------------------------------------------
SAMPLE_TEXT_512_PLUS = (
    '"""Wrapper utilities for structural manifold encoding."""\n'
    "\n"
    "from __future__ import annotations\n"
    "\n"
    "from pathlib import Path\n"
    "from typing import Dict, Optional\n"
    "\n"
    "from scripts.experiments.manifold_compression_eval import evaluate_manifold\n"
    "\n"
    "\n"
    "def build_signature_index(\n"
    "    text_root: Path,\n"
    "    window_bytes: int = 512,\n"
    "    stride_bytes: int = 384,\n"
    "    precision: int = 3,\n"
    '    tokenizer_name: str = "gpt2",\n'
    "    tokenizer_trust_remote_code: bool = False,\n"
    "    max_documents: Optional[int] = None,\n"
    ") -> Dict[str, object]:\n"
    '    """Return the same summary dictionary exposed by benchmark_eval."""\n'
    "\n"
    "    return evaluate_manifold(\n"
    "        text_root=text_root,\n"
    "        window_bytes=window_bytes,\n"
    "        stride_bytes=stride_bytes,\n"
    "        precision=precision,\n"
    "        tokenizer_name=tokenizer_name,\n"
    "        tokenizer_trust_remote_code=tokenizer_trust_remote_code,\n"
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


# ---------------------------------------------------------------------------
# Test harness
# ---------------------------------------------------------------------------
class ToolTestResult:
    """Stores the outcome of a single tool test."""

    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.response: str = ""
        self.error: str = ""
        self.assertions: List[Tuple[str, bool]] = []
        self.elapsed_ms: float = 0.0

    def assert_check(self, label: str, condition: bool) -> None:
        self.assertions.append((label, condition))
        if not condition:
            self.passed = False

    def finalize(self) -> None:
        if self.error:
            self.passed = False
        elif all(ok for _, ok in self.assertions):
            self.passed = True
        else:
            self.passed = False


def run_tool(name: str, fn, *args, **kwargs) -> ToolTestResult:
    """Execute a tool function, capture response and timing."""
    result = ToolTestResult(name)
    t0 = time.perf_counter()
    try:
        result.response = fn(*args, **kwargs)
    except Exception:
        result.error = traceback.format_exc()
    result.elapsed_ms = (time.perf_counter() - t0) * 1000
    return result


# ---------------------------------------------------------------------------
# Individual test functions
# ---------------------------------------------------------------------------


def test_get_index_stats() -> ToolTestResult:
    r = run_tool("get_index_stats", srv.get_index_stats)
    r.assert_check("returns string", isinstance(r.response, str))
    r.assert_check("contains '📊'", "📊" in r.response)
    r.assert_check("contains 'Indexed documents'", "Indexed documents" in r.response)
    r.assert_check("contains 'Valkey memory'", "Valkey memory" in r.response)
    r.assert_check("contains 'Encoder available'", "Encoder available" in r.response)
    r.assert_check("no error marker", "❌" not in r.response)
    r.finalize()
    return r


def test_ingest_repo() -> ToolTestResult:
    r = run_tool(
        "ingest_repo",
        srv.ingest_repo,
        root_dir=".",
        compute_chaos=True,
        clear_first=True,
    )
    r.assert_check("returns string", isinstance(r.response, str))
    r.assert_check("contains '✅'", "✅" in r.response)
    r.assert_check("contains 'Text files'", "Text files" in r.response)
    r.assert_check("contains 'Signatures'", "Signatures" in r.response)
    r.assert_check("reports zero errors", "Errors     : 0" in r.response)
    r.assert_check("no error marker", "❌" not in r.response)
    r.finalize()
    return r


def test_list_indexed_files() -> ToolTestResult:
    r = run_tool(
        "list_indexed_files", srv.list_indexed_files, pattern="*.py", max_results=20
    )
    r.assert_check("returns string", isinstance(r.response, str))
    r.assert_check("contains 'Indexed files'", "Indexed files" in r.response)
    r.assert_check("lists .py files", ".py" in r.response)
    r.assert_check("no error marker", "❌" not in r.response)
    r.finalize()
    return r


def test_search_code() -> ToolTestResult:
    r = run_tool(
        "search_code",
        srv.search_code,
        query="chaos_score",
        file_pattern="*.py",
        max_results=5,
    )
    r.assert_check("returns string", isinstance(r.response, str))
    r.assert_check("contains 'Found'", "Found" in r.response)
    r.assert_check("shows match context", ">>>" in r.response)
    r.assert_check("mentions mcp_server.py", "mcp_server.py" in r.response)
    r.assert_check("no error marker", "❌" not in r.response)
    r.finalize()
    return r


def test_get_file() -> ToolTestResult:
    r = run_tool("get_file", srv.get_file, path="src/manifold/encoder.py")
    r.assert_check("returns string", isinstance(r.response, str))
    r.assert_check("contains '📄'", "📄" in r.response)
    r.assert_check("shows line numbers", "1 |" in r.response)
    r.assert_check("contains 'encoder.py'", "encoder.py" in r.response)
    r.assert_check("contains actual code", "build_signature_index" in r.response)
    r.assert_check("no error marker", "❌" not in r.response)
    r.finalize()
    return r


def test_get_file_signature() -> ToolTestResult:
    r = run_tool("get_file_signature", srv.get_file_signature, path="mcp_server.py")
    r.assert_check("returns string", isinstance(r.response, str))
    r.assert_check("contains '📐'", "📐" in r.response)
    r.assert_check(
        "contains signature format",
        bool(re.search(r"c[\d.]+_s[\d.]+_e[\d.]+", r.response)),
    )
    r.assert_check("references mcp_server.py", "mcp_server.py" in r.response)
    r.assert_check("no error marker", "❌" not in r.response)
    r.finalize()
    return r


def test_compute_signature() -> ToolTestResult:
    r = run_tool("compute_signature", srv.compute_signature, text=SAMPLE_TEXT_512_PLUS)
    r.assert_check("returns string", isinstance(r.response, str))
    r.assert_check("contains '✅'", "✅" in r.response)
    r.assert_check("mentions compression ratio", "Compression ratio" in r.response)
    r.assert_check("mentions unique signatures", "Unique signatures" in r.response)
    r.assert_check("mentions total windows", "Total windows" in r.response)
    r.assert_check("mentions hazard threshold", "Hazard threshold" in r.response)
    r.assert_check("no error marker", "❌" not in r.response)
    r.finalize()
    return r


def test_verify_snippet() -> ToolTestResult:
    r = run_tool(
        "verify_snippet",
        srv.verify_snippet,
        snippet=SAMPLE_TEXT_512_PLUS,
        coverage_threshold=0.5,
    )
    r.assert_check("returns string", isinstance(r.response, str))
    r.assert_check(
        "contains VERIFIED or FAILED",
        "VERIFIED" in r.response or "FAILED" in r.response,
    )
    r.assert_check("shows coverage", "Safe coverage" in r.response)
    r.assert_check("shows match ratio", "Raw match ratio" in r.response)
    r.assert_check("shows gated hits", "Gated hits" in r.response)
    r.assert_check("no error marker", "❌" not in r.response)
    r.finalize()
    return r


def test_search_by_structure() -> ToolTestResult:
    # First get a real signature to search for
    sig_resp = srv.get_file_signature(path="mcp_server.py")
    sig_match = re.search(r"(c[\d.]+_s[\d.]+_e[\d.]+)", sig_resp)
    target_sig = sig_match.group(1) if sig_match else "c0.462_s0.800_e0.928"

    r = run_tool(
        "search_by_structure",
        srv.search_by_structure,
        signature=target_sig,
        tolerance=0.05,
        max_results=5,
    )
    r.assert_check("returns string", isinstance(r.response, str))
    r.assert_check(
        "contains 'structurally similar'", "structurally similar" in r.response
    )
    r.assert_check("shows delta values", "Δ=" in r.response)
    r.assert_check("lists file paths", ".py" in r.response or ".md" in r.response)
    r.assert_check("no error marker", "❌" not in r.response)
    r.finalize()
    return r


def test_inject_fact() -> ToolTestResult:
    """Tests zero-shot memory injection."""
    r = run_tool(
        "inject_fact",
        srv.inject_fact,
        fact_id=INJECT_FACT_ID,
        fact_text=INJECT_FACT_TEXT,
    )
    r.assert_check("returns string", isinstance(r.response, str))
    r.assert_check("contains '🚀'", "🚀" in r.response)
    r.assert_check("no error marker", "❌" not in r.response)

    verify_resp = srv.get_file(path=INJECT_FACT_ID)
    r.assert_check(
        "fact retrievable via get_file",
        INJECT_FACT_TEXT[:40] in verify_resp,
    )

    # Verify Search Code visibility
    search_resp = srv.search_code(query=FACT_QUERY, max_results=1)
    r.assert_check("visible in search_code", "test fact injected" in search_resp)
    r.finalize()
    return r


def test_remove_fact() -> ToolTestResult:
    """Tests targeted removal of the exact injected memory."""
    r = run_tool("remove_fact", srv.remove_fact, fact_id=INJECT_FACT_ID)
    r.assert_check("returns string", isinstance(r.response, str))
    r.assert_check("contains '🗑️'", "🗑️" in r.response)

    # Validate it no longer shows up
    search_resp = srv.search_code(query=FACT_QUERY, max_results=1)
    r.assert_check("erased from search_code", "No matches found" in search_resp)
    r.finalize()
    return r


def test_start_watcher_and_cli_updates() -> ToolTestResult:
    """Tests that the watcher detects CLI file creation and deletion."""
    srv._active_observer = None

    r = run_tool("start_watcher_and_cli_updates", srv.start_watcher, watch_dir=".")
    r.assert_check("watcher starts", "✅" in r.response)

    # Simulate a CLI file creation
    test_file = Path("cli_test_file.py")
    test_file.write_text("def unique_cli_test_function():\n    pass\n")
    time.sleep(2.0)  # Give watcher a moment to trigger

    search_resp = srv.search_code(query="unique_cli_test_function", max_results=1)
    r.assert_check(
        "cli creation indexed dynamically",
        "unique_cli_test_function" in search_resp and "cli_test_file.py" in search_resp,
    )

    # Simulate a CLI file deletion
    test_file.unlink()
    time.sleep(2.0)

    search_resp_after = srv.search_code(query="unique_cli_test_function", max_results=1)
    r.assert_check(
        "cli deletion unindexed dynamically", "No matches found" in search_resp_after
    )

    r.finalize()
    return r


def test_analyze_code_chaos() -> ToolTestResult:
    r = run_tool("analyze_code_chaos", srv.analyze_code_chaos, path="mcp_server.py")
    r.assert_check("returns string", isinstance(r.response, str))
    r.assert_check("contains '📈'", "📈" in r.response)
    r.assert_check("shows chaos score", "Chaos Score" in r.response)
    r.assert_check("shows entropy", "Entropy" in r.response)
    r.assert_check("shows coherence", "Coherence" in r.response)
    r.assert_check("shows collapse risk", "Collapse Risk" in r.response)
    r.assert_check("shows windows analyzed", "Windows analyzed" in r.response)
    r.assert_check("no error marker", "❌" not in r.response)
    r.finalize()
    return r


def test_batch_chaos_scan() -> ToolTestResult:
    r = run_tool("batch_chaos_scan", srv.batch_chaos_scan, pattern="*.py", max_files=5)
    r.assert_check("returns string", isinstance(r.response, str))
    r.assert_check("contains '🔍'", "🔍" in r.response)
    r.assert_check(
        "shows risk levels",
        "[HIGH]" in r.response or "[MODERATE]" in r.response or "[LOW]" in r.response,
    )
    r.assert_check("shows scores", bool(re.search(r"\d+\.\d+", r.response)))
    r.assert_check("shows file paths", ".py" in r.response)
    r.assert_check("no error marker", "❌" not in r.response)
    r.finalize()
    return r


def test_predict_structural_ejection() -> ToolTestResult:
    r = run_tool(
        "predict_structural_ejection",
        srv.predict_structural_ejection,
        path="mcp_server.py",
        horizon_days=30,
    )
    r.assert_check("returns string", isinstance(r.response, str))
    r.assert_check(
        "mentions state",
        "PERSISTENT_HIGH" in r.response
        or "OSCILLATION" in r.response
        or "LOW_FLUCTUATION" in r.response,
    )
    r.assert_check("mentions file path", "mcp_server.py" in r.response)
    r.assert_check("includes score", bool(re.search(r"score: \d+\.\d+", r.response)))
    r.assert_check("no error marker", "❌" not in r.response)
    r.finalize()
    return r


def test_visualize_manifold_trajectory() -> ToolTestResult:
    r = run_tool(
        "visualize_manifold_trajectory",
        srv.visualize_manifold_trajectory,
        path="mcp_server.py",
    )
    r.assert_check("returns string", isinstance(r.response, str))
    r.assert_check("contains '📊'", "📊" in r.response)
    r.assert_check(
        "mentions dashboard", "Dashboard" in r.response or "dashboard" in r.response
    )
    r.assert_check("references the file", "mcp_server.py" in r.response)
    r.assert_check("reports windows analyzed", "Windows analyzed" in r.response)
    r.assert_check(
        "reports chaos score", "Chaos Score" in r.response or "Avg Chaos" in r.response
    )
    r.assert_check("reports symbolic states", "Symbolic States" in r.response)
    r.assert_check("reports collapse risk", "Collapse Risk" in r.response)
    r.assert_check("PNG saved", ".png" in r.response)
    r.assert_check("no error marker", "❌" not in r.response)

    # Verify the PNG was actually created
    import re as _re

    png_match = _re.search(r"reports/[\w.]+\.png", r.response)
    if png_match:
        from pathlib import Path as _Path

        png_path = _Path(__file__).resolve().parent.parent / png_match.group()
        r.assert_check("PNG file exists on disk", png_path.exists())
        r.assert_check("PNG file has content", png_path.stat().st_size > 1000)
    else:
        r.assert_check("PNG path found in response", False)

    r.finalize()
    return r


# ---------------------------------------------------------------------------
# Report generator
# ---------------------------------------------------------------------------


def generate_report(results: List[ToolTestResult]) -> str:
    """Build a markdown report from test results."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed

    lines: List[str] = []
    lines.append("# SEP MCP Server – Tool Validation Report\n")
    lines.append(f"**Generated:** {now}  ")
    lines.append(f"**Total Tools:** {total}  ")
    lines.append(f"**Passed:** {passed}  ")
    lines.append(f"**Failed:** {failed}  ")
    lines.append(
        f"**Status:** {'✅ ALL PASS' if failed == 0 else '❌ FAILURES DETECTED'}\n"
    )

    # Summary table
    lines.append("## Summary\n")
    lines.append("| # | Tool | Status | Time (ms) | Assertions |")
    lines.append("|---|------|--------|-----------|------------|")
    for i, r in enumerate(results, 1):
        status = "✅ PASS" if r.passed else "❌ FAIL"
        assertion_detail = (
            f"{sum(1 for _, ok in r.assertions if ok)}/{len(r.assertions)}"
        )
        lines.append(
            f"| {i} | `{r.name}` | {status} | {r.elapsed_ms:.1f} | {assertion_detail} |"
        )

    lines.append("")

    # Detailed results
    lines.append("## Detailed Results\n")
    for i, r in enumerate(results, 1):
        status = "✅ PASS" if r.passed else "❌ FAIL"
        lines.append(f"### {i}. `{r.name}` — {status}\n")
        lines.append(f"**Execution time:** {r.elapsed_ms:.1f}ms\n")

        if r.error:
            lines.append("**Error:**\n")
            lines.append(f"```\n{r.error}\n```\n")

        # Assertions
        lines.append("**Assertions:**\n")
        for label, ok in r.assertions:
            mark = "✅" if ok else "❌"
            lines.append(f"- {mark} {label}")
        lines.append("")

        # Response (truncated to avoid enormous reports)
        lines.append("**Response:**\n")
        resp_display = (
            r.response
            if len(r.response) <= 2000
            else r.response[:2000] + "\n... (truncated)"
        )
        lines.append(f"```\n{resp_display}\n```\n")

        # Embed any generated PNG images referenced in the response
        png_match = re.search(r"(reports/[\w.]+\.png)", r.response)
        if png_match:
            png_rel = png_match.group(1)
            png_full = REPO_ROOT / png_rel
            if png_full.exists():
                lines.append(f"**Generated Dashboard:**\n")
                lines.append(f"![Manifold Trajectory Dashboard]({png_rel})\n")

        lines.append("---\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    print("=" * 70)
    print("  SEP MCP Server – Full Tool Validation Suite")
    print("=" * 70)
    print()

    # Re-order the execution so it naturally matches the required edge case flow
    tests = [
        ("1/16", test_ingest_repo),  # Ingest first to populate the workspace natively
        ("2/16", test_get_index_stats),  # Verify we didn't just log 0 values
        ("3/16", test_list_indexed_files),
        ("4/16", test_search_code),  # Test specific exact match querying
        ("5/16", test_get_file),
        ("6/16", test_get_file_signature),
        ("7/16", test_compute_signature),
        ("8/16", test_verify_snippet),
        ("9/16", test_search_by_structure),
        ("10/16", test_inject_fact),  # Edge case: Memory injection & Visibility
        ("11/16", test_remove_fact),  # Edge case: Target removal
        ("12/16", test_start_watcher_and_cli_updates),  # Edge case: Live CLI overrides
        ("13/16", test_analyze_code_chaos),  # Deep dive architecture tools
        ("14/16", test_batch_chaos_scan),
        ("15/16", test_predict_structural_ejection),
        ("16/16", test_visualize_manifold_trajectory),
    ]

    results: List[ToolTestResult] = []
    for label, test_fn in tests:
        tool_name = test_fn.__name__.replace("test_", "")
        print(f"  [{label}] Testing {tool_name} ...", end=" ", flush=True)
        try:
            r = test_fn()
        except Exception:
            r = ToolTestResult(tool_name)
            r.error = traceback.format_exc()
            r.finalize()
        results.append(r)
        status = "✅" if r.passed else "❌"
        print(f"{status}  ({r.elapsed_ms:.0f}ms)")

    print()

    # Generate and write report
    report = generate_report(results)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"📄 Report written to: {REPORT_PATH}")

    # Print summary
    passed = sum(1 for r in results if r.passed)
    failed = len(results) - passed
    print()
    if failed == 0:
        print(f"✅ ALL {len(results)} TOOLS PASSED")
    else:
        print(f"❌ {failed}/{len(results)} TOOLS FAILED:")
        for r in results:
            if not r.passed:
                failed_checks = [label for label, ok in r.assertions if not ok]
                print(f"   - {r.name}: {', '.join(failed_checks)}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
