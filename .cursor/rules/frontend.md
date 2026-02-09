# Frontend Conventions (Django Templates + Tailwind)

## Stack

- **Django templates** in `converter/templates/converter/` (no Next.js, no React).
- **Tailwind CSS** via CDN (see `base.html`). No separate Node build step.
- **JavaScript**: minimal, for progress polling and UI (e.g. Preview/Raw tabs, copy button). No TypeScript.

## Structure

- `base.html`: layout, Tailwind script, common blocks (`content`, `title`, etc.).
- Page templates: `index.html`, `processing.html`, `result.html`, `history.html`.
- Use `{% extends "converter/base.html" %}` and fill blocks. Keep templates focused on structure and simple conditionals; avoid heavy logic.

## Styling (Tailwind)

- Use utility classes; keep custom CSS minimal.
- Use status badges (e.g. success: green, failed: red, processing: amber) with consistent classes like `rounded-full text-xs font-medium`.
- Buttons: primary actions (e.g. upload, download) with clear hierarchy; use `disabled` and loading state where applicable.
- Forms: clear labels, error output via `{{ form.field.errors }}` and `{{ form.non_field_errors }}`.

## Responsiveness

- Prefer mobile-friendly layout (e.g. stack on small screens, table or grid on larger).
- Progress bar and history list should work on narrow viewports.

## Accessibility

- Use semantic HTML (`<form>`, `<label>`, `<button>`).
- Associate labels with inputs; show validation errors in an accessible way.

## No Separate Frontend App

- There is no `frontend/` directory, no `npm run build`, no `NEXT_PUBLIC_*`. All UI is served by Django. References to “frontend” in rules mean “Django templates and their Tailwind/JS” only.
