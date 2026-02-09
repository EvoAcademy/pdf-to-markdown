from django.db import models


# Singleton primary key for app-level settings
APP_SETTINGS_ID = 1


class AppSettings(models.Model):
    """Singleton (id=1) storing user-selected vision backend and models.

    Empty fields mean "use environment variable default".
    """

    vision_backend = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Override VISION_BACKEND: 'openai', 'gemini', or empty for env default.",
    )
    openai_model = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Override OpenAI model ID when backend is openai.",
    )
    gemini_model = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Override Gemini model ID when backend is gemini.",
    )

    class Meta:
        verbose_name = "App settings"
        verbose_name_plural = "App settings"

    def __str__(self):
        return "App settings"


def get_effective_vision_config():
    """Return (backend, openai_model, gemini_model) from DB overrides or Django settings."""
    from django.conf import settings as django_settings

    try:
        app = AppSettings.objects.filter(pk=APP_SETTINGS_ID).first()
    except Exception:
        app = None

    if app and app.vision_backend.strip():
        backend = app.vision_backend.strip().lower()
        openai_model = (app.openai_model or "").strip() or getattr(
            django_settings, "OPENAI_VISION_MODEL", "gpt-4o-mini"
        )
        gemini_model = (app.gemini_model or "").strip() or getattr(
            django_settings, "GEMINI_VISION_MODEL", "gemini-2.0-flash"
        )
        return (backend, openai_model, gemini_model)

    backend = getattr(django_settings, "VISION_BACKEND", "openai").lower()
    openai_model = getattr(django_settings, "OPENAI_VISION_MODEL", "gpt-4o-mini")
    gemini_model = getattr(django_settings, "GEMINI_VISION_MODEL", "gemini-2.0-flash")
    return (backend, openai_model, gemini_model)


class ConversionTask(models.Model):
    """Represents a single PDF-to-Markdown conversion job."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        SUCCESS = "success", "Success"
        PARTIAL_SUCCESS = "partial_success", "Partially OK"
        FAILED = "failed", "Failed"

    # ── Input ─────────────────────────────────────────────────
    original_filename = models.CharField(max_length=255)
    pdf_file = models.FileField(upload_to="uploads/pdfs/")
    prompt = models.TextField(
        help_text="The prompt sent to the vision model for each page."
    )
    start_page = models.PositiveIntegerField(
        default=1,
        help_text="First page to process (1-based).",
    )
    end_page = models.PositiveIntegerField(
        default=0,
        help_text="Last page to process (0 = last page of the document).",
    )

    # ── Output ────────────────────────────────────────────────
    markdown_file = models.FileField(
        upload_to="outputs/",
        blank=True,
        null=True,
    )

    # ── Progress / Status ─────────────────────────────────────
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    page_count = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Total number of pages in the PDF.",
    )
    pages_processed = models.PositiveIntegerField(
        default=0,
        help_text="Number of pages transcribed so far.",
    )
    error_message = models.TextField(blank=True, default="")
    failed_pages = models.JSONField(
        default=list,
        blank=True,
        help_text="List of {page: int, error: str} for pages that failed transcription.",
    )
    page_results = models.JSONField(
        default=list,
        blank=True,
        help_text="Per-page Markdown strings (one per page, same order). Used to retry only failed pages.",
    )

    # ── Metadata ──────────────────────────────────────────────
    vision_backend = models.CharField(max_length=20, blank=True, default="")
    vision_model = models.CharField(max_length=100, blank=True, default="")
    processing_time_seconds = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.original_filename} ({self.status})"

    @property
    def markdown_filename(self) -> str:
        """Safe .md filename derived from original PDF name (max 200 chars before extension)."""
        return self.original_filename.rsplit(".", 1)[0][:200] + ".md"

    @property
    def effective_status(self) -> str:
        """Status for display: treat 'success' with all pages failed as 'failed', etc."""
        if self.status != self.Status.SUCCESS:
            return self.status
        failed = getattr(self, "failed_pages", None) or []
        total = self.page_count or 0
        if total and len(failed) >= total:
            return self.Status.FAILED
        if failed:
            return self.Status.PARTIAL_SUCCESS
        return self.Status.SUCCESS

    @property
    def effective_error_message(self) -> str:
        """Error message for display; use default when effective status is failed and all pages failed."""
        if self.effective_status != self.Status.FAILED:
            return self.error_message or ""
        if self.error_message:
            return self.error_message
        failed = getattr(self, "failed_pages", None) or []
        total = self.page_count or 0
        if total and len(failed) >= total:
            return "All pages failed transcription."
        return ""
