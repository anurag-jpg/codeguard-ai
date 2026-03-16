"""
API Routes — all endpoints for the AI Bug-Fixing Assistant.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from typing import List, Optional
import logging
import io
import json

from backend.api.schemas import (
    RepoAnalysisRequest,
    InlineCodeRequest,
    AnalysisReport,
    AnalysisJobResponse,
    AnalysisStatus,
    ErrorResponse,
)
from backend.services.repo_analyzer import RepoAnalyzer
from backend.services.bug_detector import BugDetector
from backend.services.report_generator import ReportGenerator
from backend.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# ── In-memory job store (swap for Redis in production) ────────────────────────
_jobs: dict[str, AnalysisReport] = {}


def get_repo_analyzer() -> RepoAnalyzer:
    return RepoAnalyzer()


def get_bug_detector() -> BugDetector:
    return BugDetector()


def get_report_generator() -> ReportGenerator:
    return ReportGenerator()


# ── Analysis endpoints ────────────────────────────────────────────────────────

@router.post(
    "/analyze/repo",
    response_model=AnalysisJobResponse,
    status_code=202,
    summary="Submit a repository URL for async analysis",
    tags=["Analysis"],
)
async def analyze_repository(
    request: RepoAnalysisRequest,
    background_tasks: BackgroundTasks,
    analyzer: RepoAnalyzer = Depends(get_repo_analyzer),
    detector: BugDetector = Depends(get_bug_detector),
):
    """
    Clone a public GitHub / GitLab repository and run a full RAG-powered bug scan.
    Returns a job ID that you can poll via GET /analyze/status/{job_id}.
    """
    report = AnalysisReport(
        status=AnalysisStatus.PENDING,
        repo_url=str(request.repo_url),
        branch=request.branch,
    )
    _jobs[report.report_id] = report

    background_tasks.add_task(
        _run_repo_analysis,
        report.report_id,
        request,
        analyzer,
        detector,
    )

    return AnalysisJobResponse(
        job_id=report.report_id,
        status=AnalysisStatus.PENDING,
        message="Analysis job queued successfully.",
        poll_url=f"/api/v1/analyze/status/{report.report_id}",
    )


@router.post(
    "/analyze/code",
    response_model=AnalysisReport,
    summary="Analyse an inline code snippet synchronously",
    tags=["Analysis"],
)
async def analyze_inline_code(
    request: InlineCodeRequest,
    detector: BugDetector = Depends(get_bug_detector),
):
    """
    Submit a single file's source code and receive an immediate bug report.
    Best for quick checks on individual files (< 500 lines).
    """
    try:
        report = await detector.analyse_snippet(
            filename=request.filename,
            content=request.content,
            language=request.language,
        )
        return report
    except Exception as exc:
        logger.error("Inline analysis failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/analyze/upload",
    response_model=AnalysisJobResponse,
    status_code=202,
    summary="Upload one or more source files for analysis",
    tags=["Analysis"],
)
async def analyze_uploaded_files(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    detector: BugDetector = Depends(get_bug_detector),
):
    """Accept multipart file uploads and queue them for analysis."""
    MAX_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024

    uploaded = []
    for f in files:
        raw = await f.read()
        if len(raw) > MAX_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File {f.filename} exceeds {settings.MAX_FILE_SIZE_MB} MB limit.",
            )
        uploaded.append({"filename": f.filename, "content": raw.decode("utf-8", errors="replace")})

    report = AnalysisReport(
        status=AnalysisStatus.PENDING,
        repo_url=None,
        branch=None,
    )
    _jobs[report.report_id] = report
    background_tasks.add_task(_run_upload_analysis, report.report_id, uploaded, detector)

    return AnalysisJobResponse(
        job_id=report.report_id,
        status=AnalysisStatus.PENDING,
        message=f"{len(uploaded)} file(s) queued for analysis.",
        poll_url=f"/api/v1/analyze/status/{report.report_id}",
    )


# ── Status & retrieval endpoints ──────────────────────────────────────────────

@router.get(
    "/analyze/status/{job_id}",
    response_model=AnalysisReport,
    summary="Poll analysis job status / retrieve completed report",
    tags=["Analysis"],
)
async def get_analysis_status(job_id: str):
    report = _jobs.get(job_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return report


@router.get(
    "/reports",
    response_model=List[AnalysisReport],
    summary="List all analysis reports (most recent first)",
    tags=["Reports"],
)
async def list_reports(limit: int = 20, offset: int = 0):
    all_reports = list(reversed(list(_jobs.values())))
    return all_reports[offset : offset + limit]


@router.get(
    "/reports/{report_id}/export",
    summary="Download a completed report as JSON or Markdown",
    tags=["Reports"],
)
async def export_report(
    report_id: str,
    format: str = "json",
    gen: ReportGenerator = Depends(get_report_generator),
):
    report = _jobs.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    if report.status != AnalysisStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Report is not yet complete.")

    if format == "markdown":
        md = await gen.to_markdown(report)
        return StreamingResponse(
            io.BytesIO(md.encode()),
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="report-{report_id}.md"'},
        )

    return StreamingResponse(
        io.BytesIO(report.json(indent=2).encode()),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="report-{report_id}.json"'},
    )


@router.delete(
    "/reports/{report_id}",
    status_code=204,
    summary="Delete a report",
    tags=["Reports"],
)
async def delete_report(report_id: str):
    if report_id not in _jobs:
        raise HTTPException(status_code=404, detail="Report not found.")
    del _jobs[report_id]


# ── Background tasks ──────────────────────────────────────────────────────────

async def _run_repo_analysis(
    job_id: str,
    request: RepoAnalysisRequest,
    analyzer: RepoAnalyzer,
    detector: BugDetector,
):
    report = _jobs[job_id]
    try:
        report.status = AnalysisStatus.PROCESSING
        files = await analyzer.clone_and_parse(
            repo_url=str(request.repo_url),
            branch=request.branch,
            focus_paths=request.focus_paths,
            ignore_paths=request.ignore_paths,
            max_files=request.max_files,
        )
        result = await detector.analyse_files(files)
        _jobs[job_id] = result
        _jobs[job_id].report_id = job_id
        _jobs[job_id].repo_url = str(request.repo_url)
        _jobs[job_id].branch = request.branch
    except Exception as exc:
        logger.error("Repo analysis job %s failed: %s", job_id, exc, exc_info=True)
        report.status = AnalysisStatus.FAILED
        report.error_message = str(exc)


async def _run_upload_analysis(job_id: str, files: list, detector: BugDetector):
    report = _jobs[job_id]
    try:
        report.status = AnalysisStatus.PROCESSING
        result = await detector.analyse_files(files)
        _jobs[job_id] = result
        _jobs[job_id].report_id = job_id
    except Exception as exc:
        logger.error("Upload analysis job %s failed: %s", job_id, exc, exc_info=True)
        report.status = AnalysisStatus.FAILED
        report.error_message = str(exc)
