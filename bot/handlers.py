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
from bot.matchmaking import start_chat, stop_chat, forward_message, inline_callback_handler
from bot.utils import (
    is_registered, register_user, get_user_data, generate_random_username,
    update_username, get_user_by_username, add_search_request, get_search_requests, clear_search_requests
)

GENDER, NAME, EDIT_USERNAME = range(3)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_url = "https://graph.org/file/2e37a57d083183ea24761-9cc38246fecc1af393.jpg"
    button = InlineKeyboardMarkup([[InlineKeyboardButton("Start Chatting", callback_data="start_chat")]])
    await update.message.reply_photo(photo=photo_url,
                                     caption="**Welcome to TeleMingle**\nChat with strangers anonymously. Tap below to begin.",
                                     reply_markup=button, parse_mode="Markdown")

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

# New /edit command handlers

async def edit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user_data(user_id)

    if not user:
        await update.message.reply_text("You are not registered yet. Use /chat to register first.")
        return ConversationHandler.END

    if user.get("username"):
        await update.message.reply_text(f"Your current username is: {user['username']}\nIf you want to change it, just send new username.")
        return EDIT_USERNAME

    # No username, offer button to generate one
    reply_markup = ReplyKeyboardMarkup([["Generate Username"]], one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("You don't have a username yet. Press the button to generate one.", reply_markup=reply_markup)
    return EDIT_USERNAME

async def edit_username_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if text == "Generate Username":
        username = generate_random_username()
        update_username(user_id, username)
        await update.message.reply_text(f"Username *{username}* created! You can now start chatting.", parse_mode="Markdown",
                                        reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    else:
        # Check if username is unique
        if get_user_by_username(text):
            await update.message.reply_text("This username is already taken. Try another one or press 'Generate Username'.")
            return EDIT_USERNAME

        update_username(user_id, text)
        await update.message.reply_text(f"Username *{text}* set! You can now start chatting.", parse_mode="Markdown",
                                        reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /search <username>")
        return
    username = context.args[0].lower()
    user = get_user_data(user_id)
    if not user or not user.get("username"):
        await update.message.reply_text("You need a username to use this command. Use /edit to create one.")
        return

    target = get_user_by_username(username)
    if not target:
        await update.message.reply_text("User not found.")
        return

    target_id = target["user_id"]

    if target_id == user_id:
        await update.message.reply_text("You cannot search yourself.")
        return

    add_search_request(target_id, user_id)
    await update.message.reply_text(f"Request sent to {username}. They need to accept with /join {user['username']}.")

async def join_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) == 0:
        await update.message.reply_text("Usage: /join <username>")
        return
    username = context.args[0].lower()
    user = get_user_data(user_id)
    if not user or not user.get("search_requests"):
        await update.message.reply_text("No pending requests.")
        return

    requesters = get_search_requests(user_id)
    requester = None
    for requester_id in requesters:
        r_user = get_user_data(requester_id)
        if r_user and r_user.get("username") == username:
            requester = requester_id
            break

    if not requester:
        await update.message.reply_text("No request from this username.")
        return

    # Connect users directly (bypass waiting queue)
    from bot.matchmaking import active_chats
    active_chats[user_id] = requester
    active_chats[requester] = user_id

    clear_search_requests(user_id)

    await update.message.reply_text(f"You are now connected with {username}.")
    await context.bot.send_message(chat_id=requester, text=f"{user.get('username')} accepted your chat request.")

def register_handlers(app):
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("chat", chat_command)],
        states={
            GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, gender_handler)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name_handler)],
            EDIT_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_username_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("end", end_command))
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("edit", edit_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("join", join_command))
    app.add_handler(CallbackQueryHandler(button_callback, pattern="^start_chat$"))
    app.add_handler(CallbackQueryHandler(inline_callback_handler, pattern="^end_chat$"))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
