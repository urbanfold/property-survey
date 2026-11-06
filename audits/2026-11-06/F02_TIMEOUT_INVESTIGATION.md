# Read-only F02 timeout investigation — 2026-11-06

## Scope and evidence

No Supabase endpoint was invoked during this investigation, no notification was sent, and no secrets, deployments, records, cleanup, GitHub remote refs or production settings were changed. Local audit documentation only. Prepared source inspected at HEAD ac15c68d4f9d7521744eea2f062f9eff88ad6773, including shared receiver, dashboard receiver, Deno wrapper, gateway and existing mocked timeout test. This is NOT independent inspection of the deployed dashboard source.

Owner reconciled the unexpected request: 23 events, 22 accepted, one uncertain, zero sending; 22 receipts, 22 committed capture attempts; no receipt attempts other than one. Owner confirmed accept restored. These totals establish an additional accepted/captured notification rather than merely an old accepted duplicate response.

Request evidence: 2026-11-06 11:09:40.437390 UTC start, HTTP 200 accepted after 2.303 seconds (approximately 11:09:42.740 UTC). Fixture 6, submission 2026-11-06T11:09:39.552512+00:00. Recommend logs window 11:08–11:12 UTC for both receiver and gateway.

## Prepared code findings

- Deno entry point passes `env: name => Deno.env.get(name)` into each handler invocation. The receiver reads `STAGING_RECEIVER_BEHAVIOUR` inside the request handler; no module-level environment caching in prepared source.
- `env('STAGING_RECEIVER_BEHAVIOUR') || 'accept'`: absent/empty setting silently selects accept. A nonempty unrecognised setting returns 503. Consequently a plain malformed nonempty value does not explain fast success if this exact source is deployed.
- Only after a successful capture SQL RPC, the exact `timeout_after_capture` mode awaits a real 12-second Promise/setTimeout before creating the response. The entry point injects no sleep override. Capture failure returns 422 and cannot yield this accepted result.
- Prepared gateway awaits receiver response headers with AbortSignal.timeout(10000), then records uncertain on timeout. The intended receiver does not construct its success response before sleeping, so response-body-only timeout semantics do not explain this result under the reviewed source.
- Existing unit test injects fake sleep and verifies argument 12000; it does not establish deployed source equality or actual managed-runtime timing.
- Existing receiver/gateway source does not log chosen mode, build tag, or correlation ID. Ordinary access logs may provide timing/status/deployment version but cannot directly establish the mode string after it was restored.

## Supabase remote secret guidance

Official source retrieved read-only:
https://raw.githubusercontent.com/supabase/supabase/master/apps/docs/content/guides/functions/secrets.mdx
Canonical documentation: https://supabase.com/docs/guides/functions/secrets
Source SHA-256 c6fae0a51edba282999a4f60f5ba37cdfa8aa5cecd7f3e57933c5ea143e7c649.
Quote: "Your functions read a new secret immediately, so you don't need to redeploy."
The separate restart guidance on that page concerns local runtime environment-file troubleshooting, not a remote redeployment requirement. The canonical HTML URL was blocked by the network proxy; the official GitHub docs source returned HTTP 200. This guidance does not prove a particular dashboard save applied to this runtime or rule out a platform incident.

## Access limits and most likely cause

No Supabase management connector, management token, or authorised dashboard browser session is available here. Available dummy accounts do not grant deployed source, secret metadata or Edge logs access. Do not request broad account tokens or substitute credentials. Deployed source and historical invocation logs remain uninspected directly.

Most likely effective fault mode was not applied: either runtime did not receive the exact variable (and fell back to accept), or deployed receiver/entry point differs from prepared source. Neither is established as root cause. Ordinary secret propagation/restart is not the documented expected explanation. Gateway deployment differences remain possible until both deployed sources are compared; HTTP success alone is not deployment attestation.

## Narrow corrective plan — approval required before implementation/config/deployment/test

1. Operator read-only inspection in project hexhtduvqzleoazusskh: copy active deployed receiver index.ts and any imported modules, plus active gateway source; note deployed version/deployment time. Do not Save/Deploy. Share code without embedded credentials if any.
2. Operator export invocation and execution logs for both functions at 2026-11-06 11:08–11:12 UTC; retain status, timing and deployment/request IDs, redact tokens/headers/private payloads. Check exact secret NAME and that restored value is accept, without sharing other secret values. A current value does not prove its historical value.
3. If source differs, prepare the smallest staging-only correction for review; no automatic replacement. If the name/save target was wrong, correct only that staging configuration after approval. No production, JWT, billing, RLS or schema changes.
4. If read-only evidence cannot resolve mode, propose a narrowly scoped receiver-only diagnostic change: require explicit valid mode (fail closed on missing value), log only safe mode/build tag and opaque delivery correlation ID; never tokens, keys, recipients or payloads. Approval needed for code changes and staging redeployment. No new endpoint is necessary. Restore accept after any approved test.
5. A future approved single dummy timeout request must use a fresh saved revision, then restore accept before duplicate check and reconcile counts. Do not reuse the accepted event expecting it to timeout: deduplication returns its existing accepted status and bypasses delivery.

Current recommendation: HOLD further timeout requests and redeployments pending deployed source/log review. Existing notifications remain in accept mode as owner-confirmed; timeout protection remains unverified in the deployed environment. No cleanup or push.
