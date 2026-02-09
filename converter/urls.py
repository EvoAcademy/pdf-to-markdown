from django.urls import path

from . import views

app_name = "converter"

urlpatterns = [
    path("", views.index, name="index"),
    path("processing/<int:pk>/", views.processing, name="processing"),
    path("api/status/<int:pk>/", views.task_status, name="task_status"),
    path("result/<int:pk>/", views.result, name="result"),
    path("retry/<int:pk>/", views.retry_task, name="retry_task"),
    path("download/<int:pk>/", views.download, name="download"),
    path("download-pdf/<int:pk>/", views.download_pdf, name="download_pdf"),
    path("history/", views.history, name="history"),
    path("history/bulk-delete/", views.history_bulk_delete, name="history_bulk_delete"),
    path("settings/", views.settings_view, name="settings"),
]
