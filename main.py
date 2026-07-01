"""
Telegram Whitelist Bot - Compatible with python-telegram-bot 20.7
"""

import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)

import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

ALLOWED_WORDS = {
    "لیست",
    "برای من",
    "list",
    "for me",
}

MAX_WARNINGS = 3

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

warning_count = {}


def is_allowed(text):
    text_lower = text.lower()
    return any(word in text_lower for word in ALLOWED_WORDS)


async def is_admin(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    member = await context.bot.get_chat_member(chat_id, user_id)
    return member.status in ("administrator", "creator")


async def filter_message(update, context):
    message = update.effective_message
    user = update.effective_user

    if not message or not message.text:
        return

    if await is_admin(update, context):
        return

    if is_allowed(message.text):
        return

    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"Delete failed: {e}")
        return

    user_id = user.id
    warning_count[user_id] = warning_count.get(user_id, 0) + 1
    count = warning_count[user_id]

    if count >= MAX_WARNINGS:
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, user_id)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"⛔ {user.first_name} banned after {MAX_WARNINGS} warnings."
            )
            warning_count.pop(user_id, None)
        except Exception as e:
            logger.warning(f"Ban failed: {e}")
    else:
        remaining = MAX_WARNINGS - count
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                f"⚠️ {user.first_name}, your message was deleted.\n"
                f"Only messages with allowed words are permitted.\n"
                f"Warning {count}/{MAX_WARNINGS} — {remaining} left before ban"
            ),
        )


async def add_word(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Only admins can use this command.")
        return
    if not context.args:
        await update.message.reply_text("📝 Usage: /addword word")
        return
    word = " ".join(context.args).strip().lower()
    ALLOWED_WORDS.add(word)
    await update.message.reply_text(f"✅ Word '{word}' added to allowed list.")


async def remove_word(update, context):
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Only admins can use this command.")
        return
    if not context.args:
        await update.message.reply_text("📝 Usage: /removeword word")
        return
    word = " ".join(context.args).strip().lower()
    ALLOWED_WORDS.discard(word)
    await update.message.reply_text(f"🗑️ Word '{word}' removed from allowed list.")


async def list_words(update, context):
    if not await is_admin(update, context):
        return
    if not ALLOWED_WORDS:
        await update.message.reply_text("📋 Allowed words list is empty!")
        return
    words = "\n".join(f"• {w}" for w in sorted(ALLOWED_WORDS))
    await update.message.reply_text(f"📋 Allowed words:\n{words}")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("addword", add_word))
    app.add_handler(CommandHandler("removeword", remove_word))
    app.add_handler(CommandHandler("listwords", list_words))
    app.add_handler(
        MessageHandler(filters.TEXT & filters.ChatType.GROUPS, filter_message)
    )

    logger.info("Bot started!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
