"""
markpdf.converter - Main document conversion orchestrator.
"""

import io
import os
import re
import sys
from typing import Optional, List, Tuple, Any

# Optional PyMuPDF
try:
    import pymupdf

    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

# Optional PyPDF2 fallback
try:
    import PyPDF2

    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

# Local modules
from .ocr import is_ocr_available, ocr_image_pil, ocr_pixmap
from .tables import extract_page_tables

SUPPORTED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".tiff", ".bmp")
SUPPORTED_EXTENSIONS = (".pdf",) + SUPPORTED_IMAGE_EXTENSIONS


def format_markdown_heading(text: str) -> str:
    """Detect heading patterns and prepend markdown heading markers (#, ##, ###)."""
    trimmed = text.strip()
    # Match Chapter headings (BAB 1, BAB II, etc.)
    if re.match(r"^BAB\s+[IVXLCDM\d]+", trimmed, re.IGNORECASE):
        return f"# {trimmed}"

    # Match numbered section headings (e.g. 1.1, 1.1.2, 3.5.4)
    m = re.match(r"^(\d+(\.\d+)+)\s+(.*)", trimmed, re.DOTALL)
    if m:
        nums = m.group(1).split(".")
        level = min(len(nums) + 1, 5)
        prefix = "#" * level
        return f"{prefix} {trimmed}"

    return text


def format_markdown_toc(toc_items: list) -> str:
    """Format PyMuPDF doc.get_toc() list into a GitHub Markdown Table of Contents."""
    if not toc_items:
        return ""
    lines = ["# Table of Contents", ""]
    for lvl, title, pno in toc_items:
        indent = "  " * (max(1, lvl) - 1)
        slug = re.sub(r"[^\w\s-]", "", title.lower()).strip().replace(" ", "-")
        lines.append(f"{indent}- [{title}](#{slug}) *(p. {pno})*")
    return "\n".join(lines)


def extract_graphics_candidates(
    page,
    doc,
    min_dim: int = 40,
    min_area: int = 2000,
) -> List[Tuple[Any, str, int]]:
    """
    Detect candidate graphics, diagrams, and pictures on a page.

    Returns:
        List of tuples: (bbox_rect, gtype, xref)
    """
    candidates = []
    page_rect = page.rect
    is_mostly_text = len(page.get_text().strip()) >= 50

    # 1. Embedded raster images (diagrams, flowcharts, screenshots, photos)
    for img in page.get_image_info(xrefs=True):
        bbox = pymupdf.Rect(img["bbox"])
        if bbox.width < min_dim or bbox.height < min_dim:
            continue
        if (bbox.width * bbox.height) < min_area:
            continue
        # Skip full-page background images if page already has digital text
        if is_mostly_text and (bbox.width >= page_rect.width * 0.85 and bbox.height >= page_rect.height * 0.85):
            continue
        xref = img.get("xref", 0)
        candidates.append((bbox, "image", xref))

    # 2. Vector drawing clusters (flowcharts, diagrams drawn with vector paths)
    if hasattr(page, "cluster_drawings"):
        for rect in page.cluster_drawings():
            if rect.width < min_dim or rect.height < min_dim:
                continue
            if (rect.width * rect.height) < min_area:
                continue
            # Avoid duplicate if already covered by an image
            if any(r.intersects(rect) and (r & rect).get_area() > 0.5 * rect.get_area() for r, _, _ in candidates):
                continue
            # For vector drawings, check if native text already covers it
            if len(page.get_text(clip=rect).strip()) > 15:
                continue
            candidates.append((rect, "drawing", 0))

    return candidates


