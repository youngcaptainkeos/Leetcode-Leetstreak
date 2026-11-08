# Persistent store review account

The publisher provisions a dedicated account through private Render environment
variables: `REVIEWER_EMAIL`, `REVIEWER_PASSWORD_HASH`, and
`REVIEWER_LEETCODE_USERNAME`. Do not place their values in source control,
extension packages, public issues, or release notes. The password hash uses the
same salted PBKDF2 format as ordinary accounts; no raw password is deployed.

Startup provisioning is idempotent and serialized across PostgreSQL workers.
It creates a missing reviewer, retains its ID and data on subsequent deploys,
and refuses to convert an ordinary account or silently replace its coding
identity. Changing the configured hash rotates its password and invalidates
old sessions. There is no reviewer-account expiry; ordinary session expiry
still requires signing in again. Database backups and retaining the private
service configuration remain the publisher's responsibility.

`is_reviewer` is controlled by the server, not signup or account settings. Normal
users keep their existing ranking and profile visibility. Reviewers are excluded
from Global, Friends and group rankings, public solve feeds, and other users'
profile/group-member results. They can view ordinary rankings and profiles, sync
their public demo data, and save study plans normally. They can create isolated
review groups; they cannot join real participants' groups or send kudos.

The publisher-managed login cannot change its password or coding handles, use
password recovery, or delete itself. Targeted administrative deletion and the
destructive bulk-reset endpoint also reject removal of a configured reviewer.
For intentional retirement, remove private provisioning configuration and use a
reviewed database operation; do not distribute database access to reviewers.

Provide the login only in the Chrome Web Store's confidential test instructions.
Explain its isolated social behavior and publisher-managed identity there. It
uses public demo profile data, not ownership of the external coding account.
Replace any removed review-account credentials in the existing store item.

This is a server-side change and works with the published 1.0.0 client and the
prepared 1.0.1 package. No new extension ZIP or permissions are required.
