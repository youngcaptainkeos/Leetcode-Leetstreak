"""Synthetic-only authentication checks; no server, database, or provider calls."""
import base64
import hashlib
import hmac
import importlib
import json
import os
import time
import unittest
from unittest.mock import patch

# A fictional test-only value, never a deployed signing key.
os.environ.setdefault("JWT_SECRET", "synthetic-unit-test-key-" + "x" * 40)
from app import auth, config


def signed(payload, header=None):
    encode = lambda value: base64.urlsafe_b64encode(json.dumps(value).encode()).rstrip(b"=").decode()
    unsigned = encode(header or {"alg": "HS256", "typ": "JWT"}) + "." + encode(payload)
    signature = hmac.new(config.JWT_SECRET.encode(), unsigned.encode(), hashlib.sha256).digest()
    return unsigned + "." + base64.urlsafe_b64encode(signature).rstrip(b"=").decode()


class TokenTests(unittest.TestCase):
    def claims(self):
        now = int(time.time())
        return {"sub": "1", "user_id": 1, "iat": now, "exp": now + 60}

    def test_roundtrip_and_stable_key(self):
        token = auth.create_access_token(1)
        self.assertEqual(auth.decode_access_token(token)["sub"], "1")
        importlib.reload(auth)
        self.assertEqual(auth.decode_access_token(token)["sub"], "1")

    def test_required_claims(self):
        for key in self.claims():
            claims = self.claims()
            del claims[key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                auth.decode_access_token(signed(claims))

    def test_invalid_claims(self):
        for change in [
            {"sub": "0"}, {"sub": "-1"}, {"user_id": 2}, {"user_id": True},
            {"exp": int(time.time()) - 1}, {"exp": "tomorrow"},
            {"iat": int(time.time()) + 300}, {"nbf": int(time.time()) + 300},
        ]:
            with self.subTest(change=change), self.assertRaises(ValueError):
                auth.decode_access_token(signed({**self.claims(), **change}))

    def test_header_validation_even_when_signed(self):
        for header in [{"alg": "none", "typ": "JWT"}, {"alg": "HS512", "typ": "JWT"}, {"alg": "HS256"}, []]:
            token = signed(self.claims(), header if header != [] else ["invalid"])
            with self.subTest(header=header), self.assertRaises(ValueError):
                auth.decode_access_token(token)

    def test_malformed_and_tampered_tokens(self):
        token = auth.create_access_token(1)
        for value in ["", "a.b", "!.!.!", "a" * 8193, token[:-5] + "wrong", signed(["not", "claims"])]:
            with self.subTest(value=value[:20]), self.assertRaises(ValueError):
                auth.decode_access_token(value)

    def test_production_key_required(self):
        for values in [{}, {"JWT_SECRET": "short"}, {"APP_ENV": "production", "ALLOW_EPHEMERAL_JWT": "true"}]:
            with patch.dict(os.environ, values, clear=True), self.assertRaises(RuntimeError):
                config.load_jwt_secret()

    def test_ephemeral_key_is_explicit_and_development_only(self):
        with patch.dict(os.environ, {"APP_ENV": "development", "ALLOW_EPHEMERAL_JWT": "true"}, clear=True):
            self.assertNotEqual(config.load_jwt_secret(), config.load_jwt_secret())


if __name__ == "__main__":
    unittest.main()
