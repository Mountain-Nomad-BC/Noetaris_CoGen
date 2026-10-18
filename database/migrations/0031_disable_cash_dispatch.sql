-- User decision: no cash use. Preserve all historical balances and events.
UPDATE cost_accounts SET enabled=false WHERE name LIKE 'cash-%';

CREATE OR REPLACE FUNCTION nsai_reserve_cost(p_id text,p_account text,p_provider text,p_estimate bigint,p_input bigint,p_output bigint)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE old public.cost_reservations%ROWTYPE; account_row public.cost_accounts%ROWTYPE; total public.cost_accounts%ROWTYPE;
BEGIN
 IF p_account LIKE 'cash-%' THEN RAISE EXCEPTION 'Cash dispatch is prohibited; governance demonstration only' USING ERRCODE='42501'; END IF;
 IF public.nsai_actor_role() NOT IN ('operator','service') OR nullif(current_setting('nsai.job_id',true),'') IS NOT NULL THEN
  RAISE EXCEPTION 'Cost reservation not permitted' USING ERRCODE='42501';
 END IF;
 IF p_id IS NULL OR p_id !~ '^[a-f0-9]{64}$' OR p_account IS NULL OR p_account='cash-total'
    OR p_provider IS NULL OR p_provider !~ '^[a-z][a-z0-9_-]{0,63}$'
    OR p_estimate IS NULL OR p_estimate NOT BETWEEN 0 AND 1000000000000
    OR p_input IS NULL OR p_input NOT BETWEEN 0 AND 1000000000
    OR p_output IS NULL OR p_output NOT BETWEEN 0 AND 1000000000 THEN
  RAISE EXCEPTION 'Invalid cost reservation';
 END IF;
 -- One short global ledger lock gives deterministic cross-bucket lock ordering.
 PERFORM pg_advisory_xact_lock(878732);
 SELECT * INTO old FROM public.cost_reservations WHERE id=p_id;
 IF FOUND THEN
  IF old.actor<>public.nsai_actor() OR old.account<>p_account OR old.provider<>p_provider
     OR old.estimate_units<>p_estimate OR old.input_token_ceiling<>p_input OR old.output_token_ceiling<>p_output THEN
   RAISE EXCEPTION 'Cost reservation unavailable' USING ERRCODE='42501';
  END IF;
  RETURN p_id;
 END IF;
 SELECT * INTO account_row FROM public.cost_accounts WHERE name=p_account FOR UPDATE;
 IF NOT FOUND OR NOT account_row.enabled OR account_row.spent_units+account_row.reserved_units+p_estimate>account_row.limit_units THEN
  RAISE EXCEPTION 'Provider or allocation unavailable';
 END IF;
 IF p_account LIKE 'cash-%' THEN
  SELECT * INTO STRICT total FROM public.cost_accounts WHERE name='cash-total' FOR UPDATE;
  IF NOT total.enabled OR total.spent_units+total.reserved_units+p_estimate>total.limit_units THEN
   RAISE EXCEPTION 'Cash exposure ceiling reached';
  END IF;
  UPDATE public.cost_accounts SET reserved_units=reserved_units+p_estimate WHERE name='cash-total';
 END IF;
 UPDATE public.cost_accounts SET reserved_units=reserved_units+p_estimate WHERE name=p_account;
 INSERT INTO public.cost_reservations(id,actor,account,provider,estimate_units,input_token_ceiling,output_token_ceiling)
 VALUES(p_id,public.nsai_actor(),p_account,p_provider,p_estimate,p_input,p_output);
 INSERT INTO public.cost_events(reservation_id,actor,kind,units) VALUES(p_id,public.nsai_actor(),'reserved',p_estimate);
 RETURN p_id;
END $$;
