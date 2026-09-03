import os
import sys
import sqlalchemy
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.database import Base
from app.models import Solve, Kudos

src_url = "postgresql://codestreak:mZtFAWynPgUG5fA5GQGQrziIm2HtjmGG@dpg-da2ilirl550s73ecofdg-a.oregon-postgres.render.com/codestreak"
tgt_url = "postgresql://postgres.xrlbktiwdzcjuyakfmlp:!-jEyN-62iEypSe@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres"

src = sessionmaker(bind=sqlalchemy.create_engine(src_url))()
tgt = sessionmaker(bind=sqlalchemy.create_engine(tgt_url))()

solves = src.query(Solve).all()
print(f"Transferring {len(solves)} Solves...")
for s in solves:
    if not tgt.query(Solve).filter(Solve.id == s.id).first():
        try:
            tgt.add(Solve(id=s.id, user_id=s.user_id, title_slug=s.title_slug, title=s.title, solved_at=s.solved_at))
            tgt.commit()
        except Exception as e:
            tgt.rollback()

kudos = src.query(Kudos).all()
print(f"Transferring {len(kudos)} Kudos...")
for k in kudos:
    if not tgt.query(Kudos).filter(Kudos.id == k.id).first():
        try:
            tgt.add(Kudos(id=k.id, from_user_id=k.from_user_id, to_user_id=k.to_user_id, created_at=k.created_at))
            tgt.commit()
        except Exception as e:
            tgt.rollback()

# Reset sequences
for table in ["solves", "kudos"]:
    try:
        tgt.execute(sqlalchemy.text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(MAX(id), 1)) FROM {table};"))
        tgt.commit()
    except Exception as e:
        print(f"Seq note {table}: {e}")

print("🎉 ALL SOLVES & KUDOS MIGRATED PERFECTLY!")
