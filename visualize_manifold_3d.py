import sys
import os
import json
import argparse
from pathlib import Path

# Add project root to sys.path
REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Attempt to import dependencies early
try:
    import pandas as pd
    import plotly.express as px
except ImportError:
    print("Error: Please install pandas and plotly: pip install pandas plotly")
    sys.exit(1)

from mcp_server import _get_valkey, FILE_HASH_PREFIX, _decompress


def generate_3d_plot(pattern="*"):
    v = _get_valkey()
    if not v.ping():
        print("Valkey not reachable. Please ensure the server is running.")
        sys.exit(1)

    print(f"Querying valkey for pattern: {pattern}")
    data = []

    # Simple fnmatch check
    from fnmatch import fnmatch

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
            # Parse 'c0.445_s0.000_e0.934'
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

            # Determine grouping by top-level folder
            path_parts = Path(rel_path).parts
            if len(path_parts) > 1:
                group = path_parts[0]
            else:
                group = "/"

            data.append(
                {
                    "File": rel_path,
                    "Directory": group,
                    "Coherence": c,
                    "Entropy": e,
                    "ChaosHazard": chaos,
                    "Stability": s,
                }
            )
        except Exception as exc:
            pass  # Skip problematic files

    if not data:
        print(
            f"No structural data found for pattern: '{pattern}'. Try re-ingesting the repo."
        )
        sys.exit(1)

    df = pd.DataFrame(data)
    print(
        f"Extracted {len(df)} files with structural signatures. Generating 3D plot..."
    )

    # Determine bounds based on actual data but cap to sensible phase space
    fig = px.scatter_3d(
        df,
        x="Coherence",
        y="Entropy",
        z="ChaosHazard",
        color="Directory",
        hover_name="File",
        hover_data=["Stability"],
        title="Structural Manifold Phase Space",
        opacity=0.8,
        color_discrete_sequence=px.colors.qualitative.Plotly,
    )

    # Emphasize visual layout to reflect the "Probability Volume"
    fig.update_layout(
        scene=dict(
            xaxis_title="Coherence (C)",
            yaxis_title="Entropy (E)",
            zaxis_title="Chaos (Hazard)",
            xaxis=dict(
                range=[
                    max(0.0, df["Coherence"].min() - 0.05),
                    min(1.0, df["Coherence"].max() + 0.05),
                ]
            ),
            yaxis=dict(
                range=[
                    max(0.0, df["Entropy"].min() - 0.05),
                    min(1.0, df["Entropy"].max() + 0.05),
                ]
            ),
            zaxis=dict(
                range=[
                    max(0.0, df["ChaosHazard"].min() - 0.05),
                    min(1.0, df["ChaosHazard"].max() + 0.05),
                ]
            ),
        ),
        margin=dict(l=0, r=0, b=0, t=50),
        legend=dict(title="Top-Level Directory"),
    )

    # Save the interactive map to HTML
    output_file = "manifold_3d_scatter.html"
    fig.write_html(output_file, auto_open=False)
    print(
        f"✅ Generated 3D Phase Space Visualization -> \nfile://{Path(output_file).resolve()}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate 3D Phase Space Visualization of Codebase"
    )
    parser.add_argument(
        "--pattern", type=str, default="*", help="Glob pattern to filter files"
    )
    args = parser.parse_args()
    generate_3d_plot(args.pattern)
