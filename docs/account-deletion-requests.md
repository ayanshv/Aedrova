# In-app account deletion requests

The iPhone app accepts an authenticated deletion request in Account settings. The request is private and retries reuse the same reference. The database stores the authenticated user ID, request reference, request time, and optional completion time. Submission does not change account access or delete anything.

## Before enabling for customers

1. Apply `supabase/migrations/202611140001_account_deletion_requests.sql` to staging. On a signed iPhone build pointed at staging, use a disposable confirmed account to submit a request, reopen the receipt, and check that a second disposable account cannot see it.
2. Assign a privacy operator to check the private queue every business day. The app tells people to allow up to 30 days. Apply any shorter deadlines that apply to a particular request and contact the requester if additional time is needed. Confirm that replies reach both direct email and Apple private relay addresses where applicable.
3. Rehearse fulfillment on disposable Google and Apple staging accounts. Verify personal data and user-generated content across Auth, workspaces, files, and connected services. Preserve other members’ records and handle workspace ownership and billing with the applicable safeguards. Remove or restrict sessions and grants. Record any legally required retention and replay completed removals after backup restoration.
4. For Sign in with Apple, use Apple’s [token revocation endpoint](https://developer.apple.com/documentation/signinwithapplerestapi/revoke-tokens) when a valid provider token is available. Use [Apple’s TN3194 procedure](https://developer.apple.com/documentation/technotes/tn3194-handling-account-deletions-and-revoking-tokens-for-sign-in-with-apple) for accounts without a retained token. The iPhone app keeps an Apple refresh token only in memory when Supabase returns one after Apple OAuth. After submission it can send that token to the environment’s Aedrova API. The API requires an authenticated pending request, checks the token belongs to the linked Apple identity, and calls Apple. The API does not persist the token. Verify real revocation and owner-operated deletion on a disposable account before publishing the app.
5. After staging acceptance, apply the same migration to production before distributing a build that offers the flow.

## Private operator queue

In the correct project’s Supabase SQL Editor, an authorized operator can check pending requests using:

```sql
select id, user_id, requested_at
from aedrova_private.account_deletion_requests
where completed_at is null
order by requested_at;
```

Use the linked Auth record to identify the address for fulfillment. Keep that address in the approved private support workflow. Process the scoped deletion, verify the result, and confirm completion to the requester. After confirming that the request was completed, set `completed_at` on the one matching request reference. Keep the minimal receipt for the approved retention period and then purge it.

## Enable Apple revocation

In Render, open **aedrova-beta-staging → Environment**. Set `AEDROVA_APPLE_REVOKE_CLIENT_ID` to the staging Apple Services ID configured in Supabase and `AEDROVA_APPLE_REVOKE_CLIENT_SECRET` to its current Apple client secret. Deploy the API containing `POST /api/account/apple/revoke`. Use production’s matching values in **aedrova-website → Environment** after the staging rehearsal. Rotate both services’ client secrets alongside the corresponding Supabase values. Keep the Apple signing key and all client secrets private.

Sign in to staging on a signed iPhone with a disposable Apple account. Open **Account → Delete account**, submit, and check for the request reference and revocation confirmation. In the test device’s **Settings → Apple Account → Sign in with Apple**, confirm the Aedrova authorization was removed. Verify the operator can complete the account purge, preserve teammate data, and send the completion email. Repeat with a disposable Google account and separately exercise the Apple fallback when no refresh token is available.

## Review chat reports

Use a restricted operator session to read pending entries in `aedrova_private.chat_reports`, ordered by `created_at`. Assign coverage each day to review reports within 24 hours. Review the excerpt and reason, verify the applicable workspace and message, take action under the terms, and record review time. Repeat the rehearsal with a report, a blocked DM, and an unblock. Keep report excerpts in the approved support workflow. Include them in account deletion review and purge them on the approved retention schedule.
