from telegram import (
    Update, ReplyKeyboardMarkup, ReplyKeyboardRemove,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler
)

from bot.matchmaking import (
    start_chat, stop_chat, forward_message, inline_callback_handler
)
from bot.utils import is_registered, register_user

# States for registration
GENDER, NAME = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_url = "https://graph.org/file/2e37a57d083183ea24761-9cc38246fecc1af393.jpg"
    button = InlineKeyboardMarkup([
        [InlineKeyboardButton("Start Chatting", callback_data="start_chat")]
    ])
    await update.message.reply_photo(
        photo=photo_url,
        caption="**Welcome to TeleMingle**\nChat with strangers anonymously. Tap below to begin.",
        reply_markup=button,
        parse_mode="Markdown"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Please use /chat to start!")

async def chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_registered(user_id):
        await start_chat(user_id, update, context)
        return ConversationHandler.END

    reply_markup = ReplyKeyboardMarkup([["Male", "Female"]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Select your gender:", reply_markup=reply_markup)
    return GENDER

async def gender_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["gender"] = update.message.text
    await update.message.reply_text("Now, please enter your name:", reply_markup=ReplyKeyboardRemove())
    return NAME

async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    name = update.message.text
    gender = context.user_data["gender"]
    register_user(user_id, gender, name)
    await update.message.reply_text(f"✅ Registered successfully as *{name}*! Starting chat...", parse_mode="Markdown")
    await start_chat(user_id, update, context)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registration cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def end_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await stop_chat(user_id, update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await forward_message(user_id, update, context)

def register_handlers(app):
    # Registration conversation
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("chat", chat_command)],
        states={
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, gender_handler)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("end", end_command))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_callback, pattern="^start_chat$"))  # Inline Start Chat button
    app.add_handler(CallbackQueryHandler(inline_callback_handler, pattern="^end_chat$"))  # Inline End Chat button
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
