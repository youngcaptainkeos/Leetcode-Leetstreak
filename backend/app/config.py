import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://codestreak:codestreak@localhost:5432/codestreak"
)
POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", "15"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
ADMIN_SECRET = os.getenv("ADMIN_SECRET", "codestreak_secret_admin_key_2026")
JWT_SECRET = os.getenv("JWT_SECRET", "codestreak_jwt_secret_key_super_safe_2026")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 90
