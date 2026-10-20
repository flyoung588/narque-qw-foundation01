import unittest,copy
from foundation01.contract import validate, displace, compare,SCHEMA
from foundation01.rdkit_bridge import from_smiles
from foundation01.runner import run_world

class Foundation01ContractTests(unittest.TestCase):
 def setUp(self):
  self.spec=from_smiles('CO','TEST_CO')
 def test_unimplemented_hypothesis_mode_refused(self):
  s=copy.deepcopy(self.spec);s["epistemic_mode"]="MODEL_CHALLENGE"
  with self.assertRaises(ValueError):validate(s)
 def test_unimplemented_extrapolative_mode_refused(self):
  s=copy.deepcopy(self.spec);s["epistemic_mode"]="EXTRAPOLATIVE"
  with self.assertRaises(ValueError):validate(s)
 def test_good_unhardcoded(self):
  self.assertGreater(validate(self.spec)['electron_count'],0)
 def test_missing_atoms_refused(self):
  s=copy.deepcopy(self.spec);s['matter']['atoms']=[]
  with self.assertRaises(ValueError):validate(s)
 def test_spin_parity_refused(self):
  s=copy.deepcopy(self.spec);s['matter']['spin_2S']=1
  with self.assertRaises(ValueError):validate(s)
 def test_infinite_xyz_refused(self):
  s=copy.deepcopy(self.spec);s['matter']['atoms'][0]['xyz_angstrom'][1]=float('nan')
  with self.assertRaises(ValueError):validate(s)
 def test_collision_refused(self):
  s=copy.deepcopy(self.spec);s['matter']['atoms'][1]['xyz_angstrom']=s['matter']['atoms'][0]['xyz_angstrom'][:]
  with self.assertRaises(ValueError):validate(s)
 def test_different_composition_refused(self):
  a=run_world(self.spec);b=run_world(from_smiles('N','TEST_N'))
  self.assertEqual(compare(a,b)['status'],'INCOMPARABLE')
 def test_valid_geometry_branch(self):
  s=displace(self.spec,len(self.spec['matter']['atoms'])-1,[0,0,.04],'CHILD')
  self.assertEqual(len(s['matter']['atoms']),len(self.spec['matter']['atoms']))
  a=run_world(self.spec);b=run_world(s)
  self.assertEqual(compare(a,b)['status'],'MODEL_INTERNAL_DIFFERENCE')
 def test_engine_method_refused(self):
  s=copy.deepcopy(self.spec);s['physics']['engine']='pyscf'
  with self.assertRaises(ValueError):validate(s)
 def test_noninteroperable_methods_refused(self):
  a=run_world(self.spec)
  s=copy.deepcopy(self.spec);s['physics']['method']='UFF'
  b=run_world(s)
  self.assertEqual(compare(a,b)['status'],'INCOMPARABLE')
 def test_ase_pyscf_worldspec_validated_without_loading(self):
  s=copy.deepcopy(self.spec);s['physics']={'engine':'ase-pyscf','method':'RHF','basis':'sto-3g','observables':['energy','forces']}
  self.assertGreater(validate(s)['electron_count'],0)
 def test_species_spin_restriction(self):
  s=copy.deepcopy(self.spec);s['matter']['atoms']=s['matter']['atoms'][:1]
  s['matter']['bonds']=[];s['matter']['charge']=0;s['matter']['spin_2S']=1
  s['physics']={'engine':'ase-pyscf','method':'RHF','basis':'sto-3g','observables':['energy','forces']}
  with self.assertRaises(ValueError):validate(s)

 def test_unhardcoded_fourth_quantum_system(self):
  import pathlib,json
  path=pathlib.Path(__file__).resolve().parents[1]/'cloud'/'third_worldspec_LiH.json'
  spec=json.loads(path.read_text())
  meta=validate(spec)
  self.assertEqual(meta['electron_count'],4)
  self.assertEqual([x['element'] for x in spec['matter']['atoms']],['Li','H'])
  self.assertEqual(spec['physics']['engine'],'ase-pyscf')

 def test_quantum_domain_no_large_unbounded_job(self):
  import pathlib,json
  path=pathlib.Path(__file__).resolve().parents[1]/'cloud'/'third_worldspec_LiH.json'
  spec=json.loads(path.read_text())
  spec['physics']['basis']='cc-pv5z'
  with self.assertRaisesRegex(ValueError,'QUANTUM_ONE_SHOT_DOMAIN_LIMIT'):validate(spec)

 def test_quantum_domain_no_expensive_unqualified_method(self):
  import pathlib,json
  path=pathlib.Path(__file__).resolve().parents[1]/'cloud'/'third_worldspec_LiH.json'
  spec=json.loads(path.read_text())
  spec['physics']['method']='RKS'
  with self.assertRaisesRegex(ValueError,'QUANTUM_ONE_SHOT_DOMAIN_LIMIT'):validate(spec)

if __name__=='__main__': unittest.main()
