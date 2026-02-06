"""Convert PDF pages to base64-encoded PNG images entirely in memory."""

import base64
import logging

import pymupdf

logger = logging.getLogger(__name__)


def pdf_to_base64_images(pdf_path: str, max_pages: int = 0) -> tuple[list[str], int]:
    """Open *pdf_path*, render each page to PNG and return base64 strings.

    Args:
        pdf_path: Filesystem path to the PDF.
        max_pages: Maximum number of pages to process. 0 means all pages.

    Returns:
        A tuple of (list_of_base64_strings, total_pages_processed).
    """
    doc = pymupdf.open(pdf_path)
    total = len(doc)

    if max_pages > 0:
        total = min(max_pages, total)

    logger.info("Converting %d page(s) from %s", total, pdf_path)

    images: list[str] = []
    for i in range(total):
        page = doc.load_page(i)
        pix = page.get_pixmap()
        # Direct PNG bytes from pixmap — no temp files, no PIL needed
        png_bytes = pix.tobytes("png")
        images.append(base64.b64encode(png_bytes).decode("ascii"))

    doc.close()
    logger.info("Converted %d page(s) to base64 images", len(images))
    return images, total
