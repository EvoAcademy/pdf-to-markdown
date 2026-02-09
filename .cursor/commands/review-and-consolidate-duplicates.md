# Review and Consolidate Duplicates

This command reviews recent project activity to find duplicate code, redundant logic, or similar files, and suggests or performs consolidations where appropriate.

## Instructions

1. **Identify recent activity**:
   - Use `git log --name-status --since="7 days ago"` or inspect recently modified files
   - Consider files in the current working tree or mentioned in context

2. **Search for duplicates and redundancies**:
   - Similar logic in views, forms, or services
   - Duplicate validation or formatting code
   - Repeated patterns in templates (consider template tags or includes)
   - Overlapping helpers or utilities

3. **Analyze consolidation opportunities**:
   - Logic that can move into `converter/services/` or shared helpers
   - Template snippets that can be `{% include %}` or base blocks
   - Repeated form validation that can be centralized

4. **Propose and execute consolidations**:
   - Extract shared functions or service helpers
   - Refactor duplicate code to use them
   - Remove redundant files after consolidating
   - Update imports and references

5. **Report**:
   - List duplicates found
   - Describe consolidations performed
   - List modified or deleted files

## Areas to Review

- **converter/**: views, forms, services (pdf_to_images, vision, processing), templates
- **config/**: settings or URL patterns if duplicated
- **Templates**: repeated HTML or Tailwind patterns

## Notes

- Be conservative: do not consolidate when separation is intentional
- Preserve behavior: ensure refactors do not change functionality
- This project has no separate frontend app or DRF; focus on Django app and templates.
