from telegram import (
    Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
)
from telegram.ext import (
    CommandHandler, MessageHandler, filters, CallbackQueryHandler,
    ContextTypes, ConversationHandler
)
from bot.matchmaking import (
    start_chat, stop_chat, forward_message,
    inline_callback_handler, handle_search_command, handle_join_command
)
from bot.utils import is_registered, register_user, update_username, get_user_data

GENDER, NAME, EDIT = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    button = InlineKeyboardMarkup([
        [InlineKeyboardButton("Start Chatting", callback_data="start_chat")]
    ])
    await update.message.reply_photo(
        photo="https://graph.org/file/2e37a57d083183ea24761-9cc38246fecc1af393.jpg",
        caption="**Welcome to TeleMingle**\nChat with strangers anonymously. Tap below to begin.",
        reply_markup=button,
        parse_mode="Markdown"
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("Use /chat to start chatting!")

async def chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_registered(user_id):
        await start_chat(user_id, update, context)
        return ConversationHandler.END

    markup = ReplyKeyboardMarkup([["Male", "Female"]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Select your gender:", reply_markup=markup)
    return GENDER

async def gender_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["gender"] = update.message.text
    await update.message.reply_text("Enter your name:", reply_markup=ReplyKeyboardRemove())
    return NAME

async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    gender = context.user_data["gender"]
    name = update.message.text
    register_user(user_id, gender, name)

    await update.message.reply_text(f"Registered successfully! Searching for partner...", parse_mode="Markdown")
    await start_chat(user_id, update, context)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

async def edit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup([["Generate Username"]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Tap below to generate a new username.", reply_markup=keyboard)
    return EDIT

async def handle_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "Generate Username":
        username = update_username(update.effective_user.id)
        await update.message.reply_text(f"Your new username: @{username}\nYou can now chat.", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    else:
        await update.message.reply_text("Please tap the button to proceed.")
        return EDIT

def register_handlers(app):
    reg_conv = ConversationHandler(
        entry_points=[CommandHandler("chat", chat_command)],
        states={
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, gender_handler)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    edit_conv = ConversationHandler(
        entry_points=[CommandHandler("edit", edit_command)],
        states={
            EDIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("end", stop_chat))
    app.add_handler(CommandHandler("search", handle_search_command))
    app.add_handler(CommandHandler("join", handle_join_command))
    app.add_handler(reg_conv)
    app.add_handler(edit_conv)
    app.add_handler(CallbackQueryHandler(button_callback, pattern="^start_chat$"))
    app.add_handler(CallbackQueryHandler(inline_callback_handler, pattern="^end_chat$"))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, forward_message))
