# PDF to Markdown

A Django web application that converts PDF documents to Markdown using AI vision models. Upload a PDF, and the app renders each page as an image, sends it to a vision LLM (OpenAI or Google Gemini), and produces a downloadable `.md` file.

## Features

- **Drag-and-drop PDF upload** with configurable size and page range (start/end page)
- **Dual vision backends** — OpenAI and Google Gemini, switchable via environment or in-app **Settings**
- **Editable transcription prompt** per conversion
- **Background processing** with real-time progress bar (no HTTP timeouts)
- **Concurrent API calls** — pages are transcribed in parallel via `ThreadPoolExecutor`
- **Rendered Markdown preview** with Preview / Raw tab switcher
- **Conversion history** with search, bulk delete, status badges (including “Partially OK”), and download links (PDF + .md)
- **Retry failed pages** — For partial runs, retry only the pages that failed transcription
- **Cleanup management command** to purge old tasks and files

## Quick Start

```bash
# 1. Clone and enter the project
cd pdf-to-markdown

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your API key (OPENAI_API_KEY or GEMINI_API_KEY)

# 5. Run migrations
python manage.py migrate

# 6. Start the server
python manage.py runserver
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## Configuration

All settings are controlled via environment variables (`.env` file). See [docs/configuration.md](docs/configuration.md) for the full reference.

| Variable | Default | Description |
|---|---|---|
| `VISION_BACKEND` | `openai` | `openai` or `gemini` |
| `OPENAI_API_KEY` | — | Required when backend is `openai` |
| `OPENAI_VISION_MODEL` | `gpt-4o-mini` | OpenAI model ID |
| `GEMINI_API_KEY` | — | Required when backend is `gemini` |
| `GEMINI_VISION_MODEL` | `gemini-2.0-flash` | Gemini model ID |
| `VISION_MAX_WORKERS` | `4` | Concurrent API calls per task |
| `MAX_PDF_PAGES` | `100` | Max pages to process (0 = unlimited) |
| `MAX_PDF_SIZE_MB` | `50` | Max upload size in MB |

## Project Structure

```
pdf_to_markdown/
├── manage.py
├── requirements.txt
├── .env.example
├── config/                          # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── converter/                       # Main application
│   ├── models.py                    # ConversionTask model
│   ├── views.py                     # Upload, processing, result, download, history
│   ├── forms.py                     # Upload form with editable prompt
│   ├── urls.py                      # Route definitions
│   ├── admin.py                     # Admin registration
│   ├── services/
│   │   ├── pdf_to_images.py         # PyMuPDF PDF-to-base64 (in-memory)
│   │   ├── vision.py                # OpenAI / Gemini backends
│   │   └── processing.py            # Background thread orchestrator
│   ├── templates/converter/
│   │   ├── base.html                # Tailwind CDN layout
│   │   ├── index.html               # Upload form
│   │   ├── processing.html          # Progress bar + polling
│   │   ├── result.html              # Markdown preview + download
│   │   └── history.html             # Task list
│   └── management/commands/
│       └── cleanup_old_tasks.py     # Purge old tasks
└── docs/                            # Documentation
    ├── architecture.md
    ├── configuration.md
    └── api.md
```

## Documentation

- [Architecture](docs/architecture.md) — system design, data flow, and processing pipeline
- [Configuration](docs/configuration.md) — full environment variable reference
- [API & URL Reference](docs/api.md) — all routes, views, and the JSON status endpoint
- [Changelog](CHANGELOG.md) — version history and breaking changes

## Management Commands

**Cleanup old tasks:**

```bash
# Delete tasks older than 30 days (default)
python manage.py cleanup_old_tasks

# Delete tasks older than 7 days
python manage.py cleanup_old_tasks --days=7

# Preview what would be deleted
python manage.py cleanup_old_tasks --days=7 --dry-run
```

## License

This project is for personal/internal use.
