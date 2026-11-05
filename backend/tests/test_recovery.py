from datetime import timedelta
import unittest
from unittest.mock import AsyncMock, patch

from sqlalchemy import create_engine, text, inspect
import tempfile

import test_access as fixtures
from app import main
from app.auth import create_access_token, hash_password
from app.email_service import DeliveryResult
from app.models import User, AuthLimit
from app.migrations import migrate_auth
from app.recovery import utcnow

NEW_PASSWORD = "a fictional long passphrase"


class RecoveryTests(unittest.TestCase):
    setUp = fixtures.AccessTests.setUp
    tearDown = fixtures.AccessTests.tearDown
    headers = fixtures.AccessTests.headers

    def initiate(self, identifier="demo1@example.com", accepted=True):
        sender = AsyncMock(return_value=DeliveryResult("accepted" if accepted else "failed", "synthetic"))
        with patch.object(main, "send_otp_email", new=sender):
            response = self.client.post("/api/users/forgot-password/initiate", json={"email_or_username": identifier})
        code = sender.call_args.args[2] if sender.call_args else None
        return response, code

    def verify(self, code, identifier="demo1@example.com", password=NEW_PASSWORD):
        return self.client.post("/api/users/forgot-password/verify", json={"email_or_username": identifier, "otp": code, "new_password": password})

    def test_initiation_is_generic_and_code_is_not_plaintext(self):
        known, code = self.initiate()
        unknown, _ = self.initiate("missing@example.com")
        self.assertEqual(known.status_code, 200)
        self.assertEqual(known.json(), unknown.json())
        self.assertNotIn("email", known.json())
        self.db.expire_all()
        user = self.db.query(User).filter_by(id=1).one()
        self.assertIsNone(user.reset_otp)
        self.assertNotEqual(user.reset_otp_hash, code)
        self.assertEqual(len(user.reset_otp_hash), 64)
        self.assertTrue(all("example.com" not in row.bucket_key for row in self.db.query(AuthLimit).all()))

    def test_success_is_single_use_and_revokes_old_sessions(self):
        old = self.headers()
        _, code = self.initiate()
        self.assertEqual(self.verify(code).status_code, 200)
        self.assertEqual(self.verify(code).status_code, 400)
        self.assertEqual(self.client.get("/api/users/1/dashboard", headers=old).status_code, 401)
        login = self.client.post("/api/users/login", json={"leetcode_username": "demo1@example.com", "password": NEW_PASSWORD})
        self.assertEqual(login.status_code, 200)
        new = {"Authorization": "Bearer " + login.json()["access_token"]}
        self.assertEqual(self.client.get("/api/users/1/dashboard", headers=new).status_code, 200)

    def test_attempt_exhaustion_and_persisted_rate_limits(self):
        _, code = self.initiate()
        wrong = "000000" if code != "000000" else "999999"
        for _ in range(5):
            self.assertEqual(self.verify(wrong).status_code, 400)
        self.assertEqual(self.verify(code).status_code, 400)
        for _ in range(4):
            self.verify(wrong)
        self.assertEqual(self.verify(wrong).status_code, 429)

    def test_resend_invalidates_old_code_and_cooldown_does_not_send(self):
        _, old = self.initiate()
        second, no_code = self.initiate()
        self.assertEqual(second.status_code, 200)
        self.assertIsNone(no_code)
        user = self.db.query(User).filter_by(id=1).one()
        user.otp_last_requested_at = utcnow() - timedelta(seconds=61)
        self.db.commit()
        with patch.object(main.secrets, "choice", return_value="9" if old != "999999" else "8"):
            _, new = self.initiate()
        self.assertNotEqual(old, new)
        self.assertEqual(self.verify(old).status_code, 400)
        self.assertEqual(self.verify(new).status_code, 200)
        self.assertEqual(self.initiate()[0].status_code, 429)

    def test_expired_code_and_failed_delivery_are_unusable(self):
        _, code = self.initiate()
        user = self.db.query(User).filter_by(id=1).one()
        user.otp_expires_at = utcnow() - timedelta(seconds=1)
        user.otp_last_requested_at = utcnow() - timedelta(seconds=61)
        self.db.commit()
        self.assertEqual(self.verify(code).status_code, 400)
        _, failed_code = self.initiate(accepted=False)
        self.assertEqual(self.verify(failed_code).status_code, 400)

    def test_ambiguous_handle_cannot_reset_arbitrary_user(self):
        self.db.query(User).filter_by(id=2).update({User.leetcode_username: "demo_1"})
        self.db.commit()
        response, code = self.initiate("demo_1")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(code)
        self.assertIsNotNone(self.initiate("demo1@example.com")[1])

    def test_password_policy_preserves_legacy_login(self):
        self.db.query(User).filter_by(id=1).update({User.password_hash: hash_password("old")})
        self.db.commit()
        self.assertEqual(self.client.post("/api/users/login", json={"leetcode_username": "demo1@example.com", "password": "old"}).status_code, 200)
        _, code = self.initiate()
        self.assertEqual(self.verify(code, password="short").status_code, 422)
        self.assertEqual(self.verify(code, password="passwordpassword").status_code, 422)

    def test_authenticated_password_change_and_revoke_sessions(self):
        old = self.headers()
        body = {"current_password": "synthetic-password", "new_password": NEW_PASSWORD}
        self.assertEqual(self.client.post("/api/users/2/change-password", json=body, headers=old).status_code, 403)
        change = self.client.post("/api/users/1/change-password", json=body, headers=old)
        self.assertEqual(change.status_code, 200)
        self.assertEqual(self.client.get("/api/users/1/dashboard", headers=old).status_code, 401)
        new = {"Authorization": "Bearer " + change.json()["access_token"]}
        self.assertEqual(self.client.post("/api/users/1/revoke-sessions", headers=new).status_code, 200)
        self.assertEqual(self.client.get("/api/users/1/dashboard", headers=new).status_code, 401)


class MigrationTests(unittest.TestCase):
    def test_additive_auth_migration_is_repeatable_and_preserves_history(self):
        with tempfile.TemporaryDirectory(prefix="leetstreak-migration-test-") as directory:
            engine = create_engine("sqlite:///" + directory + "/old.db")
            with engine.begin() as connection:
                connection.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, reset_otp VARCHAR(6), otp_expires_at TIMESTAMP, points FLOAT)"))
                connection.execute(text("INSERT INTO users (id, reset_otp, points) VALUES (1, '123456', 42.5)"))
            migrate_auth(engine)
            migrate_auth(engine)
            with engine.connect() as connection:
                row = connection.execute(text("SELECT points, session_version, reset_otp FROM users WHERE id=1")).one()
                self.assertEqual(tuple(row), (42.5, 0, None))
                self.assertEqual(connection.execute(text("SELECT COUNT(*) FROM schema_migrations")).scalar(), 1)
            engine.dispose()
