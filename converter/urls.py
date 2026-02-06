from django.urls import path

from . import views

app_name = "converter"

urlpatterns = [
    path("", views.index, name="index"),
    path("processing/<int:pk>/", views.processing, name="processing"),
    path("api/status/<int:pk>/", views.task_status, name="task_status"),
    path("result/<int:pk>/", views.result, name="result"),
    path("download/<int:pk>/", views.download, name="download"),
    path("history/", views.history, name="history"),
]
