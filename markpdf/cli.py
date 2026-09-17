"""
markpdf.cli - Command-line interface for markpdf.
"""

import argparse
import os
import sys

from . import __version__
from .converter import convert_pdf_to_text


def main():
    parser = argparse.ArgumentParser(
        prog="markpdf",
        description="Fast, offline PDF & Image to Markdown & Text converter with diagram OCR and table extraction.",
    )
    parser.add_argument("files", nargs="*", default=[], help="The PDF or image file(s) to convert (.pdf, .png, .jpg, .webp, .tiff).")
    parser.add_argument(
        "-f",
        "--format",
        choices=["auto", "txt", "md"],
        default="auto",
        help="Output format: 'txt' (plain text), 'md' (Markdown with tables & headings), or 'auto' (determined by output file extension, default: txt).",
    )
    parser.add_argument(
        "-m",
        "--markdown",
        action="store_true",
        help="Shorthand for --format md.",
    )
    parser.add_argument(
        "--toc",
        action="store_true",
        help="Generate a Markdown Table of Contents from PDF outline/bookmarks when in Markdown mode.",
    )
    parser.add_argument(
        "--ocr",
        choices=["auto", "always", "never"],
        default="auto",
        help="OCR mode: 'auto' (default, OCR if page has little/no text), 'always' (force OCR), 'never' (disable OCR).",
    )
    parser.add_argument(
        "--force-ocr",
        action="store_true",
        help="Shorthand for --ocr always.",
    )
    parser.add_argument(
        "--no-ocr",
        action="store_true",
        help="Shorthand for --ocr never.",
    )
    parser.add_argument(
        "--no-ocr-graphics",
        dest="ocr_graphics",
        action="store_false",
        default=True,
        help="Disable OCR on embedded graphics, diagrams, and pictures.",
    )
    parser.add_argument(
        "--no-graphic-labels",
        dest="label_graphics",
        action="store_false",
        default=True,
        help="Omit '[Diagram/Graphic OCR]' label before text extracted from graphics.",
    )
    parser.add_argument(
        "-l",
        "--lang",
        default="eng",
        help="Tesseract OCR language (default: 'eng').",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Rendering resolution for OCR (default: 300).",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=20,
        help="Minimum character threshold below which a page is OCR'd in auto mode (default: 20).",
    )
    parser.add_argument(
        "--min-graphic-dim",
        type=int,
        default=40,
        help="Minimum pixel dimension (width/height) for graphics/diagrams to be OCR'd (default: 40).",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Target output file path or directory (default: same directory as input file).",
    )
    parser.add_argument(
        "--page-markers",
        action="store_true",
        help="Include page delimiters between pages.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress per-page progress output.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    args = parser.parse_args()

    # Determine format
    out_format = args.format
    if args.markdown:
        out_format = "md"
    elif out_format == "auto":
        if args.output and args.output.lower().endswith(".md"):
            out_format = "md"
        else:
            out_format = "txt"

    ocr_mode = args.ocr
    if args.force_ocr:
        ocr_mode = "always"
    elif args.no_ocr:
        ocr_mode = "never"

    input_files = list(args.files)
    if not input_files:
        while True:
            try:
                user_input = input("File path (or press Enter to finish): ").strip()
                if not user_input:
                    break
                input_files.append(user_input)
            except EOFError:
                break

    if len(input_files) > 1 and args.output and not os.path.isdir(args.output):
        os.makedirs(args.output, exist_ok=True)

    success = True
    for file_path in input_files:
        res = convert_pdf_to_text(
            file_path=file_path,
            output_path=args.output,
            output_format=out_format,
            ocr_mode=ocr_mode,
            ocr_graphics=args.ocr_graphics,
            lang=args.lang,
            dpi=args.dpi,
            min_chars=args.min_chars,
            min_graphic_dim=args.min_graphic_dim,
            label_graphics=args.label_graphics,
            verbose=not args.quiet,
            add_page_markers=args.page_markers,
            add_toc=args.toc,
        )
        if not res:
            success = False

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
