"""
markpdf - Fast, offline PDF to Markdown & Text converter with diagram OCR and table extraction.
"""

__version__ = "0.3.0"

from .converter import convert_pdf_to_text
from .tables import format_markdown_table, extract_page_tables
from .ocr import is_ocr_available, setup_tesseract_path

# Convenient top-level alias
convert_pdf = convert_pdf_to_text

__all__ = [
    "__version__",
    "convert_pdf_to_text",
    "convert_pdf",
    "format_markdown_table",
    "extract_page_tables",
    "is_ocr_available",
    "setup_tesseract_path",
]
