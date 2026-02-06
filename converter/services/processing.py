"""Background processing orchestrator.

Spawns a daemon thread to convert a PDF to Markdown without blocking
the HTTP request/response cycle.
"""

from __future__ import annotations

import logging
import threading
import time

from django.conf import settings
from django.core.files.base import ContentFile

from converter.models import ConversionTask

from .pdf_to_images import pdf_to_base64_images
from .vision import transcribe_images_to_markdown

logger = logging.getLogger(__name__)


def start_processing(task_id: int) -> None:
    """Spawn a daemon thread that runs the full conversion pipeline."""
    thread = threading.Thread(
        target=_process_task,
        args=(task_id,),
        daemon=True,
        name=f"converter-task-{task_id}",
    )
    thread.start()
    logger.info("Started background thread for task %d", task_id)


def _process_task(task_id: int) -> None:
    """Execute the full pipeline: PDF -> images -> vision API -> .md file.

    Updates the ConversionTask record in the DB as it progresses so the
    polling endpoint can relay status to the browser.
    """
    try:
        task = ConversionTask.objects.get(pk=task_id)
    except ConversionTask.DoesNotExist:
        logger.error("Task %d not found — aborting", task_id)
        return

    task.status = ConversionTask.Status.PROCESSING
    task.vision_backend = settings.VISION_BACKEND
    task.vision_model = (
        settings.OPENAI_VISION_MODEL
        if settings.VISION_BACKEND == "openai"
        else settings.GEMINI_VISION_MODEL
    )
    task.save(update_fields=["status", "vision_backend", "vision_model"])

    start = time.time()

    try:
        # 1. PDF -> base64 images
        max_pages = task.max_pages or settings.MAX_PDF_PAGES
        images, page_count = pdf_to_base64_images(task.pdf_file.path, max_pages)
        task.page_count = page_count
        task.save(update_fields=["page_count"])

        # 2. Vision API -> Markdown (concurrent, with progress updates)
        markdown_text = transcribe_images_to_markdown(
            images,
            task.prompt,
            on_page_done=_make_progress_callback(task_id),
        )

        # 3. Save Markdown file
        safe_name = (
            task.original_filename.rsplit(".", 1)[0][:200] + ".md"
        )
        task.markdown_file.save(
            safe_name,
            ContentFile(markdown_text.encode("utf-8")),
            save=False,
        )

        task.status = ConversionTask.Status.SUCCESS
        task.processing_time_seconds = time.time() - start
        task.save(
            update_fields=[
                "markdown_file",
                "status",
                "processing_time_seconds",
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


def _make_progress_callback(task_id: int):
    """Return a thread-safe callback that increments pages_processed."""
    lock = threading.Lock()
    counter = {"n": 0}

    def callback(page_idx: int) -> None:
        with lock:
            counter["n"] += 1
            ConversionTask.objects.filter(pk=task_id).update(
                pages_processed=counter["n"]
            )

    return callback
