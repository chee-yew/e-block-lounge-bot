"""Application entry point for local polling."""

import asyncio
import logging

from e_block_bot.bot import create_bot, create_dispatcher
from e_block_bot.config import get_settings
from e_block_bot.db import close_database, create_engine, create_session_factory, init_database


async def run() -> None:
    """Start polling for Telegram updates until interrupted."""

    settings = get_settings()
    engine = create_engine(settings.database_url)
    await init_database(engine)
    session_factory = create_session_factory(engine)
    bot = create_bot(settings)
    dispatcher = create_dispatcher(session_factory, settings)

    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()
        await close_database(engine)


def main() -> None:
    """Configure logging and run the application."""

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(run())


if __name__ == "__main__":
    main()
