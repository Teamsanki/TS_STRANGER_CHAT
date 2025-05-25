# bot/matchmaking.py

from telegram import Update
from telegram.ext import ContextTypes
from bot.utils import (
    get_user_data,
    get_user_by_username,
    save_active_chat,
    delete_active_chat,
    get_active_partner,
    is_user_busy
)

waiting_users = []

async def start_chat(user_id, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_user_busy(user_id):
        await update.message.reply_text("You're already in a chat. Use /end to leave.")
        return

    for partner_id in waiting_users:
        if partner_id != user_id and not is_user_busy(partner_id):
            user_data = get_user_data(user_id)
            partner_data = get_user_data(partner_id)

            if user_data and partner_data:
                save_active_chat(user_id, partner_id)
                save_active_chat(partner_id, user_id)
                waiting_users.remove(partner_id)

                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"You're now connected to a *{partner_data['gender']}*.\nUsername: `{partner_data['username']}`",
                    parse_mode="Markdown"
                )
                await context.bot.send_message(
                    chat_id=partner_id,
                    text=f"You're now connected to a *{user_data['gender']}*.\nUsername: `{user_data['username']}`",
                    parse_mode="Markdown"
                )
                return

    waiting_users.append(user_id)
    await update.message.reply_text("Looking for someone to chat with...")

async def stop_chat(user_id, update: Update, context: ContextTypes.DEFAULT_TYPE):
    partner_id = get_active_partner(user_id)
    if partner_id:
        delete_active_chat(user_id)
        delete_active_chat(partner_id)

        await context.bot.send_message(chat_id=user_id, text="You left the chat.")
        await context.bot.send_message(chat_id=partner_id, text="Your partner left the chat.")
    else:
        if user_id in waiting_users:
            waiting_users.remove(user_id)
        await update.message.reply_text("You are not currently in a chat.")

async def forward_message(user_id, update: Update, context: ContextTypes.DEFAULT_TYPE):
    partner_id = get_active_partner(user_id)
    if not partner_id:
        await update.message.reply_text("You're not in a chat. Use /chat to find someone.")
        return

    if update.message.text:
        await context.bot.send_message(chat_id=partner_id, text=update.message.text)
    elif update.message.voice:
        await context.bot.send_voice(chat_id=partner_id, voice=update.message.voice.file_id)
    elif update.message.sticker:
        await context.bot.send_sticker(chat_id=partner_id, sticker=update.message.sticker.file_id)
    elif update.message.video_note:
        await context.bot.send_video_note(chat_id=partner_id, video_note=update.message.video_note.file_id)

async def inline_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "end_chat":
        user_id = query.from_user.id
        await stop_chat(user_id, update, context)
        await query.message.edit_text("Chat ended.")
