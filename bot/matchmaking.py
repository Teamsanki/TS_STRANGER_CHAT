from bot.utils import get_user_data
from telegram import InlineKeyboardMarkup, InlineKeyboardButton

waiting_users = []
active_chats = {}

async def start_chat(user_id, update, context):
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

        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("End Chat", callback_data="end_chat")]])

        await context.bot.send_message(chat_id=partner_id, text=intro_for_partner, parse_mode="Markdown", reply_markup=keyboard)
        await context.bot.send_message(chat_id=user_id, text=intro_for_user, parse_mode="Markdown", reply_markup=keyboard)
    else:
        waiting_users.append(user_id)
        await update.message.reply_text("Waiting for a stranger to connect...")

async def stop_chat(user_id, update, context):
    if user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        active_chats.pop(partner_id, None)
        await context.bot.send_message(chat_id=partner_id, text="The stranger has ended the chat.")
        await context.bot.send_message(chat_id=user_id, text="You have left the chat.")
    elif user_id in waiting_users:
        waiting_users.remove(user_id)
        await update.message.reply_text("You have left the waiting queue.")
    else:
        await update.message.reply_text("You're not in a chat.")

async def forward_message(user_id, update, context):
    if user_id not in active_chats:
        await update.message.reply_text("Use /chat to connect with someone.")
        return

    partner_id = active_chats[user_id]
    user_info = get_user_data(user_id)
    name = user_info.get("name", "Stranger")
    gender = user_info.get("gender", "Unknown")
    prefix = f"Message from *{name}* ({gender}):"

    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("End Chat", callback_data="end_chat")]])

    if update.message.text:
        await context.bot.send_message(chat_id=partner_id, text=f"{prefix}\n{update.message.text}", parse_mode="Markdown", reply_markup=keyboard)
    elif update.message.video_note:
        await context.bot.send_video_note(chat_id=partner_id, video_note=update.message.video_note.file_id, reply_markup=keyboard)
    elif update.message.voice:
        await context.bot.send_voice(chat_id=partner_id, voice=update.message.voice.file_id, reply_markup=keyboard)
    elif update.message.sticker:
        await context.bot.send_sticker(chat_id=partner_id, sticker=update.message.sticker.file_id)
    elif update.message.photo:
        await context.bot.send_photo(chat_id=partner_id, photo=update.message.photo[-1].file_id, caption=prefix, parse_mode="Markdown", reply_markup=keyboard)
    elif update.message.video:
        await context.bot.send_video(chat_id=partner_id, video=update.message.video.file_id, caption=prefix, parse_mode="Markdown", reply_markup=keyboard)
    elif update.message.document:
        await context.bot.send_document(chat_id=partner_id, document=update.message.document.file_id, caption=prefix, parse_mode="Markdown", reply_markup=keyboard)
    elif update.message.animation:
        await context.bot.send_animation(chat_id=partner_id, animation=update.message.animation.file_id, caption=prefix, parse_mode="Markdown", reply_markup=keyboard)
    else:
        await update.message.reply_text("Unsupported message type.")
