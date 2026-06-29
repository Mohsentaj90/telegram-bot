"""
ربات تلگرام - فیلتر Whitelist کلمات
نسخه سازگار با python-telegram-bot 13.15
"""

import logging
from telegram import Update
from telegram.ext import (
    Updater,
    MessageHandler,
    CommandHandler,
    Filters,
    CallbackContext,
)

BOT_TOKEN = "8768235339:AAHoOrTZLMX880hXkw3JqCg8c_FbrbYwVQs"

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


def is_admin(update, context):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    member = context.bot.get_chat_member(chat_id, user_id)
    return member.status in ("administrator", "creator")


def filter_message(update, context):
    message = update.effective_message
    user = update.effective_user

    if not message or not message.text:
        return

    if is_admin(update, context):
        return

    if is_allowed(message.text):
        return

    try:
        message.delete()
    except Exception as e:
        logger.warning(f"حذف پیام ناموفق: {e}")
        return

    user_id = user.id
    warning_count[user_id] = warning_count.get(user_id, 0) + 1
    count = warning_count[user_id]

    if count >= MAX_WARNINGS:
        try:
            context.bot.ban_chat_member(update.effective_chat.id, user_id)
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"⛔ {user.first_name} بعد از {MAX_WARNINGS} اخطار از گروه بن شد."
            )
            warning_count.pop(user_id, None)
        except Exception as e:
            logger.warning(f"بن کردن ناموفق: {e}")
    else:
        remaining = MAX_WARNINGS - count
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=(
                f"⚠️ {user.first_name}، پیام تو حذف شد.\n"
                f"فقط پیام‌هایی که شامل کلمات مجاز باشن قابل ارساله.\n"
                f"اخطار {count}/{MAX_WARNINGS} — {remaining} اخطار تا بن"
            ),
        )


def add_word(update, context):
    if not is_admin(update, context):
        update.message.reply_text("❌ فقط ادمین‌ها می‌تونن از این دستور استفاده کنن.")
        return

    if not context.args:
        update.message.reply_text("📝 استفاده: /addword کلمه")
        return

    word = " ".join(context.args).strip().lower()
    ALLOWED_WORDS.add(word)
    update.message.reply_text(f"✅ کلمه «{word}» به لیست مجاز اضافه شد.")


def remove_word(update, context):
    if not is_admin(update, context):
        update.message.reply_text("❌ فقط ادمین‌ها می‌تونن از این دستور استفاده کنن.")
        return

    if not context.args:
        update.message.reply_text("📝 استفاده: /removeword کلمه")
        return

    word = " ".join(context.args).strip().lower()
    ALLOWED_WORDS.discard(word)
    update.message.reply_text(f"🗑️ کلمه «{word}» از لیست مجاز حذف شد.")


def list_words(update, context):
    if not is_admin(update, context):
        return

    if not ALLOWED_WORDS:
        update.message.reply_text("📋 لیست کلمات مجاز خالیه!")
        return

    words = "\n".join(f"• {w}" for w in sorted(ALLOWED_WORDS))
    update.message.reply_text(f"📋 کلمات مجاز:\n{words}")


def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("addword", add_word))
    dp.add_handler(CommandHandler("removeword", remove_word))
    dp.add_handler(CommandHandler("listwords", list_words))
    dp.add_handler(MessageHandler(Filters.text & Filters.group, filter_message))

    logger.info("ربات شروع به کار کرد...")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