def convert_image(
    image_path: str,
    output_path: Optional[str] = None,
    output_format: str = "txt",
    lang: str = "eng",
    label_graphics: bool = True,
    verbose: bool = True,
) -> Optional[str]:
    """
    Convert a standalone image (.png, .jpg, .webp, .tiff) to Markdown or plain text via OCR.
    """
    if not os.path.exists(image_path):
        print(f"Error: Image file not found at '{image_path}'", file=sys.stderr)
        return None

    if not is_ocr_available():
        print("Error: Tesseract OCR is not available. Please install tesseract.", file=sys.stderr)
        return None

    try:
        from PIL import Image

        img = Image.open(image_path)
        if verbose:
            print(f"Processing image '{image_path}' ({img.width}x{img.height}, format: {output_format})...")

        txt = ocr_image_pil(img, lang=lang, upscale=True)

        is_md = output_format == "md"
        if is_md:
            if label_graphics:
                content = "> **[Image OCR]**\n" + "\n".join(f"> {line}" for line in txt.split("\n"))
            else:
                content = txt
        else:
            content = f"[Image OCR]:\n{txt}" if label_graphics else txt

        ext = ".md" if is_md else ".txt"
        if output_path:
            if os.path.isdir(output_path):
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                final_output_path = os.path.join(output_path, f"{base_name}{ext}")
            else:
                final_output_path = output_path
        else:
            base_name = os.path.splitext(image_path)[0]
            final_output_path = f"{base_name}{ext}"

        with open(final_output_path, "w", encoding="utf-8") as out_f:
            out_f.write(content.strip() + "\n")

        print(f"Successfully converted '{image_path}' to '{final_output_path}'")
        return final_output_path

    except Exception as e:
        print(f"An error occurred during image conversion: {e}", file=sys.stderr)
        return None


