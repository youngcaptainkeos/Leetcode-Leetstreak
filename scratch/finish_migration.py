import os
import sys
import sqlalchemy
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.database import Base
from app.models import User, DailyActivity, Group, GroupMember, Solve, Kudos

src_url = "postgresql://codestreak:mZtFAWynPgUG5fA5GQGQrziIm2HtjmGG@dpg-da2ilirl550s73ecofdg-a.oregon-postgres.render.com/codestreak"
tgt_url = "postgresql://postgres.xrlbktiwdzcjuyakfmlp:!-jEyN-62iEypSe@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres"

src = sessionmaker(bind=sqlalchemy.create_engine(src_url))()
tgt = sessionmaker(bind=sqlalchemy.create_engine(tgt_url))()

# 1. Groups
groups = src.query(Group).all()
print(f"👥 Syncing {len(groups)} Groups...")
for g in groups:
    if not tgt.query(Group).filter(Group.id == g.id).first():
        try:
            tgt.add(Group(id=g.id, name=g.name, code=g.code, creator_id=g.creator_id, created_at=g.created_at))
            tgt.commit()
        except Exception as e:
            tgt.rollback()

# 2. Members
members = src.query(GroupMember).all()
print(f"👤 Syncing {len(members)} Group Members...")
for m in members:
    if not tgt.query(GroupMember).filter(GroupMember.id == m.id).first():
        try:
            tgt.add(GroupMember(id=m.id, group_id=m.group_id, user_id=m.user_id, joined_at=m.joined_at))
            tgt.commit()
        except Exception as e:
            tgt.rollback()

# 3. Solves
solves = src.query(Solve).all()
print(f"🔥 Syncing {len(solves)} Solves...")
for s in solves:
    if not tgt.query(Solve).filter(Solve.id == s.id).first():
        try:
            tgt.add(Solve(id=s.id, user_id=s.user_id, title_slug=s.title_slug, title=s.title, solved_at=s.solved_at))
            tgt.commit()
        except Exception as e:
            tgt.rollback()

# 4. Kudos
kudos = src.query(Kudos).all()
print(f"👏 Syncing {len(kudos)} Kudos...")
for k in kudos:
    if not tgt.query(Kudos).filter(Kudos.id == k.id).first():
        try:
            tgt.add(Kudos(id=k.id, from_user_id=k.from_user_id, to_user_id=k.to_user_id, created_at=k.created_at))
            tgt.commit()
        except Exception as e:
            tgt.rollback()

# Reset sequences
for table in ["users", "daily_activity", "groups", "group_members", "solves", "kudos"]:
    try:
        tgt.execute(sqlalchemy.text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(MAX(id), 1)) FROM {table};"))
        tgt.commit()
    except Exception as e:
        print(f"Seq note {table}: {e}")

print("🎉 FINISH MIGRATION COMPLETE!")
