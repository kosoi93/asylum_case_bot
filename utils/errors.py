class BotError(Exception):
    """Base class for bot-related errors."""


class PDFProcessingError(BotError):
    pass


class OpenAIAPIError(BotError):
    pass
