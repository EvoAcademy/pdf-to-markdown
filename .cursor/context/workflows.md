# Key Workflows — PDF to Markdown

## Convert PDF to Markdown

1. User opens `/` (upload form), optionally edits the default transcription prompt and page range.
2. User selects a PDF and submits. POST `/` → view validates form, saves PDF to `MEDIA_ROOT/uploads/pdfs/`, creates a `ConversionTask` (status `pending`), spawns background thread, redirects to `/processing/<pk>/`.
3. Processing page loads; JavaScript polls `GET /api/status/<pk>/` every 2 seconds. Progress bar shows `pages_processed` / `page_count`.
4. Background thread: sets status `processing`, converts PDF to images (PyMuPDF), calls vision API per page (parallel via ThreadPoolExecutor), writes Markdown to `MEDIA_ROOT/outputs/`, sets status `success` or `failed`.
5. When status is `success` or `failed`, JS redirects to `/result/<pk>/` or shows error. Result page: preview (rendered Markdown), raw tab, download .md link; optional download original PDF.

## View History

1. User opens `/history/`. View lists all `ConversionTask` (newest first).
2. Each row: filename, status badge, pages, timing, backend; links to result, download, or processing depending on status.

## Cleanup Old Tasks

1. Run management command: `python manage.py cleanup_old_tasks [--days=N] [--dry-run]`.
2. Deletes tasks older than N days (default 30) and their associated files. Use `--dry-run` to preview.

No authentication, no async queue (Celery); background work is in-process threads. See `docs/architecture.md` for data flow diagram.
