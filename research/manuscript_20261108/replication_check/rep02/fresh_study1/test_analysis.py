import unittest
from analyze import trajectory
class AnalysisTests(unittest.TestCase):
 def test_censoring_preexposure_and_seed_exclusion(self):
  terms=[dict(id=0,word='example',linguistic='lexical',sentiment='positive')]
  s=dict(source_agent=0,target_cycles=100,completed=True,posts=[],comments=[],exposures=[dict(agent=1,term_ids=[0],cycle=2,turn=1),dict(agent=2,term_ids=[0],cycle=3,turn=2)],events=[])
  for agent,cycle in [(0,1),(1,3),(2,1)]:s['events'].append(dict(agent=agent,cycle=cycle,turn=agent,action='write',generated=dict(term_ids=[0])))
  terms,pairs,curves,counts,summary=trajectory(s,terms,'SYNTHETIC_TEST_ONLY')
  self.assertEqual(terms[0]['exposure_linked_first_users'],1)
  self.assertEqual(terms[0]['preexposure_first_users'],1)
  self.assertIsNone(terms[0]['time_50percent']);self.assertFalse(terms[0]['time_50percent_observed'])
  self.assertEqual(terms[0]['time_50percent_followup'],100);self.assertEqual(len(pairs),9)
  self.assertEqual(curves[-1]['linked_users'],1)
 def test_same_turn_exposure_is_prior_to_comment(self):
  s=dict(source_agent=0,target_cycles=100,posts=[],comments=[],exposures=[dict(agent=1,term_ids=[0],cycle=2,turn=1)],events=[dict(agent=1,cycle=2,turn=1,action='comment',generated=dict(term_ids=[0]))])
  u,p,*_=trajectory(s,[dict(id=0,word='example',linguistic='lexical',sentiment='positive')],'SYNTHETIC_TEST_ONLY')
  self.assertEqual(u[0]['time_first_linked_use'],2);self.assertEqual(u[0]['exposure_to_use_mean_cycle_lag'],0)
if __name__=='__main__':unittest.main()
