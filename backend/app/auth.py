import base64
import hashlib
import hmac
import json
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

from .config import JWT_SECRET, JWT_EXPIRATION_DAYS

logger = logging.getLogger("codestreak.auth")


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a unique salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    return f"{salt.hex()}${key.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored salt$key hash."""
    if not stored_hash or '$' not in stored_hash:
        return False
    try:
        salt_hex, key_hex = stored_hash.split('$', 1)
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)
        actual_key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        return secrets.compare_digest(expected_key, actual_key)
    except Exception as e:
        logger.error("Verify password error: %s", e)
        return False


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')


def _base64url_decode(data_str: str) -> bytes:
    padding = '=' * (4 - (len(data_str) % 4))
    return base64.urlsafe_b64decode(data_str + padding)


def create_access_token(user_id: int) -> str:
    """Create a signed JWT access token for user_id."""
    header = {"alg": "HS256", "typ": "JWT"}
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=JWT_EXPIRATION_DAYS)
    payload = {
        "sub": str(user_id),
        "user_id": user_id,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp())
    }

    header_bytes = json.dumps(header, separators=(',', ':')).encode('utf-8')
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')

    unsigned_token = f"{_base64url_encode(header_bytes)}.{_base64url_encode(payload_bytes)}"
    signature = hmac.new(JWT_SECRET.encode('utf-8'), unsigned_token.encode('utf-8'), hashlib.sha256).digest()
    return f"{unsigned_token}.{_base64url_encode(signature)}"


def decode_access_token(token: str) -> dict:
    """Decode and verify JWT access token."""
    parts = token.split('.')
    if len(parts) != 3:
        raise ValueError("Invalid token format")

    unsigned_token = f"{parts[0]}.{parts[1]}"
    signature = _base64url_decode(parts[2])
    expected_signature = hmac.new(JWT_SECRET.encode('utf-8'), unsigned_token.encode('utf-8'), hashlib.sha256).digest()

    if not secrets.compare_digest(signature, expected_signature):
        raise ValueError("Invalid token signature")

    payload_bytes = _base64url_decode(parts[1])
    payload = json.loads(payload_bytes.decode('utf-8'))

    if payload.get("exp") and int(datetime.now(timezone.utc).timestamp()) > payload["exp"]:
        raise ValueError("Token expired")

    return payload
