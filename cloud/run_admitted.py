"""Run exactly one bounded Foundation-01 quantum execution; preserve any partial evidence."""
import os,sys,subprocess,json,hashlib,traceback,platform,time
from pathlib import Path
from quantum_admission import admit

out=Path('/out');out.mkdir(parents=True,exist_ok=True)
try:
    admit(out)
    from foundation01.contract import validate
    candidate=Path('/app/cloud/third_worldspec_LiH.json')
    spec=json.loads(candidate.read_text())
    meta=validate(spec)
    if (spec['physics']['engine']!='ase-pyscf' or spec['physics']['method']!='RHF' or spec['physics']['basis']!='cc-pvdz' or
        len(spec['matter']['atoms'])>8 or meta['electron_count']>30):
        raise ValueError('THIRD_INPUT_OUTSIDE_APPROVED_QUANTUM_DOMAIN')
    (out/'third_input_sha256.json').write_text(json.dumps({'spec_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'meta':meta,'object_id':spec['object_id'],'source':'prewritten before any live quantum request'},indent=2)+'\n')
    import ase,pyscf,numpy,scipy,jsonschema
    (out/'installed_versions.json').write_text(json.dumps({'python':platform.python_version(),'ase':ase.__version__,'pyscf':pyscf.__version__,'numpy':numpy.__version__,'scipy':scipy.__version__,'jsonschema':jsonschema.__version__ if hasattr(jsonschema,'__version__') else 'installed'},indent=2)+'\n')
    cmd=[sys.executable,'-B','/app/run_quantum_once.py','--out',str(out),'--third-spec',str(candidate)]
    print('FOUNDATION_QUANTUM_START',flush=True)
    code=subprocess.run(cmd,timeout=420,cwd='/app').returncode
    print('FOUNDATION_QUANTUM_EXIT',code,flush=True)
    if code:raise RuntimeError(f'QUANTUM_SCIENCE_JOB_FAILED_CODE_{code}')
except BaseException as e:
    (out/'cloud_execution_failure.json').write_text(json.dumps({'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()},indent=2)+'\n')
    raise
