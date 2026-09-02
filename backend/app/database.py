from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

db_url = DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Strip invalid psycopg2 query options like ?pgbouncer=true
if "?pgbouncer=true" in db_url:
    db_url = db_url.replace("?pgbouncer=true", "")
elif "&pgbouncer=true" in db_url:
    db_url = db_url.replace("&pgbouncer=true", "")

engine = create_engine(db_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
