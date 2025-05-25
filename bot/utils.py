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
import random
import string

from bot.matchmaking import (
    start_chat, stop_chat, forward_message, inline_callback_handler
)
from bot.utils import is_registered, register_user, get_user_data, update_username

# States for registration
GENDER, NAME = range(2)

# State for /edit username
EDIT_USERNAME = range(1)

def generate_random_username(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

# /start command handler
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

# /chat command handler & registration flow
async def chat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_registered(user_id):
        user_data = get_user_data(user_id)
        # If user has no bot username, create one automatically
        if not user_data.get("bot_username"):
            new_username = generate_random_username()
            update_username(user_id, new_username)
            await update.message.reply_text(
                f"Your username @{new_username} has been created! You can now start chatting."
            )
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

    # Automatically create username after registration
    new_username = generate_random_username()
    update_username(user_id, new_username)

    await update.message.reply_text(
        f"✅ Registered successfully as *{name}*!\nYour username is @{new_username}.\nStarting chat...",
        parse_mode="Markdown"
    )
    await start_chat(user_id, update, context)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Registration cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# /end command handler
async def end_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await stop_chat(user_id, update, context)

# Forward messages during chat
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await forward_message(user_id, update, context)

# Inline callback handler for "End Chat" button
# Already imported inline_callback_handler from matchmaking

# /edit command to create/regenerate username
async def edit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)

    if user_data and user_data.get("bot_username"):
        await update.message.reply_text(
            f"Your current username is @{user_data['bot_username']}.\nTo regenerate username, press the button below.",
            reply_markup=ReplyKeyboardMarkup([["Regenerate Username"]], one_time_keyboard=True, resize_keyboard=True)
        )
        return EDIT_USERNAME
    else:
        # No username yet, create one
        new_username = generate_random_username()
        update_username(user_id, new_username)
        await update.message.reply_text(
            f"Your username @{new_username} has been created! You can now start chatting with /chat.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

async def edit_username_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if text == "Regenerate Username":
        new_username = generate_random_username()
        update_username(user_id, new_username)
        await update.message.reply_text(
            f"Your new username is @{new_username}. Use /chat to start chatting.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    else:
        await update.message.reply_text("Please press the button to regenerate your username.")
        return EDIT_USERNAME

async def cancel_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Username edit cancelled.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Function to register all handlers
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

    # Username edit conversation
    edit_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("edit", edit_command)],
        states={
            EDIT_USERNAME: [MessageHandler(filters.Regex("^(Regenerate Username)$"), edit_username_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel_edit)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("end", end_command))
    app.add_handler(conv_handler)
    app.add_handler(edit_conv_handler)
    app.add_handler(CallbackQueryHandler(button_callback, pattern="^start_chat$"))  # Inline Start Chat button
    app.add_handler(CallbackQueryHandler(inline_callback_handler, pattern="^end_chat$"))  # Inline End Chat button
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
