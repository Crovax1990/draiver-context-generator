"""
Draiver Context Generator – Audit Module

Produces a structured JSON audit report for every processing run, tracking
per-document status, warnings, errors, and image extraction results.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class AuditLog:
    """
    Collects per-document audit entries during a processing run and writes
    a JSON report at the end.
    """

    def __init__(self) -> None:
        self._started_at = datetime.now(tz=timezone.utc).isoformat()
        self._entries: list[dict] = []

    # ── Per-document tracking ─────────────────────────────────────────────────

    def add_entry(
        self,
        source_file: str,
        *,
        status: str = "success",
        page_count: int = 0,
        images_extracted: int = 0,
        warnings: list[str] | None = None,
        error: str | None = None,
        file_size_mb: float = 0.0,
    ) -> None:
        """
        Records the processing result for a single document.

        Args:
            source_file:      Filename of the source document.
            status:           "success", "partial", or "failed".
            page_count:       Number of pages detected.
            images_extracted:  Number of images saved.
            warnings:         List of warning messages captured during parsing.
            error:            Fatal error message (if status == "failed").
            file_size_mb:     File size in MB.
        """
        entry = {
            "source_file": source_file,
            "status": status,
            "file_size_mb": round(file_size_mb, 2),
            "page_count": page_count,
            "images_extracted": images_extracted,
            "warnings": warnings or [],
            "error": error,
        }
        self._entries.append(entry)

    # ── Report generation ─────────────────────────────────────────────────────

    def write_report(self, output_dir: Path) -> Path:
        """
        Writes the full audit report as `audit_report.json` in output_dir.

        Returns:
            Path to the written report file.
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        successes = [e for e in self._entries if e["status"] == "success"]
        partials = [e for e in self._entries if e["status"] == "partial"]
        failures = [e for e in self._entries if e["status"] == "failed"]

        report = {
            "run_timestamp": self._started_at,
            "summary": {
                "total_documents": len(self._entries),
                "successful": len(successes),
                "partial": len(partials),
                "failed": len(failures),
                "total_images_extracted": sum(
                    e["images_extracted"] for e in self._entries
                ),
                "total_warnings": sum(len(e["warnings"]) for e in self._entries),
            },
            "documents": self._entries,
        }

        report_path = output_dir / "audit_report.json"
        report_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        logger.info("Audit report written: %s", report_path)
        return report_path

    # ── Helpers ───────────────────────────────────────────────────────────────

    @property
    def entries(self) -> list[dict]:
        return self._entries
