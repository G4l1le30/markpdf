"""
markpdf.ocr - Offline OCR helpers powered by Tesseract and Pillow.
"""

import os
import shutil

try:
    from PIL import Image
    import pytesseract

    HAS_OCR = True
except ImportError:
    HAS_OCR = False


def setup_tesseract_path() -> bool:
    """Ensure pytesseract can locate the tesseract binary on macOS / Linux."""
    if not HAS_OCR:
        return False

    if shutil.which("tesseract"):
        return True

    common_paths = [
        "/opt/homebrew/bin/tesseract",
        "/usr/local/bin/tesseract",
        "/usr/bin/tesseract",
    ]
    for path in common_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            pytesseract.pytesseract.tesseract_cmd = path
            return True
    return False


def is_ocr_available() -> bool:
    """Check if both pytesseract and the tesseract binary are available."""
    return HAS_OCR and setup_tesseract_path()


def ocr_image_pil(img_obj, lang: str = "eng", upscale: bool = True) -> str:
    """
    Perform OCR on a PIL Image with transparency handling and optional upscaling for diagrams.

    Args:
        img_obj: PIL Image instance.
        lang: Tesseract language code(s) (e.g. 'eng', 'ind', 'eng+ind').
        upscale: Whether to upscale small diagram fonts via Lanczos resampling.

    Returns:
        Extracted text string, or empty string if no alphanumeric text was found.
    """
    if not HAS_OCR:
        return ""

    if img_obj.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", img_obj.size, (255, 255, 255))
        if img_obj.mode == "P":
            img_obj = img_obj.convert("RGBA")
        mask = img_obj.split()[-1] if img_obj.mode in ("RGBA", "LA") else None
        bg.paste(img_obj, mask=mask)
        img_obj = bg
    else:
        img_obj = img_obj.convert("RGB")

    # Upscale smaller images/diagrams so small text labels (8-10pt) are recognized reliably
    w, h = img_obj.size
    if upscale and max(w, h) < 1800:
        scale = min(2.0, 1800.0 / max(w, h))
        if scale > 1.1:
            img_obj = img_obj.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

    text = pytesseract.image_to_string(img_obj, lang=lang).strip()
    # Filter out pure punctuation noise (e.g. noise from background patterns)
    if not any(c.isalnum() for c in text):
        return ""
    return text


def ocr_pixmap(pix, lang: str = "eng") -> str:
    """Perform OCR on a PyMuPDF pixmap using pytesseract."""
    if not HAS_OCR:
        return ""
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return ocr_image_pil(img, lang=lang, upscale=False)
