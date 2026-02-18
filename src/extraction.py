"""
Draiver Context Generator – Extraction Module

Converts each document with Docling and returns structured context dicts.
Captures per-document warnings, extracts images, and feeds the audit log.
"""
import io
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from docling.document_converter import DocumentConverter
from docling_core.types.doc import ImageRefMode

from src.audit import AuditLog

logger = logging.getLogger(__name__)

# One shared converter instance (avoids reloading models for every file)
_converter = DocumentConverter()


def extract_context(
    file_path: Path,
    images_dir: Path | None = None,
) -> dict | None:
    """
    Converts a single document to Markdown using Docling and returns a
    structured context dictionary.  Optionally extracts images.

    Args:
        file_path:  Absolute or relative path to the source document.
        images_dir: Directory to save extracted images.  If None, images
                    are not saved to disk.

    Returns:
        A dict with keys:
            - title (str)
            - source_file (str)
            - markdown_content (str)
            - page_count (int)
            - images_extracted (int)
            - warnings (list[str])
        Returns None if conversion fails completely.
    """
    logger.info("Processing: %s", file_path.name)

    # Capture warnings emitted by Docling during conversion
    warnings_captured: list[str] = []
    thread_name = threading.current_thread().name
    handler = _WarningCapture(file_path.name, warnings_captured, thread_name)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    try:
        result = _converter.convert(str(file_path))
        doc = result.document

        markdown_content = doc.export_to_markdown()
        page_count = _get_page_count(doc)

        # ── Image extraction ──────────────────────────────────────────────
        images_extracted = 0
        if images_dir is not None:
            images_extracted = _extract_images(doc, file_path.stem, images_dir)

        return {
            "title": file_path.stem.replace("_", " ").replace("-", " ").title(),
            "source_file": file_path.name,
            "markdown_content": markdown_content,
            "page_count": page_count,
            "images_extracted": images_extracted,
            "warnings": list(warnings_captured),  # copy
        }

    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to process '%s' on thread '%s': %s", file_path.name, thread_name, exc)
        return None
    finally:
        root_logger.removeHandler(handler)


def extract_all(
    file_paths: list[Path],
    audit: AuditLog,
    images_dir: Path | None = None,
    num_threads: int = 1,
) -> tuple[list[dict], list[str]]:
    """
    Runs extract_context on every path in parallel and records results in the audit log.

    Args:
        file_paths:  List of document paths from the ingestion step.
        audit:       AuditLog instance to populate.
        images_dir:  Directory to save extracted images (shared across docs).
        num_threads: Number of parallel worker threads to use.

    Returns:
        A tuple (successful_docs, failed_filenames).
    """
    successful: list[dict] = []
    failed: list[str] = []

    def _worker(path: Path):
        file_size_mb = path.stat().st_size / (1024 * 1024)
        result = extract_context(path, images_dir=images_dir)

        if result is not None:
            # Decide status: "partial" if there were warnings
            status = "partial" if result["warnings"] else "success"
            audit.add_entry(
                result["source_file"],
                status=status,
                page_count=result["page_count"],
                images_extracted=result["images_extracted"],
                warnings=result["warnings"],
                file_size_mb=file_size_mb,
            )
            return result
        else:
            audit.add_entry(
                path.name,
                status="failed",
                error=f"Docling conversion failed (see console logs)",
                file_size_mb=file_size_mb,
            )
            return path.name

    logger.info("Starting extraction with pool size: %d", num_threads)
    
    with ThreadPoolExecutor(max_workers=num_threads, thread_name_prefix="worker") as executor:
        results = list(executor.map(_worker, file_paths))

    for res in results:
        if isinstance(res, dict):
            successful.append(res)
        else:
            failed.append(res)

    logger.info(
        "Extraction complete: %d succeeded, %d failed.",
        len(successful),
        len(failed),
    )
    return successful, failed


# ── Image extraction helpers ──────────────────────────────────────────────────

def _extract_images(doc, doc_stem: str, images_dir: Path) -> int:
    """
    Saves all images found in the Docling document to images_dir.

    Images are named: <doc_stem>_img_<N>.<ext>

    Returns the number of images successfully saved.
    """
    images_dir.mkdir(parents=True, exist_ok=True)
    count = 0

    # Docling exposes pictures as a list on the document object
    if not hasattr(doc, "pictures") or not doc.pictures:
        return 0

    for idx, pic in enumerate(doc.pictures):
        try:
            if pic.image is None or pic.image.pil_image is None:
                continue

            pil_img = pic.image.pil_image
            ext = "png"
            img_name = f"{doc_stem}_img_{idx:03d}.{ext}"
            img_path = images_dir / img_name

            pil_img.save(str(img_path), format="PNG")
            count += 1
            logger.debug("Saved image: %s", img_name)

        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Could not save image %d from '%s': %s", idx, doc_stem, exc
            )

    if count:
        logger.info("Extracted %d image(s) from '%s'.", count, doc_stem)
    return count


# ── Warning capture ──────────────────────────────────────────────────────────

class _WarningCapture(logging.Handler):
    """
    A temporary logging handler that intercepts WARNING and ERROR messages
    from Docling loggers during the conversion of a specific document.
    Messages are stored in the provided list for later audit reporting.
    """

    # Docling logger prefixes we want to capture
    _DOCLING_PREFIXES = ("docling.",)

    def __init__(self, source_file: str, target_list: list[str], thread_name: str) -> None:
        super().__init__(level=logging.WARNING)
        self._source_file = source_file
        self._target_list = target_list
        self._thread_name = thread_name

    def emit(self, record: logging.LogRecord) -> None:
        # Only capture logs emitted by the same thread that created this handler
        if threading.current_thread().name == self._thread_name:
            if any(record.name.startswith(p) for p in self._DOCLING_PREFIXES):
                msg = f"[{record.levelname}] {record.name}: {record.getMessage()}"
                self._target_list.append(msg)


# ── Other helpers ─────────────────────────────────────────────────────────────

def _get_page_count(doc) -> int:
    """Safely extracts page count from a Docling document object."""
    try:
        if hasattr(doc, "pages") and doc.pages:
            return len(doc.pages)
    except Exception:  # noqa: BLE001
        pass
    return 0
