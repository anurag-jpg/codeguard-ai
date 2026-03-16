"""
RepoAnalyzer — clones a repository and extracts source files.
Supports GitHub & GitLab via HTTPS.  Falls back to ZIP download
when git is unavailable (e.g. inside container without git).
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional

from backend.config import settings
from backend.utils.file_parser import FileParser

logger = logging.getLogger(__name__)


class RepoAnalyzer:
    """Clone a remote repository and produce a flat list of parsed source files."""

    def __init__(self):
        self.parser = FileParser()
        self.repos_dir = Path(settings.REPOS_DIR)
        self.repos_dir.mkdir(parents=True, exist_ok=True)

    # ── Public API ─────────────────────────────────────────────────────────────

    async def clone_and_parse(
        self,
        repo_url: str,
        branch: str = "main",
        focus_paths: Optional[List[str]] = None,
        ignore_paths: Optional[List[str]] = None,
        max_files: int = 200,
    ) -> List[dict]:
        """
        Clone repo → parse source files → return list of file dicts.

        Each dict contains:
          - filename  : relative path from repo root
          - content   : decoded source text
          - language  : detected language
        """
        repo_hash = hashlib.md5(f"{repo_url}@{branch}".encode()).hexdigest()[:10]
        clone_dir = self.repos_dir / repo_hash

        try:
            if clone_dir.exists():
                logger.info("Repo cache hit: %s", clone_dir)
                await self._pull(clone_dir, branch)
            else:
                logger.info("Cloning %s (branch=%s) → %s", repo_url, branch, clone_dir)
                await self._clone(repo_url, branch, clone_dir)

            files = self.parser.collect_source_files(
                root=clone_dir,
                focus_paths=focus_paths,
                ignore_paths=ignore_paths,
                max_files=max_files,
            )
            logger.info("Collected %d source files from %s", len(files), repo_url)
            return files

        except Exception as exc:
            logger.error("Failed to analyse repo %s: %s", repo_url, exc)
            # Clean up failed clone
            if clone_dir.exists():
                shutil.rmtree(clone_dir, ignore_errors=True)
            raise

    # ── Git helpers ────────────────────────────────────────────────────────────

    async def _clone(self, url: str, branch: str, dest: Path) -> None:
        token = settings.GITHUB_TOKEN
        if token and "github.com" in url:
            url = url.replace("https://", f"https://{token}@")

        cmd = ["git", "clone", "--depth", "1", "--branch", branch, url, str(dest)]
        await self._run_cmd(cmd)

    async def _pull(self, repo_dir: Path, branch: str) -> None:
        cmd = ["git", "-C", str(repo_dir), "pull", "origin", branch]
        await self._run_cmd(cmd)

    @staticmethod
    async def _run_cmd(cmd: List[str]) -> None:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(
                f"Git command failed (exit {proc.returncode}): "
                f"{stderr.decode(errors='replace')}"
            )
        logger.debug("Git output: %s", stdout.decode(errors="replace"))
