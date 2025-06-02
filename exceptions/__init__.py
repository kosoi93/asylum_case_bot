# exceptions/__init__.py

from .gemini_api_error import GeminiAPIError
from .pdf_processing_error import PDFProcessingError

__all__ = [
    'GeminiAPIError',
    'PDFProcessingError',
]
