"""Vision API backends — OpenAI and Gemini.

The public entry point is ``transcribe_images_to_markdown()``.  It reads
``settings.VISION_BACKEND`` to dispatch to the correct provider and uses
``concurrent.futures.ThreadPoolExecutor`` for concurrent page processing.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Optional

from django.conf import settings

logger = logging.getLogger(__name__)


# ── Public API ────────────────────────────────────────────────


def transcribe_images_to_markdown(
    base64_images: list[str],
    prompt: str,
    on_page_done: Optional[Callable[[int], None]] = None,
) -> str:
    """Transcribe a list of base64 page images to a single Markdown string.

    Args:
        base64_images: List of base64-encoded PNG strings (one per page).
        prompt: The transcription prompt to send with each image.
        on_page_done: Optional callback invoked with the page index (0-based)
            each time a page finishes.

    Returns:
        Concatenated Markdown string for all pages.
    """
    backend = settings.VISION_BACKEND.lower()
    max_workers = getattr(settings, "VISION_MAX_WORKERS", 4)

    if backend == "openai":
        transcribe_fn = _openai_transcribe_page
        model = settings.OPENAI_VISION_MODEL
    elif backend == "gemini":
        transcribe_fn = _gemini_transcribe_page
        model = settings.GEMINI_VISION_MODEL
    else:
        raise ValueError(f"Unknown VISION_BACKEND: {backend!r}")

    logger.info(
        "Transcribing %d page(s) via %s / %s (workers=%d)",
        len(base64_images),
        backend,
        model,
        max_workers,
    )

    # Pre-allocate results list to maintain page order
    results: list[str | None] = [None] * len(base64_images)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_to_idx = {
            pool.submit(transcribe_fn, img, prompt, model): idx
            for idx, img in enumerate(base64_images)
        }

        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result()
            except Exception:
                logger.exception("Page %d transcription failed", idx + 1)
                results[idx] = (
                    f"\n\n<!-- [Page {idx + 1}: transcription failed] -->\n\n"
                )

            if on_page_done is not None:
                on_page_done(idx)

    # Join pages with double newline separators
    return "\n\n".join(r for r in results if r is not None)


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
    import base64 as b64_mod

    import google.generativeai as genai

    genai.configure(api_key=settings.GEMINI_API_KEY)
    gen_model = genai.GenerativeModel(model)

    image_bytes = b64_mod.b64decode(base64_image)

    response = gen_model.generate_content(
        [
            prompt,
            {
                "mime_type": "image/png",
                "data": image_bytes,
            },
        ]
    )

    return response.text
