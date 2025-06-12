from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler

try:
    from config import TELEGRAM_BOT_TOKEN
except ImportError:  # fallback to example configuration
    from config_example import TELEGRAM_BOT_TOKEN
from handlers.document_handler import handle_document
from utils.logger import logger


async def start(update: Update, _):
    await update.message.reply_text("Добро пожаловать! Пришлите PDF для анализа.")


def main() -> None:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))

    logger.info("Bot started")
    app.run_polling()


if __name__ == "__main__":
    main()
