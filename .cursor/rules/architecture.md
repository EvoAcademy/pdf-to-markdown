# Architectural Decisions — PDF to Markdown

## Overview

- **Single Django project** with one app (`converter`) handling the full pipeline: upload, PDF→images, vision API transcription, Markdown output.
- **Local-first**: runs on `python manage.py runserver`; no deployment or production hosting assumptions.
- **No separate frontend**: UI is Django templates with Tailwind (CDN). No Next.js, no SPA.

## Backend

- Django 5.x with SQLite (default) for task tracking.
- File storage in `MEDIA_ROOT` (uploads: PDFs; outputs: Markdown files).
- No DRF, no Celery, no Redis. Background work is done in **daemon threads** (see `converter/services/processing.py`).
- Vision backends: OpenAI and Google Gemini, switchable via `VISION_BACKEND` env var.

## Frontend

- Django templates in `converter/templates/converter/` with Tailwind CSS (CDN).
- Pages: upload form, processing (progress + polling), result (preview + raw + download), history.
- No TypeScript/React; minimal JS for polling and tab switching.

## Data Flow

1. **Upload** → POST form to index view → validate, save PDF, create `ConversionTask`, spawn background thread → redirect to `/processing/<pk>/`.
2. **Processing** → Browser polls `/api/status/<pk>/` (JSON) every 2s; progress bar updates; on success/failed → redirect to result or show error.
3. **Result** → Markdown preview, raw tab, download link. Optional: download original PDF.

## Concurrency

- **Vision API**: `ThreadPoolExecutor` in `services/vision.py`; worker count from `VISION_MAX_WORKERS`.
- **Background pipeline**: one daemon thread per task in `services/processing.py`. Threads are process-bound (no Celery); acceptable for local/single-user use.

## Security (local context)

- No authentication (single-user local tool).
- API keys in environment (`.env`); never in code.
- File upload validation: extension, size, page limits via settings and form.
- CSRF enabled for forms.

## Key Paths

- **Config**: `config/settings.py`, `config/urls.py`
- **App**: `converter/` — `models.py`, `views.py`, `forms.py`, `urls.py`, `services/`, `templates/converter/`
- **Docs**: `docs/architecture.md`, `docs/configuration.md`, `docs/api.md`
