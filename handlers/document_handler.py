# handlers/document_handler.py

import os
import uuid
import sys
from telegram import Update, InputFile
from telegram.ext import CallbackContext

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from utils.pdf_processor import process_pdf
    from utils.gemini_client import analyze_text_with_gemini
    from report_generator import generate_analysis_report
    from utils.logger import logger
    from exceptions import PDFProcessingError, GeminiAPIError
    from config import PDF_PROCESSING_SETTINGS, GENERATED_REPORTS_PATH # For MAX_FILE_SIZE_MB
except ModuleNotFoundError as e:
    print(f"Error during initial import in document_handler.py: {e}.")
    # Fallback definitions for isolated testing or path issues
    class PDFProcessingError(Exception): pass
    class GeminiAPIError(Exception): pass
    def process_pdf(pdf_path): raise NotImplementedError("process_pdf fallback")
    def analyze_text_with_gemini(text_content, model_name="gemini-pro"): raise NotImplementedError("analyze_text_with_gemini fallback")
    def generate_analysis_report(case_id, original_filename, analysis_data): raise NotImplementedError("generate_analysis_report fallback")
    import logging
    logger = logging.getLogger("fallback_document_handler")
    PDF_PROCESSING_SETTINGS = {"MAX_FILE_SIZE_MB": 20}
    GENERATED_REPORTS_PATH = "data/generated_reports/"
    logger.warning("Using fallback logger and settings for Document Handler due to import error.")


# --- Notification Templates (from README 6.4, adapted) ---
# These could be moved to a dedicated notifications module later

async def notify_file_uploaded(update: Update):
    await update.message.reply_text("✅ Ваш файл успешно загружен. Начинается анализ данных, это может занять несколько минут.")

async def notify_analysis_started(update: Update):
    await update.message.reply_text("🔍 Анализ загруженного кейса начался. Мы проверяем документ. Это займет некоторое время.")

async def notify_report_generating(update: Update):
    await update.message.reply_text("⏳ Анализ завершен, и отчет готовится. Это займет всего несколько секунд.")

async def notify_report_ready(update: Update, report_filepath: str, original_filename: str):
    caption = f"📄 Ваш отчет по документу '{original_filename}' готов."
    try:
        with open(report_filepath, 'rb') as report_file:
            await update.message.reply_document(document=InputFile(report_file), caption=caption, filename=os.path.basename(report_filepath))
        logger.info(f"Report sent to user: {report_filepath}")
    except Exception as e:
        logger.error(f"Failed to send report {report_filepath} to user: {e}", exc_info=True)
        await update.message.reply_text("⚠️ Не удалось отправить готовый отчет. Пожалуйста, свяжитесь с поддержкой.")
    finally:
        # Clean up the generated report file after sending (optional, based on policy)
        if os.path.exists(report_filepath):
            try:
                os.remove(report_filepath)
                logger.info(f"Cleaned up generated report file: {report_filepath}")
            except OSError as e:
                logger.error(f"Error deleting report file {report_filepath}: {e}", exc_info=True)


async def notify_error_upload(update: Update, error_message: str = ""):
    message = "❌ Ошибка загрузки файла."
    if error_message:
        message += f" {error_message}"
    else:
        message += " Убедитесь, что загружаемый файл является PDF и его размер не превышает допустимый лимит."
    await update.message.reply_text(message)

async def notify_error_processing(update: Update, error_message: str = ""):
    message = "⚠️ Ошибка при обработке файла."
    if error_message:
        message += f" {error_message}"
    else:
        message += " Возможно, ваш PDF-документ содержит только изображения или текст недостаточной длины. Попробуйте загрузить файл с текстовым содержимым."
    await update.message.reply_text(message)

async def notify_error_api(update: Update, service_name: str = "AI"): # Changed from OpenAI to generic AI
    message = f"⚠️ Произошла ошибка при анализе кейса с помощью {service_name}. Пожалуйста, попробуйте позже. Если проблема повторяется, обратитесь в техническую поддержку."
    await update.message.reply_text(message)

async def notify_error_report_generation(update: Update):
    message = "⚠️ Не удалось создать отчет. Возможно, данные были получены с ошибкой. Пожалуйста, повторите попытку или свяжитесь с поддержкой."
    await update.message.reply_text(message)

# --- Main Document Handling Logic ---

