# E Block Lounge Bot — Codex Project Instructions

## Objective

Build a reliable Telegram bot for E Block that replaces informal lounge-booking messages with a clear, conflict-free booking workflow. The first release must let residents view availability, create a booking, view their bookings, and cancel a booking. The design must leave room for a future E Block events calendar.

## Working style

- Guide the owner through the project block by block.
- Before coding, explain the current block, its outcome, files likely to change, and the commit-sized portion being attempted.
- Keep each change small enough to understand, test, review, and revert.
- Prefer one focused pull request per feature or coherent slice.
- Do not skip tests, linting, type checking, or documentation updates.
- Do not make production changes, publish secrets, or merge pull requests without explicit owner approval.
- Preserve unrelated user changes in the working tree.

## AI collaboration protocol

- Treat this file, the project brief, and the delivery plan as the durable project context.
- At the start of each block, state the outcome, acceptance criteria, likely files, and the next commit-sized slice.
- Use one lead agent to own the plan and final integration. Parallel agents may independently review, research, or test, but should not edit the same files at the same time.
- Ask a reviewer agent to inspect the diff against the acceptance criteria before the owner reviews it.
- Use `skills/quality-check` after implementation and `skills/pull-request-review` before proposing a pull request. Use `skills/booking-domain-review` for booking, availability, cancellation, admin, or database work.
- Do not ask an agent to implement a whole future block when the current block has not been reviewed. Keep changes small enough to understand, test, and revert.
- Record assumptions, verification commands, failed checks, and remaining risks in the final handoff or pull request description.

## Git convention

All Git work in this project must follow the [SE-EDU Git conventions](https://se-education.org/guides/conventions/git.html):

- Write commit subjects in imperative mood, capitalize the first letter, omit the final period, and keep them within 72 characters (aim for 50).
- Use a category or scope when useful, such as `feat: Add start command` or `docs: Define contribution rules`.
- For non-trivial commits, add a body separated by a blank line, wrapped at 72 characters. Explain what changed and why; the diff explains how.
- Use meaningful kebab-case branch names. This project prefixes branches with `codex/`, for example `codex/block-1-bot-skeleton`.
- Keep commits focused and reviewable. Split unrelated changes into separate commits.
- Pull requests must describe the problem, the change, verification evidence, and remaining risks.

These rules apply whenever an agent suggests, creates, reviews, or documents Git commits, branches, or pull requests in this repository.

## Product constraints

- Use private chat for booking details where practical.
- Store times explicitly in the project's configured timezone; do not rely on the server's local timezone.
- Prevent overlapping bookings at the database/service boundary, not only in the user interface.
- Keep resident data minimal and avoid logging message contents or bot tokens.
- Treat admin actions as privileged and auditable.
- Model lounge bookings and future planned events as separate domain concepts.

## Engineering defaults

- Python with aiogram 3.
- PostgreSQL for persistent data.
- SQLAlchemy and Alembic for persistence and migrations.
- pytest for tests; Ruff for formatting/linting; Pyright or mypy for type checking.
- Environment variables for secrets; commit `.env.example`, never real credentials.
- Keep Telegram handlers thin; put business rules in services and persistence behind repositories.

## Definition of done

A change is ready only when its acceptance criteria are met, tests cover the important behavior, quality checks pass, documentation is updated when needed, and the final response states what changed, what was verified, and what remains.

## Current delivery block

Block 0 — project constitution and repository setup. Do not start the booking feature until this block is reviewed by the owner.

Read `docs/PROJECT_BRIEF.md` and `docs/DELIVERY_PLAN.md` before making substantive changes.
