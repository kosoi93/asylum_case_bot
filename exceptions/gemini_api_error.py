# exceptions/gemini_api_error.py

import sys
import os
# Add parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
try:
    from utils.errors import TelegramCaseBotError
except ModuleNotFoundError:
    # Fallback for direct execution or import issues
    class TelegramCaseBotError(Exception): pass


class GeminiAPIError(TelegramCaseBotError):
    """Custom exception for errors related to Google Gemini API interactions."""
    def __init__(self, message="An error occurred with the Gemini API", status_code=None, original_exception=None):
        super().__init__(message, original_exception)
        self.status_code = status_code # status_code might not be directly applicable for Gemini client library errors
        self.message = message         # but can be used for HTTP errors if making raw requests.

    def __str__(self):
        if self.status_code:
            return f"Gemini API Error (Status {self.status_code}): {self.message}"
        return f"Gemini API Error: {self.message}"

if __name__ == '__main__':
    try:
        raise GeminiAPIError("Failed to connect to Gemini API", status_code=500)
    except GeminiAPIError as e:
        print(f"Caught expected Gemini API error: {e}")

    try:
        raise GeminiAPIError("Another Gemini API error", original_exception=RuntimeError("Underlying runtime issue"))
    except GeminiAPIError as e:
        print(f"Caught expected Gemini API error with original: {e}")
