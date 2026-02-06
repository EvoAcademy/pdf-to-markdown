# API & URL Reference

All routes are defined in `converter/urls.py` under the `converter` namespace.

## Routes

| Method | URL | View | Name | Description |
|---|---|---|---|---|
| GET | `/` | `index` | `converter:index` | Display the upload form |
| POST | `/` | `index` | `converter:index` | Submit a PDF for conversion |
| GET | `/processing/<pk>/` | `processing` | `converter:processing` | Processing page with progress bar |
| GET | `/api/status/<pk>/` | `task_status` | `converter:task_status` | JSON status endpoint (for polling) |
| GET | `/result/<pk>/` | `result` | `converter:result` | Result page with Markdown preview |
| GET | `/download/<pk>/` | `download` | `converter:download` | Download the `.md` file |
| GET | `/history/` | `history` | `converter:history` | List all conversion tasks |
| — | `/admin/` | Django admin | — | Admin interface for ConversionTask |

## Upload (POST `/`)

Submit a multipart form with these fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `pdf_file` | File | Yes | The PDF file to convert. Must have a `.pdf` extension and be within the configured size limit. |
| `prompt` | Text | Yes | The transcription prompt sent to the vision model for each page. Pre-filled with the default prompt. |
| `max_pages` | Integer | No | Maximum number of pages to process. `0` or empty means all pages. |

On success, the server creates a `ConversionTask`, starts background processing, and redirects to `/processing/<pk>/`.

On validation error, the form is re-rendered with error messages.

## Status API (GET `/api/status/<pk>/`)

Returns the current state of a task as JSON. This endpoint is polled by the processing page every 2 seconds.

**Response:**

```json
{
  "status": "processing",
  "page_count": 14,
  "pages_processed": 5,
  "error_message": ""
}
```

**Fields:**

| Field | Type | Description |
|---|---|---|
| `status` | string | One of: `pending`, `processing`, `success`, `failed` |
| `page_count` | integer or null | Total pages in the PDF (null if not yet determined) |
| `pages_processed` | integer | Number of pages transcribed so far |
| `error_message` | string | Error details when `status` is `failed`; empty otherwise |

**Status transitions:**

```
pending → processing → success
                     → failed
```

## Result Page (GET `/result/<pk>/`)

Displays the conversion result. The page includes:

- **Status badge** — success (green) or failed (red)
- **Metadata** — page count, processing time, backend/model used
- **Preview tab** — Markdown rendered as HTML (with tables, fenced code, and TOC support)
- **Raw tab** — the raw Markdown text with a copy-to-clipboard button
- **Download button** — links to `/download/<pk>/`

If the task failed, the error message is displayed instead of the preview.

## Download (GET `/download/<pk>/`)

Serves the Markdown file as a download with:

- `Content-Type: text/markdown; charset=utf-8`
- `Content-Disposition: attachment; filename="<original-name>.md"`

Returns 404 if the task is not in `success` status or the file is missing.

## History Page (GET `/history/`)

Lists all `ConversionTask` records ordered by creation date (newest first). Each row shows:

- Original filename
- Status badge (color-coded)
- Pages processed / total
- Processing time
- Vision backend
- Date created
- Action links (View, Download, Progress, or Details depending on status)

## Admin

The `ConversionTask` model is registered in Django admin at `/admin/`. The admin view provides:

- List display with key fields
- Filters by status, backend, and date
- Search by filename
- Read-only fields for computed/system values
