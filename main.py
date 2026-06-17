import asyncio
from telegram.ext import ApplicationBuilder
from telegram.ext import MessageHandler, filters
from handlers.message_handler import handle_message
from handlers.onboarding_handler import get_onboarding_handler
from config import TELEGRAM_BOT_TOKEN, PORT, WEBHOOK_URL

async def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(get_onboarding_handler())
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    await app.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook")
    app.run_webhook(listen="0.0.0.0",port=PORT,webhook_path="/webhook")


if __name__ == "__main__":
    asyncio.run(main())
