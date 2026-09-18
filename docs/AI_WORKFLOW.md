# AI-assisted development workflow

This project uses AI to speed up implementation while keeping design decisions and ownership with the project owner.

## Roles

- **Lead agent:** understands the current block, proposes the narrow slice, edits the code, and prepares the handoff.
- **Implementer agent:** handles an isolated coding task when parallel work is useful.
- **Reviewer agent:** checks the diff against acceptance criteria, architecture, security, and maintainability.
- **Quality agent:** runs the configured formatter, linter, type checker, tests, and secret checks.

Use parallel agents for independent work such as researching a library, reviewing an existing diff, or writing tests for a stable interface. Do not have two agents edit overlapping files without an explicit integration plan.

## Block loop

1. Refine the issue and acceptance criteria.
2. Create a branch from `main`, using a name such as `block-1-bot-skeleton` or `1234-bot-skeleton` when an issue exists.
3. Explain the next small commit before editing.
4. Implement one coherent slice with tests and documentation.
5. Run the quality checks and record their exact results.
6. Ask for a focused review of the diff.
7. Open a pull request with the acceptance criteria, design notes, verification evidence, and remaining risks.
8. Review and merge only after owner approval.

## Useful prompt shape

Give the agent the current block, the acceptance criteria, the files in scope, constraints, and the required verification. Ask it to preserve unrelated changes and stop at the block boundary. This makes the result easier to review than asking for the entire bot in one prompt.

## Pull request checklist

- The change maps to one block or a clearly bounded slice.
- Handlers remain thin and business rules remain testable outside Telegram.
- Tests cover the important success and failure paths.
- Configuration uses environment variables and no real secrets are committed.
- Documentation and migrations match the implementation.
- Formatting, linting, type checking, and tests have recorded results.
