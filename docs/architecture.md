# Architecture

## Overview

PDF to Markdown is a Django application with a single app (`converter`) that handles the full pipeline: PDF upload, page-to-image conversion, vision API transcription, and Markdown output. It uses SQLite for task tracking and the local filesystem (`MEDIA_ROOT`) for file storage.

## Data Flow

```
Browser                          Django Server
───────                          ─────────────
1. Upload PDF + prompt ──POST──► index view
                                  ├─ Validate form
                                  ├─ Save PDF to MEDIA_ROOT/uploads/pdfs/
                                  ├─ Create ConversionTask (status=pending)
                                  └─ Spawn background thread
                                       │
2. Redirect to /processing/<pk>/ ◄─────┘
   JS polls /api/status/<pk>/
   every 2 seconds                Background Thread
                                  ──────────────────
                                  ├─ Set status=processing
                                  ├─ PDF → base64 images (PyMuPDF, in-memory)
                                  ├─ Update page_count in DB
                                  ├─ For each page (concurrent ThreadPoolExecutor):
                                  │   ├─ Send image + prompt to vision API
                                  │   ├─ On success: store result
                                  │   ├─ On failure: insert placeholder comment
                                  │   └─ Increment pages_processed in DB
                                  ├─ Join all page results into single Markdown
                                  ├─ Save .md to MEDIA_ROOT/outputs/
                                  └─ Set status=success (or failed)
                                       │
3. Polling detects success ◄────────────┘
   Redirect to /result/<pk>/
   ├─ Rendered Markdown preview
   ├─ Raw Markdown tab
   └─ Download .md button
```

## Key Design Decisions

### Background Processing via Threads

Vision API calls are slow (5-15 seconds per page). Processing a multi-page PDF synchronously within an HTTP request would cause browser timeouts. Instead:

- The upload view creates the task and immediately spawns a **daemon thread** that runs the pipeline.
- The browser is redirected to a **processing page** that polls a lightweight JSON endpoint (`/api/status/<pk>/`) every 2 seconds.
- When the status becomes `success` or `failed`, the browser redirects to the result page.

This approach requires no external infrastructure (no Celery, no Redis). The tradeoff is that background threads are lost if the Django process restarts mid-task. For a single-user development tool, this is an acceptable tradeoff.

### Concurrent Vision API Calls

Pages are transcribed in parallel using `concurrent.futures.ThreadPoolExecutor`. The number of workers is controlled by the `VISION_MAX_WORKERS` setting (default: 4). This significantly reduces total processing time for multi-page PDFs.

Page order is preserved by pre-allocating a results list indexed by page number, regardless of which page finishes first.

### In-Memory PDF-to-Image Conversion

PyMuPDF's `pixmap.tobytes("png")` produces PNG bytes directly in memory. There is no need to write temporary files to disk, invoke PIL, or do base64 round-trips through the filesystem. This is faster and avoids temp-file cleanup issues.

### Partial Failure Handling

If a single page fails to transcribe (API error, timeout, etc.), the pipeline does not abort. Instead:

- The failed page gets a placeholder: `<!-- [Page X: transcription failed] -->`
- All other pages are still included in the output
- The task status is set to `success` (partial) as long as at least one page succeeded
- The task only gets `failed` status if the entire pipeline throws an unrecoverable exception

### Editable Prompt

The transcription prompt is stored per-task in the database, not hardcoded. Users can modify the prompt in the upload form for each conversion. The default prompt is configured via the `DEFAULT_PROMPT` setting.

## Model: ConversionTask

The `ConversionTask` model tracks the full lifecycle of a conversion:

| Field | Type | Purpose |
|---|---|---|
| `original_filename` | CharField | Display name of the uploaded PDF |
| `pdf_file` | FileField | Path to the uploaded PDF in MEDIA_ROOT |
| `prompt` | TextField | The transcription prompt used for this task |
| `max_pages` | PositiveIntegerField | Page limit (0 = all) |
| `markdown_file` | FileField | Path to the output .md file |
| `status` | CharField (choices) | `pending` / `processing` / `success` / `failed` |
| `page_count` | PositiveIntegerField | Total pages detected in the PDF |
| `pages_processed` | PositiveIntegerField | Pages completed so far (for progress) |
| `error_message` | TextField | Error details if status is `failed` |
| `vision_backend` | CharField | `openai` or `gemini` |
| `vision_model` | CharField | Model ID used (e.g. `gpt-4o-mini`) |
| `processing_time_seconds` | FloatField | Wall-clock time for the conversion |
| `created_at` | DateTimeField | When the task was created |
| `updated_at` | DateTimeField | Last modification timestamp |

## Service Layer

The business logic is separated from views into three service modules:

| Module | Responsibility |
|---|---|
| `services/pdf_to_images.py` | Opens a PDF with PyMuPDF, renders pages to PNG bytes in memory, returns base64 strings |
| `services/vision.py` | Dispatches to OpenAI or Gemini based on settings, runs concurrent API calls, handles per-page errors |
| `services/processing.py` | Orchestrates the full pipeline in a background thread, updates task status and progress in the DB |
