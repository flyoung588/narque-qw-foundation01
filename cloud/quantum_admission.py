"""Fail-closed admission for a bounded GitHub-hosted science process."""
import json,os,platform,sys,hashlib
from pathlib import Path


def admit(out):
    root=Path('/sys/fs/cgroup')
    keys=['memory.max','memory.swap.max','cpu.max','memory.events','memory.peak','cpu.stat']
    controls={k:(root/k).read_text().strip() for k in keys}
    network=sorted(p.name for p in Path('/sys/class/net').iterdir())
    affinity=sorted(os.sched_getaffinity(0))
    data={'cgroup':controls,'network_interfaces':network,'affinity':affinity,'python':platform.python_version(),'run_id':os.environ.get('GITHUB_RUN_ID'),'source_sha':os.environ.get('GITHUB_SHA')}
    (Path(out)/'admission.json').write_text(json.dumps(data,indent=2)+'\n')
    mem=int(controls['memory.max']) if controls['memory.max']!='max' else 10**100
    quota,period=controls['cpu.max'].split()
    if (mem>1024**3 or controls['memory.swap.max']!='0' or quota=='max' or int(quota)>int(period) or network!=['lo'] or len(affinity)!=1):
        raise RuntimeError('QUANTUM_RUNNER_ADMISSION_FAILED')
    return data

if __name__=='__main__':
    out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
    try:admit(out)
    except Exception as e:
        (out/'admission_failure.json').write_text(json.dumps({'type':type(e).__name__,'message':str(e)},indent=2)+'\n')
        raise
