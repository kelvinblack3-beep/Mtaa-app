"""Password hashing, session tokens, and security helpers."""
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional

from passlib.context import CryptContext
from jose import jwt, JWTError

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def generate_session_token() -> str:
    """Cryptographically secure random session token."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Store only the hash of the session token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Optional JWT helper (primary auth uses server-side sessions)."""
    settings = get_settings()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(seconds=settings.session_max_age_seconds)
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_access_token(token: str) -> Optional[str]:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        return payload.get("sub")
    except JWTError:
        return None
