"""Git churn analysis for computing churn × chaos friction scores.

This module tracks how frequently files are modified (churn) and combines
it with chaos scores to identify high-friction areas of the codebase.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class ChurnMetrics:
    """Git churn metrics for a single file."""

    file_path: str
    total_commits: int
    recent_commits: int  # Last 90 days
    last_modified: datetime
    age_days: int
    commits_per_month: float
    unique_authors: int
    lines_added: int
    lines_deleted: int
    churn_score: float  # Normalized churn metric (0-1)


class GitChurnAnalyzer:
    """Analyze Git repository churn to identify high-friction files."""

    def __init__(self, repo_path: Path):
        """Initialize the churn analyzer.

        Args:
            repo_path: Path to the Git repository root
        """
        self.repo_path = Path(repo_path)
        self._verify_git_repo()

    def _verify_git_repo(self) -> None:
        """Verify that the path is a valid Git repository."""
        try:
            subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Not a valid Git repository: {self.repo_path}") from e

    def get_file_churn(
        self, file_path: str, days_back: int = 365
    ) -> Optional[ChurnMetrics]:
        """Get churn metrics for a specific file.

        Args:
            file_path: Relative path to the file
            days_back: Number of days to analyze (default 365)

        Returns:
            ChurnMetrics object or None if file has no Git history
        """
        file_path_obj = Path(file_path)

        # Get commit count
        try:
            total_commits_result = subprocess.run(
                ["git", "log", "--follow", "--oneline", "--", str(file_path)],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            total_commits = len(total_commits_result.stdout.strip().split("\n"))
            if total_commits == 1 and not total_commits_result.stdout.strip():
                total_commits = 0
        except subprocess.CalledProcessError:
            return None

        if total_commits == 0:
            return None

        # Get recent commits (last 90 days)
        ninety_days_ago = (
            datetime.now() - timedelta(days=90)
        ).strftime("%Y-%m-%d")
        try:
            recent_result = subprocess.run(
                [
                    "git",
                    "log",
                    "--follow",
                    "--since",
                    ninety_days_ago,
                    "--oneline",
                    "--",
                    str(file_path),
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            recent_commits = len(recent_result.stdout.strip().split("\n"))
            if recent_commits == 1 and not recent_result.stdout.strip():
                recent_commits = 0
        except subprocess.CalledProcessError:
            recent_commits = 0

        # Get last modified date (using %cI for strict ISO 8601)
        try:
            last_commit_result = subprocess.run(
                [
                    "git",
                    "log",
                    "-1",
                    "--format=%cI",  # Strict ISO 8601 format
                    "--follow",
                    "--",
                    str(file_path),
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            last_modified_str = last_commit_result.stdout.strip()
            last_modified = datetime.fromisoformat(last_modified_str)
        except (subprocess.CalledProcessError, ValueError):
            last_modified = datetime.now()

        # Get file age (first commit date, using %cI for strict ISO 8601)
        try:
            first_commit_result = subprocess.run(
                [
                    "git",
                    "log",
                    "--follow",
                    "--format=%cI",  # Strict ISO 8601 format
                    "--reverse",
                    "--",
                    str(file_path),
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            first_commit_str = first_commit_result.stdout.strip().split("\n")[0]
            first_commit = datetime.fromisoformat(first_commit_str)
            age_days = (datetime.now() - first_commit).days
        except (subprocess.CalledProcessError, ValueError, IndexError):
            age_days = 0

        # Get unique authors
        try:
            authors_result = subprocess.run(
                [
                    "git",
                    "log",
                    "--follow",
                    "--format=%an",
                    "--",
                    str(file_path),
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            unique_authors = len(set(authors_result.stdout.strip().split("\n")))
        except subprocess.CalledProcessError:
            unique_authors = 1

        # Get lines added/deleted
        try:
            numstat_result = subprocess.run(
                [
                    "git",
                    "log",
                    "--follow",
                    "--numstat",
                    "--format=",
                    "--",
                    str(file_path),
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            lines_added = 0
            lines_deleted = 0
            for line in numstat_result.stdout.strip().split("\n"):
                if line and not line.startswith("-"):
                    parts = line.split()
                    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                        lines_added += int(parts[0])
                        lines_deleted += int(parts[1])
        except (subprocess.CalledProcessError, ValueError):
            lines_added = 0
            lines_deleted = 0

        # Calculate commits per month
        age_months = max(age_days / 30.0, 1.0)
        commits_per_month = total_commits / age_months

        # Calculate normalized churn score (0-1)
        # Formula: (recent_commits * 3 + commits_per_month) / max_expected_value
        # Max expected: 30 recent commits + 10 commits/month = 60
        churn_score = min(1.0, (recent_commits * 3 + commits_per_month) / 60.0)

        return ChurnMetrics(
            file_path=str(file_path),
            total_commits=total_commits,
            recent_commits=recent_commits,
            last_modified=last_modified,
            age_days=age_days,
            commits_per_month=commits_per_month,
            unique_authors=unique_authors,
            lines_added=lines_added,
            lines_deleted=lines_deleted,
            churn_score=churn_score,
        )

    def get_repo_churn(
        self, file_pattern: str = "*", days_back: int = 365
    ) -> Dict[str, ChurnMetrics]:
        """Get churn metrics for all files matching a pattern.

        OPTIMIZED: Uses vectorized Git operations to avoid N+1 subprocess spawning.
        Processes entire repository in a single Git log command.

        Args:
            file_pattern: Glob pattern to filter files
            days_back: Number of days to analyze

        Returns:
            Dictionary mapping file paths to ChurnMetrics
        """
        from collections import defaultdict
        from fnmatch import fnmatch

        # Get all tracked files
        try:
            ls_result = subprocess.run(
                ["git", "ls-files"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            all_files = ls_result.stdout.strip().split("\n")
        except subprocess.CalledProcessError:
            return {}

        # Filter by pattern
        matched_files = {f for f in all_files if fnmatch(f, file_pattern)}

        if not matched_files:
            return {}

        # VECTORIZED APPROACH: Single Git log command for entire repo
        # Format: %cI (ISO date) | %an (author) | file_path | +lines | -lines
        try:
            log_result = subprocess.run(
                [
                    "git",
                    "log",
                    "--numstat",
                    "--format=%cI|%an",
                    "--follow",
                    "--",
                ] + list(matched_files),  # Only scan matched files
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
                timeout=60,  # Prevent infinite hangs on huge repos
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            # Fallback to per-file analysis if vectorized fails
            return self._get_repo_churn_fallback(matched_files, days_back)

        # Parse the output
        commit_data = defaultdict(lambda: {
            "total_commits": 0,
            "recent_commits": 0,
            "authors": set(),
            "lines_added": 0,
            "lines_deleted": 0,
            "first_commit": None,
            "last_commit": None,
        })

        ninety_days_ago = datetime.now() - timedelta(days=90)
        current_commit_date = None
        current_commit_author = None

        for line in log_result.stdout.strip().split("\n"):
            if not line:
                continue

            # Commit header line: "2026-02-21T15:30:00-06:00|Author Name"
            if "|" in line and not line.startswith("\t"):
                parts = line.split("|", 1)
                if len(parts) == 2:
                    try:
                        current_commit_date = datetime.fromisoformat(parts[0])
                        current_commit_author = parts[1]
                    except ValueError:
                        continue
                continue

            # Numstat line: "45\t23\tpath/to/file.py"
            parts = line.split("\t")
            if len(parts) == 3:
                added_str, deleted_str, file_path = parts
                
                if file_path not in matched_files:
                    continue

                # Parse line counts (handle binary files showing '-')
                try:
                    lines_added = int(added_str) if added_str != '-' else 0
                    lines_deleted = int(deleted_str) if deleted_str != '-' else 0
                except ValueError:
                    lines_added = 0
                    lines_deleted = 0

                # Update metrics
                data = commit_data[file_path]
                data["total_commits"] += 1
                data["lines_added"] += lines_added
                data["lines_deleted"] += lines_deleted

                if current_commit_author:
                    data["authors"].add(current_commit_author)

                if current_commit_date:
                    if current_commit_date >= ninety_days_ago:
                        data["recent_commits"] += 1

                    if data["last_commit"] is None or current_commit_date > data["last_commit"]:
                        data["last_commit"] = current_commit_date

                    if data["first_commit"] is None or current_commit_date < data["first_commit"]:
                        data["first_commit"] = current_commit_date

        # Convert to ChurnMetrics objects
        churn_data = {}
        now = datetime.now()

        for file_path, data in commit_data.items():
            if data["total_commits"] == 0:
                continue

            # Calculate age
            age_days = (
                (now - data["first_commit"]).days
                if data["first_commit"]
                else 0
            )

            # Calculate commits per month
            age_months = max(age_days / 30.0, 1.0)
            commits_per_month = data["total_commits"] / age_months

            # Calculate churn score
            churn_score = min(
                1.0, (data["recent_commits"] * 3 + commits_per_month) / 60.0
            )

            churn_data[file_path] = ChurnMetrics(
                file_path=file_path,
                total_commits=data["total_commits"],
                recent_commits=data["recent_commits"],
                last_modified=data["last_commit"] or now,
                age_days=age_days,
                commits_per_month=commits_per_month,
                unique_authors=len(data["authors"]),
                lines_added=data["lines_added"],
                lines_deleted=data["lines_deleted"],
                churn_score=churn_score,
            )

        return churn_data

    def _get_repo_churn_fallback(
        self, matched_files: Set[str], days_back: int
    ) -> Dict[str, ChurnMetrics]:
        """Fallback to per-file analysis if vectorized approach fails.

        Args:
            matched_files: Set of file paths to analyze
            days_back: Number of days to analyze

        Returns:
            Dictionary mapping file paths to ChurnMetrics
        """
        churn_data = {}
        for file_path in matched_files:
            metrics = self.get_file_churn(file_path, days_back)
            if metrics:
                churn_data[file_path] = metrics
        return churn_data

    def compute_friction_score(
        self, chaos_score: float, churn_score: float
    ) -> Tuple[float, str]:
        """Compute friction score = chaos × churn.

        High friction = complex files that are frequently modified.

        Args:
            chaos_score: Chaos/complexity score (0-1)
            churn_score: Churn score (0-1)

        Returns:
            Tuple of (friction_score, risk_level)
        """
        friction = chaos_score * churn_score

        if friction >= 0.30:
            risk_level = "CRITICAL"
        elif friction >= 0.20:
            risk_level = "HIGH"
        elif friction >= 0.10:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        return friction, risk_level

    def get_high_friction_files(
        self,
        chaos_data: Dict[str, float],
        churn_data: Dict[str, ChurnMetrics],
        threshold: float = 0.20,
    ) -> List[Tuple[str, float, str]]:
        """Identify high-friction files.

        Args:
            chaos_data: Dictionary mapping file paths to chaos scores
            churn_data: Dictionary mapping file paths to ChurnMetrics
            threshold: Minimum friction score to include

        Returns:
            List of (file_path, friction_score, risk_level) tuples, sorted by friction
        """
        friction_files = []

        for file_path in set(chaos_data.keys()) & set(churn_data.keys()):
            chaos = chaos_data[file_path]
            churn = churn_data[file_path].churn_score
            friction, risk = self.compute_friction_score(chaos, churn)

            if friction >= threshold:
                friction_files.append((file_path, friction, risk))

        # Sort by friction score descending
        friction_files.sort(key=lambda x: x[1], reverse=True)
        return friction_files
