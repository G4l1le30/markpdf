"""
markpdf.tables - Table detection and GitHub-flavored Markdown table formatting.
"""

from typing import Any, List, Dict


def format_markdown_table(rows: List[List[Any]]) -> str:
    """
    Convert a 2D list of extracted table cells into a clean GitHub-flavored Markdown table.

    Args:
        rows: 2D list of cell values.

    Returns:
        Formatted Markdown table string.
    """
    if not rows:
        return ""

    cleaned_rows = []
    for r in rows:
        cleaned_row = []
        for c in r:
            val = str(c).strip() if c is not None else ""
            val = val.replace("\n", "<br>").replace("|", "\\|")
            cleaned_row.append(val)
        if any(cleaned_row):
            cleaned_rows.append(cleaned_row)

    if not cleaned_rows:
        return ""

    col_count = max(len(r) for r in cleaned_rows)
    header = cleaned_rows[0] + [""] * (col_count - len(cleaned_rows[0]))

    md = ["| " + " | ".join(header) + " |"]
    md.append("| " + " | ".join("---" for _ in range(col_count)) + " |")
    for row in cleaned_rows[1:]:
        padded_row = row + [""] * (col_count - len(row))
        md.append("| " + " | ".join(padded_row) + " |")

    return "\n".join(md)


def extract_page_tables(page: Any) -> List[Dict[str, Any]]:
    """
    Detect tables on a PyMuPDF page and convert them to formatted Markdown tables.

    Returns:
        List of dicts with keys: 'bbox', 'rect', 'content'
    """
    extracted_tables = []
    if not hasattr(page, "find_tables"):
        return extracted_tables

    try:
        tabs = page.find_tables()
        for t in tabs.tables:
            table_md = format_markdown_table(t.extract())
            if table_md:
                import pymupdf
                t_rect = pymupdf.Rect(t.bbox)
                extracted_tables.append({
                    "bbox": t.bbox,
                    "rect": t_rect,
                    "content": table_md,
                })
    except Exception:
        pass

    return extracted_tables
