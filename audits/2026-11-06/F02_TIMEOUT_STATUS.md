# F02 timeout attempt — 2026-11-06

Staging only: hexhtduvqzleoazusskh. Reviewed source commit ac15c68d4f9d7521744eea2f062f9eff88ad6773. Development branch retains prior unpushed/uncommitted work. No push, merge, deployment, secret modification or cleanup by the assistant.

Owner confirmed STAGING_RECEIVER_BEHAVIOUR=timeout_after_capture saved and had approved the controlled timeout procedure. One request was made, after fresh successful dummy B sign-in and exact original fixture-6 state checks. Only dedicated fixture 6's notes/submission timestamp were updated and cloud readback verified before requesting notification.

**Unexpected result: HTTP 200 accepted in 2.303 seconds.** Expected HTTP 202 uncertain after approximately 10 seconds was NOT observed. The runner stopped at this failed expectation and made no second request. It did not run the planned delayed readback or duplicate phase. Complete saved fixture row hash matched before/after the request; original B property row hash also matched. Original A/rooms/photos and entitlements were not written.

Evidence: F02_TIMEOUT_EVIDENCE.json; one-use runner f02_timeout_once.py. No credentials/tokens recorded. The evidence guard prevents accidental rerun.

This result does not establish successful timeout protection. It is consistent with the effective receiver not using the requested delay, but exact cause is unknown: settings propagation/name/value/project or deployed receiver behaviour must be checked. Ordinary-user access does not expose deployed secret values or management source/logs. No config inference is claimed as direct verification.

Operator next step: restore STAGING_RECEIVER_BEHAVIOUR=accept in the identified staging project, even though observed response already resembled accept mode. Do not retry or create another submission. Reconcile privileged counts before planning a fresh fault test.

Assuming no unrelated activity and one successful capture, EXPECTED (not directly verified) lifetime totals now: events 23, accepted 22, uncertain 1, sending 0, receipts 22, capture_attempts 22, repeat-capture receipts 0. These differ from the proposed timeout totals because this request returned accepted. Privileged reconciliation must determine actual outcome. Existing previous evidence remains retained. Cleanup 008 must not run.

## Restoration acknowledgement and saved-data check

Owner confirmed staging receiver setting restored to accept. This is owner-reported configuration evidence; no management read of secrets is available. Fresh B authentication and read-only full-row SHA-256 checks confirmed fixture 6 and the original B survey still match the recorded timeout-attempt snapshots. No further notification request or mutation made. Privileged reconciliation remains pending. Exact new submission timestamp: 2026-11-06T11:09:39.552512+00:00.
