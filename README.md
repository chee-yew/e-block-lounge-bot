# E Block Lounge Bot

Telegram bot for clear, conflict-free booking of the E Block lounge.

The project is being built block by block. Read the [project brief](docs/PROJECT_BRIEF.md),
[delivery plan](docs/DELIVERY_PLAN.md), [AI workflow](docs/AI_WORKFLOW.md), and
[contribution guidance](AGENTS.md) before making changes.

## Local setup

1. Install Python 3.12 or newer.
2. Create and activate a virtual environment.
3. Install the package with development dependencies:

   ```text
   python -m pip install -e ".[dev]"
   ```

4. Copy `.env.example` to `.env` when application configuration is introduced.
5. Run the quality checks described below.

## Run the bot locally

After Block 1 is complete, set `TELEGRAM_BOT_TOKEN` in `.env` and run:

```text
python -m e_block_bot.main
```

The bot currently responds to `/start`. Never commit `.env` or a real Telegram token.

## Quality checks

```text
ruff format --check .
ruff check .
mypy src
pytest
```

The bot is not yet implemented. Booking behavior begins only after Block 0 is reviewed.
