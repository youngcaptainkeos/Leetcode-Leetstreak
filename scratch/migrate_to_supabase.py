import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add backend path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.database import Base
from app.models import User, DailyActivity, Group, GroupMember, Solve, Kudos


def run_migration(source_url: str, target_url: str):
    if target_url.startswith("postgres://"):
        target_url = target_url.replace("postgres://", "postgresql://", 1)
    if "?pgbouncer=true" in target_url:
        target_url = target_url.replace("?pgbouncer=true", "")

    print(f"📦 Source Database: {source_url}")
    print(f"⚡ Target Supabase Database: {target_url}")

    src_engine = create_engine(source_url)
    SrcSession = sessionmaker(bind=src_engine)
    src = SrcSession()

    tgt_engine = create_engine(target_url)
    TgtSession = sessionmaker(bind=tgt_engine)
    tgt = TgtSession()

    print("🧹 Resetting Supabase schema to match production...")
    Base.metadata.drop_all(bind=tgt_engine)
    Base.metadata.create_all(bind=tgt_engine)

    # 1. Users
    users = src.query(User).all()
    print(f"👥 Transferring {len(users)} Users...")
    for u in users:
        tgt.add(
            User(
                id=u.id,
                name=u.name,
                leetcode_username=u.leetcode_username,
                email=u.email,
                password_hash=u.password_hash,
                reset_otp=u.reset_otp,
                otp_expires_at=u.otp_expires_at,
                avatar_url=u.avatar_url,
                easy_count=u.easy_count,
                medium_count=u.medium_count,
                hard_count=u.hard_count,
                official_streak=u.official_streak,
                created_at=u.created_at,
            )
        )
    tgt.commit()

    # 2. Daily Activities
    activities = src.query(DailyActivity).all()
    print(f"📊 Transferring {len(activities)} Daily Activity records...")
    for a in activities:
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

    print("\n🎉 MIGRATION SUCCESSFUL! All 100% live production data copied to Supabase!")


if __name__ == "__main__":
    src_url = os.getenv("SOURCE_DATABASE_URL")
    tgt_url = os.getenv("TARGET_DATABASE_URL")

    if not src_url or not tgt_url:
        print("❌ Error: Both SOURCE_DATABASE_URL and TARGET_DATABASE_URL are required.")
        sys.exit(1)

    run_migration(src_url, tgt_url)
