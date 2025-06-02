# exceptions/pdf_processing_error.py

import sys
import os
# Add parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
try:
    from utils.errors import TelegramCaseBotError
except ModuleNotFoundError:
    # Fallback for direct execution or import issues
    class TelegramCaseBotError(Exception): pass


class PDFProcessingError(TelegramCaseBotError):
    """Custom exception for errors during PDF processing."""
    def __init__(self, message="An error occurred during PDF processing", original_exception=None):
        super().__init__(message, original_exception)
        self.message = message # Explicitly set message attribute


if __name__ == '__main__':
    try:
        raise PDFProcessingError("Could not extract text from PDF.")
    except PDFProcessingError as e:
        print(f"Caught expected PDF Processing error: {e}")

    try:
        raise PDFProcessingError("PDF file is corrupted", original_exception=IOError("File read failed"))
    except PDFProcessingError as e:
        print(f"Caught expected PDF Processing error with original: {e}")
