import asyncio
import os
import signal
from telegram.ext import Application
from bot.handlers import setup_handlers
from bot.state import is_shutting_down  # now imported from a neutral module

def setup_signal_handlers(application: Application):
    from bot.state import is_shutting_down

    def shutdown():
        import bot.state
        bot.state.is_shutting_down = True
        asyncio.create_task(application.stop())

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown)

async def main():
    token = os.getenv("BOT_TOKEN")
    application = Application.builder().token(token).build()
    setup_handlers(application)
    setup_signal_handlers(application)
    await application.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped gracefully.")
