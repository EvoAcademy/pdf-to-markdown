# Changelog

## [Unreleased] – 2025-02-06

### Added

- **App settings (UI)** — New Settings page to override vision backend and model per app (stored in DB). Choose OpenAI or Gemini and preset/custom model IDs; empty = use environment defaults. Nav link in base template; route `converter:settings`, view `settings_view`.
- **AppSettings model** — Singleton (`id=1`) with `vision_backend`, `openai_model`, `gemini_model`. Helper `get_effective_vision_config()` in `converter/models.py` returns `(backend, openai_model, gemini_model)` from DB or Django settings.
- **Page range on upload** — Upload form uses **Start page** and **End page** (1-based) instead of a single “max pages”. End page `0` = last page. Client-side PDF page count via pdf.js on the index page to show range and defaults.
- **Partial success and per-page failure tracking** — New status `partial_success` when some pages fail transcription. `ConversionTask` has `failed_pages` (list of `{page, error}`) and `page_results` (per-page Markdown strings). Result page shows which pages failed and allows retrying only those pages.
- **Retry failed pages** — Route `GET /retry/<pk>/` (`retry_task`). If task has `page_results` and `failed_pages`, re-runs only failed pages and merges into existing result; otherwise creates a new task and runs full conversion. Result page shows “Retry conversion” in each failed-page error box.
- **History search** — `GET /history/?q=...` filters tasks by filename (case-insensitive).
- **History bulk delete** — Checkboxes per row, “Select all”, and “Delete selected” button; POST to `converter:history_bulk_delete` with `ids[]` and optional `q` to preserve search.
- **Download original PDF** — Route `GET /download-pdf/<pk>/` (`download_pdf`) to download the uploaded PDF. Linked from result page and history (PDF column).
- **Settings form** — `SettingsForm` in `converter/forms.py` (vision_backend, openai/gemini model choices and custom ID fields); validation for “Custom” when model is custom.

### Changed

- **Upload form** — Replaced `max_pages` with `start_page` (default 1) and `end_page` (default 0). Form `clean()` validates `end_page >= start_page`. Shared `INPUT_CLASS` and `NUMBER_CLASS` for styling.
- **ConversionTask model** — `max_pages` removed; `start_page` (default 1) and `end_page` (default 0) added. New fields: `failed_pages` (JSONField), `page_results` (JSONField). New `Status.PARTIAL_SUCCESS`. Properties: `effective_status` (success/partial_success/failed for display) and `effective_error_message` (includes “All pages failed” when applicable).
- **PDF → images** — `pdf_to_base64_images()` now takes `start_page` and `end_page` (1-based); `0` for end = last page. Returns images only for that range.
- **Processing pipeline** — Uses `get_effective_vision_config()` instead of reading Django settings directly. Supports `retry_failed_only`: when True and task has `page_results`/`failed_pages`, only failed pages are re-transcribed and results merged. Saves `failed_pages` and `page_results`; sets status to `PARTIAL_SUCCESS` when some pages fail, `FAILED` when all fail.
- **Vision service** — `transcribe_images_to_markdown()` now takes optional `failed_pages` (mutable list to append `{page, error}`) and `indices_to_process` (subset of indices for retries). Returns `(full_markdown, page_results)`. Uses `get_effective_vision_config()`. Gemini backend switched to `google-genai` client API (PIL Image input).
- **Result page** — Status badge uses `effective_status` (Success / Partially OK / Failed). Failed-page placeholders in Markdown are replaced with error boxes (title, error text, “Retry conversion” link). Download PDF button added. Download .md allowed for success and partial_success.
- **History and processing** — History uses `effective_status` for badges and links; “PDF” link on each row. Processing page handles `partial_success` in polling (shows “Done (some pages failed). Redirecting...”).
- **Config** — `SECRET_KEY` in `config/settings.py` simplified to one-line fallback.
- **Dependencies** — `google-generativeai` replaced with `google-genai>=1.0,<2.0` for Gemini.

### Fixed

- Result and history now distinguish “Partially OK” (some pages failed) from “Success” and “Failed”, and allow viewing/downloading partial Markdown and retrying only failed pages.

### Removed

- **ConversionTask.max_pages** — Replaced by `start_page` and `end_page` (migrations 0002–0005).
- **Upload form field `max_pages`** — Replaced by `start_page` and `end_page`.

### Breaking changes

- **Upload API** — POST `/` form fields are now `start_page` and `end_page` instead of `max_pages`. Clients must send page range (or rely on defaults: 1 and 0).
- **Gemini dependency** — Package is now `google-genai`; `google-generativeai` is no longer used. Code uses `genai.Client` and `client.models.generate_content(model=..., contents=[prompt, pil_image])`.
- **Status API** — Polling response `status` can now be `partial_success` in addition to `pending` / `processing` / `success` / `failed`.

### Migration notes

- Run `python manage.py migrate` to apply migrations 0002–0005 (ConversionTask schema changes and AppSettings).
- If you relied on `max_pages` in scripts or API, switch to `start_page` and `end_page` (1-based; 0 for “last page” on end).
- Replace `google-generativeai` with `google-genai` in the environment; Gemini API usage is unchanged at the product level.
