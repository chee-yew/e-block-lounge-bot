# E Block Lounge Bot

Telegram bot for clear, conflict-free booking of the E Block lounge.

## Features

- 24-hour lounge with 30-minute start-time increments
- Resident-selected durations from 30 minutes up to 3 hours
- Maximum 3 hours of active bookings per resident per local calendar day
- Availability lookup by date
- Booking with an optional purpose
- Personal booking list and cancellation
- Administrator listing and cancellation commands
- PostgreSQL support, Alembic migrations, and a local SQLite mode
- Database-level protection against competing active bookings

## Local development

1. Install Python 3.12 or newer.
2. Create and activate a virtual environment.
3. Install the project with `python -m pip install -e ".[dev]"`.
4. Copy `.env.example` to `.env` and set `TELEGRAM_BOT_TOKEN`.
5. Run `python -m e_block_bot.main`.

The default local database is `e_block_bot.db` using SQLite. The application creates
its tables on startup for convenience. For a deployed database, run `alembic upgrade head`
before starting the bot.

## User commands

```text
/start
/availability
/book
/mybookings
/cancel BOOKING_ID
```

Booking details are intended for private chats. The availability view shows only
current bookings, including the resident's Telegram handle; unlisted times are
assumed available. Admin commands are available only to IDs listed in
`ADMIN_USER_IDS`:

```text
/admin_bookings
/admin_cancel BOOKING_ID
```

## Deployment with Docker Compose

Set `TELEGRAM_BOT_TOKEN` and `ADMIN_USER_IDS` in the deployment environment, then run:

```text
docker compose up --build -d
docker compose exec bot alembic upgrade head
```

The included Compose file runs PostgreSQL and the bot with polling. For a managed host,
use the same container, set `DATABASE_URL` to a PostgreSQL `postgresql+asyncpg://...`
URL, and run the migration command as the release step.

## Quality checks

```text
ruff format --check .
ruff check .
python -m mypy src
pytest
```

Never commit `.env`, real Telegram tokens, or resident message contents.
