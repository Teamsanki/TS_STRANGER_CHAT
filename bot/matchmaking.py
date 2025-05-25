# bot/matchmaking.py

from telegram import Update
from telegram.ext import ContextTypes
from bot.utils import (
    add_to_waiting_list,
    remove_from_waiting_list,
    get_waiting_user,
    get_partner,
    set_partner,
    clear_partner,
    get_user_data,
    get_user_id_by_username,
    save_pending_request,
    get_pending_request,
    remove_pending_request
)

async def start_chat(user_id, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if get_partner(user_id):
        await update.message.reply_text("You're already in a chat. Use /stop to end the current chat.")
        return

    partner_id = get_waiting_user(user_id)
    if partner_id:
        remove_from_waiting_list(partner_id)
        set_partner(user_id, partner_id)
        set_partner(partner_id, user_id)

        user_data = get_user_data(user_id)
        partner_data = get_user_data(partner_id)

        await context.bot.send_message(
            user_id,
            f"You're now connected to a *{partner_data['gender']}* with username: @{partner_data['username']}",
            parse_mode="Markdown"
        )
        await context.bot.send_message(
            partner_id,
            f"You're now connected to a *{user_data['gender']}* with username: @{user_data['username']}",
            parse_mode="Markdown"
        )
    else:
        add_to_waiting_list(user_id)
        await update.message.reply_text("Waiting for a partner...")

async def stop_chat(user_id, update: Update, context: ContextTypes.DEFAULT_TYPE):
    partner_id = get_partner(user_id)

    if partner_id:
        await context.bot.send_message(partner_id, "The stranger has left the chat.")
        clear_partner(partner_id)

    clear_partner(user_id)
    remove_from_waiting_list(user_id)

    await update.message.reply_text("You have left the chat.")

async def forward_message(user_id, update: Update, context: ContextTypes.DEFAULT_TYPE):
    partner_id = get_partner(user_id)
    if not partner_id:
        return

    if update.message.text:
        await context.bot.send_message(partner_id, update.message.text)
    elif update.message.voice:
        await context.bot.send_voice(partner_id, update.message.voice.file_id)
    elif update.message.sticker:
        await context.bot.send_sticker(partner_id, update.message.sticker.file_id)
    elif update.message.video_note:
        await context.bot.send_video_note(partner_id, update.message.video_note.file_id)

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /search <username>")
        return

    target_username = args[0].lstrip("@")
    requester_id = update.effective_user.id
    target_id = get_user_id_by_username(target_username)

    if not target_id:
        await update.message.reply_text("User not found.")
        return

    request_id = f"{requester_id}_{target_id}"
    save_pending_request(target_id, request_id)

    await context.bot.send_message(
        target_id,
        f"You received a chat request from @{get_user_data(requester_id)['username']}.\n"
        f"Use /join {request_id} to accept."
    )
    await update.message.reply_text(f"Request sent to @{target_username}")

async def handle_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text("Usage: /join <request_id>")
        return

    request_id = args[0]
    target_id = update.effective_user.id
    pending = get_pending_request(target_id)

    if pending != request_id:
        await update.message.reply_text("No matching request found.")
        return

    requester_id, target_id_confirm = request_id.split("_")
    if int(target_id_confirm) != target_id:
        await update.message.reply_text("Request ID mismatch.")
        return

    set_partner(int(requester_id), target_id)
    set_partner(target_id, int(requester_id))

    user_data = get_user_data(int(requester_id))
    partner_data = get_user_data(target_id)

    await context.bot.send_message(
        int(requester_id),
        f"You are now connected to *{partner_data['gender']}* with username: @{partner_data['username']}",
        parse_mode="Markdown"
    )
    await context.bot.send_message(
        target_id,
        f"You are now connected to *{user_data['gender']}* with username: @{user_data['username']}",
        parse_mode="Markdown"
    )

    remove_pending_request(target_id)
