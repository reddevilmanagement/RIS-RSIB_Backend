"""
Security utilities — password hashing, JWT token management, and token blacklist.

Token structure:
  access token  → short-lived (30 min), carries sub + role + jti
  refresh token → long-lived  (7 days),  carries sub + jti only
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ─── Password Hashing ─────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ─── In-memory token blacklist (refresh tokens) ───────────────────────
# Production: replace with Redis SET with TTL matching token expiry.
_blacklisted_jtis: set[str] = set()


def blacklist_token(jti: str) -> None:
    """Add a token JTI to the blacklist (logout)."""
    _blacklisted_jtis.add(jti)


def is_token_blacklisted(jti: str) -> bool:
    """Check whether a token JTI has been revoked."""
    return jti in _blacklisted_jtis


# ─── JWT Tokens ───────────────────────────────────────────────────────
def create_access_token(
    subject: Any,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.

    Payload claims:
      sub  — user ID (str)
      role — UserRole value
      jti  — unique token ID (for future revocation)
      type — "access"
      exp  — expiry timestamp
      iat  — issued-at timestamp
    """
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {
        "sub":  str(subject),
        "role": role,
        "jti":  str(uuid.uuid4()),
        "type": "access",
        "iat":  now,
        "exp":  expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: Any) -> tuple[str, str]:
    """
    Create a signed JWT refresh token.

    Returns:
        (encoded_token, jti) — caller stores jti to enable revocation.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    jti = str(uuid.uuid4())
    payload = {
        "sub":  str(subject),
        "jti":  jti,
        "type": "refresh",
        "iat":  now,
        "exp":  expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM), jti


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT token.

    Returns the payload dict on success, None on any failure
    (expired, invalid signature, malformed).
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        return None
