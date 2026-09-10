# Git conventions

This project follows the [SE-EDU Git conventions](https://se-education.org/guides/conventions/git.html).
The repository-specific rules below make those conventions concrete for this project.

## Commits

- Use imperative mood: `Add start command`, not `Added start command`.
- Capitalize the first letter and do not end the subject with a period.
- Keep the subject within 72 characters and aim for 50 or fewer.
- Use a category or scope when helpful: `feat: Add start command`.
- Add a body for non-trivial commits. Separate it with a blank line, wrap it at 72 characters, and explain what changed and why.
- Keep each commit focused on one teachable, reviewable slice.

## Branches

- Use meaningful lowercase kebab-case names.
- If the branch relates to an issue, prefix it with the issue number.
- Examples: `block-0-repository-setup`, `availability-slots`, `1234-bot-skeleton`.

## Pull requests

Each pull request should normally cover one coherent block or slice and include:

- the problem and acceptance criteria
- the design and scope of the change
- tests and quality checks run
- remaining risks or follow-up work

Do not merge or publish production changes without owner approval.
