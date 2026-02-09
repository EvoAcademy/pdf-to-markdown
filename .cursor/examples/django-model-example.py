"""
Example Django model following this project's conventions.
See converter/models.py (ConversionTask) for the real model.
"""
from django.db import models


class ExampleTask(models.Model):
    """
    Example showing conventions used in this project:
    - Default AutoField PK (no UUID)
    - TextChoices for status
    - FileField with upload_to
    - Meta.ordering
    """
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    name = models.CharField(max_length=255)
    input_file = models.FileField(upload_to="uploads/example/")
    output_file = models.FileField(upload_to="outputs/", blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.status})"
