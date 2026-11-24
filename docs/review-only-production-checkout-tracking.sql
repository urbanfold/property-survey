-- REVIEW ONLY: proposed production checkout tracking. Do not execute or deploy
-- without separate approval, isolated database tests and a rollback plan.
-- Stores references only, never card details, checkout URLs or Stripe secrets.
BEGIN;
CREATE TABLE public.survey_checkout_attempts (
  checkout_session_id text PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  attempt_id uuid NOT NULL,
  live_mode boolean NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT survey_checkout_attempt_identity UNIQUE (user_id, attempt_id, live_mode),
  CONSTRAINT survey_checkout_attempt_mode CHECK (
    (live_mode AND checkout_session_id ~ '^cs_live_[A-Za-z0-9]+$')
    OR (NOT live_mode AND checkout_session_id ~ '^cs_test_[A-Za-z0-9]+$')
  )
);
CREATE INDEX survey_checkout_attempts_owner_mode_created_idx
  ON public.survey_checkout_attempts(user_id, live_mode, created_at DESC);
ALTER TABLE public.survey_checkout_attempts ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.survey_checkout_attempts FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT ON TABLE public.survey_checkout_attempts TO service_role;
-- No client policies: browser access is mediated by authenticated backend code.
-- Backend must derive user_id from verified auth, not from the request body.
-- Persist the reference before returning a checkout URL. Retry using the same
-- Stripe idempotency key and verify any existing row matches all identities.
-- Recovery must bound the number and age of Stripe lookups, revalidate each
-- session and check existing redemption/revocation state before displaying credit.
-- Retention and account deletion behavior must be reviewed before release.
COMMIT;
-- Proposed rollback (only before customer use, or after preserving needed records):
-- DROP TABLE public.survey_checkout_attempts;
