"""
Draiver Context Generator – Central Configuration
"""
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"

# ── Supported input formats ───────────────────────────────────────────────────
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".txt"}

# ── Output mode ───────────────────────────────────────────────────────────────
# "per_document" → one .md file per source document (default)
# "single"       → one aggregated context.md file
DEFAULT_OUTPUT_MODE = "per_document"

# ── Markdown output options ───────────────────────────────────────────────────
# Include YAML frontmatter at the top of each output file
INCLUDE_FRONTMATTER = True

# Include a Table of Contents in single-mode output
INCLUDE_TOC = True
