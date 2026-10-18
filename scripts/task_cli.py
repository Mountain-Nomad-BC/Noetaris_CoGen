"""Simple source-of-record task ledger manager. Does not modify status without user command.

Examples: python scripts/task_cli.py next
          python scripts/task_cli.py show ING-02
          python scripts/task_cli.py set ING-02 IN_PROGRESS
          python scripts/task_cli.py set ING-02 PASS
"""
import csv,json,sys
from pathlib import Path


def main():
    P=Path(__file__).resolve().parents[1]/'plans'
    PATH=P/'TASK_LEDGER.json'
    VALID={'NOT_STARTED','IN_PROGRESS','BLOCKED','PASS','FAIL','DEFER',
           'SCAFFOLD_READY','STATIC_PASS_RUNTIME_UNVERIFIED','EXISTING_UNVERIFIED',
           'ANALYZED_NOT_PORTED','HELPER_READY','CONFIG_ONLY','CLIENT_ONLY',
           'CONTRACT_READY','SOURCE_AUDITED_PARTIAL','HELPER_ONLY',
           'BASELINE_ONLY','MINI_CONSOLE_EXISTS','SMOKE_ONLY','PURE_GATE_READY',
           'PARTIAL_EXISTING','CLIENT_SCAFFOLD_ONLY','MINIMAL_FIXTURES_READY',
           'STATIC_BASELINE_ONLY','NOT_COMPLETE','IN_PROGRESS','BASIC_DEMO_EXISTS'}
    tasks=json.loads(PATH.read_text())
    by_id={t['id']:t for t in tasks}

    def deps(t):return [x.strip() for x in t['depends_on'].split(',') if x.strip()]

    def ready(t):return all(by_id[d]['status']=='PASS' for d in deps(t))

    def show(t):
        for k,v in t.items(): print(f'{k}: {v}')

    cmd=sys.argv[1:] or ['next']
    if cmd[0]=='next':
        for t in tasks:
            if t['status'] not in ('PASS','DEFER'):
                pending=[d for d in deps(t) if by_id[d]['status']!='PASS']
                print(f"{t['id']:9} {t['status'][:18]:18} {'READY' if not pending else 'wait '+','.join(pending):18} {t['title']}")
    elif cmd[0]=='show' and len(cmd)==2 and cmd[1] in by_id:show(by_id[cmd[1]])
    elif cmd[0]=='set' and len(cmd)==3 and cmd[1] in by_id and cmd[2] in VALID:
        t=by_id[cmd[1]]
        if cmd[2]=='PASS' and not ready(t):
            raise SystemExit('Cannot mark PASS: prerequisites not all PASS: '+','.join(d for d in deps(t) if by_id[d]['status']!='PASS'))
        t['status']=cmd[2]
        PATH.write_text(json.dumps(tasks,indent=2)+'\n',encoding='utf-8')
        with (P/'TASK_LEDGER.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=list(tasks[0]));w.writeheader();w.writerows(tasks)
        print(t['id'],'=',t['status'])
    else:
        raise SystemExit('Usage: task_cli.py next | show TASK-ID | set TASK-ID {IN_PROGRESS|BLOCKED|PASS|FAIL|DEFER}')


if __name__ == "__main__":
    main()
