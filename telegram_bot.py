import os
import logging
from groq import Groq
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Keys
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_KEY = os.environ.get("GROQ_API_KEY")

client = Groq(api_key=GROQ_KEY)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """تو یک دستیار هوشمند فارسی‌زبان با نام «احمد ربانی» هستی.

قوانین مهم:
- همیشه به فارسی پاسخ بده، حتی اگر سوال به زبان دیگه‌ای بود
- پاسخ‌هایت مفید، دوستانه و دقیق باشند
- از اموجی مناسب استفاده کن
- مختصر و مفید باش، اما اگر نیاز بود توضیح کامل بده
- در صورت نیاز از مثال استفاده کن"""

# تاریخچه مکالمه به ازای هر کاربر
user_histories: dict[int, list] = {}

def get_history(user_id: int) -> list:
    if user_id not in user_histories:
        user_histories[user_id] = []
    return user_histories[user_id]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name or "دوست"
    await update.message.reply_text(
        f"سلام {user_name}! 👋\n\n"
        "من دستیار هوشمند *احمد ربانی* هستم 🤖\n"
        "هر سوالی داری بپرس، خوشحال میشم کمک کنم!\n\n"
        "دستورات:\n"
        "🔄 /reset — شروع مکالمه جدید\n"
        "ℹ️ /help — راهنما",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *راهنمای ربات احمد ربانی*\n\n"
        "• هر پیامی بفرستی باهوش جواب می‌دم\n"
        "• تاریخچه مکالمه رو یادم می‌مونه\n"
        "• /reset برای شروع مکالمه جدید\n\n"
        "💡 می‌تونی ازم بخوای:\n"
        "— سوال و جواب\n"
        "— نوشتن متن\n"
        "— ترجمه\n"
        "— خلاصه‌سازی\n"
        "— برنامه‌نویسی\n"
        "— و هر چیز دیگه‌ای!",
        parse_mode="Markdown"
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_histories[user_id] = []
    await update.message.reply_text("✅ مکالمه جدید شروع شد! چطور می‌تونم کمکت کنم؟")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    try:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )

        history = get_history(user_id)
        history.append({"role": "user", "content": user_text})

        # نگه داشتن آخرین ۲۰ پیام
        if len(history) > 20:
            history = history[-20:]
            user_histories[user_id] = history

        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
        )

        reply = response.choices[0].message.content
        history.append({"role": "assistant", "content": reply})

        await update.message.reply_text(reply)

    except Exception as e:
        logger.error(f"Error for user {user_id}: {e}")
        await update.message.reply_text(
            "⚠️ متأسفم، خطایی رخ داد. لطفاً دوباره تلاش کنید یا /reset بزنید."
        )

def main():
    if not TELEGRAM_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN not set!")
    if not GROQ_KEY:
        raise ValueError("GROQ_API_KEY not set!")

    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🚀 Bot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
