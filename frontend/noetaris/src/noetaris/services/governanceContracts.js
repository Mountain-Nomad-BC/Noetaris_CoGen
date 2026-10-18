const integer = value => Number.isSafeInteger(value) && value >= 0;
const digest = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
export function governanceOverview(value) {
  const names = ['amd-credits','evolus-credits'];
  const limits = ['concurrent_users','requests_per_minute','generations_per_user','ingestions_per_user','generations_per_day','gpu_jobs','gpu_queue'];
  const accounts = value?.credit_ledger?.accounts;
  if (value?.mode !== 'demonstration-only' || value.cash_dispatch_enabled !== false || value.local_token_ceiling !== null ||
      value.credit_ledger?.provider_billing_cap_guaranteed !== false || value.credit_ledger?.unknown_outcomes_remain_reserved !== true ||
      !Array.isArray(accounts) || accounts.length !== 2 || new Set(accounts.map(row=>row.name)).size !== 2 ||
      accounts.some(row=>!names.includes(row.name) || row.unit !== 'provider-credit-unit' || !['limit','reserved','spent'].every(key=>integer(row[key])) || typeof row.enabled !== 'boolean' || !['disabled','ceiling','90-percent','75-percent','normal'].includes(row.alert)) ||
      !limits.every(key=>integer(value.limits?.[key]) && value.limits[key]>0) ||
      !['explanation','generation_accounting','configuration_source'].every(key=>typeof value[key] === 'string'))
    throw new Error('Unrecognized governance response; no balances or limits assumed.');
  return value;
}
export function usageObservation(value) {
  if(value?.metric_version !== 'local-resource/1' || value.period !== 'current UTC day' ||
    !['attempts','completed_inferences','latency_observations','token_observations'].every(key=>integer(value[key])) ||
    !['observed_latency_ms','observed_completion_tokens'].every(key=>value[key]===null || integer(value[key])) ||
    value.completed_is_verified_resolution !== false || value.financial_cost !== null || value.verified_outcome_cost !== null || !digest(value.source_receipt_sha256))
      throw new Error('Unrecognized measured usage; unknown observations remain unknown.');
  return value;
}
