# Document Latest Changes

This command analyzes **uncommitted changes only** and creates or updates documentation.

## Instructions

1. **Review pending changes** (uncommitted only):
   - Use `git status` and `git diff` (and `git diff --staged` if needed)
   - Identify what was modified, added, or removed

2. **Analyze the changes**:
   - Categorize by type (features, fixes, refactors, etc.)
   - Note affected areas (converter app, config, docs, templates, services)
   - Note breaking changes or significant behavior changes
   - Identify new or removed functionality

3. **Create documentation**:
   - Update or create `CHANGELOG.md` with a structured entry
   - Or create a dated file (e.g. `CHANGES_YYYY-MM-DD.md`) if preferred
   - Include: summary, list of changes by category, new features, bug fixes, breaking changes, migration notes if any
   - Use markdown with clear sections

4. **Check for duplicates and obsolete content**:
   - Scan `CHANGELOG.md`, `README.md`, `docs/` for overlapping or repeated content
   - Prefer a single source of truth; consolidate or cross-link; remove outdated sections

5. **Update Cursor context when data or API changes**:
   - If models, fields, or routes change: update `.cursor/context/data-models.md` and `.cursor/context/api-spec.md` so they stay in sync with the codebase.

6. **Update TODO.md** (if present):
   - Keep pending items at the top; completed items in a "SOLVED / COMPLETED" section at the end
   - Mark completed items with `[x]` and ✅ **COMPLETED**
   - Add new TODO items if new work was identified

7. **Report**:
   - Tell the user what was documented and where it was saved
   - Mention any important or breaking changes

## Documentation Structure

```markdown
# Changelog / Latest Changes

## [Date] - Summary

### Added
- New features or functionality

### Changed
- Modifications to existing behavior

### Fixed
- Bug fixes

### Removed
- Removed or deprecated features

### Breaking Changes
- Changes that require attention or migration
```

## Areas to Document

- **converter app**: views, forms, models, services, templates
- **config**: settings, URLs
- **docs**: architecture, configuration, api
- **Dependencies**: requirements.txt changes

## Notes

- Be thorough but concise
- Use plain language; include file/function names when helpful
- No deployment or frontend-version steps (project is local-first, Django templates only)
