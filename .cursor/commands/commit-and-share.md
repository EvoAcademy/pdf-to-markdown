# Commit and Share Repository URL

This command performs a commit with a descriptive message based on recent changes and returns the repository URL.

## Instructions

1. **Review recent changes**: Use `git status` and `git diff` to see modified, added, or deleted files.

2. **Generate descriptive commit message**:
   - Create a clear, concise commit message from the changes
   - Use conventional commit format when appropriate (feat:, fix:, refactor:, docs:, etc.)
   - Include a short summary of the main changes

3. **Perform the commit**:
   - Run `git add .` to stage changes
   - Run `git commit -m "descriptive message"` with the generated message

4. **Get and return repository URL**:
   - Run `git remote get-url origin`
   - Convert SSH URL to HTTPS if needed
   - Return the repository URL to the user

## Usage Example

When the user requests this command:
- Analyze recent changes
- Create an appropriate commit message
- Make the commit
- Return something like: "✅ Commit completed. Repository: https://github.com/username/pdf-to-markdown"

## Notes

- Message should be descriptive but concise
- If there are no changes, inform the user
- Pushing to remote is optional (user can push when they want; project is local-first)