"""Only changed mechanism: pool selection for voluntary reads."""
import hashlib,random

def select_pool(posts,read_ids,agent,source,seed,cycle,p):
 assert 0<=p<=1
 ordinary=[x for x in posts if x['id'] not in read_ids and x['agent']!=agent]
 if agent==source:return ordinary,'source_baseline',None
 coin=random.Random(int(hashlib.sha256((str(seed)+f'/c{cycle}/a{agent}/recommendation_branch').encode()).hexdigest()[:8],16)).random()
 if coin<p:
  pool=[x for x in posts if x['initial_material'] and x['agent']!=agent]
  assert len(pool)==60
  return pool,'recommended_source',coin
 return ordinary,'ordinary_unread',coin
