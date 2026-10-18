"""Read-only staged deployment assessment; never creates admission substitutes."""
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess
import urllib.error
import urllib.request
from uuid import uuid4

from check_release_readiness import validate,source_snapshot
from start_integration import ROOT,STATE,PROJECT
from qualification_shards import coverage


def regression_snapshot(root):
    snapshot=source_snapshot(root)
    snapshot.update({p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in (root/'tests').rglob('*') if p.is_file() and (p.suffix=='.py' or p.name.endswith('.test.ts'))})
    return snapshot


def assess_frontend_operations(receipt,identity):
    roles={'operator':{'read'},'viewer':{'read'},'reviewer':{'read','review'},'admin':{'read','review','admin'}}
    pages={'developers':'read','models':'read','integrations':'read','analytics':'admin','observability':'admin',
           'audit':'review','governance':'admin','settings':'admin'}
    expected={(role,page) for role in roles for page in pages}
    checks=receipt.get('checks',[])
    valid=(isinstance(checks,list) and len(checks)==len(expected) and
           all(isinstance(c,dict) for c in checks))
    if valid:
        valid={(c.get('role'),c.get('page')) for c in checks}==expected
    if valid:
        for c in checks:
            allowed=pages[c['page']] in roles[c['role']]
            valid=valid and c.get('passed') is True and c.get('allowed') is allowed and (
                type(c.get('live_rows')) is int and c['live_rows']>0 if allowed else
                c.get('explicit_permission_denial') is True)
    paths={'developers':'/v1/capabilities','models':'/v1/model/status','integrations':'/v1/integrations/status',
           'analytics':'/v1/admin/resources','observability':'/v1/admin/resources',
           'audit':'/v1/audit','governance':'/v1/admin/security','settings':'/v1/admin/security'}
    responses=receipt.get('api_responses',[])
    required_requests={(role,paths[page]) for role in roles for page in pages if pages[page] in roles[role]}
    valid=(valid and receipt.get('status')=='PASS_SCOPED' and receipt.get('identity')==identity and
           receipt.get('identity_unchanged') is True and receipt.get('page_errors')==[] and
           isinstance(responses,list) and bool(responses) and
           all(isinstance(r,dict) and type(r.get('status')) is int and 100<=r['status']<500 for r in responses) and
           required_requests<={(r.get('role'),r.get('path')) for r in responses if r['status']==200})
    return dict(status='PASS_SCOPED' if valid else 'NEEDS_CURRENT_RUN',
                scope='Seven live read-only operations pages across four roles; not full frontend feature acceptance',
                expected_cases=len(expected),observed_cases=len(checks) if isinstance(checks,list) else 0)


def assess_regression(folder,identity,current_source):
    """Reconcile actual JUnit cases and immutable runtime/source identities."""
    receipt=json.loads((folder/'receipt.json').read_text())
    nodes=json.loads((folder/'collection.json').read_text())
    actual,_=coverage(nodes,[folder/'tests.xml'])
    counts=actual['counts']
    passed=(receipt.get('status')=='PASS_SCOPED' and receipt.get('coverage_exact') is True and
            receipt.get('source_unchanged') is True and receipt.get('source_before')==current_source and
            receipt.get('api_image')==identity['images']['api'] and
            receipt.get('db_image')==identity['images']['db'] and
            receipt.get('cleanup',{}).get('complete') is True and actual['exact'] and
            receipt.get('counts')==counts and counts['tests']>0 and
            all(counts[k]==0 for k in ('failures','errors','skipped')) and
            receipt.get('result',{}).get('exit_code')==0 and
            receipt.get('result',{}).get('timed_out') is False)
    return dict(status='PASS_SCOPED' if passed else 'NEEDS_CURRENT_RUN',counts=counts,
                source_matches=receipt.get('source_before')==current_source,
                coverage_exact=actual['exact'],independent_acceptance=False)


def http_status(path):
    try:
        with urllib.request.urlopen('http://127.0.0.1:8790'+path,timeout=5) as response:
            response.read(16384)
            return response.status
    except urllib.error.HTTPError as error:return error.code
    except (OSError,TimeoutError):return None


