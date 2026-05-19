"""
Entry point.
Starts Flask (in a background thread) and the Telegram bot (blocking).
"""
import asyncio
import threading
import logging

from telegram.ext import ApplicationBuilder

from config import BOT_TOKEN, FLASK_HOST, FLASK_PORT
from db.models import init_db
from app.routes import flask_app, set_bot
import bot.handlers.domains  as h_domains
import bot.handlers.urls     as h_urls
import bot.handlers.filters  as h_filters
import bot.handlers.generate as h_generate
import bot.handlers.notify   as h_notify
import bot.handlers.devices  as h_devices

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def run_flask():
    logger.info("Flask listening on %s:%s", FLASK_HOST, FLASK_PORT)
    flask_app.run(host=FLASK_HOST, port=FLASK_PORT, use_reloader=False)


def main():
    # 1. Init database
    init_db()
    logger.info("Database initialised.")

    # 2. post_init runs inside the bot's event loop right before polling starts
    #    — the only safe moment to capture the running loop
    async def post_init(app):
        loop = asyncio.get_running_loop()
        set_bot(app.bot, loop)
        logger.info("Bot loop wired to Flask notification route.")

    # 3. Build Telegram app with post_init hook
    tg_app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # 4. Register all command handlers
    h_domains.register(tg_app)
    h_urls.register(tg_app)
    h_filters.register(tg_app)
    h_generate.register(tg_app)
    h_notify.register(tg_app)
    h_devices.register(tg_app)

    # 5. Start Flask in a daemon thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # 6. Start Telegram polling (blocks; post_init fires before first poll)
    logger.info("Bot polling started.")
    tg_app.run_polling()


if __name__ == "__main__":
    main()
