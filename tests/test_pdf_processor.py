import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
import pytest

from utils.pdf_processor import extract_text_from_pdf


def test_extract_text_from_standard_pdf():
    sample_pdf_path = "tests/samples/standard_case.pdf"
    extracted_text = extract_text_from_pdf(sample_pdf_path)
    assert extracted_text != "", "Extracted text should not be empty"


def test_extract_text_from_encrypted_pdf():
    encrypted_pdf_path = "tests/samples/encrypted_case.pdf"
    with pytest.raises(Exception):
        extract_text_from_pdf(encrypted_pdf_path)
