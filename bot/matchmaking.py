from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from bot.utils import get_user_data, get_user_by_username
import uuid

waiting_users = []
active_chats = {}
pending_requests = {}

def get_intro_markup():
    return InlineKeyboardMarkup([[InlineKeyboardButton("End Chat", callback_data="end_chat")]])

async def start_chat(user_id, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if user_id in active_chats:
        await update.message.reply_text("You're already in a chat. Use /end to disconnect.")
        return
    if user_id in waiting_users:
        await update.message.reply_text("You're already in the queue. Please wait...")
        return

    if waiting_users:
        partner_id = waiting_users.pop(0)
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id

        partner_info = get_user_data(partner_id)
        user_info = get_user_data(user_id)

        intro_for_user = f"You're now connected to a stranger!\nGender: *{partner_info['gender']}*\nUsername: `{partner_info['username']}`"
        intro_for_partner = f"You're now connected to a stranger!\nGender: *{user_info['gender']}*\nUsername: `{user_info['username']}`"

        markup = get_intro_markup()
        await context.bot.send_message(partner_id, intro_for_partner, parse_mode="Markdown", reply_markup=markup)
        await context.bot.send_message(user_id, intro_for_user, parse_mode="Markdown", reply_markup=markup)
    else:
        waiting_users.append(user_id)
        await update.message.reply_text("Waiting for a stranger to connect...")

async def stop_chat(user_id, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        active_chats.pop(partner_id, None)
        await context.bot.send_message(partner_id, "The stranger has ended the chat.")
        await update.message.reply_text("You have left the chat.")
    elif user_id in waiting_users:
        waiting_users.remove(user_id)
        await update.message.reply_text("You left the waiting queue.")
    else:
        await update.message.reply_text("You're not in a chat.")

async def forward_message(user_id, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if user_id not in active_chats:
        await update.message.reply_text("Use /chat to connect with someone.")
        return

    partner_id = active_chats[user_id]
    sender_info = get_user_data(user_id)
    sender_label = f"*{sender_info['username']} says:*"

    reply_markup = get_intro_markup()

    msg = update.message
    if msg.text:
        await context.bot.send_message(partner_id, f"{sender_label}\n{msg.text}", parse_mode="Markdown", reply_markup=reply_markup)
    elif msg.video_note:
        await context.bot.send_message(partner_id, sender_label, parse_mode="Markdown", reply_markup=reply_markup)
        await context.bot.send_video_note(partner_id, msg.video_note.file_id)
    elif msg.voice:
        await context.bot.send_message(partner_id, sender_label, parse_mode="Markdown", reply_markup=reply_markup)
        await context.bot.send_voice(partner_id, msg.voice.file_id)
    elif msg.sticker:
        await context.bot.send_message(partner_id, sender_label, parse_mode="Markdown", reply_markup=reply_markup)
        await context.bot.send_sticker(partner_id, msg.sticker.file_id)
    else:
        await update.message.reply_text("Unsupported message type.")

async def inline_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if query.data == "end_chat":
        await query.answer("Ending chat...")
        dummy_update = Update(update.update_id, message=query.message)
        await stop_chat(user_id, dummy_update, context)
        await query.message.delete()

# Custom matchmaking

async def search_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /search <username>")
        return
    target_username = context.args[0]
    target_user = get_user_by_username(target_username)

    if not target_user:
        await update.message.reply_text("User not found.")
        return
    if target_user["_id"] == user_id:
        await update.message.reply_text("You cannot search yourself.")
        return

    join_id = str(uuid.uuid4())[:6]
    pending_requests[join_id] = (user_id, target_user["_id"])

    await context.bot.send_message(
        chat_id=target_user["_id"],
        text=f"You have a chat request from `{get_user_data(user_id)['username']}`.\nTo accept, use `/join {join_id}`",
        parse_mode="Markdown"
    )

    await update.message.reply_text("Request sent. Waiting for them to accept...")

async def join_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /join <id>")
        return
    join_id = context.args[0]
    if join_id not in pending_requests:
        await update.message.reply_text("Invalid or expired request.")
        return

    requester_id, target_id = pending_requests.pop(join_id)
    if user_id != target_id:
        await update.message.reply_text("This request was not for you.")
        return

    active_chats[requester_id] = target_id
    active_chats[target_id] = requester_id

    req_user = get_user_data(requester_id)
    tgt_user = get_user_data(target_id)

    await context.bot.send_message(requester_id, f"You are now connected with `{tgt_user['username']}`", parse_mode="Markdown", reply_markup=get_intro_markup())
    await context.bot.send_message(target_id, f"You are now connected with `{req_user['username']}`", parse_mode="Markdown", reply_markup=get_intro_markup())
