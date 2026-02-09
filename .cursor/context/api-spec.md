# API & URL Reference

All routes are under the `converter` namespace (`converter/urls.py`). No authentication (local tool).

## HTML Routes

| Method | URL | View | Description |
|--------|-----|------|-------------|
| GET | `/` | `index` | Upload form |
| POST | `/` | `index` | Submit PDF + prompt + page range → create task, redirect to processing |
| GET | `/processing/<pk>/` | `processing` | Processing page with progress bar; JS polls status |
| GET | `/result/<pk>/` | `result` | Result page: Markdown preview, raw tab, download, retry failed pages |
| GET | `/retry/<pk>/` | `retry_task` | Retry failed pages only (or full conversion if no per-page data); redirect to processing |
| GET | `/history/` | `history` | List all conversion tasks (optional `?q=` search by filename) |
| POST | `/history/bulk-delete/` | `history_bulk_delete` | Delete selected tasks (body: `ids`, optional `q`) |
| GET | `/settings/` | `settings_view` | Vision backend and model overrides form |
| GET | `/download/<pk>/` | `download` | Download the `.md` file |
| GET | `/download-pdf/<pk>/` | `download_pdf` | Download the original PDF |

## JSON API (for polling)

### GET `/api/status/<pk>/`

Returns current task state. Polled every 2 seconds from the processing page.

**Response:**

```json
{
  "status": "processing",
  "page_count": 14,
  "pages_processed": 5,
  "error_message": ""
}
```

- `status`: `pending` | `processing` | `success` | `partial_success` | `failed`
- `page_count`: integer or null
- `pages_processed`: integer
- `error_message`: string (non-empty when `status` is `failed`)

## Upload (POST `/`)

Multipart form:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pdf_file` | File | Yes | PDF file; extension and size validated |
| `prompt` | Text | Yes | Transcription prompt (default from settings) |
| `start_page` | Integer | No | First page to process (1-based); default 1 |
| `end_page` | Integer | No | Last page (1-based); 0 or empty = last page of document |

On success: redirect to `/processing/<pk>/`. On error: re-render form with errors.

## Admin

- `/admin/`: Django admin for `ConversionTask` and `AppSettings` (list, filters, search).

Full details: `docs/api.md`.
