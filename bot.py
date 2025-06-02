# bot.py

import sys
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

try:
    from config import TELEGRAM_BOT_TOKEN
    from utils.logger import logger
    from handlers.document_handler import handle_document
except ModuleNotFoundError as e:
    print(f"Error during initial import in bot.py: {e}. Ensure all modules are in place.")
    # Fallback for critical components if run in an incomplete environment
    TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE" # Needs a real token to run
    import logging
    logger = logging.getLogger("fallback_bot")
    async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Document handler is not fully loaded due to import errors.")
    logger.warning("Using fallback logger and settings for Bot due to import error.")

# --- User Agreement Flow (README 1.2) ---
# States for ConversationHandler
AGREEMENT, HANDLE_PDF = range(2)
USER_AGREEMENT_ACCEPTED = "user_agreement_accepted"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Sends a welcome message and the user agreement if not already accepted."""
    user_id = update.message.from_user.id
    logger.info(f"User {user_id} started interaction with /start.")

    if context.user_data.get(USER_AGREEMENT_ACCEPTED):
        await update.message.reply_text(
            "Добро пожаловать! Вы уже приняли пользовательское соглашение.\n"
            "Вы можете загрузить PDF-файл для анализа."
        )
        return HANDLE_PDF # Proceed to state where PDF can be handled

    keyboard = [
        [InlineKeyboardButton("✅ Принять (Accept)", callback_data="agreement_accept")],
        [InlineKeyboardButton("❌ Отклонить (Decline)", callback_data="agreement_decline")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    agreement_text = (
        "Добро пожаловать в Telegram Case Bot!\n\n"
        "Перед использованием бота, пожалуйста, ознакомьтесь и примите пользовательское соглашение.\n"
        "Основные положения:\n"
        "1. Бот предназначен для анализа политических кейсов в формате PDF.\n"
        "2. Загружая документ, вы подтверждаете, что имеете право на его использование и анализ.\n"
        "3. Анализ предоставляется с помощью AI и носит рекомендательный характер.\n"
        "4. Мы не храним ваши документы после обработки (они удаляются).\n"
        "5. Мы стремимся обеспечить конфиденциальность, но не несем ответственности за утечки данных из-за действий третьих лиц или уязвимостей вне нашего контроля.\n\n"
        "Нажимая 'Принять', вы соглашаетесь с этими условиями."
    )
    await update.message.reply_text(agreement_text, reply_markup=reply_markup)
    return AGREEMENT


async def agreement_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles user's response to the agreement."""
    query = update.callback_query
    await query.answer() # Acknowledge callback query
    user_id = query.from_user.id

    if query.data == "agreement_accept":
        logger.info(f"User {user_id} accepted the agreement.")
        context.user_data[USER_AGREEMENT_ACCEPTED] = True
        await query.edit_message_text(text="Спасибо! Вы приняли пользовательское соглашение.\nТеперь вы можете загружать PDF-файлы для анализа.")
        return HANDLE_PDF # Transition to state where PDF can be handled
    else:
        logger.info(f"User {user_id} declined the agreement.")
        await query.edit_message_text(text="Вы отклонили пользовательское соглашение. К сожалению, вы не можете использовать бот без его принятия.\nЕсли передумаете, просто введите /start снова.")
        return ConversationHandler.END # End conversation


async def agreement_declined_direct_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Informs user they need to accept agreement if they try to upload PDF first."""
    user_id = update.message.from_user.id
    logger.info(f"User {user_id} tried to upload a document without accepting agreement.")
    await update.message.reply_text("Пожалуйста, сначала примите пользовательское соглашение, введя команду /start.")
    # Optionally, could directly trigger the start_command flow here.


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a help message."""
    user_id = update.message.from_user.id
    logger.info(f"User {user_id} requested /help.")
    help_text = (
        "Этот бот помогает анализировать политические кейсы в формате PDF.\n"
        "1. Введите /start, чтобы начать и принять пользовательское соглашение.\n"
        "2. После принятия соглашения, просто отправьте PDF-файл в чат.\n"
        "3. Бот проанализирует документ и пришлет вам отчет.\n\n"
        "Доступные команды:\n"
        "/start - Начать работу с ботом и принять соглашение.\n"
        "/help - Показать это сообщение.\n"
        "/cancel - Отменить текущую операцию (если применимо)."
    )
    await update.message.reply_text(help_text)

async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the current operation (like agreement)."""
    user_id = update.message.from_user.id
    logger.info(f"User {user_id} used /cancel.")
    await update.message.reply_text("Операция отменена. Введите /start, чтобы начать заново.")
    # Clear any user-specific state if necessary, e.g., agreement status
    if USER_AGREEMENT_ACCEPTED in context.user_data:
        del context.user_data[USER_AGREEMENT_ACCEPTED]
    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    logger.info("Starting Telegram Case Bot...")

    if TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE" or not TELEGRAM_BOT_TOKEN:
        logger.critical("TELEGRAM_BOT_TOKEN is not set or is a placeholder! Please set it in config.py or .env file.")
        sys.exit("Telegram Bot Token not configured.")

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Conversation handler for agreement and PDF handling
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            AGREEMENT: [CallbackQueryHandler(agreement_callback)],
            HANDLE_PDF: [MessageHandler(filters.Document.PDF & (~filters.UpdateType.EDITED_MESSAGE), handle_document)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CommandHandler("start", start_command) # Allow restarting conversation by re-entering through /start
        ],
    )

    application.add_handler(conv_handler)

    # Handler for PDF documents sent outside the main conversation flow
    # or when the conversation is not in a state to handle PDFs.
    async def independent_pdf_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.message.from_user.id # Ensure update.message exists
        if not update.message: # Should not happen with MessageHandler but good practice
            return

        # Check if user has accepted agreement
        if not context.user_data.get(USER_AGREEMENT_ACCEPTED):
            logger.info(f"User {user_id} sent PDF directly without prior agreement. Prompting /start.")
            await agreement_declined_direct_upload(update, context)
        else:
            # User accepted agreement but might not be in HANDLE_PDF state (e.g., conversation ended/timed out)
            # Directly call handle_document.
            logger.info(f"User {user_id} sent PDF directly (agreement accepted). Processing with handle_document.")
            await handle_document(update, context)

    # This handler should only trigger if the ConversationHandler does not.
    # Add this handler with a specific group to manage priority relative to ConversationHandler.
    # ConversationHandler defaults to group 0. Handlers in higher groups are processed later.
    application.add_handler(MessageHandler(
        filters.Document.PDF & (~filters.UpdateType.EDITED_MESSAGE),
        independent_pdf_handler
    ), group=1)

    application.add_handler(CommandHandler("help", help_command))

    logger.info("Bot is polling for updates...")
    application.run_polling()

    logger.info("Bot has stopped.")

if __name__ == "__main__":
    main()
