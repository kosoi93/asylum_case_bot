# utils/errors.py

class TelegramCaseBotError(Exception):
    """Base class for exceptions in this application."""
    def __init__(self, message="An application error occurred", original_exception=None):
        super().__init__(message)
        self.original_exception = original_exception
        self.message = message

    def __str__(self):
        if self.original_exception:
            return f"{self.message}: {self.original_exception}"
        return self.message

if __name__ == '__main__':
    try:
        raise TelegramCaseBotError("This is a test of the base error class.")
    except TelegramCaseBotError as e:
        print(f"Caught expected error: {e}")

    try:
        raise TelegramCaseBotError("Base error with original exception", ValueError("Original value error"))
    except TelegramCaseBotError as e:
        print(f"Caught expected error with original: {e}")