def inspect_services():
    command=['docker','compose','-p',PROJECT,'-f',str(STATE/'compose.json'),'ps','-q']
    result=subprocess.run(command,capture_output=True,timeout=30)
    if result.returncode:raise RuntimeError('Integration container inventory unavailable')
    ids=result.stdout.decode().split()
    if not ids:raise RuntimeError('Integration project is not running')
    result=subprocess.run(['docker','inspect',*ids],capture_output=True,timeout=30)
    if result.returncode:raise RuntimeError('Integration inspection unavailable')
    networks={}
    for item in json.loads(result.stdout):
        for entry in item['NetworkSettings']['Networks'].values():
            network_id=entry['NetworkID']
            if network_id not in networks:
                network_result=subprocess.run(['docker','network','inspect',network_id],capture_output=True,timeout=30)
                if network_result.returncode:raise RuntimeError('Integration network inspection unavailable')
                network=json.loads(network_result.stdout)[0]
                networks[network_id]=dict(internal=network['Internal'],
                    owned=network.get('Labels',{}).get('com.docker.compose.project')==PROJECT,
                    name=network.get('Labels',{}).get('com.docker.compose.network'))
    services=[]
    for item in json.loads(result.stdout):
        labels=item['Config'].get('Labels',{})
        if labels.get('com.docker.compose.project')!=PROJECT:
            raise RuntimeError('Foreign container in integration inventory')
        ports=[dict(container=port,host_ip=entry['HostIp'],host_port=entry['HostPort'])
               for port,entries in item['NetworkSettings']['Ports'].items() for entry in entries or []]
        services.append(dict(service=labels.get('com.docker.compose.service'),image=item['Image'],
            running=item['State']['Running'],health=item['State'].get('Health',{}).get('Status'),
            read_only=item['HostConfig']['ReadonlyRootfs'],published_ports=ports,
            user=item['Config']['User'],privileged=item['HostConfig']['Privileged'],
            cap_drop=item['HostConfig'].get('CapDrop') or [],cap_add=item['HostConfig'].get('CapAdd') or [],
            security_opt=item['HostConfig'].get('SecurityOpt') or [],
            memory=item['HostConfig']['Memory'],nano_cpus=item['HostConfig']['NanoCpus'],
            pids_limit=item['HostConfig'].get('PidsLimit'),
            network_mode=item['HostConfig']['NetworkMode'],
            pid_mode=item['HostConfig'].get('PidMode',''),ipc_mode=item['HostConfig'].get('IpcMode',''),
            devices=bool(item['HostConfig'].get('Devices') or item['HostConfig'].get('DeviceRequests')),
            networks=[networks[n['NetworkID']] for n in item['NetworkSettings']['Networks'].values()]))
    return services


def runtime_violations(services):
    """Check actual runtime isolation, rather than intended Compose settings."""
    expected={'api','db','parser','llama-cpp','ui','encoder'}
    issues=[]
    if len(services)!=len(expected) or {s['service'] for s in services}!=expected:
        issues.append('Service inventory differs from the six-service profile')
    allowed_networks={'api':{'data','parser','model','edge','encoder'},'db':{'data'},
        'parser':{'parser'},'llama-cpp':{'model'},'encoder':{'encoder'},'ui':{'edge','front'}}
    for service in services:
        name=service['service']
        def reject(condition,reason):
            if condition:issues.append(str(name)+': '+reason)
        reject(not service['running'] or service['health']!='healthy','not running and healthy')
        reject(service['read_only'] is not True,'writable root filesystem')
        reject(service['user']!=({'db':'70:70','ui':'101:101'}.get(name,'10001:10001')),'unexpected runtime user')
        reject(service['privileged'] is not False or service['cap_add'] or 'ALL' not in service['cap_drop'],
               'capability or privileged-mode drift')
        reject('no-new-privileges:true' not in service['security_opt'],'new privileges not disabled')
        reject(any('unconfined' in option for option in service['security_opt']),'unconfined security profile')
        reject(service['pid_mode'] not in {'','private'} or service['ipc_mode'] not in {'','private'},
               'shared process or IPC namespace')
        reject(service['devices'],'unexpected device access')
        reject(type(service['memory']) is not int or service['memory']<=0 or service['memory']>8*1024**3,
               'memory limit missing or outside bounded profile')
        reject(type(service['nano_cpus']) is not int or not 0<service['nano_cpus']<=4*10**9,
               'CPU limit missing or outside bounded profile')
        reject(type(service['pids_limit']) is not int or not 0<service['pids_limit']<=128,
               'process limit missing or outside bounded profile')
        reject(service['network_mode'] in {'host','none'} or service['network_mode'].startswith('container:'),
               'unexpected network namespace')
        ports=service['published_ports']
        expected_ports=[dict(container='8080/tcp',host_ip='127.0.0.1',host_port='8790')] if name=='ui' else []
        reject(ports!=expected_ports,'unexpected published ports')
        nets=service['networks']
        reject(len(nets)!=len(allowed_networks.get(name,set())) or
               {n['name'] for n in nets}!=allowed_networks.get(name,set()),'network membership drift')
        reject(any(n['owned'] is not True or n['internal'] is not (n['name']!='front') for n in nets),
               'network ownership or egress isolation drift')
    return issues


