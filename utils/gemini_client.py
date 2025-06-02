# utils/gemini_client.py

import google.generativeai as genai
import os
import sys

# Add parent directory (project root) to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from config import GEMINI_API_KEY
    from exceptions import GeminiAPIError
    from utils.logger import logger
except ModuleNotFoundError as e:
    print(f"Error during initial import in gemini_client.py: {e}.")
    # Fallback definitions for direct execution or testing
    GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE" # Replace with a real key for direct testing if needed
    class GeminiAPIError(Exception): pass
    import logging
    logger = logging.getLogger("fallback_gemini_client")
    logger.warning("Using fallback logger and settings for Gemini Client due to import error.")

# Configure the generative AI client with the API key
if GEMINI_API_KEY and GEMINI_API_KEY != "YOUR_GEMINI_API_KEY_HERE":
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        logger.info("Google Generative AI client configured successfully.")
    except Exception as e:
        logger.error(f"Failed to configure Google Generative AI client: {e}", exc_info=True)
        # This error will likely manifest when trying to use the API, not at configure time
        # unless there's an immediate validation, which is not typical for just genai.configure.
else:
    logger.warning("GEMINI_API_KEY not found or is a placeholder. Gemini API calls will likely fail.")


# Default model to use if not specified
DEFAULT_MODEL_NAME = "gemini-pro" # Or "gemini-1.5-flash", "gemini-1.0-pro" etc.

def analyze_text_with_gemini(text_content: str, model_name: str = DEFAULT_MODEL_NAME) -> str:
    """
    Analyzes the given text content using the Google Gemini API.

    Args:
        text_content (str): The text to be analyzed.
        model_name (str): The name of the Gemini model to use.

    Returns:
        str: The analysis result from Gemini.

    Raises:
        GeminiAPIError: If there's an issue with the API call or configuration.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        logger.error("Gemini API key is not configured. Cannot analyze text.")
        raise GeminiAPIError("Gemini API key is not configured.")

    try:
        logger.info(f"Initializing Gemini model: {model_name}")
        model = genai.GenerativeModel(model_name)

        # For simplicity, we'll use a basic prompt.
        # This can be made more sophisticated based on "political case analysis" needs.
        # The prompt engineering is crucial for good results.
        prompt = (
            "Please analyze the following political case document. "
            "Identify key arguments, potential inconsistencies, and provide a brief summary and recommendations. "
            "Focus on factual analysis and avoid expressing personal opinions. "
            "Present the output clearly, perhaps with sections for Summary, Arguments, Inconsistencies, and Recommendations.\n\n"
            "Document Text:\n"
            f"{text_content}"
        )

        logger.info(f"Sending request to Gemini API with model {model_name}. Text length: {len(text_content)}")
        # The generate_content API can also stream responses using `stream=True`
        response = model.generate_content(prompt)

        # Accessing the text from the response parts
        # The response structure can vary. Ensure to handle cases where `response.text` might be empty
        # or if the content is split into multiple parts.
        if response.parts:
            analysis_result = "".join(part.text for part in response.parts if hasattr(part, 'text'))
        elif hasattr(response, 'text') and response.text:
             analysis_result = response.text
        else:
            # This case might occur if the response was blocked or had no content.
            # Check `response.prompt_feedback` for block reasons.
            logger.warning(f"Gemini API response has no text content. Prompt feedback: {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'N/A'}")
            raise GeminiAPIError("Gemini API returned an empty response or content was blocked.")

        logger.info(f"Successfully received analysis from Gemini. Result length: {len(analysis_result)}")
        return analysis_result

    except Exception as e:
        # Catching a broad exception here because various errors can occur:
        # - google.api_core.exceptions.GoogleAPIError (and its subclasses like PermissionDenied, InvalidArgument)
        # - ValueError (e.g. if API key is malformed during model interaction)
        # - RuntimeError, etc.
        logger.error(f"Error during Gemini API call with model {model_name}: {e}", exc_info=True)
        raise GeminiAPIError(f"Failed to get analysis from Gemini: {e}", original_exception=e)


if __name__ == '__main__':
    logger.info("Running gemini_client.py directly for testing.")

    # IMPORTANT: To run this test, you need a valid GEMINI_API_KEY set in your environment
    # or in the fallback GEMINI_API_KEY variable above.
    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        logger.warning("Cannot run __main__ test for gemini_client: GEMINI_API_KEY is not set.")
        print("\nTo test gemini_client.py directly, please set the GEMINI_API_KEY environment variable.")
        print("Example: export GEMINI_API_KEY='your_actual_api_key'")
    else:
        sample_case_text = (
            "Case Document: The People vs. John Doe\n"
            "Date: 2024-01-15\n"
            "Allegation: Public disturbance and resisting arrest.\n"
            "Prosecution Argument: Mr. Doe was found shouting loudly in a public park at 2 AM, violating noise ordinances. "
            "When approached by Officer Smith, Mr. Doe allegedly became aggressive and refused to comply with orders, leading to an arrest.\n"
            "Defense Argument: Mr. Doe claims he was having a heated but private phone conversation and did not realize his volume. "
            "He states he was startled by Officer Smith's approach and his reactions were misinterpreted as aggression. "
            "He denies resisting arrest, stating he was trying to understand the situation.\n"
            "Witness Statement (Ms. Jane Ray): Heard loud shouting from her apartment nearby. Could not discern words."
        )

        logger.info("Attempting to analyze sample text with Gemini...")
        try:
            # Using a generally available model, e.g., gemini-1.0-pro or gemini-1.5-flash
            # gemini-pro is a good default.
            # For the latest models, check Google's documentation.
            analysis = analyze_text_with_gemini(sample_case_text, model_name="gemini-1.0-pro")
            print("\n--- Gemini Analysis Result ---")
            print(analysis)
            print("--- End of Gemini Analysis ---")
            logger.info("Sample text analysis successful.")

        except GeminiAPIError as e:
            print(f"\nError during Gemini analysis test: {e}")
            logger.error(f"Gemini analysis test failed: {e}", exc_info=True)
        except Exception as e:
            print(f"\nAn unexpected error occurred during the test: {e}")
            logger.error(f"Unexpected error in gemini_client __main__: {e}", exc_info=True)
