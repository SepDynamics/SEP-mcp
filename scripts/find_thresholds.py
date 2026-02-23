import json
import numpy as np
import os
import sys

# Ensure imports work from /sep/structural-manifold-compression/SEP-mcp
sys.path.insert(0, "/sep/structural-manifold-compression/SEP-mcp")

from src.manifold.valkey_client import ValkeyWorkingMemory
import faiss


def get_thresholds():
    v = ValkeyWorkingMemory()
    if not v.ping():
        print("Valkey not reachable.")
        return

    def _decompress(data: bytes) -> bytes:
        import zstandard

        dctx = zstandard.ZstdDecompressor()
        return dctx.decompress(data)

    hazards = []
    coherences = []
    entropies = []

    FILE_HASH_PREFIX = "manifold:file:"

    for key_bytes in v.raw_r.scan_iter(
        f"{FILE_HASH_PREFIX}*".encode("utf-8"), count=500
    ):
        try:
            # Get Chaos
            raw_chaos = v.raw_r.hget(key_bytes, b"chaos")
            if raw_chaos:
                js_bytes = _decompress(raw_chaos)
                js = js_bytes.decode("utf-8", errors="replace")
                chaos_data = json.loads(js)
                chaos = float(chaos_data.get("chaos_score", 0.0))
                if chaos > 0.0:
                    hazards.append(chaos)

            # Get C, S, E from Sig
            raw_sig = v.raw_r.hget(key_bytes, b"sig")
            if raw_sig:
                sig_str = raw_sig.decode("utf-8", errors="replace")
                parts = sig_str.split("_")
                if len(parts) == 3:
                    c = float(parts[0][1:])
                    e = float(parts[2][1:])
                    coherences.append(c)
                    entropies.append(e)

        except Exception:
            pass

    if not hazards:
        print("No hazard scores found. Run ingest_repo first?")
        return

    hazards = np.array(hazards, dtype=np.float32).reshape(-1, 1)

    # Cluster into 3 groups
    kmeans = faiss.Kmeans(d=1, k=3, niter=50, verbose=False)
    kmeans.train(hazards)

    centroids = kmeans.centroids.flatten()
    centroids.sort()

    print(f"Total files analyzed: {len(hazards)}")
    print(f"Chaos Percentile 33.3%: {np.percentile(hazards, 33.3):.3f}")
    print(f"Chaos Percentile 66.6%: {np.percentile(hazards, 66.6):.3f}")

    if coherences and entropies:
        print(
            f"Coherence Percentile 33.3% (Sparse): {np.percentile(coherences, 33.3):.3f}"
        )
        print(
            f"Coherence Percentile 66.6% (Simple): {np.percentile(coherences, 66.6):.3f}"
        )
        print(
            f"Entropy Percentile 33.3% (Low Ent): {np.percentile(entropies, 33.3):.3f}"
        )
        print(f"Entropy Percentile 66.6% (Dense): {np.percentile(entropies, 66.6):.3f}")


if __name__ == "__main__":
    get_thresholds()
