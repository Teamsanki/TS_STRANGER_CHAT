from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils import get_user_data

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

        intro_for_user = f"You are now connected to a stranger!\nName: *{partner_info['name']}*\nGender: *{partner_info['gender']}*"
        intro_for_partner = f"You are now connected to a stranger!\nName: *{user_info['name']}*\nGender: *{user_info['gender']}*"

        await context.bot.send_message(chat_id=partner_id, text=intro_for_partner, parse_mode="Markdown")
        await context.bot.send_message(chat_id=user_id, text=intro_for_user, parse_mode="Markdown")
    else:
        waiting_users.append(user_id)
        await update.message.reply_text("Waiting for a stranger to connect...")

async def stop_chat(user_id, update, context):
    if user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        active_chats.pop(partner_id, None)
        await context.bot.send_message(chat_id=partner_id, text="The stranger has ended the chat.")
        await update.message.reply_text("You have left the chat.")
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
    partner_info = get_user_data(partner_id)

    partner_name = partner_info.get("name", "Unknown")
    partner_gender = partner_info.get("gender", "Unknown")
    prefix_text = f"Message from {partner_name}, Gender: {partner_gender}\n\n"

    end_button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("End Chat", callback_data="end_chat")]]
    )

    msg = update.message

    async def send_with_prefix(method, **kwargs):
        text = kwargs.get("caption") or kwargs.get("text") or ""
        if "caption" in kwargs:
            kwargs["caption"] = prefix_text + text
        if "text" in kwargs:
            kwargs["text"] = prefix_text + text
        kwargs["reply_markup"] = end_button
        await method(chat_id=partner_id, **{k: v for k, v in kwargs.items() if v is not None})

    if msg.text and msg.text.strip() != "":
        await send_with_prefix(context.bot.send_message, text=msg.text)

    elif msg.photo:
        photo_file_id = msg.photo[-1].file_id
        await send_with_prefix(context.bot.send_photo, photo=photo_file_id, caption=msg.caption)

    elif msg.video:
        await send_with_prefix(context.bot.send_video, video=msg.video.file_id, caption=msg.caption)

    elif msg.video_note:
        # video_note does not support caption, so send text separately
        await context.bot.send_video_note(chat_id=partner_id, video_note=msg.video_note.file_id)
        await context.bot.send_message(chat_id=partner_id, text=prefix_text, reply_markup=end_button)

    elif msg.voice:
        await send_with_prefix(context.bot.send_voice, voice=msg.voice.file_id, caption=msg.caption)

    elif msg.sticker:
        await context.bot.send_message(chat_id=partner_id, text=prefix_text, reply_markup=end_button)
        await context.bot.send_sticker(chat_id=partner_id, sticker=msg.sticker.file_id)

    elif msg.document:
        await send_with_prefix(context.bot.send_document, document=msg.document.file_id, caption=msg.caption)

    elif msg.animation:
        await send_with_prefix(context.bot.send_animation, animation=msg.animation.file_id, caption=msg.caption)

    else:
        await update.message.reply_text("Unsupported message type.")