async def handle_document(update: Update, context: CallbackContext):
    """
    Handles incoming documents (PDFs).
    This function implements the main processing flow described in README 2.3.
    """
    if not update.message or not update.message.document: # Added check for update.message
        logger.warning("handle_document called without a message or document.")
        return

    document_file = update.message.document
    original_filename = document_file.file_name
    user_id = update.message.from_user.id
    case_id = str(uuid.uuid4()) # Unique ID for this processing instance

    logger.info(f"Received document: {original_filename} from user {user_id}. Case ID: {case_id}")

    # 1. Check file type and size
    if not original_filename.lower().endswith(".pdf"):
        logger.warning(f"User {user_id} uploaded non-PDF file: {original_filename}")
        await notify_error_upload(update, "Пожалуйста, загрузите файл в формате PDF.")
        return

    max_size_bytes = int(PDF_PROCESSING_SETTINGS.get("MAX_FILE_SIZE_MB", 20)) * 1024 * 1024
    if document_file.file_size > max_size_bytes:
        logger.warning(f"User {user_id} uploaded file exceeding size limit: {original_filename} ({document_file.file_size} bytes)")
        await notify_error_upload(update, f"Размер файла превышает лимит в {PDF_PROCESSING_SETTINGS['MAX_FILE_SIZE_MB']}MB.")
        return

    case_temp_dir = os.path.join("temp_files", case_id)
    os.makedirs(case_temp_dir, exist_ok=True)
    temp_pdf_path = os.path.join(case_temp_dir, original_filename)

    downloaded_file_path = None # Store the path of the downloaded file
    extracted_text = None
    analysis_result_text = None
    report_filepath = None

    try:
        logger.info(f"[{case_id}] Downloading PDF: {original_filename}")
        await notify_file_uploaded(update)

        tg_file = await context.bot.get_file(document_file.file_id)
        # Use download_to_drive which returns the path to the downloaded file
        downloaded_file_object = await tg_file.download_to_drive(custom_path=temp_pdf_path)
        downloaded_file_path = str(downloaded_file_object) # Convert File object to string path
        logger.info(f"[{case_id}] PDF downloaded to: {downloaded_file_path}")

        logger.info(f"[{case_id}] Processing PDF: {downloaded_file_path}")
        extracted_text, detected_lang = process_pdf(downloaded_file_path)
        logger.info(f"[{case_id}] PDF processed. Language: {detected_lang}, Text length: {len(extracted_text)}")

        await notify_analysis_started(update)
        logger.info(f"[{case_id}] Sending text to Gemini for analysis. Length: {len(extracted_text)}")

        gemini_raw_analysis = analyze_text_with_gemini(extracted_text)
        logger.info(f"[{case_id}] Received analysis from Gemini.")

        parsed_analysis_data = {
            "summary": gemini_raw_analysis, # Main analysis here
            "arguments": "Extracted arguments will be detailed here if parsed separately.",
            "inconsistencies": "Noted inconsistencies will be detailed here if parsed separately.",
            "recommendations": "Specific recommendations will be detailed here if parsed separately."
        }
        # The prompt in gemini_client.py asks for structured output.
        # Future work: Implement parsing of gemini_raw_analysis if it's a single string
        # containing these sections, or adapt gemini_client to return a dict.

        await notify_report_generating(update)
        logger.info(f"[{case_id}] Generating PDF report.")
        report_filepath = generate_analysis_report(case_id, original_filename, parsed_analysis_data)
        logger.info(f"[{case_id}] PDF report generated: {report_filepath}")

        await notify_report_ready(update, report_filepath, original_filename)

    except PDFProcessingError as e:
        logger.error(f"[{case_id}] PDF Processing Error for {original_filename}: {e}", exc_info=True)
        await notify_error_processing(update, str(e))
    except GeminiAPIError as e:
        logger.error(f"[{case_id}] Gemini API Error for {original_filename}: {e}", exc_info=True)
        await notify_error_api(update, service_name="Gemini")
    except Exception as e:
        logger.error(f"[{case_id}] Unexpected error handling document {original_filename}: {e}", exc_info=True)
        await update.message.reply_text("⚠️ Произошла непредвиденная ошибка при обработке вашего документа. Мы уже разбираемся.")
    finally:
        if downloaded_file_path and os.path.exists(downloaded_file_path): # Check downloaded_file_path
            try:
                os.remove(downloaded_file_path)
                logger.info(f"[{case_id}] Cleaned up temporary PDF: {downloaded_file_path}")
            except OSError as e:
                logger.error(f"[{case_id}] Error deleting temporary PDF {downloaded_file_path}: {e}", exc_info=True)

        if os.path.exists(case_temp_dir):
            if not os.listdir(case_temp_dir):
                try:
                    os.rmdir(case_temp_dir)
                    logger.info(f"[{case_id}] Cleaned up empty temporary directory: {case_temp_dir}")
                except OSError as e:
                     logger.error(f"[{case_id}] Error deleting temporary directory {case_temp_dir}: {e}", exc_info=True)
            else:
                logger.info(f"[{case_id}] Temporary directory {case_temp_dir} not empty ({os.listdir(case_temp_dir)}), not removing.")


if __name__ == '__main__':
    logger.info("document_handler.py is not designed for direct execution.")
    print("To test handle_document, integrate it with a Telegram bot structure.")
