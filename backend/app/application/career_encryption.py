"""Keep private Career text out of database statements and error logs."""
from cryptography.fernet import Fernet, InvalidToken

from app.application.errors import ExternalServiceError
from app.core.config import settings


def career_cipher(*, scope: str = "Interview transcript") -> Fernet:
    key = settings.CAREER_TRANSCRIPT_KEY
    if key:
        try:
            return Fernet(key.get_secret_value())
        except ValueError:
            pass
    raise ExternalServiceError(f"{scope} storage is unavailable")


def open_private_text(cipher: Fernet, ciphertext: str) -> str:
    try:
        return cipher.decrypt(ciphertext).decode("utf-8")
    except (InvalidToken, UnicodeError):
        raise ExternalServiceError("Private Career content could not be opened") from None
