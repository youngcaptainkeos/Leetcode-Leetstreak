# Key Management, Session Stability & Rotation Policy

This document defines the signing key lifecycle, session predictability, safe rotation procedures, and deployment verification for LeetStreak.

---

## 1. Signing Key Requirements

LeetStreak uses HMAC-SHA256 (`HS256`) to issue and verify tamper-proof JSON Web Tokens (JWT) for client sessions.

1. **Production Requirement**:
   - `JWT_SECRET` must be set in the hosting environment (e.g. Render Dashboard).
   - The key must contain **at least 32 bytes** (256 bits) of high-entropy cryptographic randomness.
   - If `JWT_SECRET` is missing, blank, or fewer than 32 bytes, the backend fails closed immediately during startup with `RuntimeError: JWT_SECRET must contain at least 32 bytes` or `RuntimeError: Set a stable JWT_SECRET before starting the application.`
2. **Development / Ephemeral Mode**:
   - Ephemeral keys are strictly forbidden in production.
   - If and only if `APP_ENV=development` or `APP_ENV=test`, setting `ALLOW_EPHEMERAL_JWT=true` allows starting without a pre-configured secret. A temporary 48-byte key is generated per process with a prominent warning: `Development-only temporary signing key enabled; restart invalidates sessions.`

### Generating a Strong Secret
Operators should generate keys using cryptographically secure random sources:
```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```
*Never commit the output of this command to Git, documentation, or public repositories.*

---

## 2. Session Revocation & Key Rotation

LeetStreak supports two levels of session revocation:

### Level A: Per-User Session Revocation (Targeted)
- When a user changes their password, completes password recovery, or requests device revocation, the backend atomically increments `User.session_version` in the database.
- Any existing JWT containing an older session version (`ver < current_session_version`) is immediately rejected by `backend/app/security.py` with HTTP 401 Unauthorized (`Please sign in again.`).
- **Impact**: Only the affected user is logged out; other users' active sessions remain completely unaffected.

### Level B: Global Key Rotation (Fleet-Wide)
In the event of suspected key exposure or periodic fleet credential rotation:
1. Generate a new 48-byte URL-safe secret.
2. In the hosting provider (e.g. Render Web Service Settings -> Environment Variables), update `JWT_SECRET`.
3. Trigger a redeploy / restart of the API service.
4. **Impact & Sign-Out Effects**:
   - Every existing JWT was signed with the previous key. When decoded under the new key, HMAC-SHA256 signature verification fails (`Invalid token signature`).
   - The API immediately returns HTTP 401 Unauthorized.
   - **Client Behavior**:
     - **Browser Extension**: `extension/src/lib/api.ts` intercepts HTTP 401, verifies the active token, and emits `AUTH_EXPIRED`. The extension popup (`extension/src/App.tsx`) clears local token storage, displays `Your session expired. Please sign in again.`, and renders the login form.
     - **Web Application**: `web/app/lib/api.ts` intercepts HTTP 401 and emits `leetstreak:auth-expired`. `web/main.tsx` clears session state and navigates cleanly to `/login`.
   - No user data, streaks, or points are altered by key rotation; users simply sign in with their existing password to receive a freshly signed token.

---

## 3. Hosting Verification & Blueprint Configuration

In `render.yaml`, `JWT_SECRET` is configured with `generateValue: true`:
```yaml
      - key: JWT_SECRET
        generateValue: true
      - key: ADMIN_SECRET
        sync: false
      - key: APP_ENV
        value: production
```
- `generateValue: true` instructs Render to generate a unique cryptographically secure secret upon initial service deployment and persist it across deployments.
- `ADMIN_SECRET` is marked `sync: false`, requiring operators to supply it manually in the Render Dashboard so administrative secrets are never committed to repository history.
- **Verification Step**: Operators should verify in the Render dashboard that `JWT_SECRET` exists as a secret environment variable and that service startup logs show zero warnings about ephemeral keys.
