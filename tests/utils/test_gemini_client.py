# tests/utils/test_gemini_client.py
import pytest
import os
import sys
from unittest.mock import patch, MagicMock

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from utils.gemini_client import analyze_text_with_gemini
from exceptions import GeminiAPIError
from config import GEMINI_API_KEY

# Ensure GEMINI_API_KEY is set to something (even a dummy) for tests to run without immediate failure
# The actual API call will be mocked.
@pytest.fixture(autouse=True)
def ensure_api_key_for_test(monkeypatch):
    # Check if the original GEMINI_API_KEY from config is problematic
    original_key = GEMINI_API_KEY
    if not original_key or original_key == "YOUR_GEMINI_API_KEY_HERE":
        monkeypatch.setattr("utils.gemini_client.GEMINI_API_KEY", "TEST_API_KEY_DUMMY")
        # If config itself is directly imported and used elsewhere in the module under test
        if 'config' in sys.modules:
             monkeypatch.setattr(sys.modules['config'], "GEMINI_API_KEY", "TEST_API_KEY_DUMMY")


@patch('utils.gemini_client.genai.GenerativeModel')
def test_analyze_text_with_gemini_success(mock_generative_model):
    # Mock the model and its response
    mock_model_instance = MagicMock()
    mock_response = MagicMock()
    # Simulate response.parts having text
    part_with_text = MagicMock()
    part_with_text.text = "Gemini analysis result."
    mock_response.parts = [part_with_text]
    mock_response.text = None # Ensure parts logic is tested

    mock_model_instance.generate_content.return_value = mock_response
    mock_generative_model.return_value = mock_model_instance

    result = analyze_text_with_gemini("Some sample text")
    assert result == "Gemini analysis result."
    mock_generative_model.assert_called_with("gemini-pro") # or your default model
    # Check that prompt contains the input text
    call_args = mock_model_instance.generate_content.call_args
    assert "Some sample text" in call_args[0][0]

@patch('utils.gemini_client.genai.GenerativeModel')
def test_analyze_text_with_gemini_success_with_response_text_attribute(mock_generative_model):
    # Mock the model and its response
    mock_model_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.parts = [] # No parts
    mock_response.text = "Gemini analysis result via text attribute." # Simulate response.text has content

    mock_model_instance.generate_content.return_value = mock_response
    mock_generative_model.return_value = mock_model_instance

    result = analyze_text_with_gemini("Some sample text with response.text")
    assert result == "Gemini analysis result via text attribute."


@patch('utils.gemini_client.genai.GenerativeModel')
def test_analyze_text_with_gemini_api_error(mock_generative_model):
    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.side_effect = Exception("Simulated API Error")
    mock_generative_model.return_value = mock_model_instance

    with pytest.raises(GeminiAPIError, match="Failed to get analysis from Gemini"):
        analyze_text_with_gemini("Some text")

@patch('utils.gemini_client.genai.configure') # Mock configure as well if it's relevant to key failure
@patch('utils.gemini_client.genai.GenerativeModel')
def test_analyze_text_with_gemini_no_api_key(mock_generative_model, mock_configure, monkeypatch):
    # Temporarily unset API key for this test
    monkeypatch.setattr("utils.gemini_client.GEMINI_API_KEY", None)
    if 'config' in sys.modules:
        monkeypatch.setattr(sys.modules['config'], "GEMINI_API_KEY", None)


    with pytest.raises(GeminiAPIError, match="Gemini API key is not configured"):
        analyze_text_with_gemini("Some text")

@patch('utils.gemini_client.genai.GenerativeModel')
def test_analyze_text_with_gemini_empty_response(mock_generative_model):
    mock_model_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.parts = [] # No parts
    mock_response.text = None  # No text attribute

    # Simulate prompt_feedback if needed for the specific error message branch
    mock_prompt_feedback = MagicMock()
    # Example: mock_prompt_feedback.block_reason = "SAFETY"
    # For the "content was blocked" part of the error message, this detail might be useful.
    # However, the current error message is generic "empty response or content was blocked."
    mock_response.prompt_feedback = mock_prompt_feedback

    mock_model_instance.generate_content.return_value = mock_response
    mock_generative_model.return_value = mock_model_instance

    with pytest.raises(GeminiAPIError, match="Gemini API returned an empty response or content was blocked"):
        analyze_text_with_gemini("Risky text")
