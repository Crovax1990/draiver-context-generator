"""
Draiver Context Generator – CLI Entry Point

Usage:
    python main.py [--mode per_document|single] [--input PATH] [--output PATH]

Examples:
    python main.py
    python main.py --mode single
    python main.py --input ./my_docs --output ./my_output
"""
import argparse
import logging
import sys
from pathlib import Path

# Ensure src/ is importable when running from project root
sys.path.insert(0, str(Path(__file__).parent / "src"))

import config
from src.audit import AuditLog
from src.ingestion import scan_input_folder
from src.extraction import extract_all
from src.output_writer import write_output


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
        datefmt="%H:%M:%S",
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Draiver Context Generator – converts documents to Markdown context files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--mode",
        choices=["per_document", "single"],
        default=config.DEFAULT_OUTPUT_MODE,
        help=(
            "Output mode: 'per_document' creates one .md per source file (default), "
            "'single' aggregates everything into context.md."
        ),
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=config.INPUT_DIR,
        metavar="PATH",
        help=f"Input folder (default: {config.INPUT_DIR})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=config.OUTPUT_DIR,
        metavar="PATH",
        help=f"Output folder (default: {config.OUTPUT_DIR})",
    )
    parser.add_argument(
        "--threads",
        type=int,
        default=config.DEFAULT_THREADS,
        help=f"Number of parallel threads (default: {config.DEFAULT_THREADS})",
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        default=False,
        help="Skip image extraction from documents.",
    )
    return parser.parse_args()


def main() -> int:
    _setup_logging()
    logger = logging.getLogger("main")
    args = _parse_args()

    logger.info("=== Draiver Context Generator ===")
    logger.info("Input : %s", args.input)
    logger.info("Output: %s", args.output)
    logger.info("Mode   : %s", args.mode)
    logger.info("Threads: %d", args.threads)

    # Prepare output subdirectories
    images_dir = None
    if not args.no_images:
        images_dir = args.output / config.IMAGES_SUBDIR
        logger.info("Images: %s", images_dir)

    # Initialize audit log
    audit = AuditLog()

    # ── Step 1: Ingestion ─────────────────────────────────────────────────────
    try:
        file_paths = scan_input_folder(args.input)
    except FileNotFoundError as exc:
        logger.error(str(exc))
        return 1

    if not file_paths:
        logger.warning("No supported documents found in '%s'. Nothing to do.", args.input)
        return 0

    # ── Step 2: Extraction ────────────────────────────────────────────────────
    docs, failed = extract_all(
        file_paths, 
        audit=audit, 
        images_dir=images_dir,
        num_threads=args.threads
    )

    # ── Step 3: Output ────────────────────────────────────────────────────────
    if docs:
        written = write_output(docs, args.output, mode=args.mode)
    else:
        written = []
        logger.error("All documents failed to process. Check the logs above.")

    # ── Step 4: Audit report ──────────────────────────────────────────────────
    report_path = audit.write_report(args.output)

    # ── Summary ───────────────────────────────────────────────────────────────
    _print_summary(docs, failed, written, report_path, images_dir)

    return 0 if docs else 1


def _print_summary(
    docs: list[dict],
    failed: list[str],
    written: list[Path],
    report_path: Path,
    images_dir: Path | None,
) -> None:
    """Prints a final human-readable summary to stdout."""
    total_images = sum(d.get("images_extracted", 0) for d in docs)
    total_warnings = sum(len(d.get("warnings", [])) for d in docs)

    print()
    print("=" * 56)
    print(f"  Documents processed  : {len(docs)}")
    if failed:
        print(f"  Documents FAILED     : {len(failed)} → {failed}")
    if total_warnings:
        print(f"  Total warnings       : {total_warnings}")
    print(f"  Images extracted     : {total_images}")
    print(f"  Output files written : {len(written)}")
    for path in written:
        print(f"    → {path}")
    print(f"  Audit report         : {report_path}")
    if images_dir and images_dir.exists():
        img_count = len(list(images_dir.glob("*.png")))
        print(f"  Images dir           : {images_dir} ({img_count} files)")
    print("=" * 56)


if __name__ == "__main__":
    sys.exit(main())
