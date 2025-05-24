from telegram.ext import ApplicationBuilder
from bot.handlers import register_handlers
from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

app = ApplicationBuilder().token(BOT_TOKEN).build()
register_handlers(app)

app.run_polling()
