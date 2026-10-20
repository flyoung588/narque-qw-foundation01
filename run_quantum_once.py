"""Executable quantum pilot, REQUIRES live ASE/PySCF environment and scope approval.

Does not dispatch, install dependencies or write to remote endpoints. It uses
single-point electronic Born-Oppenheimer mean-field, not time-dependent TDSE.
"""
import os
for key in ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","VECLIB_MAXIMUM_THREADS","NUMEXPR_NUM_THREADS"):
    os.environ[key]="1"
import argparse,json,hashlib,signal,time,traceback,resource,sys
from pathlib import Path
from foundation01.contract import validate,displace,compare
from foundation01.runner import run_world,save_json


def deadline(*_):raise TimeoutError("FINITE_QUANTUM_PILOT_CPU_WALL_BUDGET")


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out',default='quantum-output')
    p.add_argument('--third-spec',default=None,help='A new, physically valid runtime-supplied WorldSpec, not a hardcoded molecule adapter')
    args=p.parse_args();start=time.monotonic();out=Path(args.out);out.mkdir(exist_ok=True,parents=True)
    signal.signal(signal.SIGALRM,deadline);signal.alarm(420)
    passed=[];failed=[];observations={}
    inputs=['ase_pyscf_hehp.json','ase_pyscf_h2o.json','pyscf_atomic_h.json']
    if args.third_spec:inputs.append(str(Path(args.third_spec).resolve()))
    try:
        for ix,entry in enumerate(inputs):
            path=Path(entry) if Path(entry).is_absolute() else Path(__file__).parent/'examples'/entry
            spec=json.loads(path.read_text());validate(spec)
            save_json(out/(path.stem+'.input_receipt.json'), {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'object_id':spec['object_id'],'electron_count':validate(spec)['electron_count'],'scope':'bounded mean-field BO quantum single point'})
            print('QUANTUM_WORLD_START',path.stem,flush=True)
            obs=run_world(spec)
            name=path.stem
            save_json(out/(name+'.observation.json'),obs)
            observations[name]=obs
            print('QUANTUM_WORLD_RESULT',name,obs['status'],flush=True)
            if obs['status'] != 'CALCULATED' or not obs['observation'].get('electronic_structure_solved',False):
                raise RuntimeError('NO_QUANTUM_ELECTRONIC_COMPUTATION_FOR_'+name)
            passed.append(name)
        atom=observations['pyscf_atomic_h']['observation']['energy']
        if not(-0.5-1e-5<=atom<=-0.3):raise RuntimeError('H_ANALYTIC_LIMIT_CHECK_FAILED')
        initial=observations['ase_pyscf_hehp']
        perturbed=displace(initial['spec'],1,[0,0,0.002],'WORLD_HEHPLUS_BRANCH')
        branch=run_world(perturbed)
        save_json(out/'hehp_branch.observation.json',branch)
        comp=compare(initial,branch)
        save_json(out/'hehp_geometry_compare.json',comp)
        if comp['status']!='MODEL_INTERNAL_DIFFERENCE':raise RuntimeError('SAME_PHYSICS_GEOMETRY_COMPARE_FAIL')
        # Force = -gradient with respect to nuclear Cartesian coordinates (energy eV, distance Å)
        h=.001
        plus=run_world(displace(initial['spec'],1,[0,0,h],'FINITE_PLUS'))
        minus=run_world(displace(initial['spec'],1,[0,0,-h],'FINITE_MINUS'))
        fd=-(plus['observation']['energy_eV']-minus['observation']['energy_eV'])/(2*h)
        force=initial['observation']['forces_eV_per_angstrom'][1][2]
        delta=abs(fd-force)
        save_json(out/'hehp_force_fd.json',{'finite_difference_eV_per_angstrom':fd,'analytic_gradient_from_PySCF_eV_per_angstrom':force,
            'absolute_error_eV_per_angstrom':delta,'step_angstrom':h,
            'source':'same PySCF electronic integral engine; numerical gradient consistency, not independent physical validation'})
        if delta>.05:raise RuntimeError('FORCE_CONSISTENCY_FAILURE')
        result={'status':'W1_BOUNDED_QUANTUM_CONSTRUCTION_PROVEN', 'actually_executed_inputs':passed,
                'one_dynamic_runtime_spec_input':bool(args.third_spec),'third_input':str(Path(args.third_spec).name) if args.third_spec else None,
                'quantum_electronic_energy_observations':{x:{'energy_Eh':v['observation']['energy'],'basis':v['observation']['basis'],'method':v['observation']['method']} for x,v in observations.items()},
                'H_analytic_minus_half_error_Eh':atom+0.5,'HeHplus_force_fd_error_eV_per_angstrom':delta,
                'W2_independent_engine':'NOT_TESTED','W3_autonomous_feedback':'NOT_TESTED','new_physical_discovery':'NOT_TESTED',
                'scope':'nonperiodic fixed-nuclei finite-basis mean-field energy/gradient only'}
        save_json(out/'FINAL_RECEIPT.json',result)
        print(json.dumps(result,indent=2))
    except Exception as e:
        failed.append(str(e));save_json(out/'FAILURE_RECEIPT.json',{'error':str(e),'traceback':traceback.format_exc(),
                'partial_passed':passed,'no_scope_relaxation':True})
        raise
    finally:
        signal.alarm(0)
        save_json(out/'RESOURCES.json',{'wall_seconds':time.monotonic()-start,'rusage_ru_maxrss_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                          'rusage_user_seconds':resource.getrusage(resource.RUSAGE_SELF).ru_utime,'rusage_system_seconds':resource.getrusage(resource.RUSAGE_SELF).ru_stime})
        manifest={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in out.iterdir() if f.is_file() and f.name!='SHA256.json'}
        save_json(out/'SHA256.json',manifest)
if __name__=='__main__':main()