def convert_pdf_to_text(
    file_path: str,
    output_path: Optional[str] = None,
    output_format: str = "txt",
    ocr_mode: str = "auto",
    ocr_graphics: bool = True,
    lang: str = "eng",
    dpi: int = 300,
    min_chars: int = 20,
    min_graphic_dim: int = 40,
    label_graphics: bool = True,
    verbose: bool = True,
    add_page_markers: bool = False,
    add_toc: bool = False,
) -> Optional[str]:
    """
    Converts a PDF or image file to plain text or Markdown with OCR and table extraction.

    Args:
        file_path: Path to the input PDF or image file.
        output_path: Target output text or markdown file path or directory.
        output_format: 'txt' for plain text, 'md' for structured Markdown with tables & headings.
        ocr_mode: 'auto' (OCR if page text < min_chars), 'always' (force OCR), 'never' (disable OCR).
        ocr_graphics: Whether to detect and OCR embedded diagrams/pictures on pages.
        lang: Language code for Tesseract (e.g., 'eng', 'ind', 'eng+ind').
        dpi: Rendering DPI resolution for OCR.
        min_chars: Minimum character threshold for auto full-page OCR.
        min_graphic_dim: Minimum pixel dimension for graphics/diagrams to be OCR'd.
        label_graphics: Whether to label graphic OCR blocks.
        verbose: Whether to log extraction progress.
        add_page_markers: Whether to add page delimiters in output.
        add_toc: Whether to generate a Markdown Table of Contents from PDF outline/bookmarks.

    Returns:
        The path to the output file, or None if an error occurred.
    """
    if not os.path.exists(file_path):
        print(f"Error: File not found at '{file_path}'", file=sys.stderr)
        return None

    lower_path = file_path.lower()

    # Standalone image support
    if lower_path.endswith(SUPPORTED_IMAGE_EXTENSIONS):
        return convert_image(
            image_path=file_path,
            output_path=output_path,
            output_format=output_format,
            lang=lang,
            label_graphics=label_graphics,
            verbose=verbose,
        )

    if not lower_path.endswith(".pdf"):
        supported = ", ".join(SUPPORTED_EXTENSIONS)
        print(f"Error: Unsupported file format '{file_path}'. Supported: {supported}", file=sys.stderr)
        return None

    ocr_available = is_ocr_available()

    if (ocr_mode in ("auto", "always") or ocr_graphics) and not ocr_available:
        if ocr_mode == "always":
            print(
                f"Error: OCR requested ('{ocr_mode}'), but 'pytesseract' or 'tesseract' binary is not available.",
                file=sys.stderr,
            )
            return None
        if verbose:
            print("Note: OCR is not available. Falling back to native text extraction.", file=sys.stderr)

    if not HAS_PYMUPDF and not HAS_PYPDF2:
        print("Error: Neither 'pymupdf' nor 'PyPDF2' is installed.", file=sys.stderr)
        return None

    try:
        from PIL import Image

        pages_text = []
        graphic_cache = {}  # xref -> extracted text (deduplicates repeated logos/diagrams)
        is_md = output_format == "md"

        if HAS_PYMUPDF:
            doc = pymupdf.open(file_path)
            total_pages = len(doc)

            # Check for document TOC / outline bookmarks
            if is_md and add_toc:
                try:
                    toc_items = doc.get_toc()
                    if toc_items:
                        md_toc = format_markdown_toc(toc_items)
                        if md_toc:
                            pages_text.append(md_toc)
                except Exception:
                    pass

            if verbose:
                ocr_info = f"OCR: {ocr_mode}" + (", graphics OCR: on" if ocr_graphics and ocr_available else "")
                format_info = f"format: {output_format}"
                print(f"Processing '{file_path}' ({total_pages} page{'s' if total_pages != 1 else ''}, {format_info}, {ocr_info})...")

            for page_idx in range(total_pages):
                page = doc[page_idx]
                page_num = page_idx + 1

                native_text = page.get_text()
                native_len = len(native_text.strip())

                # Check if full-page OCR is needed
                full_page_ocr = False
                if ocr_available:
                    if ocr_mode == "always":
                        full_page_ocr = True
                    elif ocr_mode == "auto" and native_len < min_chars:
                        full_page_ocr = True

                if full_page_ocr:
                    if verbose:
                        print(f"  Page {page_num}/{total_pages}: Running full-page OCR ({lang}, {dpi} DPI)...", end="", flush=True)
                    pix = page.get_pixmap(dpi=dpi, alpha=False)
                    page_str = ocr_pixmap(pix, lang=lang)
                    if not page_str and native_text.strip():
                        page_str = native_text.strip()
                    if verbose:
                        print(f" done ({len(page_str)} chars)")
                else:
                    elements = []

                    # 1. Table Detection
                    table_rects = []
                    extracted_tables = extract_page_tables(page)
                    for t_info in extracted_tables:
                        table_rects.append(t_info["rect"])
                        elements.append({
                            "y0": t_info["rect"].y0,
                            "x0": t_info["rect"].x0,
                            "type": "table",
                            "content": t_info["content"],
                        })

                    # 2. Extract Text Blocks (filtering out blocks that sit inside detected tables)
                    for b in page.get_text("blocks"):
                        # b: (x0, y0, x1, y1, text, block_no, block_type)
                        if b[6] == 0 and b[4].strip():
                            b_rect = pymupdf.Rect(b[:4])
                            inside_table = any(
                                t_rect.contains(b_rect) or (t_rect & b_rect).get_area() > 0.5 * b_rect.get_area()
                                for t_rect in table_rects
                            )
                            if inside_table:
                                continue

                            block_text = b[4].strip()
                            if is_md:
                                block_text = format_markdown_heading(block_text)

                            elements.append({
                                "y0": b[1],
                                "x0": b[0],
                                "type": "text",
                                "content": block_text,
                            })

                    # 3. If graphics OCR is enabled, scan for diagrams/pictures
                    graphics_count = 0
                    if ocr_graphics and ocr_available and ocr_mode != "never":
                        candidate_regions = extract_graphics_candidates(page, doc, min_dim=min_graphic_dim)
                        for bbox, gtype, xref in candidate_regions:
                            # Check cache for repeated graphics
                            if xref and xref in graphic_cache:
                                cached_txt = graphic_cache[xref]
                                if cached_txt:
                                    if is_md:
                                        content = f"> **[Diagram/Graphic OCR]**\n" + "\n".join(f"> {l}" for l in cached_txt.split("\n")) if label_graphics else cached_txt
                                    else:
                                        content = f"[Diagram/Graphic OCR]:\n{cached_txt}" if label_graphics else cached_txt
                                    elements.append({
                                        "y0": bbox.y0,
                                        "x0": bbox.x0,
                                        "type": "graphic",
                                        "content": content,
                                    })
                                continue

                            txt = ""
                            if gtype == "image" and xref:
                                try:
                                    base_img = doc.extract_image(xref)
                                    if base_img and "image" in base_img:
                                        img_obj = Image.open(io.BytesIO(base_img["image"]))
                                        txt = ocr_image_pil(img_obj, lang=lang, upscale=True)
                                except Exception:
                                    pass

                            if not txt and gtype == "drawing":
                                pix = page.get_pixmap(clip=bbox, dpi=dpi, alpha=False)
                                txt = ocr_pixmap(pix, lang=lang)

                            if xref:
                                graphic_cache[xref] = txt

                            if txt:
                                graphics_count += 1
                                if is_md:
                                    content = f"> **[Diagram/Graphic OCR]**\n" + "\n".join(f"> {l}" for l in txt.split("\n")) if label_graphics else txt
                                else:
                                    content = f"[Diagram/Graphic OCR]:\n{txt}" if label_graphics else txt

                                elements.append({
                                    "y0": bbox.y0,
                                    "x0": bbox.x0,
                                    "type": "graphic",
                                    "content": content,
                                })

                    # Sort all text, tables, and diagrams in vertical reading order
                    elements.sort(key=lambda el: (el["y0"], el["x0"]))
                    page_str = "\n\n".join(el["content"] for el in elements).strip()

                    if verbose:
                        extras = []
                        if len(table_rects) > 0:
                            extras.append(f"{len(table_rects)} table{'s' if len(table_rects) != 1 else ''}")
                        if graphics_count > 0:
                            extras.append(f"{graphics_count} graphic{'s' if graphics_count != 1 else ''} OCR'd")

                        extra_str = f" + {', '.join(extras)}" if extras else ""
                        print(f"  Page {page_num}/{total_pages}: Extracted native text{extra_str} ({len(page_str)} total chars)")

                if add_page_markers:
                    if is_md:
                        pages_text.append(f"---\n*Page {page_num}*\n\n{page_str}")
                    else:
                        pages_text.append(f"--- Page {page_num} ---\n{page_str}")
                else:
                    pages_text.append(page_str)

            doc.close()

        else:
            # Fallback to PyPDF2 (native extraction only)
            if verbose:
                print(f"Processing '{file_path}' using PyPDF2 (native extraction only)...")
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                total_pages = len(reader.pages)
                for page_idx in range(total_pages):
                    page = reader.pages[page_idx]
                    page_num = page_idx + 1
                    text = page.extract_text() or ""
                    cleaned_text = text.strip()
                    if is_md:
                        cleaned_text = format_markdown_heading(cleaned_text)
                    if add_page_markers:
                        if is_md:
                            pages_text.append(f"---\n*Page {page_num}*\n\n{cleaned_text}")
                        else:
                            pages_text.append(f"--- Page {page_num} ---\n{cleaned_text}")
                    else:
                        pages_text.append(cleaned_text)

        # Determine output text path
        ext = ".md" if is_md else ".txt"
        if output_path:
            if os.path.isdir(output_path):
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                final_output_path = os.path.join(output_path, f"{base_name}{ext}")
            else:
                final_output_path = output_path
        else:
            base_name = os.path.splitext(file_path)[0]
            final_output_path = f"{base_name}{ext}"

        combined_text = "\n\n".join(pages_text).strip() + "\n"

        with open(final_output_path, "w", encoding="utf-8") as out_f:
            out_f.write(combined_text)

        print(f"Successfully converted '{file_path}' to '{final_output_path}'")
        return final_output_path

    except Exception as e:
        print(f"An error occurred during conversion: {e}", file=sys.stderr)
        return None
