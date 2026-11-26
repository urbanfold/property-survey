-- Disposable PostgreSQL fixture. Never run against an application database.
\set ON_ERROR_STOP on
CREATE ROLE anon NOLOGIN;
CREATE ROLE authenticated NOLOGIN;
CREATE ROLE service_role NOLOGIN BYPASSRLS;
CREATE SCHEMA auth;
CREATE TABLE auth.users(id uuid PRIMARY KEY);
CREATE FUNCTION auth.uid() RETURNS uuid LANGUAGE sql STABLE AS $$ SELECT nullif(current_setting('request.jwt.claim.sub',true),'')::uuid $$;
CREATE FUNCTION auth.jwt() RETURNS jsonb LANGUAGE sql STABLE AS $$ SELECT coalesce(nullif(current_setting('request.jwt.claims',true),'')::jsonb,'{}'::jsonb) $$;
GRANT USAGE ON SCHEMA auth TO authenticated, service_role;
CREATE TABLE public.properties(id uuid PRIMARY KEY,user_id uuid NOT NULL REFERENCES auth.users(id));
CREATE TABLE public.survey_free_allocations(user_id uuid PRIMARY KEY,property_id uuid NOT NULL);
CREATE TABLE public.survey_credit_purchases(
 checkout_session_id text PRIMARY KEY,payment_intent_id text UNIQUE NOT NULL,
 user_id uuid NOT NULL REFERENCES auth.users(id),live_mode boolean NOT NULL,
 purchased_at timestamptz DEFAULT now(),redeemed_property_id uuid UNIQUE,redeemed_at timestamptz
);
CREATE TABLE public.survey_credit_revocations(payment_intent_id text PRIMARY KEY,reason text);
ALTER TABLE public.survey_credit_purchases ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.survey_credit_purchases FROM PUBLIC,anon,authenticated;
GRANT INSERT, SELECT, UPDATE ON public.properties TO authenticated;
\ir ../docs/review-only-production-checkout-tracking.sql
\ir ../docs/review-only-production-credit-verification.sql
CREATE TRIGGER test_allowance BEFORE INSERT ON public.properties FOR EACH ROW EXECUTE FUNCTION public.enforce_survey_allowance();
INSERT INTO auth.users VALUES ('11111111-1111-4111-8111-111111111111'),('22222222-2222-4222-8222-222222222222');
INSERT INTO public.survey_credit_purchases(checkout_session_id,payment_intent_id,user_id,live_mode)
 VALUES ('cs_live_fixture1','pi_fixture1','11111111-1111-4111-8111-111111111111',true);
SET ROLE authenticated;
SELECT set_config('request.jwt.claim.sub','11111111-1111-4111-8111-111111111111',false);
SELECT set_config('request.jwt.claims','{"role":"authenticated","email":"fixture@example.invalid"}',false);
INSERT INTO public.properties VALUES('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1','11111111-1111-4111-8111-111111111111');
DO $$ BEGIN
 BEGIN
 INSERT INTO public.properties VALUES('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','11111111-1111-4111-8111-111111111111');
 RAISE EXCEPTION 'Unverified credit unexpectedly accepted';
 EXCEPTION WHEN SQLSTATE 'P0001' THEN IF SQLERRM <> 'URBANFOLD_CREDIT_REVERIFY' THEN RAISE; END IF;
 END;
 BEGIN
 PERFORM public.attest_survey_credit_verification('cs_live_fixture1','pi_fixture1','11111111-1111-4111-8111-111111111111');
 RAISE EXCEPTION 'Client attestation unexpectedly accepted';
 EXCEPTION WHEN insufficient_privilege THEN NULL; END;
 BEGIN
 PERFORM count(*) FROM public.survey_checkout_attempts;
 RAISE EXCEPTION 'Client tracking access unexpectedly accepted';
 EXCEPTION WHEN insufficient_privilege THEN NULL; END;
END $$;
RESET ROLE;
SET ROLE service_role;
SELECT public.attest_survey_credit_verification('cs_live_fixture1','pi_fixture1','11111111-1111-4111-8111-111111111111');
RESET ROLE;
SET ROLE authenticated;
INSERT INTO public.properties VALUES('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2','11111111-1111-4111-8111-111111111111');
UPDATE public.properties SET user_id=user_id WHERE id='aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2';
DO $$ BEGIN
 BEGIN
 INSERT INTO public.properties VALUES('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3','11111111-1111-4111-8111-111111111111');
 RAISE EXCEPTION 'Redeemed credit unexpectedly reused';
 EXCEPTION WHEN SQLSTATE 'P0001' THEN IF SQLERRM <> 'URBANFOLD_SURVEY_LIMIT' THEN RAISE; END IF; END;
END $$;
RESET ROLE;
INSERT INTO public.survey_credit_purchases(checkout_session_id,payment_intent_id,user_id,live_mode,stripe_verified_at)
VALUES('cs_live_fixture2','pi_fixture2','11111111-1111-4111-8111-111111111111',true,clock_timestamp()-interval '61 seconds');
SET ROLE authenticated;
DO $$ BEGIN
 BEGIN
 INSERT INTO public.properties VALUES('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3','11111111-1111-4111-8111-111111111111');
 RAISE EXCEPTION 'Expired credit unexpectedly accepted';
 EXCEPTION WHEN SQLSTATE 'P0001' THEN IF SQLERRM <> 'URBANFOLD_CREDIT_REVERIFY' THEN RAISE; END IF; END;
