import valkey
import json
import zstandard as zstd
import base64
from typing import Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .sidecar import ManifoldIndex


class ValkeyWorkingMemory:
    """
    Live connection to the Valkey (Redis) Working Memory database.
    Replaces the ephemeral IN_MEMORY_DOCS dictionary.
    """

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.r = valkey.Redis(host=host, port=port, db=db, decode_responses=True)
        self.doc_prefix = "manifold:docs:"
        self.index_key = "manifold:active_index"

    def ping(self) -> bool:
        """Check if Valkey is alive."""
        try:
            return self.r.ping()
        except valkey.ConnectionError:
            return False

    def add_document(self, doc_id: str, text: str) -> None:
        """Store a document's raw text in Valkey."""
        self.r.set(f"{self.doc_prefix}{doc_id}", text)
        self.invalidate_index()

    def remove_document(self, doc_id: str) -> None:
        """Remove a stored document from Valkey."""
        self.r.delete(f"{self.doc_prefix}{doc_id}")
        self.invalidate_index()

    def get_all_documents(self) -> Dict[str, str]:
        """Retrieve all ingested documents from Valkey.
        Note: Now retrieves from the HGET hashes structure from mcp_server.py.
        """
        docs = {}
        file_hash_prefix = "manifold:file:"

        for key in self.r.scan_iter(f"{file_hash_prefix}*"):
            doc_id = key[len(file_hash_prefix) :]
            raw = self.r.hget(key, "doc")
            if not raw:
                continue

            # Assume it's compressed using the MCP server mechanism
            try:
                ctx = zstd.ZstdDecompressor()
                content = ctx.decompress(raw.encode("latin1")).decode("utf-8")
            except Exception:
                content = raw

            docs[doc_id] = content
        return docs

    def store_cached_index(self, index: "ManifoldIndex") -> None:
        """Cache the computed ManifoldIndex in Valkey for instant retrieval."""
        payload_str = json.dumps(index.to_dict())
        payload_bytes = payload_str.encode("utf-8", errors="replace")

        ctx = zstd.ZstdCompressor(level=3)
        compressed = ctx.compress(payload_bytes)
        b64_encoded = base64.b64encode(compressed).decode("ascii")

        self.r.set(self.index_key, b64_encoded)

    def get_cached_index(self) -> Optional["ManifoldIndex"]:
        """Retrieve the cached ManifoldIndex from Valkey if it exists."""
        b64_data = self.r.get(self.index_key)
        if not b64_data:
            return None

        # Decode base64 -> decompress zstd -> decode utf-8 -> parse json
        try:
            compressed = base64.b64decode(b64_data)
            ctx = zstd.ZstdDecompressor()
            json_str = ctx.decompress(compressed).decode("utf-8", errors="replace")
            parsed = json.loads(json_str)
        except Exception as e:
            print(f"Failed to load cached index: {e}")
            return None

        meta = parsed.get("meta", {})
        signatures = parsed.get("signatures", {})
        documents = parsed.get("documents", {})

        from .sidecar import ManifoldIndex

        return ManifoldIndex(meta=meta, signatures=signatures, documents=documents)

    def invalidate_index(self) -> None:
        """Clear the active index cache to force a rebuild on next access."""
        self.r.delete(self.index_key)

    def clear_all(self) -> None:
        """Wipe the entire Working Memory (for testing)."""
        for key in self.r.scan_iter("manifold:*"):
            self.r.delete(key)

    def get_or_build_index(self) -> Optional["ManifoldIndex"]:
        """Fetch the cached index from Valkey, or build and cache a new one if missing."""
        if not self.ping():
            return None

        cached = self.get_cached_index()
        if cached is not None:
            return cached

        docs = self.get_all_documents()
        if not docs:
            return None

        from .sidecar import build_index

        new_index = build_index(
            docs,
            window_bytes=512,
            stride_bytes=384,
            precision=3,
            use_native=True,
        )
        self.store_cached_index(new_index)
        return new_index
