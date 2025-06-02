# report_generator.py

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_LEFT
from reportlab.lib import colors
import os
import datetime
import sys

try:
    from config import GENERATED_REPORTS_PATH, REPORT_TEMPLATE_PATH # REPORT_TEMPLATE_PATH might not be used initially
    from utils.logger import logger
except ModuleNotFoundError:
    print("Error during initial import in report_generator.py.")
    # Fallback definitions
    GENERATED_REPORTS_PATH = "data/generated_reports/"
    REPORT_TEMPLATE_PATH = "data/templates/report_template.docx" # Placeholder
    import logging
    logger = logging.getLogger("fallback_report_generator")
    logger.warning("Using fallback logger and settings for Report Generator.")


def create_styled_paragraph(text, style_name, styles):
    """Helper to create a Paragraph with common handling for None text."""
    return Paragraph(text if text else "N/A", styles[style_name])

def generate_analysis_report(case_id: str, original_filename: str, analysis_data: dict) -> str:
    """
    Generates a PDF report from the analysis data.

    Args:
        case_id (str): A unique identifier for the case/report.
        original_filename (str): The name of the original PDF file uploaded by the user.
        analysis_data (dict): A dictionary containing the analysis results.
                              Expected keys: 'summary', 'arguments', 'inconsistencies', 'recommendations'.
                              These keys map to the sections described in the Gemini client prompt.

    Returns:
        str: The file path of the generated PDF report.

    Raises:
        Exception: If report generation fails.
    """
    # Ensure the directory for generated reports exists
    os.makedirs(GENERATED_REPORTS_PATH, exist_ok=True)

    report_filename = f"Analysis_Report_{case_id}_{original_filename.replace('.pdf', '')}.pdf"
    report_filepath = os.path.join(GENERATED_REPORTS_PATH, report_filename)

    logger.info(f"Starting PDF report generation for case {case_id} -> {report_filepath}")

    try:
        doc = SimpleDocTemplate(report_filepath, pagesize=letter,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)
        styles = getSampleStyleSheet()

        # Custom styles
        styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY))
        styles.add(ParagraphStyle(name='CenterBold', alignment=TA_CENTER, fontName='Helvetica-Bold', fontSize=14))
        styles.add(ParagraphStyle(name='SectionTitle', fontName='Helvetica-Bold', fontSize=12, spaceBefore=12, spaceAfter=6))
        styles.add(ParagraphStyle(name='NormalLeft', alignment=TA_LEFT))

        story = []

        # Title
        story.append(create_styled_paragraph("Political Case Analysis Report", 'CenterBold', styles))
        story.append(Spacer(1, 0.25 * 72)) # inch is not defined, use points: 72 points = 1 inch

        # Metadata Table
        meta_data = [
            ["Report ID:", case_id],
            ["Original Document:", original_filename],
            ["Analysis Date:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ]
        meta_table = Table(meta_data, colWidths=[1.5 * 72, 4.5 * 72]) # 1.5 inches, 4.5 inches
        meta_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'), # Bold for keys
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 0.25 * 72))


        # Introduction (README 7.1) - We can make this more dynamic if needed
        story.append(create_styled_paragraph("Introduction", 'SectionTitle', styles))
        intro_text = (
            f"This report contains the automated analysis of the political case document titled "
            f"'{original_filename}'. The analysis was performed using an advanced AI model to identify "
            f"key aspects, potential issues, and provide recommendations based on the text provided."
        )
        story.append(create_styled_paragraph(intro_text, 'Justify', styles))
        story.append(Spacer(1, 0.2 * 72))

        # Analysis Results (README 7.1)
        # These sections correspond to the expected output from the Gemini client's prompt
        sections = {
            "Summary": analysis_data.get("summary", "No summary provided by the AI."),
            "Key Arguments": analysis_data.get("arguments", "No key arguments identified by the AI."),
            "Potential Inconsistencies": analysis_data.get("inconsistencies", "No inconsistencies identified by the AI."),
            "Recommendations": analysis_data.get("recommendations", "No recommendations provided by the AI.")
        }

        for title, content in sections.items():
            story.append(create_styled_paragraph(title, 'SectionTitle', styles))
            # Handle content that might be a list of points or a single block of text
            if isinstance(content, list):
                for point in content:
                    story.append(create_styled_paragraph(f"• {point}", 'Justify', styles))
                    story.append(Spacer(1, 0.1 * 72))
            else:
                story.append(create_styled_paragraph(content, 'Justify', styles))
            story.append(Spacer(1, 0.2 * 72))

        # Conclusion (README 7.1)
        story.append(create_styled_paragraph("Conclusion", 'SectionTitle', styles))
        conclusion_text = (
            "This automated analysis is intended to provide insights based on the textual content of the document. "
            "It is recommended to cross-verify these findings with human expertise and other sources. "
            "The AI's interpretation is based on its training data and the provided text only."
        )
        story.append(create_styled_paragraph(conclusion_text, 'Justify', styles))
        story.append(Spacer(1, 0.2 * 72))

        story.append(create_styled_paragraph(f"End of Report - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal'])) # Use styles['Normal'] for default

        doc.build(story)
        logger.info(f"Successfully generated PDF report: {report_filepath}")
        return report_filepath

    except Exception as e:
        logger.error(f"Failed to generate PDF report for case {case_id}: {e}", exc_info=True)
        # Consider raising a specific ReportGenerationError if defined
        raise Exception(f"Report generation failed for {original_filename}: {e}")


if __name__ == '__main__':
    logger.info("Running report_generator.py directly for testing.")

    # Dummy data for testing
    test_case_id = "test_case_001"
    test_original_filename = "sample_document.pdf"
    # This structure should align with what Gemini client might parse from the AI's response.
    # For now, we assume the Gemini client will return a structured dict.
    # If Gemini returns a single block of text, the Gemini client will need to parse it into this structure.
    test_analysis_data = {
        "summary": "The AI provided a concise summary of the document, highlighting its main purpose and outcome.",
        "arguments": [
            "Argument A: The prosecution presented evidence regarding financial misconduct.",
            "Argument B: The defense argued lack of intent and pointed to procedural errors."
        ],
        "inconsistencies": "An inconsistency was noted between witness statement Alpha and witness statement Beta regarding the timeline of events.",
        "recommendations": [
            "Recommendation 1: Further investigate the discrepancy in witness testimonies.",
            "Recommendation 2: Review the procedural errors alleged by the defense."
        ]
    }

    # Ensure logs directory exists for fallback logger if run directly
    os.makedirs("logs", exist_ok=True)

    try:
        # Ensure GENERATED_REPORTS_PATH exists for the test
        if not os.path.exists(GENERATED_REPORTS_PATH):
            os.makedirs(GENERATED_REPORTS_PATH, exist_ok=True)
            logger.info(f"Created directory for test reports: {GENERATED_REPORTS_PATH}")

        report_file = generate_analysis_report(test_case_id, test_original_filename, test_analysis_data)
        print(f"Successfully generated test report: {report_file}")
        logger.info(f"Test report generation successful: {report_file}")

        # Basic check: file exists
        if os.path.exists(report_file):
            print(f"File {report_file} created. Size: {os.path.getsize(report_file)} bytes.")
        else:
            print(f"Error: File {report_file} was not created.")

    except Exception as e:
        print(f"Error during report generation test: {e}")
        logger.error(f"Report generation test failed: {e}", exc_info=True)
