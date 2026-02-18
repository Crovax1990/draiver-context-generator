# Draiver Context Generator

A minimal local Python CLI that converts university lecture documents (PDF, DOCX, PPTX, TXT) into structured Markdown context files, ready to be used as a knowledge base for an AI agent.

## How it works

```
input/ (your documents)
    └── dispensa_fisica.pdf
    └── lezione_01.docx
    └── slide_intro.pptx
         ↓  Docling parsing
output/ (generated Markdown)
    └── dispensa_fisica.md
    └── lezione_01.md
    └── slide_intro.md
```

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create the input folder and add your documents
mkdir input
# copy your PDF, DOCX, PPTX, TXT files into input/
```

## Usage

```bash
# Default: one .md file per document (recommended)
python main.py

# Single aggregated output file
python main.py --mode single

# Custom paths
python main.py --input ./my_docs --output ./my_output

# Help
python main.py --help
```

## Output format

Each generated `.md` file includes:
- **YAML frontmatter** with title, source filename, page count, and generation timestamp
- **Full Markdown content** extracted by Docling (headings, paragraphs, tables, lists preserved)

In `--mode single`, a single `context.md` is produced with a Table of Contents linking all documents.

## Supported formats

| Format | Extension |
|--------|-----------|
| PDF | `.pdf` |
| Word | `.docx` |
| PowerPoint | `.pptx` |
| Plain text | `.txt` |

## Project structure

```
draiver-context-generator/
├── input/              # Place your source documents here (gitignored)
├── output/             # Generated Markdown files (gitignored)
├── src/
│   ├── ingestion.py    # Scans input folder
│   ├── extraction.py   # Docling-based conversion
│   └── output_writer.py# Markdown file generation
├── main.py             # CLI entry point
├── config.py           # Configuration
└── requirements.txt
```
