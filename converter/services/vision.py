"""Vision API backends — OpenAI and Gemini.

The public entry point is ``transcribe_images_to_markdown()``.  It reads
``settings.VISION_BACKEND`` to dispatch to the correct provider and uses
``concurrent.futures.ThreadPoolExecutor`` for concurrent page processing.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional

# Placeholder string for a failed page (must match processing/views logic)
FAILED_PAGE_PLACEHOLDER_TEMPLATE = "<!-- [Page {}: transcription failed] -->"

from django.conf import settings

from converter.models import get_effective_vision_config

logger = logging.getLogger(__name__)


# ── Public API ────────────────────────────────────────────────


def transcribe_images_to_markdown(
    base64_images: list[str],
    prompt: str,
    on_page_done: Optional[Callable[[int], None]] = None,
    failed_pages: Optional[list[dict]] = None,
    indices_to_process: Optional[list[int]] = None,
) -> tuple[str | None, list[str]]:
    """Transcribe page images to Markdown, optionally only a subset of indices.

    Args:
        base64_images: List of base64-encoded PNG strings (one per page).
        prompt: The transcription prompt to send with each image.
        on_page_done: Optional callback invoked with the page index (0-based)
            each time a page finishes.
        failed_pages: Optional mutable list; each failed page appends
            {"page": 1-based index, "error": exception message}.
        indices_to_process: If set, only these 0-based indices are transcribed
            (for retrying failed pages). Returned list has one entry per index
            in this list, in order.

    Returns:
        (full_markdown, page_results):
        - If indices_to_process is None: full_markdown is the concatenated
          string, page_results has length len(base64_images).
        - If indices_to_process is set: full_markdown is None, page_results
          has length len(indices_to_process) (results for those indices only).
    """
    backend, openai_model, gemini_model = get_effective_vision_config()
    max_workers = getattr(settings, "VISION_MAX_WORKERS", 4)

    if backend == "openai":
        transcribe_fn = _openai_transcribe_page
        model = openai_model
    elif backend == "gemini":
        transcribe_fn = _gemini_transcribe_page
        model = gemini_model
    else:
        raise ValueError(f"Unknown VISION_BACKEND: {backend!r}")

    if indices_to_process is not None:
        indices_to_process = sorted(set(indices_to_process))
        image_subset = [base64_images[i] for i in indices_to_process]
        n_results = len(indices_to_process)
        idx_to_subset_pos = {idx: pos for pos, idx in enumerate(indices_to_process)}
    else:
        image_subset = base64_images
        indices_to_process = list(range(len(base64_images)))
        n_results = len(base64_images)
        idx_to_subset_pos = {i: i for i in range(n_results)}

    logger.info(
        "Transcribing %d page(s) via %s / %s (workers=%d)",
        n_results,
        backend,
        model,
        max_workers,
    )

    results: list[str | None] = [None] * n_results

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_to_idx = {
            pool.submit(transcribe_fn, img, prompt, model): indices_to_process[pos]
            for pos, img in enumerate(image_subset)
        }

        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            pos = idx_to_subset_pos[idx]
            page_num = idx + 1
            try:
                results[pos] = future.result()
            except Exception as exc:
                err_msg = str(exc) or type(exc).__name__
                logger.exception("Page %d transcription failed", page_num)
                if failed_pages is not None:
                    failed_pages.append({"page": page_num, "error": err_msg})
                results[pos] = (
                    "\n\n"
                    + FAILED_PAGE_PLACEHOLDER_TEMPLATE.format(page_num)
                    + "\n\n"
                )

            if on_page_done is not None:
                on_page_done(idx)

    page_results_list = [r for r in results if r is not None]
    full_markdown = "\n\n".join(page_results_list) if page_results_list else ""
    if indices_to_process is None or len(indices_to_process) == len(base64_images):
        return (full_markdown, list(results))
    return (None, list(results))


# ── OpenAI backend ────────────────────────────────────────────


def _openai_transcribe_page(base64_image: str, prompt: str, model: str) -> str:
    """Transcribe a single page image using the OpenAI chat completions API."""
    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    response = client.chat.completions.create(
        model=model,
        response_format={"type": "text"},
        messages=[
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Transcribe the information in this document in Markdown format",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}",
                            "detail": "high",
                        },
                    },
                ],
            },
        ],
    )

    return response.choices[0].message.content


# ── Gemini backend ────────────────────────────────────────────


def _gemini_transcribe_page(base64_image: str, prompt: str, model: str) -> str:
    """Transcribe a single page image using the Google Gemini API."""
    import base64
    import io

    from google import genai
    from PIL import Image

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    image_bytes = base64.b64decode(base64_image)
    pil_image = Image.open(io.BytesIO(image_bytes))

    response = client.models.generate_content(
        model=model,
        contents=[prompt, pil_image],
    )

    return response.text
