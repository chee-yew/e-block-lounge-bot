# E Block Lounge Bot

Telegram bot for clear, conflict-free booking of the E Block lounge.

## Features

- Fixed two-hour lounge slots in the configured timezone
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
/availability [YYYY-MM-DD]
/book YYYY-MM-DD HH:MM [optional purpose]
/mybookings
/cancel BOOKING_ID
```

Booking details are intended for private chats. Admin commands are available only to
IDs listed in `ADMIN_USER_IDS`:

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
