from telegram import Update
from telegram.ext import ContextTypes

from utils.logger import logger
from utils import pdf_processor
from utils.openai_client import analyze_case_text
from exceptions import OpenAIAPIError, PDFProcessingError


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    document = update.message.document
    if not document:
        return

    file_path = await document.get_file()
    local_path = file_path.download()
    try:
        text = pdf_processor.extract_text_from_pdf(local_path)
    except Exception as exc:
        logger.error("PDF processing failed: %s", exc)
        await update.message.reply_text("Ошибка обработки PDF")
        raise PDFProcessingError(str(exc)) from exc

    try:
        result = analyze_case_text(text)
    except Exception as exc:
        logger.error("OpenAI request failed: %s", exc)
        await update.message.reply_text("Ошибка анализа файла")
        raise OpenAIAPIError(str(exc)) from exc

    await update.message.reply_text(result)
