"""Structural manifold sidecar for compression + verification (RAG provenance, audit, hazard gating)."""

from __future__ import annotations

import json
import subprocess
from bisect import bisect_right
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple

FORMAT_VERSION = "1"


@dataclass
class EncodedWindow:
    """Single encoded window with offsets and hazard."""

    signature: str
    hazard: float
    entropy: float
    coherence: float
    byte_start: int
    byte_end: int
    char_start: int
    char_end: int
    window_index: int

    def to_dict(self) -> Dict[str, object]:
        return {
            "signature": self.signature,
            "hazard": self.hazard,
            "entropy": self.entropy,
            "coherence": self.coherence,
            "byte_start": self.byte_start,
            "byte_end": self.byte_end,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "window_index": self.window_index,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "EncodedWindow":
        return cls(
            signature=str(data.get("signature", "")),
            hazard=float(data.get("hazard", 0.0) or 0.0),  # type: ignore
            entropy=float(data.get("entropy", 0.0) or 0.0),  # type: ignore
            coherence=float(data.get("coherence", 0.0) or 0.0),  # type: ignore
            byte_start=int(data.get("byte_start", 0) or 0),  # type: ignore
            byte_end=int(data.get("byte_end", 0) or 0),  # type: ignore
            char_start=int(data.get("char_start", 0) or 0),  # type: ignore
            char_end=int(data.get("char_end", 0) or 0),  # type: ignore
            window_index=int(data.get("window_index", 0) or 0),  # type: ignore
        )


@dataclass
class EncodeResult:
    """Encoding result for a single text span."""

    windows: List[EncodedWindow]
    prototypes: Dict[str, str]
    hazards: List[float]
    window_bytes: int
    stride_bytes: int
    precision: int
    hazard_percentile: float
    hazard_threshold: float
    original_bytes: int

    def to_dict(self) -> Dict[str, object]:
        return {
            "meta": {
                "window_bytes": self.window_bytes,
                "stride_bytes": self.stride_bytes,
                "precision": self.precision,
                "hazard_percentile": self.hazard_percentile,
                "hazard_threshold": self.hazard_threshold,
                "original_bytes": self.original_bytes,
                "windows": len(self.windows),
                "unique_signatures": len(self.prototypes),
            },
            "windows": [w.to_dict() for w in self.windows],
            "prototypes": self.prototypes,
            "hazards": self.hazards,
        }


@dataclass
class ManifoldIndex:
    """Hazard-gated manifold index."""

    meta: Dict[str, object]
    signatures: Dict[str, Dict[str, object]]
    documents: Dict[str, Dict[str, object]]

    def to_dict(self) -> Dict[str, object]:
        """Serialise index with stable format version and hazard gate."""

        hazard_threshold = self.meta.get("hazard_threshold", 0.0)
        return {
            "format_version": FORMAT_VERSION,
            "hazard_threshold": hazard_threshold,
            "meta": self.meta,
            "signatures": self.signatures,
            "documents": self.documents,
        }


@dataclass
class VerificationResult:
    """Verification response for a snippet."""

    verified: bool
    coverage: float
    match_ratio: float
    coverage_threshold: float
    hazard_threshold: float
    total_windows: int
    gated_hits: int
    matches: List[Dict[str, object]]
    matched_documents: List[str]
    reconstruction: str | None = None

    def to_dict(self) -> Dict[str, object]:
        payload = {
            "verified": self.verified,
            "coverage": self.coverage,
            "match_ratio": self.match_ratio,
            "coverage_threshold": self.coverage_threshold,
            "hazard_threshold": self.hazard_threshold,
            "total_windows": self.total_windows,
            "gated_hits": self.gated_hits,
            "matches": self.matches,
            "matched_documents": self.matched_documents,
        }
        if self.reconstruction is not None:
            payload["reconstruction"] = self.reconstruction
        return payload


def _build_byte_index(text: str) -> List[int]:
    offsets = [0]
    for ch in text:
        offsets.append(offsets[-1] + len(ch.encode("utf-8")))
    return offsets


def _byte_to_char(byte_offset: int, byte_index: Sequence[int]) -> int:
    return max(0, bisect_right(byte_index, byte_offset) - 1)


def _extract_text(record: object, text_key: str) -> str:
    if isinstance(record, dict):
        value = record.get(text_key)
    else:
        value = None
    if value is None:
        raise KeyError(f"Missing text field '{text_key}' in record: {record}")
    if not isinstance(value, str):
        value = str(value)
    return value


def _iter_text_directory(root: Path, text_key: str) -> Iterable[Tuple[str, str]]:
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        suffix = path.suffix.lower()
        if suffix not in {".txt", ".jsonl", ".ndjson", ".json", ".tokens"}:
            continue
        relative = path.relative_to(root).as_posix()
        base = relative[: -len(path.suffix)] if path.suffix else relative
        base_id = base.replace("/", "__")
        if suffix in {".txt", ".tokens"}:
            with open(path, "r", encoding="utf-8") as f:
                chunk = []
                chunk_index = 0
                for line in f:
                    chunk.append(line)
                    if len(chunk) >= 10000:
                        yield f"{base_id}__chunk{chunk_index:05d}", "".join(chunk)
                        chunk = []
                        chunk_index += 1
                if chunk:
                    yield f"{base_id}__chunk{chunk_index:05d}", "".join(chunk)
        elif suffix in {".jsonl", ".ndjson"}:
            yield from _iter_jsonl_file(path, text_key, doc_prefix=base_id)
        elif suffix == ".json":
            yield from _iter_json_file(path, text_key, doc_prefix=base_id)


def _iter_jsonl_file(
    path: Path, text_key: str, doc_prefix: str | None = None
) -> Iterable[Tuple[str, str]]:
    with path.open("r", encoding="utf-8") as handle:
        for idx, line in enumerate(handle):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = _extract_text(record, text_key)
            prefix = doc_prefix or path.stem
            doc_id = f"{prefix}__{idx:07d}"
            yield doc_id, text


def _iter_json_file(
    path: Path, text_key: str, doc_prefix: str | None = None
) -> Iterable[Tuple[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    prefix = doc_prefix or path.stem
    if isinstance(data, list):
        for idx, record in enumerate(data):
            text = _extract_text(record, text_key)
            yield f"{prefix}__{idx:07d}", text
        return
    if isinstance(data, dict):
        text = _extract_text(data, text_key)
        yield prefix, text
        return
    raise TypeError(f"Unsupported JSON structure in {path}")


def iter_text_documents(
    root: Path, json_text_key: str = "text"
) -> Iterable[Tuple[str, str]]:
    if root.is_dir():
        yield from _iter_text_directory(root, json_text_key)
        return
    suffix = root.suffix.lower()
    if suffix in {".jsonl", ".ndjson"}:
        yield from _iter_jsonl_file(root, json_text_key)
        return
    if suffix == ".json":
        yield from _iter_json_file(root, json_text_key)
        return
    yield root.stem, root.read_text(encoding="utf-8")


def sliding_windows(
    data: bytes, window_bytes: int, stride_bytes: int
) -> Iterable[Tuple[int, bytes]]:
    if not data:
        return
    if len(data) <= window_bytes:
        yield 0, data
        return
    for offset in range(0, len(data) - window_bytes + 1, stride_bytes):
        yield offset, data[offset : offset + window_bytes]
    tail_start = len(data) - window_bytes
    if tail_start % stride_bytes != 0:
        yield tail_start, data[tail_start:]


def encode_text(
    text: str,
    window_bytes: int = 512,
    stride_bytes: int = 384,
    precision: int = 3,
    use_native: bool = False,
    hazard_percentile: float = 0.8,
) -> EncodeResult:
    """Encode text into manifold signatures with hazard stats.

    Slides byte windows, computes signatures + hazards, and returns windows, prototypes, and hazard gates.
    """

    text_bytes = text.encode("utf-8")
    byte_index = _build_byte_index(text)

    windows: List[EncodedWindow] = []
    prototypes: Dict[str, str] = {}
    hazards: List[float] = []

    if not text_bytes:
        return EncodeResult(
            windows=[],
            prototypes={},
            hazards=[],
            window_bytes=window_bytes,
            stride_bytes=stride_bytes,
            precision=precision,
            hazard_percentile=hazard_percentile,
            hazard_threshold=0.0,
            original_bytes=0,
        )

    cmd = [
        str(Path(__file__).resolve().parent.parent.parent / "src/bin/byte_stream_manifold"),
        "--fd", "0",
        "--window-bytes", str(window_bytes),
        "--step-bytes", str(stride_bytes),
        "--signature-precision", str(precision)
    ]
    
    result = subprocess.run(cmd, input=text_bytes, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"byte_stream_manifold failed: {result.stderr.decode('utf-8', errors='replace')}")
        
    try:
        parsed = json.loads(result.stdout.decode("utf-8", errors="replace"))
    except json.JSONDecodeError:
        parsed = {"windows": []}

    for w in parsed.get("windows", []):
        signature = w.get("signature", "")
        hazard = float(w.get("lambda_hazard", 0.0))
        metrics = w.get("metrics", {})
        entropy = float(metrics.get("entropy", 0.0))
        coherence = float(metrics.get("coherence", 0.0))
        byte_start = int(w.get("offset_bytes", 0))
        byte_end = min(byte_start + window_bytes, len(text_bytes))
        char_start = _byte_to_char(byte_start, byte_index)
        char_end = _byte_to_char(byte_end, byte_index)
        window_index = int(w.get("index", 0))

        windows.append(
            EncodedWindow(
                signature=signature,
                hazard=hazard,
                entropy=entropy,
                coherence=coherence,
                byte_start=byte_start,
                byte_end=byte_end,
                char_start=char_start,
                char_end=char_end,
                window_index=window_index,
            )
        )

        if signature not in prototypes:
            prototypes[signature] = text_bytes[byte_start:byte_end].decode(
                "utf-8", errors="replace"
            )
        hazards.append(hazard)

    hazards.sort()
    if hazards:
        idx = int(hazard_percentile * (len(hazards) - 1))
        hazard_threshold = hazards[idx]
    else:
        hazard_threshold = 0.0
    return EncodeResult(
        windows=windows,
        prototypes=prototypes,
        hazards=hazards,
        window_bytes=window_bytes,
        stride_bytes=stride_bytes,
        precision=precision,
        hazard_percentile=hazard_percentile,
        hazard_threshold=hazard_threshold,
        original_bytes=len(text_bytes),
    )


def encode_text_to_windows(
    text: str,
    window_bytes: int = 512,
    stride_bytes: int = 384,
    precision: int = 3,
    use_native: bool = False,
    hazard_percentile: float = 0.8,
) -> Tuple[List[EncodedWindow], Dict[str, str], List[float]]:
    """Backward-compatible helper returning windows/prototypes/hazards."""

    result = encode_text(
        text,
        window_bytes=window_bytes,
        stride_bytes=stride_bytes,
        precision=precision,
        use_native=use_native,
        hazard_percentile=hazard_percentile,
    )
    return result.windows, result.prototypes, result.hazards


def _finalise_hazard_stats(raw: MutableMapping[str, float]) -> Dict[str, float]:
    count = int(raw.get("count", 0))
    total = float(raw.get("sum", 0.0))
    mean = total / count if count else 0.0
    return {
        "count": float(count),
        "min": float(raw.get("min", 0.0)),
        "max": float(raw.get("max", 0.0)),
        "mean": mean,
    }


def _aggregate_index(
    docs: Mapping[str, str],
    window_bytes: int,
    stride_bytes: int,
    precision: int,
    hazard_percentile: float,
    use_native: bool,
    store_windows: bool,
) -> ManifoldIndex:
    signatures: Dict[str, Dict[str, object]] = {}
    documents: Dict[str, Dict[str, object]] = {}
    hazards: List[float] = []
    total_windows = 0

    for doc_id, text in docs.items():
        encoded = encode_text(
            text,
            window_bytes=window_bytes,
            stride_bytes=stride_bytes,
            precision=precision,
            use_native=use_native,
            hazard_percentile=hazard_percentile,
        )
        hazards.extend(encoded.hazards)
        total_windows += len(encoded.windows)

        doc_entry: Dict[str, object] = {
            "characters": len(text),
            "bytes": len(text.encode("utf-8")),
            "window_count": len(encoded.windows),
        }
        if store_windows:
            doc_entry["windows"] = [window.to_dict() for window in encoded.windows]
        documents[doc_id] = doc_entry

        for window in encoded.windows:
            entry = signatures.get(window.signature)
            if entry is None:
                entry = {
                    "prototype": {
                        "text": encoded.prototypes[window.signature],
                        "doc_id": doc_id,
                        "byte_start": window.byte_start,
                        "byte_end": window.byte_end,
                    },
                    "occurrences": [],
                    "hazard": {"count": 0.0, "sum": 0.0, "min": 1.0, "max": 0.0},
                }
                signatures[window.signature] = entry

            occurrences = entry.get("occurrences")
            if isinstance(occurrences, list):
                occurrences.append(
                    {
                        "doc_id": doc_id,
                        "byte_start": window.byte_start,
                        "byte_end": window.byte_end,
                        "hazard": window.hazard,
                    }
                )

            stats = entry.get("hazard")
            if isinstance(stats, dict):
                stats["count"] += 1.0
                stats["sum"] += window.hazard
                stats["min"] = min(float(stats.get("min", 1.0)), window.hazard)
                stats["max"] = max(float(stats.get("max", 0.0)), window.hazard)

    hazards.sort()
    if hazards:
        idx = int(hazard_percentile * (len(hazards) - 1))
        hazard_threshold = hazards[idx]
    else:
        hazard_threshold = 0.0

    for sig, entry in signatures.items():
        stats = entry.get("hazard")
        if isinstance(stats, dict):
            entry["hazard"] = _finalise_hazard_stats(stats)

    meta: Dict[str, object] = {
        "window_bytes": window_bytes,
        "stride_bytes": stride_bytes,
        "precision": precision,
        "hazard_percentile": hazard_percentile,
        "hazard_threshold": hazard_threshold,
        "total_documents": len(docs),
        "total_windows": total_windows,
        "unique_signatures": len(signatures),
    }

    return ManifoldIndex(meta=meta, signatures=signatures, documents=documents)


def build_index(
    docs: Mapping[str, str],
    window_bytes: int = 512,
    stride_bytes: int = 384,
    precision: int = 3,
    hazard_percentile: float = 0.8,
    use_native: bool = False,
    store_windows: bool = True,
) -> ManifoldIndex:
    """Build an in-memory manifold index from a mapping of doc_id -> text."""

    return _aggregate_index(
        docs=docs,
        window_bytes=window_bytes,
        stride_bytes=stride_bytes,
        precision=precision,
        hazard_percentile=hazard_percentile,
        use_native=use_native,
        store_windows=store_windows,
    )


def build_manifold_index(
    text_root: Path,
    window_bytes: int = 512,
    stride_bytes: int = 384,
    precision: int = 3,
    hazard_percentile: float = 0.8,
    json_text_key: str = "text",
    max_documents: int | None = None,
    document_offset: int = 0,
    use_native: bool = False,
    store_windows: bool = True,
) -> Dict[str, object]:
    """Build an index from a directory/JSONL corpus (CLI helper)."""

    docs: Dict[str, str] = {}
    processed = 0
    for doc_index, (doc_id, text) in enumerate(
        iter_text_documents(text_root, json_text_key=json_text_key)
    ):
        if doc_index < max(document_offset, 0):
            continue
        if max_documents is not None and processed >= max_documents:
            break
        processed += 1
        docs[doc_id] = text

    index = _aggregate_index(
        docs=docs,
        window_bytes=window_bytes,
        stride_bytes=stride_bytes,
        precision=precision,
        hazard_percentile=hazard_percentile,
        use_native=use_native,
        store_windows=store_windows,
    )

    index.meta.update(
        {
            "text_root": str(text_root),
            "json_text_key": json_text_key,
            "max_documents": max_documents,
            "document_offset": document_offset,
        }
    )
    return index.to_dict()


def reconstruct_from_windows(
    windows: Sequence[Mapping[str, object] | EncodedWindow],
    prototypes: Mapping[str, Mapping[str, object] | str],
) -> str:
    """Reconstruct text by overlapping prototype spans following window offsets."""

    if not windows:
        return ""

    def _prototype_bytes(signature: str) -> bytes:
        proto = prototypes.get(signature)
        if proto is None:
            return b""
        if isinstance(proto, str):
            return proto.encode("utf-8", errors="replace")
        text = proto.get("text", "")
        return str(text).encode("utf-8", errors="replace")

    def _window_dict(win: Mapping[str, object] | EncodedWindow) -> Mapping[str, object]:
        if isinstance(win, EncodedWindow):
            return win.to_dict()
        return win

    sorted_windows = sorted(
        (_window_dict(w) for w in windows),
        key=lambda item: int(item.get("byte_start", 0) or 0),  # type: ignore
    )
    result = bytearray()
    for window in sorted_windows:
        signature = str(window.get("signature", ""))
        chunk = _prototype_bytes(signature)
        start = int(window.get("byte_start", 0) or 0)  # type: ignore
        if not chunk and len(result) < start:
            continue
        if len(result) < start:
            gap = start - len(result)
            result.extend(chunk[:gap])
        overlap = len(result) - start
        if overlap < 0:
            overlap = 0
        if overlap >= len(chunk):
            continue
        result.extend(chunk[overlap:])
    return result.decode("utf-8", errors="replace")


def verify_snippet(
    text: str,
    index: ManifoldIndex | Mapping[str, object],
    *,
    hazard_threshold: float | None = None,
    coverage_threshold: float = 0.5,
    window_bytes: int | None = None,
    stride_bytes: int | None = None,
    precision: int | None = None,
    use_native: bool = False,
    include_reconstruction: bool = False,
) -> VerificationResult:
    """Verify a snippet by matching signatures and gating by hazard.

    Coverage = low-hazard matched windows / total windows. Uses hazard gate from index unless overridden.
    """

    meta = (
        index.meta
        if isinstance(index, ManifoldIndex)
        else (index.get("meta", {}) if isinstance(index, Mapping) else {})
    )
    signatures = index.signatures if isinstance(index, ManifoldIndex) else index.get("signatures", {})  # type: ignore[arg-type]

    window_bytes = window_bytes or int(meta.get("window_bytes", 512) if isinstance(meta, dict) else 512)
    stride_bytes = stride_bytes or int(meta.get("stride_bytes", 384) if isinstance(meta, dict) else 384)
    precision = precision or int(meta.get("precision", 3) if isinstance(meta, dict) else 3)
    hazard_threshold = (
        hazard_threshold
        if hazard_threshold is not None
        else float(meta.get("hazard_threshold", 0.0) if isinstance(meta, dict) else 0.0)
    )

    encoded = encode_text(
        text,
        window_bytes=window_bytes,
        stride_bytes=stride_bytes,
        precision=precision,
        use_native=use_native,
    )
    windows = encoded.windows

    matched_windows = 0
    gated_hits = 0
    total_windows = len(windows)
    matched_documents: set[str] = set()
    matches: List[Dict[str, object]] = []

    for window in windows:
        entry = signatures.get(window.signature, {}) if isinstance(signatures, dict) else {}
        if not entry:
            continue

        matched_windows += 1
        matches.append(
            {
                "window_index": window.window_index,
                "signature": window.signature,
                "hazard": window.hazard,
                "byte_start": window.byte_start,
                "byte_end": window.byte_end,
                "char_start": window.char_start,
                "char_end": window.char_end,
            }
        )

        if window.hazard <= hazard_threshold:
            gated_hits += 1

        occurrences = entry.get("occurrences", []) if isinstance(entry, dict) else []
        if isinstance(occurrences, list):
            for occ in occurrences:
                if isinstance(occ, dict) and "doc_id" in occ:
                    matched_documents.add(str(occ["doc_id"]))

    coverage = gated_hits / total_windows if total_windows else 0.0
    match_ratio = len(matches) / total_windows if total_windows else 0.0

    reconstruction = None
    if include_reconstruction:
        prototypes = {
            sig: sig_entry.get("prototype", {}) if isinstance(sig_entry, dict) else {} for sig, sig_entry in (signatures.items() if isinstance(signatures, dict) else [])
        }
        reconstruction = reconstruct_from_windows(encoded.windows, prototypes)

    return VerificationResult(
        verified=coverage >= coverage_threshold,
        coverage=coverage,
        match_ratio=match_ratio,
        coverage_threshold=coverage_threshold,
        hazard_threshold=hazard_threshold,
        total_windows=total_windows,
        gated_hits=gated_hits,
        matches=matches,
        matched_documents=sorted(doc for doc in matched_documents if doc),
        reconstruction=reconstruction,
    )


def load_index(path: Path) -> ManifoldIndex:
    """Load an index from JSON on disk and validate format version."""

    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid index payload in {path}")
    version = str(data.get("format_version", "") or "")
    if version and version != FORMAT_VERSION:
        raise ValueError(
            f"Unsupported index version {version}, expected {FORMAT_VERSION}"
        )
    hazard_threshold = data.get("hazard_threshold")
    meta = data.get("meta", {})
    if hazard_threshold is not None:
        meta.setdefault("hazard_threshold", hazard_threshold)
    signatures = data.get("signatures", {})
    documents = data.get("documents", {})
    return ManifoldIndex(meta=meta, signatures=signatures, documents=documents)
