import ast
import faiss
import zstandard as zstd
import json
import base64
from dataclasses import dataclass
from typing import List, Dict, Optional, Any

# Ensure sentence-transformers is available
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


@dataclass
class SemanticNode:
    """Represents a semantic code chunk (function or class) in a file."""

    id: str
    file_path: str
    node_type: str  # 'function' or 'class'
    name: str
    signature: str
    docstring: str
    content: str
    start_line: int
    end_line: int

    def to_text(self) -> str:
        """Serialize for lightweight payload."""
        return f"{self.node_type} {self.name}{self.signature}:\n {self.docstring}"


class ASTSemanticExtractor(ast.NodeVisitor):
    """Extracts functions and classes from Python AST."""

    def __init__(self, file_path: str, source_code: str):
        self.file_path = file_path
        self.source_code = source_code
        self.source_lines = source_code.splitlines()
        self.nodes: List[SemanticNode] = []

    def _extract_text(self, node: ast.AST) -> str:
        if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
            return ""
        start = node.lineno - 1
        end = node.end_lineno
        return "\n".join(self.source_lines[start:end])

    def _get_signature(self, node: ast.AST) -> str:
        if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
            args = []
            if node.args.args:
                args = [a.arg for a in node.args.args]
            return f"({', '.join(args)})"
        return ""

    def visit_ClassDef(self, node: ast.ClassDef):
        docstring = ast.get_docstring(node) or ""
        content = self._extract_text(node)

        # Don't embed massive classes entirely, rely on methods
        if node.end_lineno and node.lineno and (node.end_lineno - node.lineno < 150):
            self.nodes.append(
                SemanticNode(
                    id=f"{self.file_path}:{node.name}",
                    file_path=self.file_path,
                    node_type="class",
                    name=node.name,
                    signature="",
                    docstring=docstring,
                    content=content,
                    start_line=node.lineno,
                    end_line=node.end_lineno or node.lineno,
                )
            )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._handle_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._handle_function(node)

    def _handle_function(self, node: ast.AST):
        docstring = ast.get_docstring(node) or ""
        content = self._extract_text(node)
        signature = self._get_signature(node)

        self.nodes.append(
            SemanticNode(
                id=f"{self.file_path}:{node.name}",
                file_path=self.file_path,
                node_type="function",
                name=node.name,
                signature=signature,
                docstring=docstring,
                content=content,
                start_line=node.lineno,
                end_line=node.end_lineno or node.lineno,
            )
        )
        self.generic_visit(node)


def extract_semantic_nodes(file_path: str, source_code: str) -> List[SemanticNode]:
    """Parse python source code into chunked semantic nodes."""
    try:
        tree = ast.parse(source_code, filename=file_path)
        extractor = ASTSemanticExtractor(file_path, source_code)
        extractor.visit(tree)
        return extractor.nodes
    except Exception:
        return []


class SemanticIndex:
    """O(1) Semantic Search FAISS Engine across code structures."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self.index: Optional[faiss.IndexFlatL2] = None
        self.metadata: Dict[int, Dict[str, Any]] = {}  # FAISS idx -> Node meta
        self.dim = 384  # Default for MiniLM

    @property
    def model(self):
        if self._model is None and SentenceTransformer is not None:
            import logging

            logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def build_index(self, nodes: List[SemanticNode]):
        """Build or rebuild the FAISS index from scratch with given nodes."""
        if not self.model or not nodes:
            return

        texts = [n.to_text() for n in nodes]
        embeddings = self.model.encode(
            texts, convert_to_numpy=True, show_progress_bar=False
        )

        if self.index is None or self.index.d != embeddings.shape[1]:
            self.dim = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(self.dim)

        self.index.reset()
        self.metadata.clear()

        self.index.add(embeddings.astype("float32"))

        for idx, n in enumerate(nodes):
            self.metadata[idx] = {
                "id": n.id,
                "file_path": n.file_path,
                "node_type": n.node_type,
                "name": n.name,
                "start_line": n.start_line,
                "end_line": n.end_line,
            }

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """O(1) retrieval of semantically matched functions/classes."""
        if not self.model or not self.index or self.index.ntotal == 0:
            return []

        query_emb = self.model.encode([query], convert_to_numpy=True).astype("float32")
        distances, indices = self.index.search(query_emb, min(top_k, self.index.ntotal))

        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx in self.metadata:
                idx_int = int(idx)
                res = self.metadata[idx_int].copy()
                res["score"] = float(distances[0][i])
                results.append(res)
        return results

    def serialize(self) -> bytes:
        """Serialize index and metadata for Valkey storage."""
        if not self.index:
            return b""

        # Serialize FAISS index
        import faiss.contrib.torch_utils

        index_bytes = faiss.serialize_index(self.index)

        # Serialize Metadata
        meta_json = json.dumps(self.metadata).encode("utf-8")

        # Create combined payload
        payload = {
            "dim": self.dim,
            "faiss": base64.b64encode(index_bytes).decode("ascii"),
            "meta": base64.b64encode(meta_json).decode("ascii"),
        }

        raw_json = json.dumps(payload).encode("utf-8")
        ctx = zstd.ZstdCompressor(level=3)
        return ctx.compress(raw_json)

    def deserialize(self, data: bytes):
        """Deserialize from Valkey storage."""
        if not data:
            return

        import base64

        try:
            ctx = zstd.ZstdDecompressor()
            raw_json = ctx.decompress(data).decode("utf-8")
            payload = json.loads(raw_json)

            index_bytes = base64.b64decode(payload["faiss"])
            self.index = faiss.deserialize_index(index_bytes)
            self.dim = payload.get("dim", self.index.d)

            meta_json = base64.b64decode(payload["meta"]).decode("utf-8")
            meta_dict = json.loads(meta_json)
            # JSON dict keys are strings, convert back to int
            self.metadata = {int(k): v for k, v in meta_dict.items()}
        except Exception as e:
            print(f"Failed to deserialize semantic index: {e}")
