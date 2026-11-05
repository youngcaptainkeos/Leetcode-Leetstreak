import os
import secrets
import logging
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://codestreak:codestreak@localhost:5432/codestreak"
)
POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", "15"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "codestreak_secret_admin_key_2026")


def load_jwt_secret() -> str:
    """Production must use an operator-managed, stable signing key."""
    secret = os.getenv("JWT_SECRET", "").strip()
    if secret:
        if len(secret.encode("utf-8")) < 32:
            raise RuntimeError("JWT_SECRET must contain at least 32 bytes.")
        return secret
    environment = os.getenv("APP_ENV", "production").strip().lower()
    if environment in {"development", "test"} and os.getenv("ALLOW_EPHEMERAL_JWT", "").lower() == "true":
        logging.getLogger("codestreak.config").warning(
            "Development-only temporary signing key enabled; restart invalidates sessions."
        )
        return secrets.token_urlsafe(48)
    raise RuntimeError("Set a stable JWT_SECRET before starting the application.")


JWT_SECRET = load_jwt_secret()
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 90
