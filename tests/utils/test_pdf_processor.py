# tests/utils/test_pdf_processor.py
import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure the project root is in sys.path to find modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from utils.pdf_processor import process_pdf, extract_text_from_pdf, is_text_sufficient, detect_document_language
from exceptions import PDFProcessingError
from config import PDF_PROCESSING_SETTINGS

# Path to sample files for tests
SAMPLES_DIR = os.path.join(project_root, "tests", "samples")
DUMMY_PDF_PATH = os.path.join(SAMPLES_DIR, "dummy.pdf")
EMPTY_PDF_PATH = os.path.join(SAMPLES_DIR, "empty.pdf") # Assume this is an image-only or truly empty PDF

@pytest.fixture(scope="module", autouse=True)
def setup_sample_files():
    os.makedirs(SAMPLES_DIR, exist_ok=True)
    # Try to create a real dummy PDF for extract_text_from_pdf
    # If pdfplumber is not available in test env or complex, this part might be skipped
    # and extract_text_from_pdf will rely more on mocking.
    try:
        import pdfplumber
        # Create a minimal valid PDF with some text
        # This is a simplified way to create a PDF; real PDF creation is complex.
        # For robust testing, a pre-made dummy.pdf is better.
        # If the subtask can create one, great. Otherwise, extract_text_from_pdf test will mock.
        if not os.path.exists(DUMMY_PDF_PATH):
             with open(DUMMY_PDF_PATH, "w") as f: # This is NOT a PDF.
                 f.write("%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n" +
                         "2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n" +
                         "3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n" +
                         "trailer<</Root 1 0 R>>") # Very basic PDF structure, likely won't have extractable text by pdfplumber easily.
             # A better dummy PDF creation would involve reportlab or a similar tool, or a pre-existing file.
             # Given the limitations, mocking extract_text_from_pdf is more reliable for CI.
        if not os.path.exists(EMPTY_PDF_PATH): # Similarly for an "empty" PDF
             with open(EMPTY_PDF_PATH, "w") as f:
                 f.write("%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n" +
                         "2 0 obj<</Type/Pages/Count 0>>endobj\n" + # No pages
                         "trailer<</Root 1 0 R>>")

    except ImportError:
        print("pdfplumber not available for creating dummy PDF in test setup.")
    except Exception as e:
        print(f"Error creating dummy PDF for tests: {e}")
    yield
    # Teardown: remove sample files if created by this fixture
    # if os.path.exists(DUMMY_PDF_PATH): os.remove(DUMMY_PDF_PATH)
    # if os.path.exists(EMPTY_PDF_PATH): os.remove(EMPTY_PDF_PATH)

@patch('utils.pdf_processor.pdfplumber.open')
def test_extract_text_from_pdf_mocked(mock_pdfplumber_open):
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "This is test text from a page."
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page, mock_page] # Two pages
    mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf

    # Create a dummy file for the path argument
    if not os.path.exists(DUMMY_PDF_PATH):
        with open(DUMMY_PDF_PATH, 'w') as f: f.write("dummy content") # ensure file exists

    text = extract_text_from_pdf(DUMMY_PDF_PATH)
    assert text == "This is test text from a page.\nThis is test text from a page."
    mock_pdfplumber_open.assert_called_with(DUMMY_PDF_PATH)

@patch('utils.pdf_processor.pdfplumber.open')
def test_extract_text_from_empty_pdf_mocked(mock_pdfplumber_open):
    mock_pdf = MagicMock()
    mock_pdf.pages = [] # No pages
    mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf
    if not os.path.exists(EMPTY_PDF_PATH):
        with open(EMPTY_PDF_PATH, 'w') as f: f.write("dummy empty content")

    with pytest.raises(PDFProcessingError, match="PDF file has no pages"):
        extract_text_from_pdf(EMPTY_PDF_PATH)

def test_is_text_sufficient():
    PDF_PROCESSING_SETTINGS["MIN_TEXT_LENGTH"] = 50
    assert is_text_sufficient("This is a long enough text for analysis purposes.") == True
    assert is_text_sufficient("Short text.") == False
    PDF_PROCESSING_SETTINGS["MIN_TEXT_LENGTH"] = 5 # For testing edge case
    assert is_text_sufficient("Tiny") == True

@patch('utils.pdf_processor.detect') # Mock langdetect.detect
def test_detect_document_language(mock_lang_detect):
    mock_lang_detect.return_value = 'en'
    assert detect_document_language("This is English text.") == 'en'
    mock_lang_detect.assert_called_with("This is English text.")

    mock_lang_detect.return_value = 'ru'
    assert detect_document_language("Это русский текст.") == 'ru'

    # Test fallback for langdetect exception
    from langdetect import lang_detect_exception # Import locally for test
    mock_lang_detect.side_effect = lang_detect_exception.LangDetectException("Langdetect failed", 0)
    assert detect_document_language("Some problematic text", default_lang='fr') == 'fr'

@patch('utils.pdf_processor.extract_text_from_pdf')
@patch('utils.pdf_processor.is_text_sufficient')
@patch('utils.pdf_processor.detect_document_language')
def test_process_pdf_success(mock_detect_lang, mock_is_sufficient, mock_extract_text):
    mock_extract_text.return_value = "Sufficient sample text."
    mock_is_sufficient.return_value = True
    mock_detect_lang.return_value = "en"

    text, lang = process_pdf("dummy_path.pdf")

    assert text == "Sufficient sample text."
    assert lang == "en"
    mock_extract_text.assert_called_with("dummy_path.pdf")
    mock_is_sufficient.assert_called_with("Sufficient sample text.")
    mock_detect_lang.assert_called_with("Sufficient sample text.")

@patch('utils.pdf_processor.extract_text_from_pdf')
@patch('utils.pdf_processor.is_text_sufficient')
def test_process_pdf_insufficient_text(mock_is_sufficient, mock_extract_text):
    mock_extract_text.return_value = "Too short."
    mock_is_sufficient.return_value = False

    with pytest.raises(PDFProcessingError, match="insufficient for analysis"):
        process_pdf("dummy_path.pdf")
