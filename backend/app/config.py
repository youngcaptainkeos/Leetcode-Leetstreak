import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://codestreak:codestreak@localhost:5432/codestreak"
)
POLL_INTERVAL_MINUTES = int(os.getenv("POLL_INTERVAL_MINUTES", "15"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
