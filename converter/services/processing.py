"""Background processing orchestrator.

Spawns a daemon thread to convert a PDF to Markdown without blocking
the HTTP request/response cycle.
"""

from __future__ import annotations

import logging
import threading
import time

from django.core.files.base import ContentFile

from converter.models import ConversionTask, get_effective_vision_config

from .pdf_to_images import pdf_to_base64_images
from .vision import transcribe_images_to_markdown

logger = logging.getLogger(__name__)


def start_processing(task_id: int, retry_failed_only: bool = False) -> None:
    """Spawn a daemon thread that runs the conversion pipeline.

    If retry_failed_only is True and the task has page_results and failed_pages,
    only the failed pages are re-transcribed and results are merged; otherwise
    a full run is performed.
    """
    thread = threading.Thread(
        target=_process_task,
        args=(task_id, retry_failed_only),
        daemon=True,
        name=f"converter-task-{task_id}",
    )
    thread.start()
    logger.info(
        "Started background thread for task %d (retry_failed_only=%s)",
        task_id,
        retry_failed_only,
    )


def _process_task(task_id: int, retry_failed_only: bool = False) -> None:
    """Execute the pipeline: PDF -> images -> vision API -> .md file.

    If retry_failed_only is True and the task has page_results and failed_pages,
    only failed pages are re-transcribed and merged into existing page_results.
    """
    try:
        task = ConversionTask.objects.get(pk=task_id)
    except ConversionTask.DoesNotExist:
        logger.error("Task %d not found — aborting", task_id)
        return

    backend, openai_model, gemini_model = get_effective_vision_config()
    task.status = ConversionTask.Status.PROCESSING
    task.vision_backend = backend
    task.vision_model = openai_model if backend == "openai" else gemini_model
    task.save(update_fields=["status", "vision_backend", "vision_model"])

    start = time.time()

    try:
        # 1. PDF -> base64 images
        images, page_count = pdf_to_base64_images(
            task.pdf_file.path,
            start_page=task.start_page,
            end_page=task.end_page,
        )
        task.page_count = page_count
        task.save(update_fields=["page_count"])

        failed_indices: list[int] | None = None
        page_results: list[str] = list(getattr(task, "page_results", None) or [])

        if retry_failed_only and page_results and getattr(task, "failed_pages", None):
            failed_pages_prev = task.failed_pages or []
            if failed_pages_prev and len(page_results) == len(images):
                failed_indices = [fp["page"] - 1 for fp in failed_pages_prev]
                failed_indices = [i for i in failed_indices if 0 <= i < len(images)]

        if failed_indices:
            # Retry only failed pages
            initial_processed = len(images) - len(failed_indices)
            task.pages_processed = initial_processed
            task.save(update_fields=["pages_processed"])
            failed_pages = []
            _, subset_results = transcribe_images_to_markdown(
                images,
                task.prompt,
                on_page_done=_make_progress_callback(task_id, initial=initial_processed),
                failed_pages=failed_pages,
                indices_to_process=failed_indices,
            )
            for i, idx in enumerate(failed_indices):
                if i < len(subset_results):
                    page_results[idx] = subset_results[i]
            markdown_text = "\n\n".join(page_results)
        else:
            # Full run
            failed_pages = []
            markdown_text, page_results = transcribe_images_to_markdown(
                images,
                task.prompt,
                on_page_done=_make_progress_callback(task_id),
                failed_pages=failed_pages,
            )

        # 3. Save Markdown file and per-page results
        task.markdown_file.save(
            task.markdown_filename,
            ContentFile(markdown_text.encode("utf-8")),
            save=False,
        )

        task.processing_time_seconds = time.time() - start
        task.failed_pages = failed_pages
        task.page_results = page_results

        # Document status: all pages failed -> FAILED; some failed -> Partially OK
        total_pages = len(images)
        if total_pages and len(failed_pages) >= total_pages:
            task.status = ConversionTask.Status.FAILED
            task.error_message = "All pages failed transcription."
            task.save(
                update_fields=[
                    "markdown_file",
                    "status",
                    "error_message",
                    "processing_time_seconds",
                    "failed_pages",
                    "page_results",
                ]
            )
        else:
            if failed_pages:
                task.status = ConversionTask.Status.PARTIAL_SUCCESS
            else:
                task.status = ConversionTask.Status.SUCCESS
            task.save(
                update_fields=[
                    "markdown_file",
                    "status",
                    "processing_time_seconds",
                    "failed_pages",
                    "page_results",
                ]
            )
        logger.info("Task %d completed in %.1fs", task_id, task.processing_time_seconds)

    except Exception as exc:
        logger.exception("Task %d failed", task_id)
        task.status = ConversionTask.Status.FAILED
        task.error_message = str(exc)
        task.processing_time_seconds = time.time() - start
        task.save(
            update_fields=["status", "error_message", "processing_time_seconds"]
        )


def _make_progress_callback(task_id: int, initial: int = 0):
    """Return a thread-safe callback that sets pages_processed = initial + n."""
    lock = threading.Lock()
    counter = {"n": 0}

    def callback(page_idx: int) -> None:
        with lock:
            counter["n"] += 1
            ConversionTask.objects.filter(pk=task_id).update(
                pages_processed=initial + counter["n"]
            )

    return callback
