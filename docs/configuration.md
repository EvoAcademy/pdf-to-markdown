# Configuration

All configuration is done through environment variables. Copy `.env.example` to `.env` and edit the values.

```bash
cp .env.example .env
```

## Environment Variables

### Vision Backend

| Variable | Default | Description |
|---|---|---|
| `VISION_BACKEND` | `openai` | Which vision provider to use. Set to `openai` or `gemini`. |

### OpenAI Settings

Used when `VISION_BACKEND=openai`.

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(empty)* | Your OpenAI API key. **Required** when using the OpenAI backend. |
| `OPENAI_VISION_MODEL` | `gpt-4o-mini` | The OpenAI model ID to use for vision requests. Any model that supports image input works (e.g. `gpt-4o`, `gpt-4o-mini`). |

### Gemini Settings

Used when `VISION_BACKEND=gemini`.

| Variable | Default | Description |
|---|---|---|
| `GEMINI_API_KEY` | *(empty)* | Your Google AI API key. **Required** when using the Gemini backend. |
| `GEMINI_VISION_MODEL` | `gemini-2.0-flash` | The Gemini model ID. Any model that supports image input works (e.g. `gemini-2.0-flash`, `gemini-1.5-pro`). |

### Processing Limits

| Variable | Default | Description |
|---|---|---|
| `VISION_MAX_WORKERS` | `4` | Maximum number of concurrent vision API calls per task. Higher values process faster but increase API rate-limit risk. |
| `MAX_PDF_PAGES` | `100` | Server-side cap on pages to process. Applies even if the user sets a higher value in the form. Set to `0` for unlimited. |
| `MAX_PDF_SIZE_MB` | `50` | Maximum allowed PDF upload size in megabytes. Also configures Django's `DATA_UPLOAD_MAX_MEMORY_SIZE` and `FILE_UPLOAD_MAX_MEMORY_SIZE`. |

### Django Settings

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | *(insecure default)* | Django secret key. Set a strong random value in production. |
| `DJANGO_DEBUG` | `True` | Set to `False` in production. Controls debug mode, allowed hosts, and log verbosity. |

## Switching Backends

To switch from OpenAI to Gemini, change two variables in `.env`:

```bash
# Before (OpenAI)
VISION_BACKEND=openai
OPENAI_API_KEY=sk-...

# After (Gemini)
VISION_BACKEND=gemini
GEMINI_API_KEY=AIza...
```

No code changes are needed. The model ID can also be changed independently:

```bash
OPENAI_VISION_MODEL=gpt-4o        # upgrade to the full model
GEMINI_VISION_MODEL=gemini-1.5-pro # use a different Gemini variant
```

## Default Prompt

The default transcription prompt sent with each page image is configured in `config/settings.py` as `DEFAULT_PROMPT`:

```
Transcribe the information in this document in Markdown format.
Keep the language of the file.
Ignore the letterhead and the footer of the document.
```

Users can override this per-conversion in the upload form. To change the default globally, edit the `DEFAULT_PROMPT` value in `config/settings.py`.

## File Storage

| Path | Contents |
|---|---|
| `media/uploads/pdfs/` | Uploaded PDF files |
| `media/outputs/` | Generated Markdown files |
| `db.sqlite3` | SQLite database with task records |

These are excluded from version control via `.gitignore`. To clean up old files, use the management command:

```bash
python manage.py cleanup_old_tasks --days=30
```

## Logging

The `converter` app logs to the console. In debug mode the level is `DEBUG`; in production it is `INFO`. Log output includes timestamps, level, and logger name:

```
[2026-02-06 19:30:00,123] INFO converter.services.processing: Started background thread for task 42
[2026-02-06 19:30:01,456] INFO converter.services.pdf_to_images: Converting 14 page(s) from /path/to/file.pdf
[2026-02-06 19:30:02,789] INFO converter.services.vision: Transcribing 14 page(s) via openai / gpt-4o-mini (workers=4)
```
