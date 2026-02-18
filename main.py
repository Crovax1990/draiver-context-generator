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
    return parser.parse_args()


def main() -> int:
    _setup_logging()
    logger = logging.getLogger("main")
    args = _parse_args()

    logger.info("=== Draiver Context Generator ===")
    logger.info("Input : %s", args.input)
    logger.info("Output: %s", args.output)
    logger.info("Mode  : %s", args.mode)

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
    docs, failed = extract_all(file_paths)

    if not docs:
        logger.error("All documents failed to process. Check the logs above.")
        return 1

    # ── Step 3: Output ────────────────────────────────────────────────────────
    written = write_output(docs, args.output, mode=args.mode)

    # ── Summary ───────────────────────────────────────────────────────────────
    print()
    print("=" * 50)
    print(f"  Documents processed : {len(docs)}")
    if failed:
        print(f"  Documents failed    : {len(failed)} → {failed}")
    print(f"  Output files written: {len(written)}")
    for path in written:
        print(f"    → {path}")
    print("=" * 50)

    return 0


if __name__ == "__main__":
    sys.exit(main())
