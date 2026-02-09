import html
import logging
from urllib.parse import quote

import markdown as md
from django.conf import settings
from django.contrib import messages
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import (
    GEMINI_MODEL_CHOICES,
    OPENAI_MODEL_CHOICES,
    SettingsForm,
    UploadForm,
)
from .models import APP_SETTINGS_ID, AppSettings, ConversionTask, get_effective_vision_config
from .services.processing import start_processing
from .services.vision import FAILED_PAGE_PLACEHOLDER_TEMPLATE

logger = logging.getLogger(__name__)


# ── Upload / Index ────────────────────────────────────────────


def index(request):
    """Show the upload form (GET) or create a task and start processing (POST)."""
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            pdf_file = form.cleaned_data["pdf_file"]
            prompt = form.cleaned_data["prompt"]
            start_page = form.cleaned_data.get("start_page") or 1
            end_page = form.cleaned_data.get("end_page") or 0

            task = ConversionTask.objects.create(
                original_filename=pdf_file.name,
                pdf_file=pdf_file,
                prompt=prompt,
                start_page=start_page,
                end_page=end_page,
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
    if task.status in (
        ConversionTask.Status.SUCCESS,
        ConversionTask.Status.PARTIAL_SUCCESS,
    ):
        return redirect("converter:result", pk=task.pk)
    if task.status == ConversionTask.Status.FAILED:
        return redirect("converter:result", pk=task.pk)

    backend, _, _ = get_effective_vision_config()
    return render(
        request,
        "converter/processing.html",
        {"task": task, "is_openai": backend == "openai"},
    )


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

    if task.markdown_file and task.status in (
        ConversionTask.Status.SUCCESS,
        ConversionTask.Status.PARTIAL_SUCCESS,
    ):
        try:
            markdown_raw = task.markdown_file.read().decode("utf-8")
            task.markdown_file.seek(0)
            # Replace transcription-failed placeholders with error UI for preview
            failed_pages = getattr(task, "failed_pages", None) or []
            markdown_for_preview = markdown_raw
            for fp in failed_pages:
                page_num = fp.get("page")
                err_msg = fp.get("error", "Unknown error")
                if page_num is None:
                    continue
                placeholder = FAILED_PAGE_PLACEHOLDER_TEMPLATE.format(page_num)
                safe_error = html.escape(err_msg)
                retry_url = reverse("converter:retry_task", kwargs={"pk": task.pk})
                replacement = (
                    f'<div class="transcription-failed-box" data-page="{page_num}">'
                    f'<p class="transcription-failed-title">Page {page_num}: transcription failed</p>'
                    f'<pre class="transcription-failed-error">{safe_error}</pre>'
                    f'<a href="{retry_url}" class="transcription-failed-retry">Retry conversion</a>'
                    "</div>"
                )
                markdown_for_preview = markdown_for_preview.replace(
                    placeholder, replacement, 1
                )
            markdown_html = md.markdown(
                markdown_for_preview,
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


# ── Retry ─────────────────────────────────────────────────────


def retry_task(request, pk):
    """Retry failed pages only (same task) if possible; otherwise start a new full conversion."""
    task = get_object_or_404(ConversionTask, pk=pk)
    if not task.pdf_file:
        raise Http404("Original PDF not available.")

    page_results = getattr(task, "page_results", None) or []
    failed_pages = getattr(task, "failed_pages", None) or []
    if page_results and failed_pages and len(page_results) == (task.page_count or 0):
        # Same task: re-run only failed pages and merge
        start_processing(task.pk, retry_failed_only=True)
        return redirect("converter:processing", pk=task.pk)
    # No per-page data or legacy task: create new task and run full conversion
    new_task = ConversionTask.objects.create(
        original_filename=task.original_filename,
        pdf_file=task.pdf_file,
        prompt=task.prompt,
        start_page=task.start_page,
        end_page=task.end_page,
    )
    start_processing(new_task.pk)
    return redirect("converter:processing", pk=new_task.pk)


# ── Download ──────────────────────────────────────────────────


def download(request, pk):
    """Serve the Markdown file as a download."""
    task = get_object_or_404(ConversionTask, pk=pk)

    if not task.markdown_file or task.effective_status == ConversionTask.Status.FAILED:
        raise Http404("Markdown file not available.")

    safe_name = task.markdown_filename

    response = FileResponse(
        task.markdown_file.open("rb"),
        content_type="text/markdown; charset=utf-8",
    )
    response["Content-Disposition"] = f'attachment; filename="{safe_name}"'
    return response


def download_pdf(request, pk):
    """Serve the original PDF file as a download."""
    task = get_object_or_404(ConversionTask, pk=pk)

    if not task.pdf_file:
        raise Http404("Original PDF not available.")

    response = FileResponse(
        task.pdf_file.open("rb"),
        content_type="application/pdf",
    )
    response["Content-Disposition"] = f'attachment; filename="{task.original_filename}"'
    return response


# ── History ───────────────────────────────────────────────────


def history(request):
    """List all conversion tasks, optionally filtered by filename search."""
    tasks = ConversionTask.objects.all()
    search_query = (request.GET.get("q") or "").strip()
    if search_query:
        tasks = tasks.filter(original_filename__icontains=search_query)
    return render(
        request,
        "converter/history.html",
        {"tasks": tasks, "search_query": search_query},
    )


def history_bulk_delete(request):
    """Delete selected conversion tasks (POST with ids)."""
    if request.method != "POST":
        return redirect("converter:history")
    ids = request.POST.getlist("ids")
    if ids:
        try:
            pk_list = [int(x) for x in ids]
            ConversionTask.objects.filter(pk__in=pk_list).delete()
        except (ValueError, TypeError):
            pass
    search_query = (request.POST.get("q") or "").strip()
    if search_query:
        return redirect(reverse("converter:history") + "?q=" + quote(search_query))
    return redirect("converter:history")


# ── Settings ──────────────────────────────────────────────────


def _get_or_create_app_settings():
    """Return the singleton AppSettings row, creating it if needed."""
    obj, _ = AppSettings.objects.get_or_create(
        pk=APP_SETTINGS_ID,
        defaults={
            "vision_backend": "",
            "openai_model": "",
            "gemini_model": "",
        },
    )
    return obj


def _model_choice_value(val: str, choices: list[tuple[str, str]]) -> str:
    """Return form choice value for a model field (value, 'custom', or '')."""
    choice_values = [c[0] for c in choices]
    if val and val in choice_values:
        return val
    if val:
        return "custom"
    return ""


def settings_view(request):
    """Show and save vision backend and model overrides."""
    app = _get_or_create_app_settings()

    if request.method == "POST":
        form = SettingsForm(request.POST)
        if form.is_valid():
            app.vision_backend = (form.cleaned_data.get("vision_backend") or "").strip()
            # Form clean() already resolves "custom" to the custom field value
            app.openai_model = (form.cleaned_data.get("openai_model") or "").strip()
            app.gemini_model = (form.cleaned_data.get("gemini_model") or "").strip()
            app.save()
            messages.success(request, "Settings saved. New conversions will use the selected model.")
            return redirect("converter:settings")
    else:
        openai_val = app.openai_model or ""
        gemini_val = app.gemini_model or ""
        openai_choice = _model_choice_value(openai_val, OPENAI_MODEL_CHOICES)
        gemini_choice = _model_choice_value(gemini_val, GEMINI_MODEL_CHOICES)
        form = SettingsForm(
            initial={
                "vision_backend": app.vision_backend or "",
                "openai_model": openai_choice,
                "openai_model_custom": openai_val if (openai_val and openai_choice == "custom") else "",
                "gemini_model": gemini_choice,
                "gemini_model_custom": gemini_val if (gemini_val and gemini_choice == "custom") else "",
            }
        )

    return render(request, "converter/settings.html", {"form": form})
