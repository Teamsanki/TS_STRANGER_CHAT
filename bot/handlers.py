from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ContextTypes
from bot.matchmaking import start_chat, stop_chat, forward_message, waiting_users, active_chats

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to TeleMingle!\nUse /megle to connect with a stranger.")

async def megler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await start_chat(user_id, update, context)

async def uhmegle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await stop_chat(user_id, update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await forward_message(user_id, update, context)

def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("megle", megler))
    app.add_handler(CommandHandler("uhmegle", uhmegle))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
