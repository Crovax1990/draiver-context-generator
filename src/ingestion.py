"""
Draiver Context Generator – Ingestion Module

Scans the input folder and returns a list of supported document paths.
"""
import logging
from pathlib import Path

from config import SUPPORTED_EXTENSIONS

logger = logging.getLogger(__name__)


def scan_input_folder(input_dir: Path) -> list[Path]:
    """
    Scans *input_dir* (flat structure) and returns all files whose extension
    is in SUPPORTED_EXTENSIONS.  Unsupported files are logged as warnings.

    Args:
        input_dir: Path to the folder containing source documents.

    Returns:
        Sorted list of Path objects for supported files.

    Raises:
        FileNotFoundError: If *input_dir* does not exist.
    """
    if not input_dir.exists():
        raise FileNotFoundError(
            f"Input directory not found: {input_dir}\n"
            "Create the folder and place your documents inside it."
        )

    supported: list[Path] = []
    skipped: list[Path] = []

    for path in sorted(input_dir.iterdir()):
        if not path.is_file():
            continue
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            supported.append(path)
        else:
            skipped.append(path)

    if skipped:
        logger.warning(
            "Skipped %d unsupported file(s): %s",
            len(skipped),
            [p.name for p in skipped],
        )

    logger.info("Found %d supported document(s) in '%s'.", len(supported), input_dir)
    return supported