def main():
    report=dict(captured_at=datetime.now(timezone.utc).isoformat(),run_id=uuid4().hex,
                authority='Read-only readiness assessment; no independent acceptance or release authorization',
                runtime_mutations_performed=False,local_report_written=True,stages={})
    errors=[]
    try:
        identity=json.loads((STATE/'identity.json').read_text())
        services=inspect_services()
        health={p:http_status(p) for p in ['/','/healthz','/readyz','/v1/documents']}
        isolation_issues=runtime_violations(services)
        local=(not isolation_issues and
               health=={'/':200,'/healthz':200,'/readyz':200,'/v1/documents':401})
        # Bind the inventory to the exact retained configuration, not just tags.
        config_hash=hashlib.sha256((STATE/'compose.json').read_bytes()).hexdigest()
        local=local and identity.get('compose_sha256')==config_hash
        image_keys={'api':'api','parser':'api','db':'db','ui':'ui','encoder':'encoder','llama-cpp':'model'}
        local=local and all(s['image']==identity.get('images',{}).get(image_keys[s['service']]) for s in services)
        report['stages']['local_integration']=dict(status='PASS_SCOPED' if local else 'FAIL',
            services=services,isolation_violations=isolation_issues,http_status=health,model_id=identity.get('model_id'),
            compose_sha256=config_hash,scope='Current local health/auth denial only; not full feature acceptance')
        receipts=[]
        for path in (ROOT/'evidence/integration-deployment').glob('http-*.json'):
            data=json.loads(path.read_text())
            if data.get('identity',{}).get('model_id','').startswith('google/gemma'):
                receipts.append((path,data))
        receipts.sort(key=lambda pair:pair[0].stat().st_mtime)
        latest=receipts[-1] if receipts else None
        current=bool(latest and latest[1].get('identity')==identity and latest[1].get('status')=='PASS')
        report['stages']['gemma_workflow']=dict(status='PASS_SCOPED' if current else 'NEEDS_CURRENT_RUN',
            latest_receipt=str(latest[0].relative_to(ROOT)) if latest else None,
            retained_failed_runs=sum(d.get('status')=='FAIL' for _,d in receipts),
            independent_quality_acceptance=False)
        recoveries=sorted((STATE/'recovery').glob('*/receipt.json'),key=lambda p:p.stat().st_mtime)
        recovery=json.loads(recoveries[-1].read_text()) if recoveries else {}
        recovery_ok=(recovery.get('status')=='PASS' and recovery.get('cleanup_complete') is True and
                     recovery.get('database_image')==identity.get('images',{}).get('db') and
                     recovery.get('application_image')==identity.get('images',{}).get('api'))
        report['stages']['recovery']=dict(status='PASS_SCOPED' if recovery_ok else 'NEEDS_CURRENT_REHEARSAL',
            receipt=str(recoveries[-1].relative_to(ROOT)) if recoveries else None,
            scope='Quiescent owned integration only; production history and PITR remain separate')
        regressions=sorted((ROOT/'evidence/integration-deployment').glob('qualification-*/receipt.json'),
                           key=lambda p:p.stat().st_mtime)
        report['stages']['regression']=(assess_regression(regressions[-1].parent,identity,regression_snapshot(ROOT))
            if regressions else dict(status='NEEDS_CURRENT_RUN'))
        report['stages']['regression']['receipt']=(str(regressions[-1].relative_to(ROOT)) if regressions else None)
        browsers=sorted((ROOT/'evidence/integration-deployment').glob('live-operations-*.json'),key=lambda p:p.stat().st_mtime)
        report['stages']['frontend_operations']=(assess_frontend_operations(json.loads(browsers[-1].read_text()),identity)
            if browsers else dict(status='NEEDS_CURRENT_RUN'))
        report['stages']['frontend_operations']['receipt']=str(browsers[-1].relative_to(ROOT)) if browsers else None
    except (OSError,ValueError,RuntimeError,KeyError,TypeError,subprocess.SubprocessError) as error:
        errors.append(type(error).__name__)
    report['stages']['partner_deployment']=dict(status='BLOCKED',
        missing=['Dedicated AMD deployment and authenticated quota/credit commissioning',
                 'Qualified remote tokenizer admission, provider accounting and controlled source-export dispatch'],
        note='Synthetic provider probes and route selection tests do not implement remote dispatch')
    report['optional_integrations']=dict(evolus=dict(status='NOT_CONFIGURED',required_for_core_deployment=False,
        dispatch_enabled=False,missing=['Verified application/workspace, workflow, agent and extractor bindings; payload/output contract and live verification']))
    gate=validate()
    report['stages']['release_admission']=dict(status=gate['status'],findings=len(gate['errors']),
                                              independent_acceptance_required=True)
    report['source_snapshot_sha256']=hashlib.sha256(json.dumps(source_snapshot(ROOT),sort_keys=True,separators=(',',':')).encode()).hexdigest()
    report['errors']=errors
    passed={'PASS','PASS_SCOPED','ADMITTED'}
    report['status']='READY' if not errors and all(s.get('status') in passed for s in report['stages'].values()) else 'NOT_READY'
    output=ROOT/'evidence/integration-deployment'/('stage-readiness-'+report['run_id']+'.json')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(status=report['status'],stages={k:v['status'] for k,v in report['stages'].items()},
                          errors=errors,report=str(output)),indent=2))
    return 0 if report['status']=='READY' else 1


if __name__=='__main__':raise SystemExit(main())
