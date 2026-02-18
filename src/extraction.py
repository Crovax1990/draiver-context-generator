"""
Draiver Context Generator – Extraction Module

Converts each document with Docling and returns structured context dicts.
"""
import logging
from pathlib import Path

from docling.document_converter import DocumentConverter

logger = logging.getLogger(__name__)

# One shared converter instance (avoids reloading models for every file)
_converter = DocumentConverter()


def extract_context(file_path: Path) -> dict | None:
    """
    Converts a single document to Markdown using Docling and returns a
    structured context dictionary.

    Args:
        file_path: Absolute or relative path to the source document.

    Returns:
        A dict with keys:
            - title (str): Inferred document title (filename stem).
            - source_file (str): Original filename.
            - markdown_content (str): Full Markdown representation.
            - page_count (int): Number of pages (if available, else 0).
        Returns None if conversion fails.
    """
    logger.info("Processing: %s", file_path.name)
    try:
        result = _converter.convert(str(file_path))
        doc = result.document

        markdown_content = doc.export_to_markdown()

        # Attempt to get page count from document metadata
        page_count = _get_page_count(doc)

        return {
            "title": file_path.stem.replace("_", " ").replace("-", " ").title(),
            "source_file": file_path.name,
            "markdown_content": markdown_content,
            "page_count": page_count,
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to process '%s': %s", file_path.name, exc)
        return None


def extract_all(file_paths: list[Path]) -> tuple[list[dict], list[str]]:
    """
    Runs extract_context on every path and separates successes from failures.

    Args:
        file_paths: List of document paths from the ingestion step.

    Returns:
        A tuple (successful_docs, failed_filenames).
    """
    successful: list[dict] = []
    failed: list[str] = []

    for path in file_paths:
        result = extract_context(path)
        if result is not None:
            successful.append(result)
        else:
            failed.append(path.name)

    logger.info(
        "Extraction complete: %d succeeded, %d failed.",
        len(successful),
        len(failed),
    )
    return successful, failed


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_page_count(doc) -> int:
    """Safely extracts page count from a Docling document object."""
    try:
        # Docling exposes pages as a dict keyed by page number
        if hasattr(doc, "pages") and doc.pages:
            return len(doc.pages)
    except Exception:  # noqa: BLE001
        pass
    return 0
