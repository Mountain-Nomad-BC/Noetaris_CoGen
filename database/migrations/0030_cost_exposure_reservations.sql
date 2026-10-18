-- Durable exposure is authoritative in PostgreSQL, never a cache or budget alert.
CREATE TABLE cost_accounts (
 name text PRIMARY KEY CHECK(name IN ('cash-total','cash-cloud','cash-api','cash-contingency','amd-credits','evolus-credits')),
 unit text NOT NULL CHECK(unit IN ('microusd','provider-credit-unit')),
 limit_units bigint NOT NULL CHECK(limit_units BETWEEN 0 AND 1000000000000000),
 reserved_units bigint NOT NULL DEFAULT 0 CHECK(reserved_units>=0),
 spent_units bigint NOT NULL DEFAULT 0 CHECK(spent_units>=0),
 enabled boolean NOT NULL DEFAULT true,
 CHECK((name LIKE 'cash-%' AND unit='microusd') OR (name NOT LIKE 'cash-%' AND unit='provider-credit-unit'))
);
-- Credit rows use explicitly declared provider units and never represent dollars.
INSERT INTO cost_accounts(name,unit,limit_units) VALUES
 ('cash-total','microusd',20000000),('cash-cloud','microusd',5000000),
 ('cash-api','microusd',10000000),('cash-contingency','microusd',5000000),
 ('amd-credits','provider-credit-unit',0),('evolus-credits','provider-credit-unit',0);
UPDATE cost_accounts SET enabled=false WHERE unit='provider-credit-unit';
CREATE TABLE cost_reservations (
 id text PRIMARY KEY CHECK(id ~ '^[a-f0-9]{64}$'), actor text NOT NULL,
 account text NOT NULL REFERENCES cost_accounts(name), provider text NOT NULL,
 estimate_units bigint NOT NULL CHECK(estimate_units BETWEEN 0 AND 1000000000000),
 input_token_ceiling bigint NOT NULL CHECK(input_token_ceiling BETWEEN 0 AND 1000000000),
 output_token_ceiling bigint NOT NULL CHECK(output_token_ceiling BETWEEN 0 AND 1000000000),
 actual_units bigint CHECK(actual_units BETWEEN 0 AND 1000000000000),
 input_tokens bigint CHECK(input_tokens BETWEEN 0 AND 1000000000),
 output_tokens bigint CHECK(output_tokens BETWEEN 0 AND 1000000000),
 state text NOT NULL DEFAULT 'reserved' CHECK(state IN ('reserved','settled')),
 created_at timestamptz NOT NULL DEFAULT now(), settled_at timestamptz
);
CREATE TABLE cost_events (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 reservation_id text NOT NULL REFERENCES cost_reservations(id),
 actor text NOT NULL, kind text NOT NULL CHECK(kind IN ('reserved','settled')),
 units bigint NOT NULL CHECK(units>=0), created_at timestamptz NOT NULL DEFAULT now(),
 UNIQUE(reservation_id,kind)
);
ALTER TABLE cost_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE cost_reservations ENABLE ROW LEVEL SECURITY;
ALTER TABLE cost_events ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON cost_accounts,cost_reservations,cost_events FROM PUBLIC;

CREATE FUNCTION nsai_reserve_cost(p_id text,p_account text,p_provider text,p_estimate bigint,p_input bigint,p_output bigint)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE old public.cost_reservations%ROWTYPE; account_row public.cost_accounts%ROWTYPE; total public.cost_accounts%ROWTYPE;
BEGIN
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

