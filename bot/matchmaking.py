from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes
from bot.utils import get_user_data
import asyncio
from bot.state import is_shutting_down

waiting_users = []
active_chats = {}

def get_intro_markup():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("End Chat", callback_data="end_chat")]
    ])

loading_stages = [
    "🟩🟥🟥🟥🟥🟥",
    "🟩🟩🟥🟥🟥🟥",
    "🟩🟩🟩🟥🟥🟥",
    "🟩🟩🟩🟩🟥🟥",
    "🟩🟩🟩🟩🟩🟥",
    "🟩🟩🟩🟩🟩🟩"
]

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

        user_info = get_user_data(user_id)
        partner_info = get_user_data(partner_id)

        intro_for_user = (
            f"You are now connected to a stranger!\n"
            f"Name: *{partner_info['name']}*\nGender: *{partner_info['gender']}*"
        )
        intro_for_partner = (
            f"You are now connected to a stranger!\n"
            f"Name: *{user_info['name']}*\nGender: *{user_info['gender']}*"
        )

        markup = get_intro_markup()
        await context.bot.send_message(chat_id=partner_id, text=intro_for_partner, parse_mode="Markdown", reply_markup=markup)
        await context.bot.send_message(chat_id=user_id, text=intro_for_user, parse_mode="Markdown", reply_markup=markup)

    else:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        await asyncio.sleep(1)
        loading_msg = await update.message.reply_text("Waiting for a stranger...")
        waiting_users.append(user_id)

        while user_id in waiting_users and not is_shutting_down:
            for stage in loading_stages:
                if user_id not in waiting_users or is_shutting_down:
                    break
                try:
                    await loading_msg.edit_text(f"Waiting for a stranger...\n\n{stage}")
                    await asyncio.sleep(0.5)
                except:
                    break

async def stop_chat(user_id, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        active_chats.pop(partner_id, None)

        await context.bot.send_message(chat_id=partner_id, text="The stranger has ended the chat.")
        await context.bot.send_message(chat_id=user_id, text="You have left the chat.")
    elif user_id in waiting_users:
        waiting_users.remove(user_id)
        await context.bot.send_message(chat_id=user_id, text="You have left the waiting queue.")
    else:
        await context.bot.send_message(chat_id=user_id, text="You're not in a chat.")

async def forward_message(user_id, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if user_id not in active_chats:
        await update.message.reply_text("Use /chat to connect with someone.")
        return

    partner_id = active_chats[user_id]
    reply_markup = get_intro_markup()
    sender_label = "*Anonymous Stranger says:*"

    if update.message.text:
        await context.bot.send_message(chat_id=partner_id, text=f"{sender_label}\n{update.message.text}", parse_mode="Markdown", reply_markup=reply_markup)
    elif update.message.video_note:
        await context.bot.send_message(chat_id=partner_id, text=sender_label, parse_mode="Markdown", reply_markup=reply_markup)
        await context.bot.send_video_note(chat_id=partner_id, video_note=update.message.video_note.file_id)
    elif update.message.voice:
        await context.bot.send_message(chat_id=partner_id, text=sender_label, parse_mode="Markdown", reply_markup=reply_markup)
        await context.bot.send_voice(chat_id=partner_id, voice=update.message.voice.file_id)
    elif update.message.sticker:
        await context.bot.send_message(chat_id=partner_id, text=sender_label, parse_mode="Markdown", reply_markup=reply_markup)
        await context.bot.send_sticker(chat_id=partner_id, sticker=update.message.sticker.file_id)
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
