"""Account-private study plans. Client progress never grants points or streaks.

Writes apply one intent against a checked revision, rather than replacing a
device's stale snapshot. Assignment operations are safe to retry after a lost
response; recent operation IDs also suppress duplicates.
"""
import copy
import ipaddress
import json
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from .database import get_db
from .models import AccountProgress, User
from .security import current_user, require_self
from .recovery import consume_limit
from .timekeeping import utc_now

router = APIRouter(prefix="/api/users/{user_id}/progress", tags=["progress"])
STARTERS = {"strivers-a2z-dsa-sheet", "top-sql-50", "top-interview-150"}
SLUG = re.compile(r"[a-z0-9-]{1,200}\Z")


class ProgressWrite(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    base_version: int = Field(ge=0)
    operation_id: str = Field(min_length=16, max_length=80, pattern=r"^[a-zA-Z0-9-]+$")
    kind: str = Field(max_length=30)
    data: dict[str, Any] = Field(default_factory=dict)


def reject(message="Invalid study-plan data."):
    raise HTTPException(422, message)


def strings(value, maximum=20000):
    if not isinstance(value, list) or len(value) > maximum or any(not isinstance(s, str) or not SLUG.fullmatch(s) for s in value):
        reject()
    return list(dict.fromkeys(value))


def safe_url(value):
    if not isinstance(value, str) or len(value) > 1000 or any(ord(c) < 33 for c in value):
        reject("Use a public HTTPS question or plan link.")
    try:
        url = urlsplit(value)
        host = (url.hostname or "").lower()
        if url.scheme != "https" or not host or url.username or url.password or url.port not in (None, 443):
            reject()
        if host == "localhost" or host.endswith((".localhost", ".local", ".internal")) or "." not in host:
            reject()
        try:
            if not ipaddress.ip_address(host).is_global:
                reject()
        except ValueError:
            pass
    except ValueError:
        reject()
    return value


def plan_definition(value):
    if not isinstance(value, dict):
        reject()
    name, slug, groups = value.get("name"), value.get("slug"), value.get("planSubGroups")
    if not isinstance(name, str) or not name.strip() or len(name) > 150 or not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) or len(slug) > 100:
        reject()
    if not isinstance(groups, list) or not 1 <= len(groups) <= 200:
        reject()
    source = value.get("source", "leetcode")
    if source not in ("leetcode", "takeuforward", "codeforces", "external"):
        reject()
    result = {"name": name.strip(), "slug": slug, "source": source, "planSubGroups": []}
    if "sourceUrl" in value:
        result["sourceUrl"] = safe_url(value["sourceUrl"])
    if "snapshotDate" in value:
        if not isinstance(value["snapshotDate"], str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value["snapshotDate"]):
            reject()
        result["snapshotDate"] = value["snapshotDate"]
    seen, names, count = set(), set(), 0
    for group in groups:
        if not isinstance(group, dict):
            reject()
        group_name, questions = group.get("name"), group.get("questions")
        if not isinstance(group_name, str) or not group_name.strip() or len(group_name) > 150 or group_name in names or not isinstance(questions, list):
            reject()
        names.add(group_name)
        clean = []
        for question in questions:
            count += 1
            if count > 1000 or not isinstance(question, dict):
                reject("A plan can contain at most 1,000 questions.")
            title, question_slug = question.get("title"), question.get("titleSlug")
            if not isinstance(title, str) or not title.strip() or len(title) > 300 or not isinstance(question_slug, str) or not SLUG.fullmatch(question_slug):
                reject()
            difficulty = question.get("difficulty")
            if difficulty not in ("EASY", "MEDIUM", "HARD", "BASIC", "CORE", "PRO", "LESSON", "PRACTICE"):
                reject()
            q = {"title": title, "titleSlug": question_slug, "difficulty": difficulty}
            if "url" in question:
                q["url"] = safe_url(question["url"])
            elif source != "leetcode":
                reject()
            if "leetcodeSlug" in question:
                q["leetcodeSlug"] = strings([question["leetcodeSlug"]])[0]
            if "kind" in question:
                if question["kind"] not in ("learning", "practice"):
                    reject()
                q["kind"] = question["kind"]
            if question_slug not in seen:
                seen.add(question_slug)
                clean.append(q)
        if clean:
            result["planSubGroups"].append({"name": group_name, "questions": clean})
    if not result["planSubGroups"]:
        reject("The plan must contain questions.")
    return result


def empty_document():
    return {"initialized": False, "customPlans": [], "hiddenPlans": [], "followed": [], "manual": [], "observed": [], "lastFullSyncAt": None, "defaultsVersion": 2, "leetcodeHandle": "", "leetcodeVersion": -1, "receipts": []}


def for_account(document, user):
    document = copy.deepcopy(document or empty_document())
    if document.get("leetcodeHandle", "").lower() != user.leetcode_username.lower() or document.get("leetcodeVersion") != user.leetcode_account_version:
        document.update(observed=[], lastFullSyncAt=None, leetcodeHandle=user.leetcode_username, leetcodeVersion=user.leetcode_account_version)
    return document


def response(row, user):
    document = for_account(row.document if row else None, user)
    initialized = document.pop("initialized")
    document.pop("receipts", None)
    return {"version": row.version if row else 0, "initialized": initialized, "state": document}


