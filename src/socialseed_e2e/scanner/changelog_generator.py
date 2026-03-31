"""Changelog generator for extracting changes from git.

This module extracts commits, classifies by type, and detects breaking changes.
"""

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Commit:
    """Represents a git commit."""

    hash: str
    message: str
    author: str
    date: str
    type: str = "unknown"


@dataclass
class ChangelogInfo:
    """Represents changelog information."""

    commits: List[Commit] = field(default_factory=list)
    breaking_changes: List[str] = field(default_factory=list)
    by_type: Dict[str, List[str]] = field(default_factory=dict)


class ChangelogGenerator:
    """Generates changelog from git commits."""

    COMMIT_TYPES = {
        "feat": "Features",
        "fix": "Bug Fixes",
        "docs": "Documentation",
        "style": "Styles",
        "refactor": "Code Refactoring",
        "test": "Tests",
        "chore": "Chores",
        "perf": "Performance",
        "ci": "CI/CD",
    }

    BREAKING_PATTERNS = [
        "breaking",
        "breaking change",
        "bc",
        "!",
    ]

    def __init__(self, project_root: Path):
        self.project_root = project_root

    def generate(self, since: str = "HEAD~50") -> ChangelogInfo:
        """Generate changelog from commits."""
        info = ChangelogInfo()

        self._extract_commits(info, since)
        self._classify_commits(info)
        self._detect_breaking_changes(info)

        return info

    def _extract_commits(self, info: ChangelogInfo, since: str) -> None:
        """Extract commits from git."""
        try:
            result = subprocess.run(
                ["git", "log", since, "--oneline", "--pretty=format:%h|%s|%an|%ad|%s"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if "|" in line:
                        parts = line.split("|")
                        if len(parts) >= 4:
                            commit = Commit(
                                hash=parts[0],
                                message=parts[1],
                                author=parts[2],
                                date=parts[3],
                            )
                            info.commits.append(commit)
        except Exception:
            pass

    def _classify_commits(self, info: ChangelogInfo) -> None:
        """Classify commits by type."""
        for commit in info.commits:
            msg_lower = commit.message.lower()
            
            for commit_type, type_name in self.COMMIT_TYPES.items():
                if msg_lower.startswith(commit_type):
                    commit.type = type_name
                    if type_name not in info.by_type:
                        info.by_type[type_name] = []
                    info.by_type[type_name].append(commit.message)
                    break

    def _detect_breaking_changes(self, info: ChangelogInfo) -> None:
        """Detect breaking changes."""
        for commit in info.commits:
            msg_lower = commit.message.lower()
            
            for pattern in self.BREAKING_PATTERNS:
                if pattern in msg_lower:
                    info.breaking_changes.append(f"{commit.hash}: {commit.message}")
                    break


def generate_changelog_doc(project_root: Path, output_path: Optional[Path] = None) -> str:
    """Generate CHANGELOG.md document."""
    generator = ChangelogGenerator(project_root)
    info = generator.generate()

    doc = "# Changelog\n\n"

    if info.breaking_changes:
        doc += "## 🚨 Breaking Changes\n\n"
        for change in info.breaking_changes:
            doc += f"- {change}\n"
        doc += "\n"

    for commit_type, type_name in generator.COMMIT_TYPES.items():
        if type_name in info.by_type and info.by_type[type_name]:
            doc += f"## {type_name}\n\n"
            for msg in info.by_type[type_name][:10]:
                doc += f"- {msg}\n"
            doc += "\n"

    doc += "---\n\n"
    doc += f"*Total commits: {len(info.commits)}*\n"

    if output_path:
        output_path.write_text(doc)

    return doc


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
        print(generate_changelog_doc(project_root))
    else:
        print("Usage: python changelog_generator.py <project_root>")
