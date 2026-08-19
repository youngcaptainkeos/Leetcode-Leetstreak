import hashlib
import os
import secrets

def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with a unique salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100000
    )
    return f"{salt.hex()}:${key.hex()}"

def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored salt:key hash."""
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
    except Exception:
        return False
