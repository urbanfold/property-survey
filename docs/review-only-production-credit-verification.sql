-- REVIEW ONLY. Requires isolated tests and separate deployment approval.
-- Apply only in coordination with the backend verification handler.
BEGIN;
ALTER TABLE public.survey_credit_purchases
  ADD COLUMN stripe_verified_at timestamptz;
-- Only a trusted server may attest that it independently checked Stripe.
CREATE FUNCTION public.attest_survey_credit_verification(session_id text, intent_id text, buyer_id uuid)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path TO '' AS $$
BEGIN
  IF session_id IS NULL OR session_id !~ '^cs_live_[A-Za-z0-9]+$'
     OR intent_id IS NULL OR intent_id !~ '^pi_[A-Za-z0-9]+$'
     OR buyer_id IS NULL THEN
    RAISE EXCEPTION 'Invalid verification reference';
  END IF;
  -- Serialize attestation and redemption for the same owner.
  PERFORM 1 FROM auth.users WHERE id = buyer_id FOR UPDATE;
  UPDATE public.survey_credit_purchases p SET stripe_verified_at = clock_timestamp()
    WHERE p.checkout_session_id = session_id AND p.payment_intent_id = intent_id
      AND p.user_id = buyer_id AND p.live_mode AND p.redeemed_property_id IS NULL
      AND NOT EXISTS (SELECT 1 FROM public.survey_credit_revocations r
        WHERE r.payment_intent_id = p.payment_intent_id);
  -- An already consumed or revoked credit is intentionally not reactivated.
END $$;
REVOKE ALL ON FUNCTION public.attest_survey_credit_verification(text,text,uuid) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.attest_survey_credit_verification(text,text,uuid) TO service_role;
-- Coordinate revocation with the account lock used by the redemption trigger.
-- A refund recorded before purchase insertion remains independently effective.
CREATE OR REPLACE FUNCTION public.revoke_survey_purchase(intent_id text, revocation_reason text)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path TO '' AS $$
DECLARE owner_id uuid;
BEGIN
  IF intent_id IS NULL OR intent_id !~ '^pi_[A-Za-z0-9]+$' THEN RAISE EXCEPTION 'Invalid payment reference.'; END IF;
  SELECT p.user_id INTO owner_id FROM public.survey_credit_purchases p WHERE p.payment_intent_id = intent_id;
  IF owner_id IS NOT NULL THEN PERFORM 1 FROM auth.users WHERE id = owner_id FOR UPDATE; END IF;
  INSERT INTO public.survey_credit_revocations(payment_intent_id,reason)
    VALUES(intent_id,left(revocation_reason,100)) ON CONFLICT(payment_intent_id) DO NOTHING;
END $$;
REVOKE ALL ON FUNCTION public.revoke_survey_purchase(text,text) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.revoke_survey_purchase(text,text) TO service_role;
-- Preserve original enforcement, adding a narrowly scoped freshness requirement.
-- Proposed maximum age: 60 seconds. This is a risk reduction, not an atomic
-- guarantee across Stripe and PostgreSQL. Never use browser time as attestation.
CREATE OR REPLACE FUNCTION public.enforce_survey_allowance()
RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER SET search_path TO '' AS $$
DECLARE
  allocated uuid;
  purchase text;
  caller_role text := auth.jwt()->>'role';
