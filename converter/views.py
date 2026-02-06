import logging

import markdown as md
from django.conf import settings
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import UploadForm
from .models import ConversionTask
from .services.processing import start_processing

logger = logging.getLogger(__name__)


# ── Upload / Index ────────────────────────────────────────────


def index(request):
    """Show the upload form (GET) or create a task and start processing (POST)."""
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            pdf_file = form.cleaned_data["pdf_file"]
            prompt = form.cleaned_data["prompt"]
            max_pages = form.cleaned_data.get("max_pages") or 0

            task = ConversionTask.objects.create(
                original_filename=pdf_file.name,
                pdf_file=pdf_file,
                prompt=prompt,
                max_pages=max_pages,
            )

            # Kick off background processing
            start_processing(task.pk)

            return redirect("converter:processing", pk=task.pk)
    else:
        form = UploadForm()

    return render(request, "converter/index.html", {"form": form})


# ── Processing (polling page) ─────────────────────────────────


def processing(request, pk):
    """Render the processing page with a JS polling loop."""
    task = get_object_or_404(ConversionTask, pk=pk)

    # If already done, redirect straight to result
    if task.status == ConversionTask.Status.SUCCESS:
        return redirect("converter:result", pk=task.pk)
    if task.status == ConversionTask.Status.FAILED:
        return redirect("converter:result", pk=task.pk)

    return render(request, "converter/processing.html", {"task": task})


# ── Status API (JSON for polling) ─────────────────────────────


def task_status(request, pk):
    """Return task status as JSON for the polling frontend."""
    task = get_object_or_404(ConversionTask, pk=pk)
    return JsonResponse(
        {
            "status": task.status,
            "page_count": task.page_count,
            "pages_processed": task.pages_processed,
            "error_message": task.error_message if task.status == "failed" else "",
        }
    )


# ── Result ────────────────────────────────────────────────────


def result(request, pk):
    """Show the conversion result with a rendered Markdown preview."""
    task = get_object_or_404(ConversionTask, pk=pk)

    markdown_html = ""
    markdown_raw = ""

    if task.markdown_file and task.status == ConversionTask.Status.SUCCESS:
        try:
            markdown_raw = task.markdown_file.read().decode("utf-8")
            task.markdown_file.seek(0)
            markdown_html = md.markdown(
                markdown_raw,
                extensions=["tables", "fenced_code", "toc"],
            )
        except Exception:
            logger.exception("Failed to read markdown for task %d", pk)

    return render(
        request,
        "converter/result.html",
        {
            "task": task,
            "markdown_html": markdown_html,
            "markdown_raw": markdown_raw,
        },
    )


# ── Download ──────────────────────────────────────────────────


def download(request, pk):
    """Serve the Markdown file as a download."""
    task = get_object_or_404(ConversionTask, pk=pk)

    if not task.markdown_file or task.status != ConversionTask.Status.SUCCESS:
        raise Http404("Markdown file not available.")

    safe_name = task.original_filename.rsplit(".", 1)[0][:200] + ".md"

    response = FileResponse(
        task.markdown_file.open("rb"),
        content_type="text/markdown; charset=utf-8",
    )
    response["Content-Disposition"] = f'attachment; filename="{safe_name}"'
    return response


# ── History ───────────────────────────────────────────────────


def history(request):
    """List all conversion tasks."""
    tasks = ConversionTask.objects.all()
    return render(request, "converter/history.html", {"tasks": tasks})
