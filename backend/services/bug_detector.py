"""
BugDetector — orchestrates the RAG pipeline to find bugs in source files.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.api.schemas import (
    AnalysisReport,
    AnalysisSummary,
    AnalysisStatus,
    BugCategory,
    BugFinding,
    FileInfo,
    Severity,
)
from backend.config import settings
from backend.utils.chunking import Chunker
from ai_engine.rag_pipeline import RAGPipeline
from ai_engine.prompts import BUG_DETECTION_SYSTEM_PROMPT, build_detection_user_prompt

logger = logging.getLogger(__name__)


class BugDetector:
    def __init__(self):
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.genai = genai
        self.model_name = "gemini-3-flash-preview"
        self.chunker = Chunker(
            chunk_size=settings.CHUNK_SIZE,
            overlap=settings.CHUNK_OVERLAP,
        )
        self.rag = RAGPipeline()

    # ── Public API ─────────────────────────────────────────────────────────────

    async def analyse_files(self, files: List[Dict[str, Any]]) -> AnalysisReport:
        """Run full bug detection on a list of file dicts."""
        start_time = time.perf_counter()

        report = AnalysisReport(
            status=AnalysisStatus.PROCESSING,
            repo_url=None,
            branch=None,
            created_at=datetime.utcnow(),
        )

        logger.info("Indexing %d files into vector store …", len(files))
        await self.rag.build_index(files)

        all_findings: List[BugFinding] = []
        file_infos: List[FileInfo] = []

        sem = asyncio.Semaphore(5)
        tasks = [self._analyse_single_file(f, sem) for f in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for f, result in zip(files, results):
            if isinstance(result, Exception):
                logger.warning("Skipping %s due to error: %s", f.get("filename"), result)
                continue
            findings, file_info = result
            all_findings.extend(findings)
            file_infos.append(file_info)

        duration = time.perf_counter() - start_time
        report.findings = all_findings
        report.files_scanned = file_infos
        report.summary = self._build_summary(all_findings, file_infos, duration)
        report.status = AnalysisStatus.COMPLETED

        logger.info(
            "Analysis complete: %d bugs in %d files (%.2fs)",
            len(all_findings), len(file_infos), duration,
        )
        return report

    async def analyse_snippet(
        self,
        filename: str,
        content: str,
        language: Optional[str] = None,
    ) -> AnalysisReport:
        """Analyse a single inline code snippet."""
        file_dict = {
            "filename": filename,
            "content": content,
            "language": language or "unknown"
        }
        return await self.analyse_files([file_dict])

    # ── Private helpers ────────────────────────────────────────────────────────

    async def _analyse_single_file(
        self,
        file: Dict[str, Any],
        sem: asyncio.Semaphore,
    ) -> tuple[List[BugFinding], FileInfo]:
        async with sem:
            filename = file.get("filename", "unknown")
            content = file.get("content", "")
            language = file.get("language", "unknown")

            context_chunks = await self.rag.retrieve(
                query=f"Bugs and issues in {filename}:\n{content[:500]}",
                top_k=settings.TOP_K_RETRIEVAL,
                exclude_file=filename,
            )

            prompt = build_detection_user_prompt(
                filename=filename,
                content=content,
                language=language,
                context_chunks=context_chunks,
            )

            raw_response = await self._call_llm(
                system=BUG_DETECTION_SYSTEM_PROMPT,
                user=prompt,
            )

            findings = self._parse_llm_response(raw_response, filename)
            file_info = FileInfo(
                path=filename,
                language=language,
                lines=content.count("\n") + 1,
                size_bytes=len(content.encode()),
            )
            return findings, file_info

    async def _call_llm(self, system: str, user: str) -> str:
        try:
            loop = asyncio.get_event_loop()
            model = self.genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system
            )
            response = await loop.run_in_executor(
                None,
                lambda: model.generate_content(user)
            )
            return response.text if response.text is not None else "{}"
        except Exception as e:
            logger.error("LLM call failed: %s", e)
            return "{}"

    def _parse_llm_response(self, raw: str, filename: str) -> List[BugFinding]:
        try:
            # Clean markdown fences if present
            clean = raw.strip()
            if clean.startswith("```"):
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
                clean = clean.strip()

            data = json.loads(clean)
        except json.JSONDecodeError:
            logger.warning("LLM returned invalid JSON for %s: %s", filename, raw[:200])
            return []

        findings = []
        for item in data.get("bugs", []):
            try:
                # Safely map severity
                severity_val = item.get("severity", "medium").lower()
                try:
                    severity = Severity(severity_val)
                except ValueError:
                    severity = Severity.MEDIUM

                # Safely map category
                category_val = item.get("category", "logic_error").lower()
                try:
                    category = BugCategory(category_val)
                except ValueError:
                    category = BugCategory.LOGIC_ERROR

                finding = BugFinding(
                    file_path=filename,
                    line_start=item.get("line_start"),
                    line_end=item.get("line_end"),
                    severity=severity,
                    category=category,
                    title=item.get("title", "Unknown bug"),
                    description=item.get("description", ""),
                    code_snippet=item.get("code_snippet"),
                    suggested_fix=item.get("suggested_fix"),
                    confidence=float(item.get("confidence", 0.7)),
                    references=item.get("references", []),
                )
                findings.append(finding)
            except Exception as exc:
                logger.debug("Skipping malformed finding: %s", exc)
        return findings

    @staticmethod
    def _build_summary(
        findings: List[BugFinding],
        files: List[FileInfo],
        duration: float,
    ) -> AnalysisSummary:
        sev_map = {s: 0 for s in Severity}
        for f in findings:
            sev_map[Severity(f.severity)] += 1

        return AnalysisSummary(
            total_files_scanned=len(files),
            total_lines_scanned=sum(f.lines for f in files),
            total_bugs_found=len(findings),
            critical_count=sev_map[Severity.CRITICAL],
            high_count=sev_map[Severity.HIGH],
            medium_count=sev_map[Severity.MEDIUM],
            low_count=sev_map[Severity.LOW],
            info_count=sev_map[Severity.INFO],
            languages_detected=list({f.language for f in files}),
            analysis_duration_seconds=round(duration, 3),
        )