BEGIN
  IF caller_role = 'service_role' OR (caller_role IS NULL AND auth.uid() IS NULL)
     OR (auth.uid() IS NOT NULL AND auth.jwt()->>'email' = 'urbanfolduk@gmail.com') THEN RETURN NEW; END IF;
  IF auth.uid() IS NULL OR NEW.user_id IS DISTINCT FROM auth.uid() THEN
    RAISE EXCEPTION 'Survey ownership is invalid.' USING ERRCODE = '42501';
  END IF;
  PERFORM 1 FROM auth.users WHERE id = NEW.user_id FOR UPDATE;
  IF EXISTS(SELECT 1 FROM public.properties WHERE id = NEW.id AND user_id = NEW.user_id) THEN RETURN NEW; END IF;
  INSERT INTO public.survey_free_allocations(user_id,property_id) VALUES(NEW.user_id,NEW.id)
    ON CONFLICT(user_id) DO NOTHING RETURNING user_id INTO allocated;
  IF allocated IS NOT NULL THEN RETURN NEW; END IF;
  SELECT p.checkout_session_id INTO purchase FROM public.survey_credit_purchases p
    WHERE p.user_id = NEW.user_id AND p.live_mode AND p.redeemed_property_id IS NULL
      AND p.stripe_verified_at >= clock_timestamp() - interval '60 seconds'
      AND p.stripe_verified_at <= clock_timestamp()
      AND NOT EXISTS(SELECT 1 FROM public.survey_credit_revocations r WHERE r.payment_intent_id = p.payment_intent_id)
    ORDER BY p.purchased_at,p.checkout_session_id FOR UPDATE LIMIT 1;
  IF purchase IS NULL THEN
    IF EXISTS(SELECT 1 FROM public.survey_credit_purchases p
      WHERE p.user_id = NEW.user_id AND p.live_mode AND p.redeemed_property_id IS NULL
        AND NOT EXISTS(SELECT 1 FROM public.survey_credit_revocations r WHERE r.payment_intent_id = p.payment_intent_id))
    THEN RAISE EXCEPTION 'URBANFOLD_CREDIT_REVERIFY' USING ERRCODE = 'P0001'; END IF;
    RAISE EXCEPTION 'URBANFOLD_SURVEY_LIMIT' USING ERRCODE = 'P0001';
  END IF;
  UPDATE public.survey_credit_purchases SET redeemed_property_id = NEW.id, redeemed_at = now()
    WHERE checkout_session_id = purchase;
  RETURN NEW;
END $$;
-- Service-only recovery selection. Filter consumed/revoked records BEFORE limiting.
CREATE FUNCTION public.list_recoverable_survey_sessions(buyer_id uuid, session_reference text DEFAULT NULL)
RETURNS TABLE(checkout_session_id text,user_id uuid,live_mode boolean)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path TO '' AS $$
 WITH candidates AS (
   SELECT p.checkout_session_id,p.user_id,p.live_mode,0 AS priority,p.purchased_at AS sort_time
   FROM public.survey_credit_purchases p
   WHERE p.user_id=buyer_id AND p.live_mode AND p.redeemed_property_id IS NULL
     AND NOT EXISTS (SELECT 1 FROM public.survey_credit_revocations r WHERE r.payment_intent_id=p.payment_intent_id)
     
     AND (session_reference IS NULL OR p.checkout_session_id=session_reference)
   UNION ALL
   SELECT t.checkout_session_id,t.user_id,t.live_mode,1,-1 * extract(epoch FROM t.created_at) * interval '1 second' + timestamptz 'epoch'
   FROM public.survey_checkout_attempts t
   WHERE t.user_id=buyer_id AND t.live_mode
     AND NOT EXISTS (SELECT 1 FROM public.survey_credit_purchases p WHERE p.checkout_session_id=t.checkout_session_id)
     AND (session_reference IS NOT NULL OR t.created_at >= now()-interval '30 days')
     AND (session_reference IS NULL OR t.checkout_session_id=session_reference)
 )
 SELECT c.checkout_session_id,c.user_id,c.live_mode FROM candidates c
 ORDER BY c.priority,c.sort_time,c.checkout_session_id LIMIT 6;
$$;
REVOKE ALL ON FUNCTION public.list_recoverable_survey_sessions(uuid,text) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.list_recoverable_survey_sessions(uuid,text) TO service_role;

COMMIT;
-- Release blockers: verify exact existing grants and trigger definitions;
-- verify server-only column writes; ensure all save paths handle re-verification;
-- verify older unredeemed purchases can be attested, regardless of tracking age;
-- validate concurrent revocation, redemption and insertion order in isolation.
-- Rollback: restore captured previous function definitions/grants before
-- removing the attestation function and column. Do not delete purchase records.
