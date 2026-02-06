from django.contrib import admin

from .models import ConversionTask


@admin.register(ConversionTask)
class ConversionTaskAdmin(admin.ModelAdmin):
    list_display = (
        "original_filename",
        "status",
        "page_count",
        "pages_processed",
        "vision_backend",
        "vision_model",
        "processing_time_seconds",
        "created_at",
    )
    list_filter = ("status", "vision_backend", "created_at")
    search_fields = ("original_filename",)
    readonly_fields = (
        "status",
        "page_count",
        "pages_processed",
        "processing_time_seconds",
        "error_message",
        "vision_backend",
        "vision_model",
        "created_at",
        "updated_at",
    )
