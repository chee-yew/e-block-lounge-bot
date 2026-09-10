---
name: e-block-quality-check
description: Verify a change in the E Block Lounge Bot through focused tests, formatting, linting, type checking, and acceptance-criteria review.
---

# E Block quality check

Use this skill after implementing or modifying code in this project.

1. Read `AGENTS.md` and the relevant issue or acceptance criteria.
2. Inspect the diff and identify unrelated changes.
3. Run the repository's configured formatter, linter, type checker, and tests.
4. Add or improve tests for changed behavior, especially failure paths.
5. Check that secrets, personal data, and generated files are not committed.
6. Report exact commands run, results, and any remaining risk.

Do not declare success when a check was skipped; state that it was skipped and why.
