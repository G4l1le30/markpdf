# markpdf

**Fast, 100% offline PDF, PowerPoint & Image to Markdown converter with embedded diagram OCR and table extraction.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![Local: 100% Offline](https://img.shields.io/badge/OCR-100%25%20Offline%20(Tesseract)-brightgreen.svg)]()

---

## Why `markpdf`?

Most document converters either:
1. **Drop visual data**: Miss text trapped inside architecture diagrams, flowcharts, screenshots, and figures.
2. **Depend on paid cloud APIs**: Require paid OpenAI / Azure vision tokens to perform OCR (e.g. Microsoft MarkItDown).
3. **Mangle document structure**: Turn normal headings or prose into broken table fragments.

`markpdf` solves this by combining the high-speed **C++ MuPDF engine (`PyMuPDF`)**, **python-pptx**, and **local Tesseract OCR**, generating clean GitHub-flavored Markdown or plain text completely offline.

---

## Benchmark vs Microsoft `markitdown`

Tested directly on a 34-page academic research proposal containing prose, 6 tables, and 2 architecture diagrams:

| Feature | Microsoft `markitdown` | `markpdf` |
| :--- | :--- | :--- |
| **Execution Time** | ⏱️ ~4.0 seconds | ⚡ **~1.8 seconds (2x faster)** |
| **Diagram OCR** | ❌ **0 chars** (Missed completely) | ✅ **100% Extracted locally** (in reading position) |
| **Table Extraction** | ✅ Markdown tables | ✅ Clean GitHub Markdown tables |
| **Formatting Reliability** | ⚠️ False-positive broken tables on headings | ✅ Pristine heading hierarchy (`#`, `###`, `####`) |
| **Privacy & Cost** | ❌ Requires paid cloud API keys for OCR | ✅ **100% Free, Local & Private** |

---

## Key Features

- **📑 Smart Hybrid PDF Extraction**: Instant native text extraction on digital pages; automatic OCR fallback on scanned/rasterized pages.
- **📽️ Native PowerPoint (`.pptx`) Support**: Converts slides, nested bullet hierarchies, speaker notes, slide tables, and embedded slide diagrams.
- **📊 Native Markdown Tables**: Converts tabular grids in PDFs and PowerPoint slides directly into GitHub-flavored Markdown tables.
- **🖼️ Diagram & Graphic OCR**: Isolates embedded figures, flowcharts, and diagrams, upscales small labels using Lanczos resampling, and weaves the OCR'd text into natural reading order.
- **🏷️ Markdown Blockquotes**: Diagram text in Markdown mode is neatly styled in blockquotes (`> **[Diagram/Graphic OCR]**`).
- **⚡ Blazing Fast**: Powered by PyMuPDF's C++ bindings rather than slow pure-Python PDF parsers.
- **🔒 Fully Offline**: Zero network calls, zero API tokens, 100% local processing.

---

## Installation

### Prerequisites
Make sure Tesseract is installed:
```bash
# macOS (Homebrew)
brew install tesseract

# Optional: Install additional languages (e.g. Indonesian)
brew install tesseract-lang

# Ubuntu / Debian
sudo apt-get install tesseract-ocr
```

### Install `markpdf`
Clone and install locally:
```bash
git clone https://github.com/G4l1le30/markpdf.git
cd markpdf
pip install -e .
```

---

## CLI Usage

### Basic Commands
```bash
# Convert PDF to Markdown (.md) with tables and diagram OCR
markpdf -m document.pdf

# Convert PowerPoint (.pptx) to Markdown with tables, notes and diagram OCR
markpdf -m presentation.pptx

# Convert standalone image (.png, .jpg, .webp) to Markdown via OCR
markpdf -m screenshot.png

# Convert to Plain Text (.txt)
markpdf document.pdf

# Specify custom output path
markpdf document.pdf -o output.md
```

### Advanced Options
```bash
# Generate Markdown Table of Contents from PDF outline/bookmarks
markpdf --toc -m book.pdf

# Force full-page OCR across all pages (e.g. corrupted text layer)
markpdf --force-ocr scanned_book.pdf

# Specify OCR languages (e.g. English + Indonesian)
markpdf -l eng+ind -m proposal.pdf

# Disable graphic/diagram OCR (extract only body text)
markpdf --no-ocr-graphics document.pdf

# Set custom DPI resolution for OCR rendering (default: 300)
markpdf --dpi 300 document.pdf

# Include page break markers
markpdf --page-markers -m document.pdf
```

### Command Flags

| Flag | Description |
|---|---|
| `-m, --markdown` | Shorthand for `--format md` (Markdown output with tables & headings) |
| `-f, --format {auto,txt,md}` | Output format (default: auto based on output extension) |
| `--toc` | Generate Markdown Table of Contents from PDF outline/bookmarks |
| `-o, --output <path>` | Custom destination file or directory |
| `--ocr {auto,always,never}` | OCR mode (default: `auto` for scanned pages/graphics) |
| `--force-ocr` | Force OCR across all pages |
| `--no-ocr` | Disable all OCR |
| `--no-ocr-graphics` | Skip diagram/graphic OCR |
| `--no-graphic-labels` | Omit `[Diagram/Graphic OCR]` header label |
| `-l, --lang <lang>` | Tesseract language code (default: `eng`) |
| `--dpi <int>` | Rendering resolution for OCR (default: `300`) |
| `--page-markers` | Include page delimiters (`---` / `*Page X*`) |
| `-q, --quiet` | Suppress per-page console logs |
| `-v, --version` | Show program version |

---

## Python API

You can also use `markpdf` programmatically:

```python
from markpdf import convert_pdf

# Convert to Markdown
output_file = convert_pdf(
    pdf_path="paper.pdf",
    output_format="md",
    ocr_mode="auto",
    lang="eng",
)
print(f"Saved to {output_file}")
```

---

## License

MIT License © 2026 Joshua Washington
