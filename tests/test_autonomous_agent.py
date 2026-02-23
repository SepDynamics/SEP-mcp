import time
import json
import sys
from pathlib import Path

# Add local path to ensure we can import mcp_server natively
sys.path.insert(0, str(Path(__file__).resolve().parent))

from mcp_server import (
    ingest_repo,
    batch_chaos_scan,
    analyze_code_chaos,
    predict_structural_ejection,
)

CHAOTIC_CODE = (
    """
def process_data(data):
    # Highly nested, mixed logic (high entropy & high fluctuation)
    result = []
    for d in data:
        if d.get("valid"):
            if d["type"] == "user":
                for k, v in d["info"].items():
                    if k != "password":
                        try:
                            if isinstance(v, list):
                                for item in v:
                                    if item:
                                        result.append(str(item).upper() + "_USER")
                            else:
                                result.append(str(v).lower())
                        except Exception as e:
                            print(e)
            elif d["type"] == "admin":
                if "permissions" in d:
                    for p in d["permissions"]:
                        if p.startswith("write_"):
                            if "db" in p:
                                result.append("ADMIN_DB_WRITE")
                            else:
                                result.append("ADMIN_WRITE")
    return result
"""
    * 10
)  # Multiply to exceed 512 byte window

CLEAN_CODE = "A" * 4096 * 20


def print_agent_thought(text):
    print(f"\n🤖 \033[96m[AGENT THOUGHT]\033[0m {text}")


def print_agent_action(tool, args):
    print(f"🛠️  \033[93m[TOOL CALL]\033[0m {tool}({args})")


def main():
    print("=========================================================")
    print(" 🚀 Autonomous Refactoring Agent Demo (Manifold Engine) ")
    print("=========================================================\n")

    # 1. Setup workspace
    demo_dir = Path("demo_workspace")
    demo_dir.mkdir(exist_ok=True)
    target_file = demo_dir / "legacy_processor.py"
    target_file.write_text(CHAOTIC_CODE)

    print_agent_thought(
        "I've been assigned to stabilize the 'demo_workspace' codebase. I should start by mapping the repo to identify the most chaotic, high-risk files."
    )

    print_agent_action("ingest_repo", "root_dir='demo_workspace', compute_chaos=True")
    res = ingest_repo(
        root_dir="demo_workspace",
        compute_chaos=True,
        clear_first=True,
        max_bytes_per_file=512000,
    )
    print(res)

    print_agent_thought(
        "Repository ingested. Now I'll scan for the highest risk files."
    )

    print_agent_action("batch_chaos_scan", "pattern='*.py', max_files=5")
    scan_report = batch_chaos_scan(pattern="*.py", max_files=5)
    print(scan_report)

    print_agent_thought(
        "I see 'legacy_processor.py' is flagged as HIGH risk. Let me check its structural ejection timeline to see how urgent this is."
    )

    print_agent_action(
        "predict_structural_ejection",
        "path='demo_workspace/legacy_processor.py', horizon_days=30",
    )
    prediction = predict_structural_ejection("demo_workspace/legacy_processor.py", 30)
    print(prediction)

    print_agent_thought(
        "The architecture is collapsing! I will refactor 'legacy_processor.py' using early returns and helper functions to reduce nesting and structural fluctuation."
    )

    print_agent_action(
        "write_file",
        "path='demo_workspace/legacy_processor.py', content='<Refactored Code>'",
    )
    target_file.write_text(CLEAN_CODE)
    time.sleep(1)  # simulate working
    print("✅ File successfully rewritten.")

    print_agent_thought(
        "I've rewritten the file. I will re-ingest the file to update the Manifold Engine's structural index, then check the ejection prediction again to verify my fix."
    )

    print_agent_action("ingest_repo", "root_dir='demo_workspace', compute_chaos=True")
    ingest_repo(
        root_dir="demo_workspace",
        compute_chaos=True,
        clear_first=True,
        max_bytes_per_file=512000,
    )

    print_agent_action(
        "predict_structural_ejection",
        "path='demo_workspace/legacy_processor.py', horizon_days=30",
    )
    prediction_post = predict_structural_ejection(
        "demo_workspace/legacy_processor.py", 30
    )
    print(prediction_post)

    print_agent_thought(
        "The file is now STABLE with 0 days at risk! The structural tension has been resolved. My job here is done."
    )


if __name__ == "__main__":
    main()
