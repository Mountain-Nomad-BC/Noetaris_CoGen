import React,{useEffect,useState} from 'react';
import {useAuth} from '../../state/AuthContext';
import {apiRequest} from '../../services/api';
import {governanceOverview,usageObservation} from '../../services/governanceContracts';

const labels={concurrent_users:'Concurrent users',requests_per_minute:'Ordinary API requests / minute / user',generations_per_user:'Active generations / user',ingestions_per_user:'Active ingestions / user',generations_per_day:'AI generations / UTC day / user',gpu_jobs:'Active GPU inference jobs',gpu_queue:'Queued GPU inference jobs'};
const observed=value=>value===null?'Unknown / not observed':String(value);
export default function LiveCostsPage(){
  const auth=useAuth();const allowed=auth.identity?.permissions?.includes('admin');
  const [reload,setReload]=useState(0);const [snapshot,setSnapshot]=useState(null);const [error,setError]=useState(null);
  useEffect(()=>{
    setSnapshot(null);setError(null);if(!allowed)return;
    const controller=new AbortController();let current=true;
    (async()=>{
      const results=await Promise.allSettled([apiRequest('/v1/admin/costs',{signal:controller.signal}),apiRequest('/v1/admin/resources',{signal:controller.signal})]);
      if(!current)return;
      try{for(const result of results)if(result.status==='rejected')throw result.reason;
        setSnapshot({overview:governanceOverview(results[0].value),usage:usageObservation(results[1].value),at:new Date().toISOString()});
      }catch(failure){setSnapshot(null);setError(failure.message);}
    })();
    return()=>{current=false;controller.abort();};
  },[allowed,auth.identity?.actor,reload]);
  if(!allowed)return <main role="alert" className="p-4">Administrator permission is required for usage and credit governance.</main>;
  return <main className="p-4 md:p-8 space-y-5 min-w-0" data-testid="live-costs">
    <h1 className="font-display text-2xl">Usage and cost governance</h1>
    <p>Cash-funded dispatch is prohibited. Usage is governed by request rates, generation allowances and resource limits.</p>
    <button className="n-btn-ghost p-2" onClick={()=>setReload(value=>value+1)}>Refresh measured governance</button>
    {error?<p role="alert">{error}</p>:!snapshot?<p role="status">Loading authoritative governance observations...</p>:<>
      <p className="break-all">Observed at {snapshot.at}. Refresh to read current balances and limits.</p>
      <section className="n-panel p-4 rounded-xl space-y-3" data-testid="live-usage-limits"><h2 className="font-display text-xl">Configured usage limits</h2>
        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3">{Object.entries(labels).map(([key,label])=><div key={key}><dt>{label}</dt><dd data-limit={key}>{snapshot.overview.limits[key]}</dd></div>)}</dl>
        <p>{snapshot.overview.generation_accounting}</p><p>Local compute has no aggregate token ceiling; per-request context/output and resource controls still apply.</p>
        <p>{snapshot.overview.configuration_source}</p>
      </section>
      <section className="n-panel p-4 rounded-xl space-y-3" data-testid="live-credit-ledgers"><h2 className="font-display text-xl">Separate provider credit ledgers</h2>
        {snapshot.overview.credit_ledger.accounts.map(account=><article className="n-glass rounded p-3" key={account.name} data-credit-account={account.name}>
          <h3>{account.name}</h3><dl className="grid grid-cols-1 sm:grid-cols-2 gap-2">{['limit','reserved','spent'].map(key=><div key={key}><dt>{key} (provider-credit units)</dt><dd data-credit-value={key}>{account[key]}</dd></div>)}</dl>
          <p>Dispatch account: {account.enabled?'enabled':'disabled'}; alert: {account.alert}.</p>
        </article>)}
        <p>Balances use provider-credit units, not dollars or interchangeable provider credits. Unknown outcomes remain reserved. Provider billing caps are not guaranteed; alerts alone do not impose a spending cap.</p>
      </section>
      <section className="n-panel p-4 rounded-xl space-y-2" data-testid="live-usage-observations"><h2 className="font-display text-xl">Measured authorized usage</h2>
        <p>{snapshot.usage.period}. Counts reflect currently authorized visible inference records; they do not attest all workspace activity.</p>
        <dl>{[['Generation attempts','attempts'],['Completed inferences','completed_inferences'],['Observed total latency (ms)','observed_latency_ms'],['Latency observations','latency_observations'],['Observed completion tokens','observed_completion_tokens'],['Token observations','token_observations'],['Financial cost','financial_cost'],['Cost per verified outcome','verified_outcome_cost']].map(([label,key])=><div key={key}><dt>{label}</dt><dd data-usage={key}>{observed(snapshot.usage[key])}</dd></div>)}</dl>
        <p>Completed inference does not mean a verified resolution. Missing denominators remain unknown.</p>
        <p className="break-all">Observation receipt SHA-256: {snapshot.usage.source_receipt_sha256}</p>
      </section>
      <section className="n-glass p-4 rounded-xl space-y-2" data-testid="cost-governance-demonstration"><h2 className="font-display text-xl">Monetary governance demonstration</h2>
        <p>{snapshot.overview.explanation}</p><p>Example only: $20 exposure, with $5 cloud, $10 API/voice and $5 contingency. These figures allocate no money and enable no provider.</p>
        <p>No cash activation or purchase controls are provided.</p>
      </section>
    </>}
  </main>;
}
