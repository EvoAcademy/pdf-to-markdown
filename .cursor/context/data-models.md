# Data Models — PDF to Markdown

## AppSettings (singleton)

Singleton model (primary key `APP_SETTINGS_ID = 1`) storing user-selected vision backend and model overrides. Empty fields mean "use environment variable default".

| Field | Type | Purpose |
|-------|------|---------|
| `vision_backend` | CharField(20) | Override: `openai`, `gemini`, or empty |
| `openai_model` | CharField(100) | Override OpenAI model ID when backend is openai |
| `gemini_model` | CharField(100) | Override Gemini model ID when backend is gemini |

**Helper:** `get_effective_vision_config()` in `converter/models.py` returns `(backend, openai_model, gemini_model)` from DB overrides or Django settings.

---

## ConversionTask

Tracks one PDF-to-Markdown conversion job.

| Field | Type | Purpose |
|-------|------|---------|
| `original_filename` | CharField(255) | Display name of uploaded PDF |
| `pdf_file` | FileField(upload_to=`uploads/pdfs/`) | Stored PDF in MEDIA_ROOT |
| `prompt` | TextField | Transcription prompt for this task |
| `start_page` | PositiveIntegerField (default 1) | First page to process (1-based) |
| `end_page` | PositiveIntegerField (default 0) | Last page (0 = last page of document) |
| `markdown_file` | FileField(upload_to=`outputs/`, null/blank) | Output .md path when done |
| `status` | CharField(choices) | `pending` / `processing` / `success` / `partial_success` / `failed` |
| `page_count` | PositiveIntegerField (null) | Total pages in PDF (or in selected range) |
| `pages_processed` | PositiveIntegerField | Pages transcribed so far (progress) |
| `error_message` | TextField | Error details when `failed` |
| `failed_pages` | JSONField (default list) | List of `{page: int, error: str}` for failed transcriptions |
| `page_results` | JSONField (default list) | Per-page Markdown strings (same order as pages); used for retry |
| `vision_backend` | CharField | `openai` or `gemini` |
| `vision_model` | CharField | Model ID (e.g. `gpt-4o-mini`) |
| `processing_time_seconds` | FloatField (null) | Wall-clock time |
| `created_at` | DateTimeField (auto_now_add) | Task creation |
| `updated_at` | DateTimeField (auto_now) | Last update |

**Meta:** `ordering = ["-created_at"]`

**Properties:**

- `effective_status` — For display: `success` / `partial_success` / `failed` (treats success-with-all-pages-failed as `failed`).
- `effective_error_message` — Error message for display; uses "All pages failed transcription." when appropriate.

No other apps or models. No users/roles; no DRF serializers.
