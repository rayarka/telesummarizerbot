from telegram import Update, Bot
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from collections import defaultdict
from config import TOKEN

# Dictionary to store recent messages for groups
recent_messages = defaultdict(list)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Hello! I can summarize the last 100 messages in this group. Use /summarize to try it out!")

async def capture_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Store recent messages in a group, including forwarded messages."""
    chat_id = update.message.chat_id

    if update.message.forward_origin:
        original_sender = update.message.api_kwargs.get('forward_sender_name', None)
        if original_sender is None:
            original_sender = update.message.api_kwargs['forward_from']['username']
        message_text = update.message.text
        sender = f"{original_sender}"

    # # Check if the message is a forwarded message
    # if update.message.forward_from:
    #     # Get original sender for forwarded text messages
    #     original_sender = update.message.forward_from.username or update.message.forward_from.full_name
    #     message_text = update.message.text
    #     sender = f"Forwarded from {original_sender}"
    # elif update.message.forward_sender_name:
    #     # If it's a forwarded message with a sender name
    #     sender = f"Forwarded from {update.message.forward_sender_name}"
    #     message_text = update.message.text
    else:
        # Regular message (not forwarded)
        sender = update.message.from_user.username or update.message.from_user.full_name
        message_text = update.message.text

    # Store the message
    recent_messages[chat_id].append({
        "user": sender,
        "text": message_text
    })

    # Keep only the last 100 messages
    if len(recent_messages[chat_id]) > 100:
        recent_messages[chat_id].pop(0)


async def summarize(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Summarize the last 100 messages and send the summary to the command issuer."""
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    if chat_id not in recent_messages:
        await update.message.reply_text("Chatid not in recent")
        return
    elif not recent_messages[chat_id]:
        await update.message.reply_text("No messages to summarize yet!")
        return

    messages = recent_messages[chat_id]

    # Organize messages by speaker
    by_speaker = defaultdict(list)
    for message in messages:
        by_speaker[message["user"].strip()].append(message["text"])

    # Summarize topics by speaker
    summary = "\n".join([
        f"<b>{speaker}</b>: {', '.join(messages[:3])}..."  # Show top 3 messages
        for speaker, messages in by_speaker.items()
    ])

    # Send the summary to the user
    await context.bot.send_message(
        chat_id=user_id,
        text=f"Summary of the last 100 messages:\n{summary}",
        parse_mode=ParseMode.HTML
    )

    # Delete the command message from the group
    await update.message.delete()

def main():
    """Main function to set up the bot."""

    application = ApplicationBuilder().token(TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("summarize", summarize))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, capture_message))

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()
