"""Convert PDF pages to base64-encoded PNG images entirely in memory."""

import base64
import logging

import pymupdf

logger = logging.getLogger(__name__)


def pdf_to_base64_images(
    pdf_path: str,
    start_page: int = 1,
    end_page: int = 0,
) -> tuple[list[str], int]:
    """Open *pdf_path*, render selected pages to PNG and return base64 strings.

    Args:
        pdf_path: Filesystem path to the PDF.
        start_page: First page to process (1-based). Defaults to 1.
        end_page: Last page to process (1-based). 0 means the last page
            of the document.

    Returns:
        A tuple of (list_of_base64_strings, total_pages_processed).
    """
    doc = pymupdf.open(pdf_path)
    total_doc_pages = len(doc)

    # Clamp to valid range (convert 1-based to 0-based)
    first = max(start_page - 1, 0)
    last = total_doc_pages if end_page <= 0 else min(end_page, total_doc_pages)

    if first >= last:
        first = 0
        last = total_doc_pages

    pages_to_process = last - first

    logger.info(
        "Converting page %d–%d (%d page(s)) from %s",
        first + 1,
        last,
        pages_to_process,
        pdf_path,
    )

    images: list[str] = []
    for i in range(first, last):
        page = doc.load_page(i)
        pix = page.get_pixmap()
        # Direct PNG bytes from pixmap — no temp files, no PIL needed
        png_bytes = pix.tobytes("png")
        images.append(base64.b64encode(png_bytes).decode("ascii"))

    doc.close()
    logger.info("Converted %d page(s) to base64 images", len(images))
    return images, pages_to_process
