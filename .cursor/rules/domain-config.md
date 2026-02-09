# Domain & Environment (Local)

## Scope

This project is intended to run **locally**. No production domains or deployment targets are configured here.

## Local Development

- **App URL**: http://localhost:8000
- **Admin**: http://localhost:8000/admin/
- **Run**: `python manage.py runserver` (after `migrate` and `.env` configured).

## Environment Variables

Configure via `.env` (copy from `.env.example`). Main variables:

- **Vision**: `VISION_BACKEND` (`openai` | `gemini`), `OPENAI_API_KEY`, `OPENAI_VISION_MODEL`, `GEMINI_API_KEY`, `GEMINI_VISION_MODEL`
- **Limits**: `MAX_PDF_PAGES`, `MAX_PDF_SIZE_MB`, `VISION_MAX_WORKERS`
- **Django**: `SECRET_KEY`, `DEBUG`; database and `MEDIA_ROOT` as needed (defaults use project directory).

See `docs/configuration.md` for the full list.