END $$;
RESET ROLE;
SET ROLE service_role;
SELECT public.revoke_survey_purchase('pi_fixture2','fixture refund');
SELECT public.attest_survey_credit_verification('cs_live_fixture2','pi_fixture2','11111111-1111-4111-8111-111111111111');
RESET ROLE;
SET ROLE authenticated;
DO $$ BEGIN
 BEGIN
 INSERT INTO public.properties VALUES('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa3','11111111-1111-4111-8111-111111111111');
 RAISE EXCEPTION 'Revoked credit unexpectedly accepted';
 EXCEPTION WHEN SQLSTATE 'P0001' THEN IF SQLERRM <> 'URBANFOLD_SURVEY_LIMIT' THEN RAISE; END IF; END;
END $$;
RESET ROLE;
DO $$ BEGIN
 IF (SELECT count(*) FROM public.properties) <> 2 THEN RAISE EXCEPTION 'Unexpected property count'; END IF;
 IF (SELECT count(*) FROM public.survey_credit_purchases WHERE redeemed_property_id IS NOT NULL) <> 1 THEN RAISE EXCEPTION 'Unexpected redemption count'; END IF;
END $$;
\echo Isolated credit verification assertions passed

-- Recovery selection regression: revoked rows must not consume the bounded result.
INSERT INTO public.survey_credit_purchases(checkout_session_id,payment_intent_id,user_id,live_mode,purchased_at)
SELECT 'cs_live_revoked'||n,'pi_revoked'||n,'11111111-1111-4111-8111-111111111111',true,now()-interval '90 days'
FROM generate_series(1,8) n;
INSERT INTO public.survey_credit_revocations(payment_intent_id,reason)
SELECT 'pi_revoked'||n,'fixture' FROM generate_series(1,8) n;
INSERT INTO public.survey_credit_purchases(checkout_session_id,payment_intent_id,user_id,live_mode,purchased_at)
VALUES ('cs_live_oldvalid','pi_oldvalid','11111111-1111-4111-8111-111111111111',true,now()-interval '100 days'),
('cs_live_other','pi_other','22222222-2222-4222-8222-222222222222',true,now()),
('cs_test_fixture','pi_testfixture','11111111-1111-4111-8111-111111111111',false,now());
INSERT INTO public.survey_checkout_attempts(checkout_session_id,user_id,attempt_id,live_mode)
VALUES ('cs_live_pending','11111111-1111-4111-8111-111111111111','bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb1',true),
('cs_live_fixture2','11111111-1111-4111-8111-111111111111','bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbb2',true);
SET ROLE authenticated;
DO $$ BEGIN
 BEGIN
 PERFORM public.list_recoverable_survey_sessions('11111111-1111-4111-8111-111111111111',NULL);
 RAISE EXCEPTION 'Client recovery selection unexpectedly allowed';
 EXCEPTION WHEN insufficient_privilege THEN NULL; END;
END $$;
RESET ROLE;
SET ROLE service_role;
DO $$ DECLARE ids text[]; BEGIN
 SELECT array_agg(s.checkout_session_id ORDER BY s.checkout_session_id) INTO ids
 FROM public.list_recoverable_survey_sessions('11111111-1111-4111-8111-111111111111',NULL) s;
 IF ids IS DISTINCT FROM ARRAY['cs_live_oldvalid','cs_live_pending']::text[] THEN RAISE EXCEPTION 'Unexpected recoverable candidates: %',ids; END IF;
 IF EXISTS(SELECT 1 FROM public.list_recoverable_survey_sessions('11111111-1111-4111-8111-111111111111','cs_live_other')) THEN RAISE EXCEPTION 'Foreign checkout exposed'; END IF;
 IF EXISTS(SELECT 1 FROM public.list_recoverable_survey_sessions('11111111-1111-4111-8111-111111111111','cs_live_fixture2')) THEN RAISE EXCEPTION 'Revoked checkout exposed'; END IF;
END $$;
RESET ROLE;
\echo Recovery filtering assertions passed

RESET ROLE;
SET ROLE service_role;
DO $$
DECLARE
  owner_id constant uuid := '11111111-1111-4111-8111-111111111111';
  other_id constant uuid := '22222222-2222-4222-8222-222222222222';
  window_checked timestamptz := date_trunc('minute', clock_timestamp());
  allowed integer := 0;
BEGIN
  FOR attempt IN 1..11 LOOP
    IF public.take_survey_payment_recovery_slot(owner_id) THEN allowed := allowed + 1; END IF;
  END LOOP;
  IF window_checked = date_trunc('minute', clock_timestamp()) AND allowed <> 10 THEN
    RAISE EXCEPTION 'Per-account request limit failed';
  END IF;
  IF NOT public.take_survey_payment_recovery_slot(other_id) THEN
    RAISE EXCEPTION 'One account exhausted another account’s recovery limit';
  END IF;
END $$;
RESET ROLE;
UPDATE public.survey_payment_recovery_limits SET window_start = clock_timestamp() - interval '2 minutes';
SET ROLE service_role;
DO $$ BEGIN
  IF NOT public.take_survey_payment_recovery_slot('11111111-1111-4111-8111-111111111111') THEN
    RAISE EXCEPTION 'Recovery limit did not reset for the next window';
  END IF;
END $$;
RESET ROLE;
SET ROLE authenticated;
DO $$ BEGIN
  BEGIN
    PERFORM public.take_survey_payment_recovery_slot('11111111-1111-4111-8111-111111111111');
    RAISE EXCEPTION 'Customer could invoke the service-only rate limit function';
  EXCEPTION WHEN insufficient_privilege THEN NULL;
  END;
END $$;
RESET ROLE;
