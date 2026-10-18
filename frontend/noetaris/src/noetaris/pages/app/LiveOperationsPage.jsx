import React,{useEffect,useState} from 'react';
import {useAuth} from '../../state/AuthContext';
import {apiRequest} from '../../services/api';
import {operationSpecs,operationView} from '../../services/operationContracts';

const display=value=>value===null?'Unknown / not observed':typeof value==='boolean'?(value?'Yes':'No'):String(value);
export default function LiveOperationsPage({kind}){
  const auth=useAuth();const spec=operationSpecs[kind];
  const allowed=!!spec&&auth.identity?.permissions?.includes(spec.permission);
  const [reload,setReload]=useState(0);const [snapshot,setSnapshot]=useState(null);const [error,setError]=useState(null);
  useEffect(()=>{
    setSnapshot(null);setError(null);if(!allowed)return;
    const controller=new AbortController();let current=true;
    apiRequest(spec.path,{signal:controller.signal}).then(value=>{
      if(current)setSnapshot({...operationView(kind,value),at:new Date().toISOString(),actor:auth.identity.actor,kind});
    }).catch(failure=>{if(current){setSnapshot(null);setError(failure.message);}});
    return()=>{current=false;controller.abort();};
  },[allowed,auth.identity?.actor,kind,reload]);
  const visible=snapshot?.actor===auth.identity?.actor&&snapshot?.kind===kind?snapshot:null;
  if(!spec)return <main role="alert">Unknown operation.</main>;
  if(!allowed)return <main role="alert" className="p-4">{spec.permission} permission is required for {spec.title.toLowerCase()}.</main>;
  return <main className="p-4 md:p-8 space-y-5 min-w-0" data-testid={'live-operation-'+kind}>
    <h1 className="font-display text-2xl">{spec.title}</h1>
    <button className="n-btn-ghost p-2" onClick={()=>setReload(v=>v+1)}>Refresh server observations</button>
    {error?<p role="alert">{error}</p>:!visible?<p role="status">Loading server observations...</p>:<>
      <p>{visible.notice}</p><p>Observed at {visible.at}</p>
      <dl className="grid grid-cols-1 md:grid-cols-2 gap-3">{visible.rows.map((row,i)=><div className="n-panel rounded p-3 min-w-0" key={i}>
        <dt>{row.label}</dt><dd className="break-all" data-observation={row.label}>{display(row.value)}</dd>
      </div>)}</dl>
      {kind==='audit'&&<section className="space-y-3" aria-label="Visible audit events">{visible.events.length===0?<p>No authorized events returned.</p>:
        visible.events.map((event,i)=><article className="n-panel rounded p-3 break-all" key={i}>
          <p>{event.at} — {event.type}</p><p>Actor: {event.actor}</p><p>SHA-256: {event.digest}</p>
        </article>)}</section>}
    </>}
  </main>;
}