def apply_operation(document, request, user):
    data, kind = request.data, request.kind
    if len(json.dumps(data).encode()) > 2_000_000:
        raise HTTPException(413, "Plan data is too large.")
    if kind == "initialize":
        if document["initialized"]:
            return
        plans = data.get("customPlans", [])
        if not isinstance(plans, list) or len(plans) > 50:
            reject("Keep at most 50 custom plans.")
        by_slug = {p["slug"]: p for p in map(plan_definition, plans) if p["slug"] not in STARTERS}
        document["customPlans"] = list(by_slug.values())
        document["hiddenPlans"] = strings(data.get("hiddenPlans", []), 1000)
        document["followed"] = strings(data.get("followed", []), 1000)
        document["manual"] = strings(data.get("manual", []))
        # Old caches have no account-generation proof. Automatic provider sync
        # will repopulate completion; importing plans never imports score proof.
    elif kind == "add":
        plan = plan_definition(data.get("plan"))
        slug = plan["slug"]
        document["customPlans"] = [p for p in document["customPlans"] if p["slug"] != slug]
        if slug not in STARTERS:
            document["customPlans"].append(plan)
        document["hiddenPlans"] = [s for s in document["hiddenPlans"] if s != slug]
        document["followed"] = list(dict.fromkeys([*document["followed"], slug]))
    elif kind == "remove":
        slug = strings([data.get("slug")])[0]
        document["customPlans"] = [p for p in document["customPlans"] if p["slug"] != slug]
        # Keep tombstones for custom plans too; another device's old cache must
        # not silently import a removed library entry again.
        document["hiddenPlans"] = list(dict.fromkeys([*document["hiddenPlans"], slug]))
        document["followed"] = [s for s in document["followed"] if s != slug]
    elif kind in ("follow", "manual"):
        slug = strings([data.get("slug")])[0]
        if type(data.get("enabled")) is not bool:
            reject()
        if kind == "follow":
            available = STARTERS | {p["slug"] for p in document["customPlans"]}
            if slug not in available or slug in document["hiddenPlans"]:
                raise HTTPException(409, "This plan was removed. Add it again before following it.")
        field = "followed" if kind == "follow" else "manual"
        document[field] = [s for s in document[field] if s != slug]
        if data["enabled"]:
            document[field].append(slug)
    elif kind == "restore":
        document["hiddenPlans"] = [s for s in document["hiddenPlans"] if s not in STARTERS]
    elif kind == "observe":
        if not isinstance(data.get("handle"), str) or data["handle"].lower() != user.leetcode_username.lower() or type(data.get("accountVersion")) is not int or data["accountVersion"] != user.leetcode_account_version:
            raise HTTPException(409, "The linked LeetCode account changed. Reopen Progress.")
        document["observed"] = list(dict.fromkeys([*document["observed"], *strings(data.get("slugs", []))]))
        stamp = data.get("syncedAt")
        now_ms = datetime.now(timezone.utc).timestamp() * 1000
        if stamp is not None and (type(stamp) not in (int, float) or not 0 < stamp <= now_ms + 300000):
            reject()
        if stamp:
            document["lastFullSyncAt"] = max(document.get("lastFullSyncAt") or 0, stamp)
    else:
        reject("Unknown progress operation.")
    if len(document["customPlans"]) > 50 or len(document["manual"]) > 20000 or len(document["observed"]) > 20000 or len(document["hiddenPlans"]) > 1000 or len(json.dumps(document).encode()) > 2_000_000:
        raise HTTPException(413, "Your saved plan library is too large.")
    document["initialized"] = True


@router.get("")
def get_progress(user_id: int, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, user_id)
    return response(db.get(AccountProgress, user_id), actor)


@router.post("")
def write_progress(user_id: int, request: ProgressWrite, db: Session = Depends(get_db), actor: User = Depends(current_user)):
    require_self(actor, user_id)
    consume_limit(db, "progress-write", str(user_id), 120, 900)
    # Lock the account before initialization as well as ordinary edits. The CAS
    # below additionally protects SQLite and rejects stale device snapshots.
    user = db.query(User).filter_by(id=user_id).populate_existing().with_for_update().one_or_none()
    if user is None:
        raise HTTPException(401, "Please sign in again.")
    insert = pg_insert if db.bind.dialect.name == "postgresql" else sqlite_insert
    db.execute(insert(AccountProgress).values(user_id=user_id, version=0, document=empty_document(), updated_at=utc_now()).on_conflict_do_nothing(index_elements=["user_id"]))
    row = db.query(AccountProgress).filter_by(user_id=user_id).populate_existing().one()
    document = for_account(row.document, user)
    if request.operation_id in document.get("receipts", []):
        return response(row, user)
    if request.base_version != row.version:
        raise HTTPException(409, "Progress changed on another device. Refresh and retry this change.")
    apply_operation(document, request, user)
    document["receipts"] = [*document.get("receipts", []), request.operation_id][-256:]
    changed = db.execute(update(AccountProgress).where(AccountProgress.user_id == user_id, AccountProgress.version == request.base_version).values(document=document, version=request.base_version + 1, updated_at=utc_now()), execution_options={"synchronize_session": False})
    if changed.rowcount != 1:
        db.rollback()
        raise HTTPException(409, "Progress changed on another device. Refresh and retry this change.")
    db.commit()
    db.expire_all()
    return response(db.get(AccountProgress, user_id), user)
