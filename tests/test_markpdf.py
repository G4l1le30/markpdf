"""
Unit tests for markpdf.
"""

import os
import tempfile
import unittest

from markpdf.tables import format_markdown_table
from markpdf.converter import format_markdown_heading, convert_pdf_to_text


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


if __name__ == "__main__":
    unittest.main()
