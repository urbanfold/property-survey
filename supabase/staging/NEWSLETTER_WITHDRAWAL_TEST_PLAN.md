# Test1 own-session newsletter withdrawal — PREPARED, NOT EXECUTED

Project hexhtduvqzleoazusskh only. Test1 b83f87d8-abf2-4800-beab-8279917804c7 / urbanfolduk+staging-reg-01@gmail.com. Existing API: get_newsletter_preference() and set_newsletter_preference(subscribe boolean). No new API/migration/frontend or permissions are needed.

## Current blocker

The signup password was randomly generated in memory and deliberately not retained or disclosed. This environment has no Test1 password, valid Test1 access/refresh session, or owner-browser session. Older A/B dummy credentials cannot be used as Test1. A database-owner/service-role connection is NOT Test1's authentication.

Therefore actual staging withdrawal has NOT been performed and cannot be claimed passed under current access. A local disposable PostgreSQL test uses authenticated roles/claims only to model the RLS/RPC semantics; it is not a Supabase-signed live session. Do not set request.jwt.claims in staging, mint/admin-create a session, manually update preferences, extract stored Auth tokens, reuse consumed verification links, reset a password or impersonate Test1.

The owner must have a still-valid genuine Test1 session in an approved staging client, or obtain one through normal login with independently retained valid credentials. No credentials/session should be posted in chat, source, screenshots or logs. If neither exists, this test remains BLOCKED; any account-recovery path requires separate approval and is outside this plan. Do not start recovery as a workaround.

## Preconditions and evidence

Separate execution approval is required. Do not execute this plan during a source review or allowlist installation. Keep dispatcher/scheduler inactive and do not send emails. Use isolated clients/sessions for Test1 and the control user; never swap a service key or another user's JWT into a client to impersonate Test1. Verify exact project URL before any call.

1. Connected reviewer runs 011_newsletter_withdrawal_evidence_readonly.sql with read-only permission. Save original signup choice=true/current consent=true, audit counts, accepted registration event and receipt hashes. If already false or records differ, STOP and report; do not resubscribe just to manufacture a test.
2. Test1 client calls auth.getUser(), verifying the server-returned immutable ID exactly matches Test1 and the account is confirmed. Never print the returned session/token. get_newsletter_preference() must report current true. Client SELECT on its own newsletter_preferences/consent_events is allowed; private registration/receipt tables remain server-only and must not be opened to customers for this test.
3. The owner/connected reviewer must also obtain a GENUINE different-user session before attempting cross-account tests. Prefer verified Test2, already false, so an ordinary same-user false call would be idempotent. Its generated password was also not retained here; no Test2 session currently supplied. Never use privileged SQL impersonation. If control session unavailable, report cross-account STAGING test blocked rather than substituting owner credentials.

## Different-user checks BEFORE changing Test1

With the genuine control client's identity verified by auth.getUser():
- A request that tries to add user_id=Test1 to set_newsletter_preference must be rejected: the only supported signature accepts subscribe, no target identity. Do not repeatedly probe or change function permissions to make it callable.
- A targeted direct update of Test1's newsletter_preferences must be denied by the existing revoked client DML grants/own-user policy. This needs explicit execution approval. Do not perform it until read-only metadata confirms those grants/policies match reviewed004.
- Connected reviewer confirms Test1 is still true, original choice unchanged and no extra Test1 audit. Stop on any unexpected success or target change; no privileged repair or automatic retry.

## Own authenticated withdrawal

Use Test1's genuine isolated staging client; revalidate auth.getUser() before mutation. The ONLY preference write is:

    await test1StagingClient.rpc('set_newsletter_preference', { subscribe: false })

No user ID, timestamp, metadata or service key is supplied. Check returned error/status; on transport ambiguity STOP, inspect state/audit before further calls. No automatic retry. Read get_newsletter_preference() and own canonical row: current opted_in=false, signup_opt_in_requested=true.

Connected reviewer compares the read-only evidence: preference_change/false audit increased exactly one; signup/verification counts and original true unchanged; registration event/receipt hashes and counts unchanged; no new notification; F02 survey evidence unchanged. Record only hashes/counts/booleans, no tokens or raw message contents.

After the first withdrawal is confirmed successful, make ONE separately planned repeat of exactly subscribe=false in the same verified Test1 session to test idempotency. This is an explicit test call, not an automatic failure retry. Recheck current false, unchanged updated_at, unchanged original choice/history and no further audit event. Do not automatically opt back in after the test.

## Minimal private SDK sequence (illustrative, not executed here)

    // test1StagingClient is already authenticated genuinely as Test1.
    // Assert its exact staging URL and auth.getUser() result first.
    const first = await test1StagingClient.rpc(
      'set_newsletter_preference', { subscribe: false }
    )
    // Stop on error; inspect own RPC state and privileged read-only evidence.
    // Only after confirmed success and planned idempotency approval:
    const repeat = await test1StagingClient.rpc(
      'set_newsletter_preference', { subscribe: false }
    )

Do not paste secret-bearing curl commands or tokens in Console/chat. Existing isolated app preference UI can perform the same RPC if its genuine account/session and staging connection are verified. Production Pages app is not the staging client.

## Rollback / boundaries

No password reset, admin confirmation, new account, dispatcher, email or schema change is part of this test. Newsletter withdrawal is a legitimate consent action: retain false and its audit unless the owner separately requests a new opt-in through the same authenticated RPC. Never erase its audit or use privileged SQL to undo it. Allowlist rollback011 concerns capture permissions only and must not alter consent/history. No cleanup008.
