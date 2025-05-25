from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from bot.utils import (
    get_user_data, get_user_by_username, get_partner, save_active_chat,
    end_chat, pending_requests, users
)

waiting_users = []

async def start_chat(user_id, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if waiting_users and waiting_users[0] != user_id:
        partner_id = waiting_users.pop(0)
        save_active_chat(user_id, partner_id)

        user_data = get_user_data(user_id)
        partner_data = get_user_data(partner_id)

        await context.bot.send_message(partner_id, f"Stranger ({user_data['gender']}) connected. Username: @{user_data['username']}")
        await context.bot.send_message(user_id, f"Stranger ({partner_data['gender']}) connected. Username: @{partner_data['username']}")
    else:
        waiting_users.append(user_id)
        await context.bot.send_message(user_id, "Waiting for a stranger to connect...")

async def stop_chat(user_id, update: Update, context: ContextTypes.DEFAULT_TYPE):
    partner_id = get_partner(user_id)
    end_chat(user_id)

    await context.bot.send_message(user_id, "Chat ended.")
    if partner_id:
        await context.bot.send_message(partner_id, "Stranger has left the chat.")

async def forward_message(user_id, update: Update, context: ContextTypes.DEFAULT_TYPE):
    partner_id = get_partner(user_id)
    if partner_id:
        if update.message.text:
            await context.bot.send_message(partner_id, update.message.text)
        elif update.message.voice:
            await context.bot.send_voice(partner_id, update.message.voice.file_id)
        elif update.message.sticker:
            await context.bot.send_sticker(partner_id, update.message.sticker.file_id)
        elif update.message.video_note:
            await context.bot.send_video_note(partner_id, update.message.video_note.file_id)

async def inline_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    await stop_chat(user_id, update, context)

async def handle_search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /search <username>")
        return

    target = get_user_by_username(args[0])
    if not target:
        await update.message.reply_text("No user found with that username.")
        return

    pending_requests.insert_one({"from": user_id, "to": target["_id"]})
    await update.message.reply_text(f"Join request sent to @{target['username']}")

    await context.bot.send_message(
        target["_id"],
        f"You received a join request from @{get_user_data(user_id)['username']}\nUse /join {user_id} to accept."
    )

async def handle_join_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /join <id>")
        return

    try:
        requester_id = int(args[0])
    except ValueError:
        await update.message.reply_text("Invalid ID.")
        return

    if not pending_requests.find_one({"from": requester_id, "to": user_id}):
        await update.message.reply_text("No such join request found.")
        return

    pending_requests.delete_one({"from": requester_id, "to": user_id})
    save_active_chat(user_id, requester_id)

    requester_data = get_user_data(requester_id)
    your_data = get_user_data(user_id)

    await context.bot.send_message(requester_id, f"Connected to @{your_data['username']} ({your_data['gender']})")
    await context.bot.send_message(user_id, f"Connected to @{requester_data['username']} ({requester_data['gender']})")
