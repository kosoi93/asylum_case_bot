# tests/test_report_generator.py
import pytest
import os
import sys
from unittest.mock import patch, MagicMock

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')) # project_root is one level up from tests/
sys.path.insert(0, project_root)

from report_generator import generate_analysis_report
from config import GENERATED_REPORTS_PATH

@pytest.fixture(scope="function", autouse=True)
def setup_report_dir(tmp_path): # Use pytest's tmp_path fixture for unique temp dirs per test
    # Monkeypatch GENERATED_REPORTS_PATH to use a temporary directory for this test run
    # This prevents cluttering the actual data/generated_reports and avoids test interference.
    original_path = GENERATED_REPORTS_PATH
    test_reports_path = tmp_path / "generated_reports"
    os.makedirs(test_reports_path, exist_ok=True)

    # Monkeypatching the config directly if it's already loaded,
    # and also the report_generator's global if it has captured it at import time.
    if 'config' in sys.modules:
        monkeypatch.setattr(sys.modules['config'], "GENERATED_REPORTS_PATH", str(test_reports_path))
    if 'report_generator' in sys.modules:
         monkeypatch.setattr(sys.modules['report_generator'], "GENERATED_REPORTS_PATH", str(test_reports_path))

    yield str(test_reports_path) # provide the path to the tests if needed

    # Teardown (cleanup) is handled automatically by tmp_path fixture
    # Restore original path if necessary, though for testing, isolating is key.
    if 'config' in sys.modules:
        monkeypatch.setattr(sys.modules['config'], "GENERATED_REPORTS_PATH", original_path)
    if 'report_generator' in sys.modules:
         monkeypatch.setattr(sys.modules['report_generator'], "GENERATED_REPORTS_PATH", original_path)


# Need to apply monkeypatch for the fixture
@pytest.fixture
def monkeypatch_paths(monkeypatch, tmp_path):
    test_reports_path = tmp_path / "generated_reports"
    os.makedirs(test_reports_path, exist_ok=True)

    # Store original path to restore later if necessary, though tmp_path makes it less critical
    original_config_path = None
    if 'config' in sys.modules:
        original_config_path = getattr(sys.modules['config'], "GENERATED_REPORTS_PATH", None)

    original_rg_path = None
    if 'report_generator' in sys.modules:
        original_rg_path = getattr(sys.modules['report_generator'], "GENERATED_REPORTS_PATH", None)

    if 'config' in sys.modules:
        monkeypatch.setattr(sys.modules['config'], "GENERATED_REPORTS_PATH", str(test_reports_path))
    if 'report_generator' in sys.modules:
         monkeypatch.setattr(sys.modules['report_generator'], "GENERATED_REPORTS_PATH", str(test_reports_path))

    yield str(test_reports_path)

    # Restore original paths
    if 'config' in sys.modules and original_config_path:
        monkeypatch.setattr(sys.modules['config'], "GENERATED_REPORTS_PATH", original_config_path)
    if 'report_generator' in sys.modules and original_rg_path:
         monkeypatch.setattr(sys.modules['report_generator'], "GENERATED_REPORTS_PATH", original_rg_path)


@patch('report_generator.SimpleDocTemplate')
def test_generate_analysis_report_success(mock_simple_doc_template, monkeypatch_paths):
    current_reports_path = monkeypatch_paths # Get the temp path from the fixture

    mock_doc_instance = MagicMock()
    mock_simple_doc_template.return_value = mock_doc_instance

    case_id = "test_001"
    original_filename = "original.pdf"
    analysis_data = {
        "summary": "This is a summary.",
        "arguments": ["Arg1", "Arg2"],
        "inconsistencies": "Some inconsistency.",
        "recommendations": ["Rec1", "Rec2"]
    }

    report_path = generate_analysis_report(case_id, original_filename, analysis_data)

    assert report_path.startswith(current_reports_path)
    assert case_id in report_path
    assert original_filename.replace('.pdf', '') in report_path
    assert report_path.endswith(".pdf")

    mock_simple_doc_template.assert_called_once()
    # Check that the first argument (filename) of SimpleDocTemplate call is correct
    assert mock_simple_doc_template.call_args[0][0] == report_path

    mock_doc_instance.build.assert_called_once()

    args, _ = mock_doc_instance.build.call_args
    story = args[0]

    # Extract text from Paragraphs, handling potential non-Paragraph objects in story
    story_texts = []
    from reportlab.platypus import Paragraph # Import for isinstance check
    for item in story:
        if isinstance(item, Paragraph):
            story_texts.append(item.text)

    assert "Political Case Analysis Report" in story_texts
    assert "This is a summary." in story_texts
    assert "• Arg1" in story_texts # Assuming lists are iterated and added as paragraphs with bullets
    assert "• Rec2" in story_texts

def test_generate_analysis_report_file_creation_real(monkeypatch_paths):
    current_reports_path = monkeypatch_paths # Get the temp path

    case_id = "real_test_002"
    original_filename = "real_doc.pdf"
    analysis_data = {
        "summary": "Real test summary.",
        "arguments": "Real arguments.", # Test with string instead of list
        "inconsistencies": "Real inconsistencies.",
        "recommendations": ["Rec A", "Rec B"] # Test with list
    }

    report_filepath = None
    try:
        report_filepath = generate_analysis_report(case_id, original_filename, analysis_data)
        assert os.path.exists(report_filepath)
        assert os.path.getsize(report_filepath) > 0

        # Verify it's in the temp path
        assert report_filepath.startswith(current_reports_path)

    finally:
        if report_filepath and os.path.exists(report_filepath):
            # No need to manually remove if tmp_path is used correctly by the fixture
            # and monkeypatch_paths correctly sets GENERATED_REPORTS_PATH
            pass # os.remove(report_filepath) # tmp_path handles cleanup

# It's good practice to ensure the module being tested can be imported
def test_report_generator_module_importable():
    import report_generator
    assert report_generator is not None