CREATE FUNCTION nsai_settle_cost(p_id text,p_actual bigint,p_input bigint,p_output bigint)
RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,public AS $$
DECLARE old public.cost_reservations%ROWTYPE; overrun boolean;
BEGIN
 IF public.nsai_actor_role() NOT IN ('operator','service') OR nullif(current_setting('nsai.job_id',true),'') IS NOT NULL THEN
  RAISE EXCEPTION 'Cost settlement not permitted' USING ERRCODE='42501';
 END IF;
 IF p_actual IS NULL OR p_actual NOT BETWEEN 0 AND 1000000000000
    OR p_input IS NULL OR p_input NOT BETWEEN 0 AND 1000000000
    OR p_output IS NULL OR p_output NOT BETWEEN 0 AND 1000000000 THEN RAISE EXCEPTION 'Invalid cost settlement'; END IF;
 PERFORM pg_advisory_xact_lock(878732);
 SELECT * INTO old FROM public.cost_reservations WHERE id=p_id FOR UPDATE;
 IF NOT FOUND OR old.actor<>public.nsai_actor() THEN RAISE EXCEPTION 'Cost reservation unavailable' USING ERRCODE='42501'; END IF;
 IF old.state='settled' THEN
  IF old.actual_units<>p_actual OR old.input_tokens<>p_input OR old.output_tokens<>p_output THEN RAISE EXCEPTION 'Settlement conflict'; END IF;
  RETURN p_id;
 END IF;
 -- Record a real provider overrun even when it exceeds the reservation or budget.
 -- Freeze new admission; never discard an invoice merely to keep a ledger green.
 overrun=p_actual>old.estimate_units OR p_input>old.input_token_ceiling OR p_output>old.output_token_ceiling;
 UPDATE public.cost_accounts SET reserved_units=reserved_units-old.estimate_units,
  spent_units=spent_units+p_actual,
  enabled=enabled AND NOT overrun AND spent_units+reserved_units-old.estimate_units+p_actual<=limit_units
 WHERE name=old.account OR (old.account LIKE 'cash-%' AND name='cash-total');
 UPDATE public.cost_reservations SET state='settled',actual_units=p_actual,input_tokens=p_input,output_tokens=p_output,settled_at=now() WHERE id=p_id;
 INSERT INTO public.cost_events(reservation_id,actor,kind,units) VALUES(p_id,public.nsai_actor(),'settled',p_actual);
 RETURN p_id;
END $$;
REVOKE ALL ON FUNCTION nsai_reserve_cost(text,text,text,bigint,bigint,bigint),nsai_settle_cost(text,bigint,bigint,bigint) FROM PUBLIC;

CREATE FUNCTION nsai_active_inference_count() RETURNS bigint LANGUAGE sql STABLE
SECURITY DEFINER SET search_path=pg_catalog,public AS $$
 SELECT count(*) FROM public.inference_runs WHERE state='reserved';
$$;
REVOKE ALL ON FUNCTION nsai_active_inference_count() FROM PUBLIC;

CREATE FUNCTION nsai_cost_status() RETURNS jsonb LANGUAGE plpgsql STABLE
SECURITY DEFINER SET search_path=pg_catalog,public AS $$
BEGIN
 IF public.nsai_actor_role() NOT IN ('admin','service') OR nullif(current_setting('nsai.job_id',true),'') IS NOT NULL THEN
  RAISE EXCEPTION 'Cost inspection not permitted' USING ERRCODE='42501';
 END IF;
 RETURN jsonb_build_object('accounts',(SELECT jsonb_agg(jsonb_build_object(
   'name',name,'unit',unit,'limit',limit_units,'reserved',reserved_units,'spent',spent_units,
   'enabled',enabled,'alert',CASE WHEN NOT enabled THEN 'disabled'
     WHEN spent_units+reserved_units>=limit_units THEN 'ceiling'
     WHEN (spent_units+reserved_units)::numeric>=limit_units::numeric*0.9 THEN '90-percent'
     WHEN (spent_units+reserved_units)::numeric>=limit_units::numeric*0.75 THEN '75-percent'
     ELSE 'normal' END) ORDER BY name) FROM public.cost_accounts),
   'unknown_outcomes_remain_reserved',true,'provider_billing_cap_guaranteed',false);
END $$;
REVOKE ALL ON FUNCTION nsai_cost_status() FROM PUBLIC;

