# Backend Conventions (Django)

## App Structure

- Single app: `converter/` at project root (no `apps/` namespace).
- Layout: `models.py`, `views.py`, `forms.py`, `urls.py`, `admin.py`, `services/`, `templates/converter/`, `management/commands/`.
- Business logic lives in **services** (`converter/services/`), not in views. Views validate input, call services, and return responses.

## Models

- Use Django `models.Model`; primary key is default `AutoField` (no UUID requirement for this project).
- Use `TextChoices` for status fields (e.g. `ConversionTask.Status`).
- Ordering: set `Meta.ordering` (e.g. `["-created_at"]`).
- Use `FileField` with `upload_to` for PDF and Markdown paths; allow `blank=True, null=True` for output until processing completes.

## Views

- Function-based or class-based views; no DRF ViewSets.
- Use `@require_http_methods` or `require_GET`/`require_POST` where appropriate.
- Return `JsonResponse` for the status API; `render` or `redirect` for HTML pages.
- Pass only needed data to templates; avoid heavy logic in the view.

## Forms

- Use Django `forms.Form` or `forms.ModelForm` in `converter/forms.py`.
- Validate file type (PDF), size (from settings), and optional `max_pages` (or page range).
- Store the transcription prompt in the model so it can be edited per conversion.

## Services

- **pdf_to_images.py**: PDF → list of base64 PNG strings (in-memory with PyMuPDF).
- **vision.py**: Call OpenAI or Gemini with image + prompt; handle concurrency and per-page errors (placeholder on failure).
- **processing.py**: Orchestrate pipeline in a background thread; update `ConversionTask` status and progress; write final Markdown to `MEDIA_ROOT`.

## Configuration

- All tunables via environment variables and `config/settings.py` (e.g. `VISION_BACKEND`, `OPENAI_API_KEY`, `MAX_PDF_PAGES`, `MEDIA_ROOT`).
- Use `os.environ.get` or `django.conf.settings`; never hardcode secrets.

## Tests

- Prefer `pytest` and `pytest-django` for new tests.
- Keep tests next to the app or in `converter/tests.py` / `converter/tests/` as appropriate.

## Type Hints

- Use Python 3.x type hints on public service functions and key view logic where it helps readability.
