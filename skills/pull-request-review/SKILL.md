---
name: e-block-pull-request-review
description: Review an E Block Lounge Bot pull request for scope, maintainability, tests, security, migrations, and documentation.
---

# E Block pull-request review

Review the pull request against its issue and acceptance criteria. Prefer a small, teachable change over a broad refactor.

Check:

- scope is limited to one coherent slice
- architecture keeps Telegram handlers separate from domain logic
- tests exercise success and important failure cases
- migrations are present and safe when the schema changes
- configuration and secrets are handled correctly
- documentation and run instructions remain accurate
- CI evidence is present or missing checks are clearly called out

Report actionable findings first. If there are no findings, state what was checked and any residual risk.
