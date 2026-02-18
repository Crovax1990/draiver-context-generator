"""
Draiver Context Generator – Output Writer Module

Writes extracted context to Markdown files in two modes:
  - per_document: one .md file per source document
  - single:       one aggregated context.md file
"""
import logging
from datetime import datetime, timezone
from pathlib import Path

from config import INCLUDE_FRONTMATTER, INCLUDE_TOC

logger = logging.getLogger(__name__)

# ── Public API ────────────────────────────────────────────────────────────────

def write_output(
    docs: list[dict],
    output_dir: Path,
    mode: str = "per_document",
) -> list[Path]:
    """
    Writes Markdown output files for the given documents.

    Args:
        docs:       List of context dicts from the extraction step.
        output_dir: Directory where output files will be written.
        mode:       "per_document" or "single".

    Returns:
        List of Path objects for the files that were written.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    if mode == "single":
        return _write_single(docs, output_dir)
    else:
        return _write_per_document(docs, output_dir)


# ── Private helpers ───────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _frontmatter(fields: dict) -> str:
    """Renders a YAML frontmatter block."""
    lines = ["---"]
    for key, value in fields.items():
        # Wrap string values in quotes to be safe
        if isinstance(value, str):
            lines.append(f'{key}: "{value}"')
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def _safe_stem(filename: str) -> str:
    """Converts a filename to a safe output stem (no extension, spaces → _)."""
    stem = Path(filename).stem
    return stem.replace(" ", "_").lower()


def _write_per_document(docs: list[dict], output_dir: Path) -> list[Path]:
    """One .md file per source document."""
    written: list[Path] = []

    for doc in docs:
        parts: list[str] = []

        if INCLUDE_FRONTMATTER:
            fm = _frontmatter(
                {
                    "title": doc["title"],
                    "source": doc["source_file"],
                    "pages": doc["page_count"],
                    "generated_at": _now_iso(),
                }
            )
            parts.append(fm)

        parts.append(f"# {doc['title']}\n")
        parts.append(doc["markdown_content"])

        out_path = output_dir / f"{_safe_stem(doc['source_file'])}.md"
        out_path.write_text("\n\n".join(parts), encoding="utf-8")
        logger.info("Written: %s", out_path.name)
        written.append(out_path)

    return written


def _write_single(docs: list[dict], output_dir: Path) -> list[Path]:
    """One aggregated context.md file."""
    parts: list[str] = []

    if INCLUDE_FRONTMATTER:
        fm = _frontmatter(
            {
                "title": "Contesto Aggregato",
                "documents": len(docs),
                "generated_at": _now_iso(),
            }
        )
        parts.append(fm)

    parts.append("# Contesto Aggregato\n")

    # Table of Contents
    if INCLUDE_TOC:
        toc_lines = ["## Indice\n"]
        for doc in docs:
            anchor = _to_anchor(doc["title"])
            toc_lines.append(f"- [{doc['title']}](#{anchor})")
        parts.append("\n".join(toc_lines))

    # Document sections
    for doc in docs:
        section = [
            "---",
            f"## {doc['title']}",
            f"> **Fonte:** `{doc['source_file']}`"
            + (f" | **Pagine:** {doc['page_count']}" if doc["page_count"] else ""),
            "",
            doc["markdown_content"],
        ]
        parts.append("\n\n".join(section))

    out_path = output_dir / "context.md"
    out_path.write_text("\n\n".join(parts), encoding="utf-8")
    logger.info("Written: %s", out_path.name)
    return [out_path]


def _to_anchor(text: str) -> str:
    """Converts a heading text to a GitHub Markdown anchor."""
    return text.lower().replace(" ", "-").replace("_", "-")
