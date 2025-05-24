from telegram import Update
from telegram.ext import ContextTypes

waiting_users = []
active_chats = {}

async def start_chat(user_id, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if user_id in active_chats:
        await update.message.reply_text("You're already in a chat. Use /uhmegle to disconnect.")
        return
    if user_id in waiting_users:
        await update.message.reply_text("Please wait, we're still looking for someone...")
        return

    if waiting_users:
        partner_id = waiting_users.pop(0)
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id

        await context.bot.send_message(chat_id=partner_id, text="Connected to a stranger! Say hi.")
        await context.bot.send_message(chat_id=user_id, text="Connected to a stranger! Say hi.")
    else:
        waiting_users.append(user_id)
        await update.message.reply_text("Waiting for a stranger to connect...")

async def stop_chat(user_id, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        active_chats.pop(partner_id, None)

        await context.bot.send_message(chat_id=partner_id, text="The stranger has left the chat.")
        await update.message.reply_text("You have left the chat.")
    elif user_id in waiting_users:
        waiting_users.remove(user_id)
        await update.message.reply_text("You have stopped waiting.")
    else:
        await update.message.reply_text("You're not in a chat.")

async def forward_message(user_id, update: Update, context: ContextTypes.DEFAULT_TYPE):
    if user_id in active_chats:
        partner_id = active_chats[user_id]
        await context.bot.send_message(chat_id=partner_id, text=update.message.text)
    else:
        await update.message.reply_text("Use /megle to connect with someone.")
