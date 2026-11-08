"""API authorization regression checks against an isolated temporary database."""
import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, patch

_temporary = tempfile.TemporaryDirectory(prefix="leetstreak-access-tests-")
os.environ["DATABASE_URL"] = "sqlite:///" + _temporary.name + "/test.db"
os.environ["JWT_SECRET"] = "synthetic-unit-test-key-" + "x" * 40
os.environ["APP_ENV"] = "test"

from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.models import User, Group, GroupMember, Solve, Kudos
from app.auth import create_access_token, hash_password


class AccessTests(unittest.TestCase):
    def setUp(self):
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
        self.db = SessionLocal()
        for number in range(1, 4):
            self.db.add(User(id=number, name=f"Demo {number}", email=f"demo{number}@example.com", leetcode_username=f"demo_{number}", password_hash=hash_password("synthetic-password")))
        self.db.add(Group(id=1, name="Synthetic Group", code="STREAK-DEMO01", creator_id=1))
        self.db.add_all([GroupMember(group_id=1, user_id=1), GroupMember(group_id=1, user_id=2)])
        self.db.commit()
        # No lifespan context: tests never start provider jobs or startup backfills.
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.db.close()

    def headers(self, user_id=1):
        return {"Authorization": "Bearer " + create_access_token(user_id)}

    def test_anonymous_routes_fail_closed(self):
        requests = [
            ("get", "/api/users/1/dashboard", None),
            ("get", "/api/leaderboard", None),
            ("get", "/api/feed/recent-solves", None),
            ("get", "/api/users/1/recent-solves", None),
            ("get", "/api/users/1/codeforces-solves", None),
            ("get", "/api/groups/my-groups/1", None),
            ("get", "/api/groups/1/leaderboard", None),
            ("post", "/api/users/1/sync", None),
            ("put", "/api/users/1/settings", {"global_leaderboard_enabled": False}),
            ("put", "/api/users/1/leetcode-username", {"leetcode_username": "demo"}),
            ("put", "/api/users/1/codeforces-username", {"codeforces_username": "demo"}),
            ("post", "/api/users/1/delete-account", {"password": "synthetic-password"}),
            ("post", "/api/groups", {"user_id": 1, "name": "Demo"}),
            ("post", "/api/groups/join", {"user_id": 1, "code": "STREAK-DEMO01"}),
            ("delete", "/api/groups/1?requester_id=1", None),
            ("delete", "/api/groups/1/members/2?requester_id=1", None),
            ("post", "/api/kudos/2", {"from_user_id": 1}),
            ("post", "/api/kudos/kudos-all", {"from_user_id": 1, "target_user_ids": [2]}),
        ]
        for method, url, payload in requests:
            with self.subTest(method=method, url=url):
                response = self.client.request(method, url, json=payload)
                self.assertEqual(response.status_code, 401, response.text)

    def test_invalid_and_deleted_accounts_are_unauthorized(self):
        for token in ["!.!.!", "invalid", create_access_token(999)]:
            response = self.client.get("/api/users/1/dashboard", headers={"Authorization": "Bearer " + token})
            self.assertEqual(response.status_code, 401)

    def test_cross_account_operations_are_forbidden(self):
        requests = [
            ("post", "/api/users/2/sync", None),
            ("put", "/api/users/2/settings", {"global_leaderboard_enabled": False}),
            ("put", "/api/users/2/leetcode-username", {"leetcode_username": "demo"}),
            ("put", "/api/users/2/codeforces-username", {"codeforces_username": "demo"}),
            ("post", "/api/users/2/delete-account", {"password": "synthetic-password"}),
            ("get", "/api/groups/my-groups/2", None),
            ("get", "/api/friends/leaderboard?user_id=2", None),
            ("get", "/api/leaderboard?user_id=2", None),
            ("post", "/api/groups", {"user_id": 2, "name": "Demo"}),
            ("post", "/api/groups/join", {"user_id": 2, "code": "STREAK-DEMO01"}),
            ("post", "/api/kudos/3", {"from_user_id": 2}),
        ]
        for method, url, payload in requests:
            with self.subTest(url=url):
                response = self.client.request(method, url, json=payload, headers=self.headers())
                self.assertEqual(response.status_code, 403, response.text)

    def test_coding_profiles_are_viewable_without_private_fields(self):
        response = self.client.get("/api/users/2/dashboard", headers=self.headers())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], 2)
        self.assertTrue({"email", "password_hash", "reset_otp"}.isdisjoint(response.json()))

    def test_group_membership_and_owner_authority(self):
        self.assertEqual(self.client.get("/api/groups/1/leaderboard", headers=self.headers(3)).status_code, 403)
        self.assertEqual(self.client.get("/api/groups/1/leaderboard?user_id=2", headers=self.headers(2)).status_code, 200)
        self.assertEqual(self.client.delete("/api/groups/1?requester_id=1", headers=self.headers(2)).status_code, 403)
        self.assertEqual(self.client.delete("/api/groups/1?requester_id=2", headers=self.headers(2)).status_code, 403)
        self.assertEqual(self.client.delete("/api/groups/1/members/1?requester_id=1", headers=self.headers()).status_code, 409)
        self.assertEqual(self.client.delete("/api/groups/1/members/2?requester_id=2", headers=self.headers(2)).status_code, 200)
        self.assertEqual(self.client.get("/api/groups/1/leaderboard", headers=self.headers(2)).status_code, 403)

    def test_group_creation_is_atomic_and_self_owned(self):
        response = self.client.post("/api/groups", json={"name": "New Demo", "user_id": 3}, headers=self.headers(3))
        self.assertEqual(response.status_code, 200, response.text)
        group_id = response.json()["id"]
        self.assertEqual(response.json()["creator_id"], 3)
        self.assertIsNotNone(self.db.query(GroupMember).filter_by(group_id=group_id, user_id=3).first())

    def test_transfer_requires_owner_and_existing_member(self):
        url = "/api/groups/1/transfer"
        self.assertEqual(self.client.post(url, json={"new_owner_id": 2}).status_code, 401)
        self.assertEqual(self.client.post(url, json={"new_owner_id": 2}, headers=self.headers(2)).status_code, 403)
        self.assertEqual(self.client.post(url, json={"new_owner_id": 3}, headers=self.headers()).status_code, 400)
        self.assertEqual(self.client.post(url, json={"new_owner_id": 2}, headers=self.headers()).status_code, 200)
        self.assertEqual(self.client.delete("/api/groups/1/members/1?requester_id=1", headers=self.headers()).status_code, 200)
        self.assertEqual(self.client.delete("/api/groups/1?requester_id=2", headers=self.headers(2)).status_code, 200)

    def test_owner_must_resolve_groups_before_account_deletion(self):
        response = self.client.post("/api/users/1/delete-account", json={"password": "synthetic-password"}, headers=self.headers())
        self.assertEqual(response.status_code, 409)
        self.assertIsNotNone(self.db.query(User).filter_by(id=1).first())

    def test_authorized_mutation_and_no_provider_on_rejected_request(self):
        with patch("app.scheduler.poll_user", new=AsyncMock(return_value=2)) as poll:
            self.assertEqual(self.client.post("/api/users/2/sync", headers=self.headers()).status_code, 403)
            poll.assert_not_awaited()
            self.assertEqual(self.client.post("/api/users/1/sync", headers=self.headers()).json()["new_solves"], 2)
        response = self.client.put("/api/users/1/settings", headers=self.headers(), json={"global_leaderboard_enabled": False})
        self.assertEqual(response.status_code, 200)

    def test_kudos_and_query_limits(self):
        response = self.client.post("/api/kudos/kudos-all", headers=self.headers(), json={"from_user_id": 1, "target_user_ids": [2, 2]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.db.query(Kudos).count(), 1)
        for url in ["/api/feed/recent-solves?limit=-1", "/api/users/2/recent-solves?limit=10000"]:
            self.assertEqual(self.client.get(url, headers=self.headers()).status_code, 422)


if __name__ == "__main__":
    unittest.main()
