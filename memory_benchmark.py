import sys
import time

sys.path.insert(0, "/sep/structural-manifold-compression/SEP-mcp")

from mcp_server import ingest_repo, get_index_stats


def main():
    print("Ingesting CPython with memory-optimized hashes (lite mode)...")
    res = ingest_repo(
        root_dir="cpython",
        max_bytes_per_file=512_000,
        clear_first=True,
        compute_chaos=True,
        lite=True,
    )
    print("\n--- INGEST RESULT ---")
    print(res)

    print("\n--- INDEX STATS ---")
    stats = get_index_stats()
    print(stats)


if __name__ == "__main__":
    main()
