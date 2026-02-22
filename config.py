"""
Draiver Context Generator – Central Configuration
"""
import os
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

# ── Parallelism ──────────────────────────────────────────────────────────────
DEFAULT_THREADS = 2

# ── Markdown output options ───────────────────────────────────────────────────
# Include YAML frontmatter at the top of each output file
INCLUDE_FRONTMATTER = True

# Include a Table of Contents in single-mode output
INCLUDE_TOC = True

# ── Image extraction ──────────────────────────────────────────────────────────
# Subdirectory inside OUTPUT_DIR where extracted images are saved
IMAGES_SUBDIR = "images"

# ── PPTX Generation ──────────────────────────────────────────────────────────
# Google API key (from environment variable)
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")

# LLM model for content generation
LLM_MODEL = "gemini-2.0-flash"
LLM_TEMPERATURE = 0.0

# Path to the PowerPoint template
TEMPLATE_PATH = BASE_DIR / "template.pptx"

# Directory for generated PPTX output
PPTX_OUTPUT_DIR = BASE_DIR / "output_pptx"

# RAG settings
RAG_CHUNK_SIZE = 1000
RAG_CHUNK_OVERLAP = 200
RAG_RETRIEVAL_K = 5
EMBEDDING_MODEL = "models/gemini-embedding-001"
