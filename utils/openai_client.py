import openai

try:
    from config import OPENAI_API_KEY
except ImportError:  # pragma: no cover - absent in repo
    from config_example import OPENAI_API_KEY
from utils.logger import logger

openai.api_key = OPENAI_API_KEY


def analyze_case_text(text: str) -> str:
    """Send text to OpenAI and return the response text."""
    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=text,
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].text.strip()
    except Exception as exc:  # pragma: no cover - network failure
        logger.error("OpenAI API call failed: %s", exc)
        raise
