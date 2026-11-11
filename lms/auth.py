"""Password hashing and credential validation (standard library only)."""
import hashlib
import hmac
import re
import secrets

from . import config

_ALGO = "pbkdf2_sha256"
_ITERATIONS = 600_000

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PASSWORD_RULES = "At least 8 characters, with an uppercase letter, a number and a special character."


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _ITERATIONS).hex()
    return f"{_ALGO}${_ITERATIONS}${salt}${digest}"


def is_hashed(stored: str) -> bool:
    return bool(stored) and stored.startswith(_ALGO + "$")


def verify_password(password: str, stored: str) -> bool:
    """Check a password against a stored hash.

    Rows created by the original prototype hold plaintext passwords; those are
    compared directly so existing learners can still sign in (and are rehashed
    by the caller on success).
    """
    if not stored:
        return False
    if not is_hashed(stored):
        return hmac.compare_digest(password.encode(), stored.encode())
    try:
        _, iterations, salt, digest = stored.split("$")
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(iterations)).hex()
    except ValueError:
        return False
    return hmac.compare_digest(candidate, digest)


def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email or ""))


def is_valid_password(password: str) -> bool:
    password = password or ""
    return (
        len(password) >= 8
        and re.search(r"[A-Z]", password) is not None
        and re.search(r"[0-9]", password) is not None
        and re.search(r"[^A-Za-z0-9]", password) is not None
    )


def admin_configured() -> bool:
    return bool(config.get_secret("ADMIN_PASSWORD"))


def check_admin_password(password: str) -> bool:
    expected = config.get_secret("ADMIN_PASSWORD")
    if not expected or not password:
        return False
    return hmac.compare_digest(password.encode(), str(expected).encode())
