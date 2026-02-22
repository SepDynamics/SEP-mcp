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
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
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
INJECT_FACT_TEXT = (
    "This is a test fact injected by the MCP tool validation suite. "
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
    r = run_tool("ingest_repo", srv.ingest_repo, root_dir=".", compute_chaos=True, clear_first=False)
    r.assert_check("returns string", isinstance(r.response, str))
    r.assert_check("contains '✅'", "✅" in r.response)
    r.assert_check("contains 'Text files'", "Text files" in r.response)
    r.assert_check("contains 'Signatures'", "Signatures" in r.response)
    r.assert_check("reports zero errors", "Errors     : 0" in r.response)
    r.assert_check("no error marker", "❌" not in r.response)
    r.finalize()
    return r


def test_list_indexed_files() -> ToolTestResult:
    r = run_tool("list_indexed_files", srv.list_indexed_files, pattern="*.py", max_results=20)
    r.assert_check("returns string", isinstance(r.response, str))
    r.assert_check("contains 'Indexed files'", "Indexed files" in r.response)
    r.assert_check("lists .py files", ".py" in r.response)
    r.assert_check("no error marker", "❌" not in r.response)
    r.finalize()
    return r


def test_search_code() -> ToolTestResult:
    r = run_tool("search_code", srv.search_code, query="chaos_score", file_pattern="*.py", max_results=5)
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
    r.assert_check("contains signature format", bool(re.search(r"c[\d.]+_s[\d.]+_e[\d.]+", r.response)))
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
    r.assert_check("contains VERIFIED or FAILED", "VERIFIED" in r.response or "FAILED" in r.response)
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
    r.assert_check("contains 'structurally similar'", "structurally similar" in r.response)
    r.assert_check("shows delta values", "Δ=" in r.response)
    r.assert_check("lists file paths", ".py" in r.response or ".md" in r.response)
    r.assert_check("no error marker", "❌" not in r.response)
    r.finalize()
    return r


def test_inject_fact() -> ToolTestResult:
    """Tests inject_fact by injecting a fact and verifying it can be retrieved."""
    # Step 1: Inject the fact
    r = run_tool(
        "inject_fact",
        srv.inject_fact,
        fact_id=INJECT_FACT_ID,
        fact_text=INJECT_FACT_TEXT,
    )
    r.assert_check("returns string", isinstance(r.response, str))
    r.assert_check("contains '🚀'", "🚀" in r.response)
    r.assert_check("mentions fact_id", INJECT_FACT_ID in r.response)
    r.assert_check("mentions codebook", "Codebook" in r.response or "codebook" in r.response.lower())
    r.assert_check("no error marker", "❌" not in r.response)

    # Step 2: Verify the fact was stored in Valkey by retrieving it via get_file
    verify_resp = srv.get_file(path=INJECT_FACT_ID)
    r.assert_check(
        "fact retrievable via get_file",
        INJECT_FACT_TEXT[:40] in verify_resp,
    )
    r.assert_check(
        "retrieved fact is not an error",
        "❌" not in verify_resp,
    )

    # Step 3: Verify via direct Valkey read
    v = srv._get_valkey()
    stored = v.r.get(f"manifold:docs:{INJECT_FACT_ID}")
    r.assert_check(
        "fact stored correctly in Valkey",
        stored == INJECT_FACT_TEXT,
    )

    # Step 4: Verify the index was invalidated (active_index should be gone)
    active_idx = v.r.get("manifold:active_index")
    r.assert_check(
        "index invalidated after injection",
        active_idx is None,
    )

    # Cleanup: remove the test fact
    v.r.delete(f"manifold:docs:{INJECT_FACT_ID}")

    r.finalize()
    return r


def test_start_watcher() -> ToolTestResult:
    # Reset the global observer so we can test fresh
    srv._active_observer = None

    r = run_tool("start_watcher", srv.start_watcher, watch_dir=".")
    r.assert_check("returns string", isinstance(r.response, str))
    r.assert_check("contains '✅'", "✅" in r.response)
    r.assert_check("mentions watcher started or already running", "Watcher" in r.response or "started" in r.response)
    r.assert_check("no error marker", "❌" not in r.response)

    # Verify internal state
    r.assert_check("observer is active", srv._active_observer is not None)

    # Test idempotency – calling again should say "already running"
    second = srv.start_watcher(watch_dir=".")
    r.assert_check("idempotent – already running", "already running" in second)

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
    r.assert_check("shows risk levels", "[HIGH]" in r.response or "[MODERATE]" in r.response or "[LOW]" in r.response)
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
    r.assert_check("mentions state", "PERSISTENT_HIGH" in r.response or "OSCILLATION" in r.response or "LOW_FLUCTUATION" in r.response)
    r.assert_check("mentions file path", "mcp_server.py" in r.response)
    r.assert_check("includes score", bool(re.search(r"score: \d+\.\d+", r.response)))
    r.assert_check("no error marker", "❌" not in r.response)
    r.finalize()
    return r


def test_visualize_manifold_trajectory() -> ToolTestResult:
    r = run_tool("visualize_manifold_trajectory", srv.visualize_manifold_trajectory, path="mcp_server.py")
    r.assert_check("returns string", isinstance(r.response, str))
    r.assert_check("contains '📊'", "📊" in r.response)
    r.assert_check("mentions dashboard", "Dashboard" in r.response or "dashboard" in r.response)
    r.assert_check("references the file", "mcp_server.py" in r.response)
    r.assert_check("reports windows analyzed", "Windows analyzed" in r.response)
    r.assert_check("reports chaos score", "Chaos Score" in r.response or "Avg Chaos" in r.response)
    r.assert_check("reports symbolic states", "Symbolic States" in r.response)
    r.assert_check("reports collapse risk", "Collapse Risk" in r.response)
    r.assert_check("PNG saved", ".png" in r.response)
    r.assert_check("no error marker", "❌" not in r.response)

    # Verify the PNG was actually created
    import re as _re
    png_match = _re.search(r"reports/[\w.]+\.png", r.response)
    if png_match:
        from pathlib import Path as _Path
        png_path = _Path(__file__).resolve().parent.parent.parent / png_match.group()
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
    lines.append(f"**Status:** {'✅ ALL PASS' if failed == 0 else '❌ FAILURES DETECTED'}\n")

    # Summary table
    lines.append("## Summary\n")
    lines.append("| # | Tool | Status | Time (ms) | Assertions |")
    lines.append("|---|------|--------|-----------|------------|")
    for i, r in enumerate(results, 1):
        status = "✅ PASS" if r.passed else "❌ FAIL"
        assertion_detail = f"{sum(1 for _, ok in r.assertions if ok)}/{len(r.assertions)}"
        lines.append(f"| {i} | `{r.name}` | {status} | {r.elapsed_ms:.1f} | {assertion_detail} |")

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
        resp_display = r.response if len(r.response) <= 2000 else r.response[:2000] + "\n... (truncated)"
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

    # Ordered test list – dependencies flow naturally (ingest first, then query)
    tests = [
        ("1/15", test_get_index_stats),
        ("2/15", test_ingest_repo),
        ("3/15", test_list_indexed_files),
        ("4/15", test_search_code),
        ("5/15", test_get_file),
        ("6/15", test_get_file_signature),
        ("7/15", test_compute_signature),
        ("8/15", test_verify_snippet),
        ("9/15", test_search_by_structure),
        ("10/15", test_inject_fact),
        ("11/15", test_start_watcher),
        ("12/15", test_analyze_code_chaos),
        ("13/15", test_batch_chaos_scan),
        ("14/15", test_predict_structural_ejection),
        ("15/15", test_visualize_manifold_trajectory),
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
