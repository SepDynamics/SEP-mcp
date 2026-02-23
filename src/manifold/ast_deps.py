"""AST-based dependency analysis for computing blast radius scores.

This module parses Python source files to extract import dependencies and
calculate how many files would be impacted by changes to a given file.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set


@dataclass
class DependencyInfo:
    """Dependency information for a single file."""

    file_path: str
    imports: Set[str] = field(default_factory=set)  # Modules this file imports
    imported_by: Set[str] = field(default_factory=set)  # Files that import this
    blast_radius: int = 0  # Number of files impacted by changes
    depth: int = 0  # Longest dependency chain
    is_core: bool = False  # True if many files depend on this


class ASTDependencyAnalyzer:
    """Analyze Python AST to compute dependency graphs and blast radius."""

    def __init__(self, repo_root: Path):
        """Initialize the dependency analyzer.

        Args:
            repo_root: Path to the repository root
        """
        self.repo_root = Path(repo_root)
        self.dependencies: Dict[str, DependencyInfo] = {}
        self.module_to_file: Dict[str, str] = {}  # Map module names to file paths

    def _extract_imports(self, file_path: Path) -> Set[str]:
        """Extract all imports from a Python file.

        Args:
            file_path: Path to the Python file

        Returns:
            Set of imported module names (full paths, not truncated)
        """
        imports = set()

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Keep full module path for accurate dependency tracking
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        # Handle relative imports properly
                        prefix = "." * node.level if node.level > 0 else ""
                        imports.add(f"{prefix}{node.module}")

        except (SyntaxError, UnicodeDecodeError, OSError):
            # Skip files that can't be parsed
            pass

        return imports

    def _file_to_module(self, file_path: Path) -> str:
        """Convert a file path to a module name.

        Args:
            file_path: Path to the file

        Returns:
            Module name (e.g., 'src.manifold.sidecar')
        """
        rel_path = file_path.relative_to(self.repo_root)
        module_parts = list(rel_path.parts)

        # Remove .py extension from last part
        if module_parts[-1].endswith(".py"):
            module_parts[-1] = module_parts[-1][:-3]

        # Remove __init__ if present
        if module_parts[-1] == "__init__":
            module_parts = module_parts[:-1]

        return ".".join(module_parts)

    # Directories to skip during AST scanning (venvs, caches, build dirs)
    SKIP_DIRS = {
        ".venv", "venv", ".env", "env",
        "node_modules", "__pycache__", ".git",
        ".tox", ".mypy_cache", ".pytest_cache",
        "build", "dist", ".eggs", "*.egg-info",
        "site-packages",
    }

    def build_dependency_graph(self, file_pattern: str = "**/*.py") -> None:
        """Build the complete dependency graph for the repository.

        Args:
            file_pattern: Glob pattern to find Python files
        """
        # Find all Python files, excluding virtual environments and caches
        py_files = [
            p for p in self.repo_root.glob(file_pattern)
            if not any(skip in p.parts for skip in self.SKIP_DIRS)
        ]

        # Build module name mapping
        for py_file in py_files:
            if py_file.is_file():
                module_name = self._file_to_module(py_file)
                rel_path = str(py_file.relative_to(self.repo_root))
                self.module_to_file[module_name] = rel_path

                # Also register package names for directories with __init__.py
                if py_file.name == "__init__.py":
                    package_name = module_name.rsplit(".", 1)[0] if "." in module_name else module_name
                    self.module_to_file[package_name] = rel_path

        # Extract imports for each file
        for py_file in py_files:
            if not py_file.is_file():
                continue

            rel_path = str(py_file.relative_to(self.repo_root))
            imports = self._extract_imports(py_file)

            self.dependencies[rel_path] = DependencyInfo(
                file_path=rel_path, imports=imports
            )

        # Build reverse dependencies (imported_by)
        for file_path, dep_info in self.dependencies.items():
            for imported_module in dep_info.imports:
                # Try to find the file that corresponds to this module
                target_file = None

                # Direct module match
                if imported_module in self.module_to_file:
                    target_file = self.module_to_file[imported_module]
                else:
                    # Try partial matches for relative imports
                    for mod_name, mod_file in self.module_to_file.items():
                        if mod_name.startswith(imported_module + ".") or mod_name.endswith("." + imported_module):
                            target_file = mod_file
                            break

                if target_file and target_file in self.dependencies:
                    self.dependencies[target_file].imported_by.add(file_path)

    def compute_blast_radius(self, file_path: str) -> int:
        """Compute the blast radius for a file.

        The blast radius is the number of files that would be impacted
        (directly or transitively) if this file were changed.

        Args:
            file_path: Relative path to the file

        Returns:
            Number of impacted files
        """
        if file_path not in self.dependencies:
            return 0

        visited = set()
        to_visit = [file_path]

        while to_visit:
            current = to_visit.pop()
            if current in visited:
                continue

            visited.add(current)

            if current in self.dependencies:
                # Add all files that import this one
                for importer in self.dependencies[current].imported_by:
                    if importer not in visited:
                        to_visit.append(importer)

        # Subtract 1 to exclude the file itself
        return len(visited) - 1

    def compute_dependency_depth(self, file_path: str) -> int:
        """Compute the maximum dependency chain depth for a file.

        Args:
            file_path: Relative path to the file

        Returns:
            Maximum depth of dependency chains
        """
        if file_path not in self.dependencies:
            return 0

        def _depth_recursive(fp: str, visited: Set[str]) -> int:
            if fp in visited:
                return 0

            visited.add(fp)

            if fp not in self.dependencies:
                return 0

            max_depth = 0
            for importer in self.dependencies[fp].imported_by:
                depth = 1 + _depth_recursive(importer, visited.copy())
                max_depth = max(max_depth, depth)

            return max_depth

        return _depth_recursive(file_path, set())

    def analyze_all(self) -> None:
        """Compute blast radius and depth for all files in the graph."""
        for file_path in self.dependencies:
            dep_info = self.dependencies[file_path]
            dep_info.blast_radius = self.compute_blast_radius(file_path)
            dep_info.depth = self.compute_dependency_depth(file_path)
            dep_info.is_core = dep_info.blast_radius > 5  # Arbitrary threshold

    def get_high_impact_files(
        self, min_blast_radius: int = 5
    ) -> List[tuple[str, DependencyInfo]]:
        """Get files with high blast radius.

        Args:
            min_blast_radius: Minimum blast radius to include

        Returns:
            List of (file_path, DependencyInfo) tuples, sorted by blast radius
        """
        high_impact = [
            (fp, info)
            for fp, info in self.dependencies.items()
            if info.blast_radius >= min_blast_radius
        ]

        high_impact.sort(key=lambda x: x[1].blast_radius, reverse=True)
        return high_impact

    def get_dependency_info(self, file_path: str) -> Optional[DependencyInfo]:
        """Get dependency information for a specific file.

        Args:
            file_path: Relative path to the file

        Returns:
            DependencyInfo or None if not found
        """
        return self.dependencies.get(file_path)

    def visualize_dependencies(self, file_path: str, max_depth: int = 2) -> str:
        """Generate a text-based dependency tree visualization.

        Args:
            file_path: Relative path to the file
            max_depth: Maximum depth to visualize

        Returns:
            Multi-line string with dependency tree
        """
        if file_path not in self.dependencies:
            return f"File not found: {file_path}"

        lines = [f"📦 {file_path}"]

        def _build_tree(fp: str, prefix: str, depth: int, visited: Set[str]) -> None:
            if depth >= max_depth or fp in visited:
                return

            visited.add(fp)

            if fp not in self.dependencies:
                return

            importers = sorted(self.dependencies[fp].imported_by)
            for i, importer in enumerate(importers):
                is_last = i == len(importers) - 1
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}{importer}")

                extension = "    " if is_last else "│   "
                _build_tree(importer, prefix + extension, depth + 1, visited.copy())

        _build_tree(file_path, "", 0, set())

        return "\n".join(lines)

    def compute_combined_score(
        self, chaos_score: float, blast_radius: int, churn_score: float = 0.0
    ) -> tuple[float, str]:
        """Compute a combined risk score incorporating chaos, blast radius, and churn.

        Args:
            chaos_score: Chaos/complexity score (0-1)
            blast_radius: Number of impacted files
            churn_score: Git churn score (0-1, optional)

        Returns:
            Tuple of (combined_score, risk_level)
        """
        # Normalize blast radius (assume max of 50 files)
        normalized_blast = min(1.0, blast_radius / 50.0)

        # Combined score: weighted average
        if churn_score > 0:
            # Include churn: chaos(40%) + blast(30%) + churn(30%)
            combined = 0.4 * chaos_score + 0.3 * normalized_blast + 0.3 * churn_score
        else:
            # No churn: chaos(60%) + blast(40%)
            combined = 0.6 * chaos_score + 0.4 * normalized_blast

        if combined >= 0.40:
            risk_level = "CRITICAL"
        elif combined >= 0.30:
            risk_level = "HIGH"
        elif combined >= 0.20:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        return combined, risk_level
