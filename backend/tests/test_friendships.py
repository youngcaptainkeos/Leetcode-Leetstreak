"""Tests for direct friendships without shared groups (FEAT-10)."""
import unittest
from datetime import datetime, timezone
import test_access as fixtures
from app.models import User, Group, GroupMember, Friendship


class TestFriendships(unittest.TestCase):
    def setUp(self):
        self.access = fixtures.AccessTests()
        self.access.setUp()
        self.client = self.access.client
        self.db = self.access.db
        self.user1_id = 1
        self.user2_id = 2
        self.user3_id = 3

        # Update user 3 with known username and Codeforces handle
        user3 = self.db.query(User).filter(User.id == self.user3_id).one()
        user3.name = "Charlie Brown"
        user3.leetcode_username = "charlie_lc"
        user3.codeforces_username = "charlie_cf"
        user3.points = 25.0
        self.db.commit()

    def tearDown(self):
        self.access.tearDown()

    def test_search_users(self):
        # Search by name
        resp = self.client.get(
            "/api/users/search?q=Charlie",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], 3)
        self.assertEqual(data[0]["name"], "Charlie Brown")
        self.assertEqual(data[0]["leetcode_username"], "charlie_lc")
        self.assertEqual(data[0]["codeforces_username"], "charlie_cf")
        self.assertNotIn("email", data[0])
        self.assertNotIn("password_hash", data[0])

        # Search by handle
        resp_cf = self.client.get(
            "/api/users/search?q=charlie_cf",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(resp_cf.status_code, 200)
        self.assertEqual(len(resp_cf.json()), 1)

    def test_send_friend_request_to_self_fails(self):
        resp = self.client.post(
            f"/api/users/{self.user1_id}/friends/request",
            json={"target": str(self.user1_id)},
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("yourself", resp.json()["detail"])

    def test_send_and_accept_friend_request(self):
        # User 1 sends request to User 3
        resp = self.client.post(
            f"/api/users/{self.user1_id}/friends/request",
            json={"target": "charlie_lc"},
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "pending")

        # Duplicate request fails with 409
        dup_resp = self.client.post(
            f"/api/users/{self.user1_id}/friends/request",
            json={"target": "charlie_lc"},
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(dup_resp.status_code, 409)

        # User 3 views incoming requests
        u3_friends = self.client.get(
            "/api/users/3/friends",
            headers=self.access.headers(3),
        )
        self.assertEqual(u3_friends.status_code, 200)
        incoming = u3_friends.json()["incoming_requests"]
        self.assertEqual(len(incoming), 1)
        req_id = incoming[0]["id"]
        self.assertEqual(incoming[0]["user"]["id"], self.user1_id)

        # User 3 accepts
        accept_resp = self.client.post(
            f"/api/users/3/friends/{req_id}/accept",
            headers=self.access.headers(3),
        )
        self.assertEqual(accept_resp.status_code, 200)
        self.assertEqual(accept_resp.json()["status"], "accepted")

        # Now both see each other as friends
        u1_friends = self.client.get(
            f"/api/users/{self.user1_id}/friends",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(len(u1_friends.json()["friends"]), 1)
        self.assertEqual(u1_friends.json()["friends"][0]["id"], 3)

        u3_friends_after = self.client.get(
            "/api/users/3/friends",
            headers=self.access.headers(3),
        )
        self.assertEqual(len(u3_friends_after.json()["friends"]), 1)
        self.assertEqual(u3_friends_after.json()["friends"][0]["id"], self.user1_id)

    def test_crossed_friend_requests_auto_accept(self):
        # User 1 sends request to User 3
        self.client.post(
            f"/api/users/{self.user1_id}/friends/request",
            json={"target": "charlie_lc"},
            headers=self.access.headers(self.user1_id),
        )
        # User 3 sends request to User 1 (crossed)
        cross_resp = self.client.post(
            "/api/users/3/friends/request",
            json={"target": str(self.user1_id)},
            headers=self.access.headers(3),
        )
        self.assertEqual(cross_resp.status_code, 200)
        self.assertEqual(cross_resp.json()["status"], "accepted")

    def test_decline_and_cancel_friend_request(self):
        # User 1 sends request to User 3
        self.client.post(
            f"/api/users/{self.user1_id}/friends/request",
            json={"target": "charlie_lc"},
            headers=self.access.headers(self.user1_id),
        )

        u1_friends = self.client.get(
            f"/api/users/{self.user1_id}/friends",
            headers=self.access.headers(self.user1_id),
        )
        outgoing = u1_friends.json()["outgoing_requests"]
        self.assertEqual(len(outgoing), 1)
        req_id = outgoing[0]["id"]

        # User 1 cancels the request
        cancel_resp = self.client.post(
            f"/api/users/{self.user1_id}/friends/{req_id}/cancel",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(cancel_resp.status_code, 200)

        # Check list is empty
        u1_friends_after = self.client.get(
            f"/api/users/{self.user1_id}/friends",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(len(u1_friends_after.json()["outgoing_requests"]), 0)

    def test_remove_friend(self):
        # Establish friendship
        f = Friendship(user_id=self.user1_id, friend_id=3, status="accepted")
        self.db.add(f)
        self.db.commit()

        # User 1 removes User 3
        rem_resp = self.client.delete(
            f"/api/users/{self.user1_id}/friends/3",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(rem_resp.status_code, 200)
        self.assertEqual(rem_resp.json()["status"], "removed")

        # Verify no longer friends
        u1_friends = self.client.get(
            f"/api/users/{self.user1_id}/friends",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(len(u1_friends.json()["friends"]), 0)

    def test_friends_leaderboard_includes_direct_friends_without_groups(self):
        # User 1 and User 3 share NO groups (group 1 only has user 1 and user 2)
        u1_u3_groups = (
            self.db.query(GroupMember.group_id)
            .filter(GroupMember.user_id.in_([self.user1_id, 3]))
            .all()
        )
        # User 3 has no group memberships
        u3_groups = self.db.query(GroupMember).filter(GroupMember.user_id == 3).count()
        self.assertEqual(u3_groups, 0)

        # Before friendship, User 3 not on User 1's friends leaderboard
        lb_before = self.client.get(
            f"/api/friends/leaderboard?user_id={self.user1_id}",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(lb_before.status_code, 200)
        entry_ids_before = [e["id"] for e in lb_before.json()["entries"]]
        self.assertNotIn(3, entry_ids_before)

        # Create direct friendship
        f = Friendship(user_id=self.user1_id, friend_id=3, status="accepted")
        self.db.add(f)
        self.db.commit()

        # After direct friendship, User 3 appears on User 1's friends leaderboard!
        lb_after = self.client.get(
            f"/api/friends/leaderboard?user_id={self.user1_id}",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(lb_after.status_code, 200)
        entry_ids_after = [e["id"] for e in lb_after.json()["entries"]]
        self.assertIn(3, entry_ids_after)
        self.assertIn(self.user1_id, entry_ids_after)

    def test_shared_group_and_direct_friend_deduplicated(self):
        # User 1 and User 2 are direct friends
        f = Friendship(user_id=self.user1_id, friend_id=self.user2_id, status="accepted")
        self.db.add(f)
        self.db.commit()

        # They also already share Group 1
        lb = self.client.get(
            f"/api/friends/leaderboard?user_id={self.user1_id}",
            headers=self.access.headers(self.user1_id),
        )
        self.assertEqual(lb.status_code, 200)
        entries = lb.json()["entries"]
        user2_entries = [e for e in entries if e["id"] == self.user2_id]
        # Must be deduplicated (only appears once)
        self.assertEqual(len(user2_entries), 1)


if __name__ == "__main__":
    unittest.main()
