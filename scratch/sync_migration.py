import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.database import Base
from app.models import User, DailyActivity, Group, GroupMember, Solve, Kudos

src_url = "postgresql://codestreak:mZtFAWynPgUG5fA5GQGQrziIm2HtjmGG@dpg-da2ilirl550s73ecofdg-a.oregon-postgres.render.com/codestreak"
tgt_url = "postgresql://postgres.xrlbktiwdzcjuyakfmlp:!-jEyN-62iEypSe@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres"

print("Connecting to databases...")
src_engine = create_engine(src_url)
tgt_engine = create_engine(tgt_url)

SrcSession = sessionmaker(bind=src_engine)
TgtSession = sessionmaker(bind=tgt_engine)

src = SrcSession()
tgt = TgtSession()

print("Truncating target tables on Supabase...")
with tgt_engine.connect() as conn:
    conn.execute(text("TRUNCATE TABLE users, daily_activity, groups, group_members, solves, kudos CASCADE;"))
    conn.commit()

# Users
users = src.query(User).all()
print(f"Transferring {len(users)} Users...")
for u in users:
    tgt.add(User(
        id=u.id, name=u.name, leetcode_username=u.leetcode_username,
        email=u.email, password_hash=u.password_hash, reset_otp=u.reset_otp,
        otp_expires_at=u.otp_expires_at, avatar_url=u.avatar_url,
        easy_count=u.easy_count, medium_count=u.medium_count,
        hard_count=u.hard_count, official_streak=u.official_streak,
        created_at=u.created_at
    ))
tgt.commit()

# Daily Activities
acts = src.query(DailyActivity).all()
print(f"Transferring {len(acts)} Daily Activities...")
for a in acts:
    tgt.add(DailyActivity(
        id=a.id, user_id=a.user_id, date=a.date, problems_solved=a.problems_solved
    ))
tgt.commit()

# Groups
groups = src.query(Group).all()
print(f"Transferring {len(groups)} Groups...")
for g in groups:
    tgt.add(Group(
        id=g.id, name=g.name, code=g.code, creator_id=g.creator_id, created_at=g.created_at
    ))
tgt.commit()

# Members
members = src.query(GroupMember).all()
print(f"Transferring {len(members)} Group Members...")
for m in members:
    tgt.add(GroupMember(
        id=m.id, group_id=m.group_id, user_id=m.user_id, joined_at=m.joined_at
    ))
tgt.commit()

# Solves
solves = src.query(Solve).all()
print(f"Transferring {len(solves)} Solves...")
for s in solves:
    tgt.add(Solve(
        id=s.id, user_id=s.user_id, title_slug=s.title_slug, title=s.title, solved_at=s.solved_at
    ))
tgt.commit()

# Kudos
kudos = src.query(Kudos).all()
print(f"Transferring {len(kudos)} Kudos...")
for k in kudos:
    tgt.add(Kudos(
        id=k.id, from_user_id=k.from_user_id, to_user_id=k.to_user_id, created_at=k.created_at
    ))
tgt.commit()

# Sequences
print("Resetting auto-increment ID sequences...")
for table in ["users", "daily_activity", "groups", "group_members", "solves", "kudos"]:
    try:
        tgt.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(MAX(id), 1)) FROM {table};"))
        tgt.commit()
    except Exception as e:
        print(f"Seq note {table}: {e}")

print("🎉 PERFECT 1:1 MIGRATION COMPLETE!")
