"""GitHub host launcher; uses one CPU, hard1GiB and direct, owned output mount."""
import json,os,pathlib,subprocess,sys,traceback
out=pathlib.Path(os.environ['RUNNER_TEMP'])/'qw-foundation01-results'
out.mkdir(parents=True,exist_ok=True)
first=min(os.sched_getaffinity(0))
cmd=['docker','create','--network','none','--memory','1g','--memory-swap','1g','--cpus','1','--cpuset-cpus',str(first),
     '--pids-limit','64','--cap-drop','ALL','--security-opt','no-new-privileges','--read-only',
     '--tmpfs','/tmp:rw,nosuid,size=256m','--user',f'{os.getuid()}:{os.getgid()}',
     '--mount',f'type=bind,src={out},dst=/out']
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','BLIS_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS']:
    cmd+=['-e',k+'=1']
cmd+=['-e','GITHUB_SHA='+os.environ.get('GITHUB_SHA',''),'core-foundation01:once']
cid=None
try:
    cid=subprocess.check_output(cmd,text=True).strip()
    conf=json.loads(subprocess.check_output(['docker','inspect',cid],text=True))[0]
    h=conf['HostConfig']
    if not(h['Memory']==1024**3 and h['MemorySwap']==1024**3 and h['NetworkMode']=='none' and h['NanoCpus']==1000000000 and not h['Privileged']):
        raise RuntimeError('HOST_CONFIG_NOT_BOUND')
    (out/'host_config_summary.json').write_text(json.dumps({'mem':h['Memory'],'memswap':h['MemorySwap'],'network':h['NetworkMode'],'nanocpus':h['NanoCpus'],'uid':conf['Config']['User'],'image':conf['Image']},indent=2)+'\n')
    code=subprocess.run(['docker','start','-a',cid],timeout=590).returncode
    if code:raise RuntimeError(f'SCIENCE_CONTAINER_EXIT_{code}')
except BaseException as e:
    (out/'host_failure.json').write_text(json.dumps({'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()},indent=2)+'\n')
    raise
finally:
    if cid:
        subprocess.run(['docker','kill',cid],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=3)
        subprocess.run(['docker','rm',cid],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=3)
