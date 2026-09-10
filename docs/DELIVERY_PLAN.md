# Block-by-block delivery plan

Each block should normally become one or more small commits and one focused pull request. The owner should understand and approve the result of a block before the next one begins.

## Block 0 — Constitution and repository setup

Outcome: project context, contribution rules, initial toolchain, and CI skeleton.

Suggested commits:

- `docs: Define project brief and engineering rules`
- `build: Add Python project structure and dependency management`
- `ci: Add formatting linting type checking and test workflow`

## Block 1 — Bot skeleton

Outcome: bot starts locally, responds to `/start`, loads configuration safely, and shuts down cleanly.

Suggested commits:

- `feat: add application configuration`
- `feat: add aiogram application bootstrap`
- `feat: add start command`

## Block 2 — Persistence foundation

Outcome: database connection, migrations, users, and health checks.

Suggested commits:

- `feat: add database session management`
- `feat: add user model and migration`
- `test: cover persistence setup`

## Block 3 — Availability

Outcome: residents can see fixed lounge slots for a chosen date.

Suggested commits:

- `feat: define lounge slot policy`
- `feat: add availability query`
- `feat: add availability conversation flow`

## Block 4 — Booking and conflict prevention

Outcome: users can book an available slot, and competing requests cannot create duplicates.

Suggested commits:

- `feat: add booking domain rules`
- `feat: persist confirmed bookings`
- `test: cover duplicate and concurrent booking cases`

## Block 5 — User self-service

Outcome: users can view and cancel their future bookings.

## Block 6 — Admin operations and auditability

Outcome: admins can inspect, cancel, and block bookings safely.

## Block 7 — Production deployment

Outcome: secrets, PostgreSQL, webhook, health check, logs, and deployment documentation are ready.

## Block 8 — Events calendar

Outcome: separate event model and `/calendar` experience, without destabilising booking behavior.

## Standard block loop

1. Write or refine the issue and acceptance criteria.
2. Create a branch from `main`.
3. Implement one narrow slice.
4. Add tests and documentation.
5. Run all quality checks.
6. Open a pull request.
7. Review the diff and verification evidence.
8. Merge only after owner approval.
