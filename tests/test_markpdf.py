"""
Unit tests for markpdf.
"""

import os
import tempfile
import unittest

from markpdf.tables import format_markdown_table
from markpdf.converter import (
    format_markdown_heading,
    format_markdown_toc,
    convert_pdf_to_text,
)


class TestMarkPDF(unittest.TestCase):
    def test_format_markdown_table(self):
        rows = [
            ["Col 1", "Col 2"],
            ["Val A", "Val B\nwith newline"],
            ["Val C", "Val | with pipe"],
        ]
        md = format_markdown_table(rows)
        self.assertIn("| Col 1 | Col 2 |", md)
        self.assertIn("| --- | --- |", md)
        self.assertIn("Val B<br>with newline", md)
        self.assertIn("Val \\| with pipe", md)

    def test_format_markdown_heading(self):
        self.assertEqual(format_markdown_heading("BAB 1 PENDAHULUAN"), "# BAB 1 PENDAHULUAN")
        self.assertEqual(format_markdown_heading("1.1 Latar Belakang"), "### 1.1 Latar Belakang")
        self.assertEqual(format_markdown_heading("3.5.4 Sub Section"), "#### 3.5.4 Sub Section")
        self.assertEqual(format_markdown_heading("Normal paragraph text."), "Normal paragraph text.")

    def test_format_markdown_toc(self):
        toc_items = [
            [1, "Introduction", 1],
            [2, "Background", 2],
            [1, "Methodology", 5],
        ]
        md_toc = format_markdown_toc(toc_items)
        self.assertIn("# Table of Contents", md_toc)
        self.assertIn("- [Introduction](#introduction) *(p. 1)*", md_toc)
        self.assertIn("  - [Background](#background) *(p. 2)*", md_toc)
        self.assertIn("- [Methodology](#methodology) *(p. 5)*", md_toc)

    def test_convert_pdf_digital(self):
        try:
            import pymupdf
        except ImportError:
            self.skipTest("pymupdf not installed")

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, "test.pdf")
            doc = pymupdf.open()
            page = doc.new_page()
            page.insert_text((72, 100), "Hello MarkPDF World!", fontsize=14)
            doc.save(pdf_path)
            doc.close()

            # Test text mode
            txt_out = convert_pdf_to_text(pdf_path, output_format="txt", verbose=False)
            self.assertTrue(os.path.exists(txt_out))
            with open(txt_out, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("Hello MarkPDF World!", content)

            # Test markdown mode
            md_out = convert_pdf_to_text(pdf_path, output_format="md", verbose=False)
            self.assertTrue(os.path.exists(md_out))
            self.assertTrue(md_out.endswith(".md"))

    def test_convert_standalone_image(self):
        try:
            from PIL import Image, ImageDraw
        except ImportError:
            self.skipTest("Pillow not installed")

        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = os.path.join(tmpdir, "sample.png")
            img = Image.new("RGB", (300, 100), color=(255, 255, 255))
            d = ImageDraw.Draw(img)
            d.text((20, 40), "Sample Image Text", fill=(0, 0, 0))
            img.save(img_path)

            res = convert_pdf_to_text(img_path, output_format="md", verbose=False)
            self.assertTrue(os.path.exists(res))
            self.assertTrue(res.endswith(".md"))


if __name__ == "__main__":
    unittest.main()
