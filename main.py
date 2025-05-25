import os
from telegram.ext import ApplicationBuilder
from bot.handlers import register_handlers  # No circular import

from dotenv import load_dotenv
load_dotenv()

# Telegram Bot Token from .env
TOKEN = os.getenv("BOT_TOKEN")

def main():
    # Build the app with your token
    app = ApplicationBuilder().token(TOKEN).build()

    # Register all handlers (from bot/handlers.py)
    register_handlers(app)

    # Start polling
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
