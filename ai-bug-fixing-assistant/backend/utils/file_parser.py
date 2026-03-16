"""
FileParser — discovers and reads source files from a local directory tree.
Handles encoding detection and language classification.
"""

from __future__ import annotations

import fnmatch
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Language detection by file extension
_EXT_LANGUAGE_MAP: Dict[str, str] = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".jsx": "javascript", ".tsx": "typescript", ".java": "java",
    ".go": "go", ".rs": "rust", ".cpp": "cpp", ".cc": "cpp",
    ".c": "c", ".h": "c", ".cs": "csharp", ".rb": "ruby",
    ".php": "php", ".swift": "swift", ".kt": "kotlin",
    ".scala": "scala", ".r": "r", ".sh": "bash",
    ".yaml": "yaml", ".yml": "yaml", ".json": "json",
    ".toml": "toml", ".md": "markdown",
}

_DEFAULT_IGNORE = {
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", "coverage", ".mypy_cache",
    ".pytest_cache", "*.min.js", "*.bundle.js", "*.lock",
    "package-lock.json", "yarn.lock", "*.pyc",
}


class FileParser:
    """Recursively collect source files from a directory."""

    def __init__(self, max_file_size_mb: int = 10):
        self.max_bytes = max_file_size_mb * 1024 * 1024

    def collect_source_files(
        self,
        root: Path,
        focus_paths: Optional[List[str]] = None,
        ignore_paths: Optional[List[str]] = None,
        max_files: int = 200,
    ) -> List[Dict]:
        """
        Walk `root` and return a list of dicts:
          { filename, content, language, size_bytes, line_count }
        """
        ignore_set = _DEFAULT_IGNORE.copy()
        if ignore_paths:
            ignore_set.update(ignore_paths)

        collected = []
        for dirpath, dirnames, filenames in os.walk(root):
            # Prune ignored directories in-place
            dirnames[:] = [
                d for d in dirnames
                if not self._is_ignored(d, ignore_set)
            ]

            for fname in filenames:
                if len(collected) >= max_files:
                    break

                fpath = Path(dirpath) / fname
                rel_path = str(fpath.relative_to(root))

                if self._is_ignored(fname, ignore_set):
                    continue

                ext = fpath.suffix.lower()
                language = _EXT_LANGUAGE_MAP.get(ext)
                if language is None:
                    continue  # skip non-source files

                # Optional focus filter
                if focus_paths and not any(
                    fnmatch.fnmatch(rel_path, pat) for pat in focus_paths
                ):
                    continue

                content = self._read_file(fpath)
                if content is None:
                    continue

                collected.append({
                    "filename": rel_path,
                    "content":  content,
                    "language": language,
                    "size_bytes": fpath.stat().st_size,
                    "line_count": content.count("\n") + 1,
                })

        logger.info("FileParser collected %d files from %s", len(collected), root)
        return collected

    def _read_file(self, path: Path) -> Optional[str]:
        try:
            if path.stat().st_size > self.max_bytes:
                logger.debug("Skipping oversized file: %s", path)
                return None
            return path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            logger.debug("Cannot read %s: %s", path, exc)
            return None

    @staticmethod
    def _is_ignored(name: str, ignore_set: set) -> bool:
        return name in ignore_set or any(
            fnmatch.fnmatch(name, pat) for pat in ignore_set
        )

    @staticmethod
    def detect_language(filename: str) -> str:
        ext = Path(filename).suffix.lower()
        return _EXT_LANGUAGE_MAP.get(ext, "unknown")
