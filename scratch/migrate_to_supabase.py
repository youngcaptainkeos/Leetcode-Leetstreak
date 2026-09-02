import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add backend path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.database import Base
from app.models import User, DailyActivity, Group, GroupMember, Solve, Kudos


def run_migration(source_url: str, target_url: str):
    # Ensure postgresql:// scheme
    if target_url.startswith("postgres://"):
        target_url = target_url.replace("postgres://", "postgresql://", 1)

    print(f"📦 Source Database: {source_url}")
    print(f"⚡ Target Supabase Database: {target_url}")

    src_engine = create_engine(source_url)
    SrcSession = sessionmaker(bind=src_engine)
    src = SrcSession()

    tgt_engine = create_engine(target_url)
    TgtSession = sessionmaker(bind=tgt_engine)
    tgt = TgtSession()

    print("🚀 Initializing schema tables on Supabase...")
    Base.metadata.create_all(bind=tgt_engine)

    # 1. Users
    users = src.query(User).all()
    print(f"👥 Transferring {len(users)} Users...")
    for u in users:
        if not tgt.query(User).filter(User.id == u.id).first():
            tgt.add(
                User(
                    id=u.id,
                    name=u.name,
                    leetcode_username=u.leetcode_username,
                    email=u.email,
                    password_hash=u.password_hash,
                    avatar_url=u.avatar_url,
                    easy_count=u.easy_count,
                    medium_count=u.medium_count,
                    hard_count=u.hard_count,
                    created_at=u.created_at,
                )
            )
    tgt.commit()

    # 2. Daily Activities
    activities = src.query(DailyActivity).all()
    print(f"📊 Transferring {len(activities)} Daily Activity records...")
    for a in activities:
        if not tgt.query(DailyActivity).filter(DailyActivity.id == a.id).first():
            tgt.add(
                DailyActivity(
                    id=a.id,
                    user_id=a.user_id,
                    date=a.date,
                    problems_solved=a.problems_solved,
                )
            )
    tgt.commit()

    # 3. Groups
    groups = src.query(Group).all()
    print(f"👥 Transferring {len(groups)} Groups...")
    for g in groups:
        if not tgt.query(Group).filter(Group.id == g.id).first():
            tgt.add(
                Group(
                    id=g.id,
                    name=g.name,
                    code=g.code,
                    creator_id=g.creator_id,
                    created_at=g.created_at,
                )
            )
    tgt.commit()

    # 4. Group Members
    members = src.query(GroupMember).all()
    print(f"👤 Transferring {len(members)} Group Members...")
    for m in members:
        if not tgt.query(GroupMember).filter(GroupMember.id == m.id).first():
            tgt.add(
                GroupMember(
                    id=m.id,
                    group_id=m.group_id,
                    user_id=m.user_id,
                    joined_at=m.joined_at,
                )
            )
    tgt.commit()

    # 5. Solves
    solves = src.query(Solve).all()
    print(f"🔥 Transferring {len(solves)} Solve records...")
    for s in solves:
        if not tgt.query(Solve).filter(Solve.id == s.id).first():
            tgt.add(
                Solve(
                    id=s.id,
                    user_id=s.user_id,
                    title_slug=s.title_slug,
                    title=s.title,
                    solved_at=s.solved_at,
                )
            )
    tgt.commit()

    # 6. Kudos
    kudos = src.query(Kudos).all()
    print(f"👏 Transferring {len(kudos)} Kudos records...")
    for k in kudos:
        if not tgt.query(Kudos).filter(Kudos.id == k.id).first():
            tgt.add(
                Kudos(
                    id=k.id,
                    from_user_id=k.from_user_id,
                    to_user_id=k.to_user_id,
                    created_at=k.created_at,
                )
            )
    tgt.commit()

    # Reset Postgres ID sequences
    print("🔄 Resetting Postgres auto-increment ID sequences...")
    for table in ["users", "daily_activity", "groups", "group_members", "solves", "kudos"]:
        try:
            tgt.execute(text(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(MAX(id), 1)) FROM {table};"))
            tgt.commit()
        except Exception as err:
            print(f"Note on sequence reset for {table}: {err}")

    print("\n🎉 MIGRATION SUCCESSFUL! All data has been copied to Supabase!")


if __name__ == "__main__":
    src_url = os.getenv("SOURCE_DATABASE_URL", "sqlite:///codestreak.db")
    tgt_url = os.getenv("TARGET_DATABASE_URL")

    if not tgt_url:
        print("❌ Error: TARGET_DATABASE_URL environment variable is required.")
        print("Usage: TARGET_DATABASE_URL='postgresql://postgres:[password]@db.xxx.supabase.co:5432/postgres' python scratch/migrate_to_supabase.py")
        sys.exit(1)

    run_migration(src_url, tgt_url)
