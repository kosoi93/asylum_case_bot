# utils/pdf_processor.py

import pdfplumber
from langdetect import detect, lang_detect_exception
import sys
import os

# Add parent directory (project root) to sys.path to allow importing config and exceptions
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from exceptions import PDFProcessingError
    from config import PDF_PROCESSING_SETTINGS
    from utils.logger import logger
except ModuleNotFoundError as e:
    print(f"Error during initial import: {e}. This might happen if run directly or due to path issues.")
    # Fallback definitions for direct execution or testing
    class PDFProcessingError(Exception): pass
    PDF_PROCESSING_SETTINGS = {"MIN_TEXT_LENGTH": 50}
    import logging
    logger = logging.getLogger("fallback_pdf_processor")
    logger.warning("Using fallback logger and settings for PDF Processor due to import error.")


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text from a given PDF file.

    Args:
        pdf_path (str): The file path to the PDF.

    Returns:
        str: The extracted text content from the PDF.

    Raises:
        PDFProcessingError: If the file is not found, not a PDF, or text extraction fails.
    """
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file not found at path: {pdf_path}")
        raise PDFProcessingError(f"PDF file not found: {pdf_path}")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = []
            if not pdf.pages:
                logger.warning(f"PDF file has no pages: {pdf_path}")
                raise PDFProcessingError("PDF file has no pages.")

            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text.append(page_text)

            extracted_text = "\n".join(full_text).strip()
            logger.info(f"Successfully extracted text from {pdf_path}. Length: {len(extracted_text)}")
            return extracted_text

    except pdfplumber.exceptions.PDFSyntaxError as e:
        logger.error(f"Invalid PDF file or syntax error for {pdf_path}: {e}", exc_info=True)
        raise PDFProcessingError(f"Invalid PDF file or syntax error: {os.path.basename(pdf_path)}", original_exception=e)
    except Exception as e:
        logger.error(f"Could not extract text from PDF {pdf_path}: {e}", exc_info=True)
        raise PDFProcessingError(f"Failed to extract text from PDF: {os.path.basename(pdf_path)}", original_exception=e)


def is_text_sufficient(text: str) -> bool:
    """
    Checks if the extracted text is substantial enough for analysis.
    (README 7.4.1: Сканирование на наличие текста)

    Args:
        text (str): The text extracted from the PDF.

    Returns:
        bool: True if text is considered sufficient, False otherwise.
    """
    min_length = PDF_PROCESSING_SETTINGS.get("MIN_TEXT_LENGTH", 50)
    is_sufficient = len(text) >= min_length
    if not is_sufficient:
        logger.warning(f"Extracted text length {len(text)} is less than minimum required {min_length}.")
    return is_sufficient


def detect_document_language(text: str, default_lang: str = 'en') -> str:
    """
    Detects the language of the given text.
    (README 7.4.2: Проверка на язык текста)

    Args:
        text (str): The text to analyze.
        default_lang (str): Default language to return in case of detection failure.

    Returns:
        str: The detected language code (e.g., 'en', 'ru').
    """
    if not text or not text.strip():
        logger.warning("Cannot detect language from empty text.")
        return default_lang # Or raise an error, depending on desired behavior

    try:
        lang = detect(text)
        logger.info(f"Detected language: {lang}")
        return lang
    except lang_detect_exception.LangDetectException as e:
        logger.warning(f"Language detection failed: {e}. Falling back to default language '{default_lang}'.")
        return default_lang


def process_pdf(pdf_path: str) -> tuple[str, str]:
    """
    Full pipeline for processing a PDF: extract text, check sufficiency, detect language.

    Args:
        pdf_path (str): Path to the PDF file.

    Returns:
        tuple[str, str]: A tuple containing the extracted text and its detected language.

    Raises:
        PDFProcessingError: If text extraction fails or text is insufficient.
    """
    logger.info(f"Starting PDF processing for: {pdf_path}")

    extracted_text = extract_text_from_pdf(pdf_path)

    if not is_text_sufficient(extracted_text):
        raise PDFProcessingError(f"Extracted text from '{os.path.basename(pdf_path)}' is insufficient for analysis.")

    detected_lang = detect_document_language(extracted_text)

    logger.info(f"PDF processing successful for: {pdf_path}. Language: {detected_lang}, Text length: {len(extracted_text)}")
    return extracted_text, detected_lang


if __name__ == '__main__':
    # Create dummy files and directories for testing
    os.makedirs("temp_pdfs", exist_ok=True)
    os.makedirs("logs", exist_ok=True) # Ensure logs dir exists for fallback logger

    # Dummy config for direct run
    if 'config' not in sys.modules:
        PDF_PROCESSING_SETTINGS = {"MIN_TEXT_LENGTH": 10}
        logger.info("Using dummy PDF_PROCESSING_SETTINGS for __main__ example.")


    # Test 1: Valid PDF
    valid_pdf_path = "temp_pdfs/valid_test.pdf"
    try:
        with pdfplumber.open(valid_pdf_path, "w") as pdf: # Create a simple PDF for testing
             pdf.add_page().extract_text = lambda: "This is a test document with enough text."
        # This is a bit of a hack for pdfplumber as it doesn't have a direct write API like this.
        # For a real test, you'd need an actual PDF file.
        # Let's assume we have a function to create a simple PDF for testing or place a sample PDF.
        # For now, we'll mock the extraction for the positive case if file creation is too complex here.
        logger.info("Note: pdfplumber cannot create PDFs directly. A real sample PDF is needed for robust testing of extract_text_from_pdf.")
        logger.info("Simulating a valid PDF scenario for other functions.")

        sample_text = "This is a sample text in English for testing purposes. It should be long enough."
        if is_text_sufficient(sample_text):
            lang = detect_document_language(sample_text)
            logger.info(f"Simulated valid PDF: Text is sufficient. Detected language: {lang}")
        else:
            logger.error("Simulated valid PDF: Text was deemed insufficient.")

    except Exception as e:
        logger.error(f"Error in valid PDF test setup: {e}")


    # Test 2: PDF with insufficient text
    insufficient_text = "Too short."
    if not is_text_sufficient(insufficient_text):
        logger.info(f"Test for insufficient text passed. Text: '{insufficient_text}'")
    else:
        logger.error(f"Test for insufficient text failed. Text: '{insufficient_text}'")

    # Test 3: Language detection
    russian_text = "Это пример текста на русском языке для проверки определения языка."
    detected_russian = detect_document_language(russian_text)
    logger.info(f"Language detection for Russian text: '{detected_russian}' (Expected: ru)")

    english_text = "This is a sample English text."
    detected_english = detect_document_language(english_text)
    logger.info(f"Language detection for English text: '{detected_english}' (Expected: en)")

    # Test 4: Non-existent file (should be caught by extract_text_from_pdf)
    try:
        process_pdf("temp_pdfs/non_existent.pdf")
    except PDFProcessingError as e:
        logger.info(f"Caught expected error for non-existent PDF: {e}")
    except Exception as e:
        logger.error(f"Unexpected error for non-existent PDF test: {e}")

    # Test 5: Simulate PDF with no pages or unextractable text (hard to create, easier to mock)
    # This would typically involve having a specific PDF file that causes pdfplumber to return no text or raise errors.
    # For this example, we'll just log the intent.
    logger.info("Further tests would require specific PDF files (e.g., image-only, corrupted, password-protected).")

    # Clean up dummy files (optional)
    # if os.path.exists(valid_pdf_path):
    #     os.remove(valid_pdf_path)
    # if os.path.exists("temp_pdfs"):
    #     os.rmdir("temp_pdfs") # rmdir only works on empty dirs
