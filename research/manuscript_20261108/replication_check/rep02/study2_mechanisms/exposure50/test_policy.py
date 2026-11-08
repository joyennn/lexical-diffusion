import unittest
from feed_policy import select_pool
class PolicyTests(unittest.TestCase):
 def setUp(self):self.posts=[dict(id=i,agent=0,initial_material=True) for i in range(60)]+[dict(id=60,agent=2,initial_material=False),dict(id=61,agent=1,initial_material=False)]
 def test_zero_matches_baseline_eligibility(self):
  pool,b,d=select_pool(self.posts,[0,60],1,0,1,1,0)
  self.assertEqual([x['id'] for x in pool],[i for i in range(1,60)])
 def test_recommendation_all60_and_rereads_allowed(self):
  pool,b,d=select_pool(self.posts,list(range(60)),1,0,1,1,1)
  self.assertEqual([x['id'] for x in pool],list(range(60)));self.assertEqual(b,'recommended_source')
 def test_source_unchanged(self):
  pool,b,d=select_pool(self.posts,[],0,0,1,1,1)
  self.assertEqual([x['id'] for x in pool],[60,61]);self.assertIsNone(d)
 def test_probability_and_reproducibility(self):
  values=[select_pool(self.posts,[],1,0,2026103000,c,.5) for c in range(1,1001)]
  share=sum(b=='recommended_source' for p,b,d in values)/1000
  self.assertTrue(.45<share<.55)
  self.assertEqual(values[0],select_pool(self.posts,[],1,0,2026103000,1,.5))
if __name__=='__main__':unittest.main()

class MetricTests(unittest.TestCase):
 def test_repeat_frequency_and_exposure_are_separate(self):
  from analyze import derive
  s=dict(source_agent=0,events=[dict(cycle=1,turn=0,agent=0,incoming=[],action='write',generated=dict(text='alpha',length_compliant=True)),dict(cycle=1,turn=1,agent=1,incoming=[dict(kind='post',agent=0,initial_material=True,text='alpha')],action='read',feed_branch='recommended_source',generated=None),dict(cycle=2,turn=1,agent=1,incoming=[],action='write',generated=dict(text='alpha alpha',length_compliant=True))])
  rows,intervals,words,doses=derive(s,'SYNTHETIC_TEST_ONLY','SYNTHETIC_TEST_ONLY');x=next(x for x in rows if x['group']=='nonseed')
  self.assertEqual(x['occurrences'],2);self.assertEqual(x['repeat_occurrences'],1);self.assertEqual(x['exposure_linked_first_users'],1);self.assertEqual(x['initial_entry_read_turns'],1)
