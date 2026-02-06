from django.db import models


class ConversionTask(models.Model):
    """Represents a single PDF-to-Markdown conversion job."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    # ── Input ─────────────────────────────────────────────────
    original_filename = models.CharField(max_length=255)
    pdf_file = models.FileField(upload_to="uploads/pdfs/")
    prompt = models.TextField(
        help_text="The prompt sent to the vision model for each page."
    )
    max_pages = models.PositiveIntegerField(
        default=0,
        help_text="Max pages to process. 0 = all pages.",
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
