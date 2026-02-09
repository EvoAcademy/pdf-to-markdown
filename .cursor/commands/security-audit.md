# Security Audit

This command performs a security-oriented review of recent project activity, focused on file handling, configuration, and input validation. Deployment and production hardening are out of scope (local-first tool).

## Instructions

1. **Identify recent activity**:
   - Review recently modified files (e.g. last 7 days or from context)
   - Focus on views, forms, services, and configuration

2. **File upload and handling**:
   - Validate PDF upload: extension, size limits, path traversal (upload_to)
   - Ensure output paths (Markdown) are under MEDIA_ROOT and not user-controllable
   - Check that download views serve only intended files and do not expose arbitrary paths

3. **Data validation**:
   - Form validation: file type, size, page range (start_page, end_page)
   - No raw SQL; use Django ORM. If raw queries exist, ensure parameters are safe
   - Validate primary keys in URL routes (e.g. task pk) and return 404 for invalid/missing

4. **Secrets and configuration**:
   - No hardcoded API keys or secrets; use environment variables
   - `.env` in `.gitignore`; `.env.example` has no real keys
   - Check that error messages and logs do not expose keys or sensitive paths

5. **Views and access**:
   - No authentication in this project; assume single-user local use
   - Confirm CSRF protection is enabled for POST forms
   - Status API and download endpoints: ensure they only return/serve data for existing ConversionTask records (no IDOR via predictable IDs if ever exposed)

6. **Generate report**:
   - List findings by category
   - Prioritize by severity (critical, high, medium, low)
   - Give specific recommendations and, where possible, suggested fixes

## Checklist (Django, local context)

- [ ] File upload validated (type, size, safe storage path)
- [ ] Download views restrict to task’s own files
- [ ] API keys and secrets only in environment
- [ ] .env in .gitignore
- [ ] CSRF enabled for forms
- [ ] No sensitive data in error responses or logs
- [ ] URL parameters (pk) validated; 404 for invalid/missing tasks

## Notes

- No JWT, DRF, or Next.js in this project; omit those from the checklist
- Rate limiting and CORS are not required for local use but can be noted if introduced later
